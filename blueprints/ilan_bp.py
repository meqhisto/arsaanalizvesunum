# -*- coding: utf-8 -*-
"""İlan ekranları (/ilanlar): liste, oluştur/düzenle, detay, durum, sil (spec §5.2–5.4)."""
from itertools import zip_longest

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from models import db
from models.arsa_models import ArsaAnaliz
from models.crm_models import Contact, Deal
from models.ilan_models import GayrimenkulSahibi, Ilan, IlanGayrimenkul
from models.user_models import User
from modules import gayrimenkul_sabitleri as sabit
from modules import ilan_servis
from modules.ilan_hesap import sayi_metni, tutar_ayristir
from modules.ilan_servis import (IlanHatasi, gorunur_gayrimenkuller, gorunur_ilanlar, gorunur_kontaklar,
                                 gorunur_kullanici_idleri, ilan_or_404, ilan_ozeti)
from modules.rapor.model import tr_currency

ilan_bp = Blueprint('ilan', __name__)

ARSA_TURLERI = ('arsa', 'tarla')
EMSAL_FORM = (('konum', 'emsal_konum[]'), ('m2', 'emsal_m2[]'), ('fiyat', 'emsal_fiyat[]'),
              ('pay_yuzde', 'emsal_pay[]'), ('link', 'emsal_link[]'), ('notlar', 'emsal_not[]'))
SKALER_ALANLAR = ('baslik', 'aciklama', 'teklif_tipi', 'durum', 'sorumlu_user_id') + ilan_servis.TUM_TIP_ALANLARI


# ---------------------------------------------------------------- yardımcılar

def tur_etiketi(g):
    tur = g.tur or 'arsa'
    if g.alt_tur:
        return sabit.etiket(sabit.ALT_TURLER.get(tur, []), g.alt_tur)
    return sabit.etiket(sabit.TURLER, tur)


def fiyat_metni(i):
    if i.teklif_tipi == 'kiralik':
        return f"{tr_currency(i.kira)}/ay" if i.kira is not None else ''
    if i.teklif_tipi == 'kat_karsiligi':
        return f"%{sayi_metni(i.sahip_payi_yuzde)}" if i.sahip_payi_yuzde is not None else ''
    return tr_currency(i.fiyat) if i.fiyat is not None else ''


def kart_ozeti(i):
    """'Kat karşılığı · 4 parsel · 3.200 m² · %50' / 'Satılık · Daire · 3+1 · 4.250.000 TL'."""
    gler = i.gayrimenkuller
    parcalar = [sabit.etiket(sabit.TEKLIF_TIPLERI, i.teklif_tipi)]
    if len(gler) > 1:
        birim = 'parsel' if all((g.tur or 'arsa') in ARSA_TURLERI for g in gler) else 'gayrimenkul'
        parcalar.append(f"{len(gler)} {birim}")
        toplam = sum(float(g.metrekare or 0) for g in gler)
        if toplam:
            parcalar.append(f"{sayi_metni(toplam)} m²")
    elif gler:
        g = gler[0]
        parcalar.append(tur_etiketi(g))
        if (g.tur or 'arsa') not in ARSA_TURLERI and g.oda_sayisi:
            parcalar.append(g.oda_sayisi)
        elif g.metrekare is not None:
            parcalar.append(f"{sayi_metni(g.metrekare)} m²")
    fiyat = fiyat_metni(i)
    if fiyat:
        parcalar.append(fiyat)
    return ' · '.join(parcalar)


def gorunur_firsatlar(i, user):
    """İlana bağlı, kullanıcının görebildiği fırsatlar (sahibi; broker için ekibi; superadmin hepsi)."""
    sorgu = i.firsatlar
    idler = gorunur_kullanici_idleri(user)
    if idler is not None:
        sorgu = sorgu.filter(Deal.user_id.in_(idler))
    return sorgu.order_by(Deal.created_at.desc(), Deal.id.desc()).all()


def silebilir_mi(i, user):
    """Oluşturan, oluşturanın broker'ı (ekibi) ve superadmin; yalnız sorumlu olan silemez."""
    idler = gorunur_kullanici_idleri(user)
    return idler is None or i.user_id in idler


def _sorumlu_secenekleri(ilan=None):
    idler = gorunur_kullanici_idleri(current_user)
    sorgu = User.query.filter(User._is_active.is_(True))
    if idler is not None:
        sorgu = sorgu.filter(User.id.in_(idler))
    kullanicilar = sorgu.order_by(User.ad, User.email).all()
    if ilan is not None and ilan.sorumlu is not None and ilan.sorumlu not in kullanicilar:
        kullanicilar.append(ilan.sorumlu)
    return [(u.id, kullanici_adi(u)) for u in kullanicilar]


def kullanici_adi(u):
    if u is None:
        return ''
    ad = ' '.join(p for p in (u.ad, u.soyad) if p)
    return ad or u.email


def _sayi_yazi(deger):
    return sayi_metni(deger) if deger is not None else ''


def gayrimenkul_json(g):
    aktif = g.aktif_ilan
    return {'id': g.id, 'baslik': g.baslik_metni, 'ozet': g.ozet,
            'm2': float(g.metrekare) if g.metrekare is not None else None,
            'kaks': float(g.kaks) if g.kaks is not None else None,
            'aktif_ilan_kodu': aktif.kod if aktif is not None else None}


def _sahip_gayrimenkulleri(contact_id):
    return (gorunur_gayrimenkuller(current_user)
            .join(GayrimenkulSahibi, GayrimenkulSahibi.gayrimenkul_id == ArsaAnaliz.id)
            .filter(GayrimenkulSahibi.contact_id == contact_id)
            .order_by(ArsaAnaliz.id).all())


def _kontak(contact_id):
    try:
        cid = int(contact_id)
    except (TypeError, ValueError):
        return None
    return gorunur_kontaklar(current_user).filter(Contact.id == cid).first()


# ---------------------------------------------------------------- form verisi

def parsel_fiyatlari(form):
    """gayrimenkul id (metin) → parsel fiyatı. Her satırın fiyatı, yanındaki gizli parsel_gayrimenkul_id[]
    ile eşlenir; böylece işaretlenmeyen satırlar sırayı kaydırmaz. Gizli alan yoksa (eski istemci)
    parsel_fiyati[] seçili gayrimenkul_id[] sırasıyla eşlenir."""
    fiyatlar = form.getlist('parsel_fiyati[]')
    idler = form.getlist('parsel_gayrimenkul_id[]') or form.getlist('gayrimenkul_id[]')
    return {gid: fiyat for gid, fiyat in zip(idler, fiyatlar)}


def formdan_veri(form):
    """POST formu → ilan_servis.ilan_kaydet veri sözlüğü."""
    veri = {alan: form.get(alan) for alan in SKALER_ALANLAR}
    veri['ana_gayrimenkul_id'] = form.get('ana_gayrimenkul_id')
    fiyatlar = parsel_fiyatlari(form)
    veri['gayrimenkuller'] = [{'id': gid, 'parsel_fiyati': fiyatlar.get(gid)}
                              for gid in form.getlist('gayrimenkul_id[]')]
    listeler = [form.getlist(ad) for _, ad in EMSAL_FORM]
    veri['emsaller'] = [dict(zip((k for k, _ in EMSAL_FORM), satir))
                        for satir in zip_longest(*listeler, fillvalue='')]
    return veri


def _ilandan_v(i):
    v = {'baslik': i.baslik or '', 'aciklama': i.aciklama or '', 'teklif_tipi': i.teklif_tipi,
         'durum': i.durum, 'sorumlu_user_id': str(i.sorumlu_user_id or '')}
    for alan in ilan_servis.TUM_TIP_ALANLARI:
        deger = getattr(i, alan)
        if alan in ilan_servis.SAYISAL_ALANLAR or alan in ilan_servis.TAMSAYI_ALANLAR:
            v[alan] = _sayi_yazi(deger)
        else:
            v[alan] = deger or ''
    return v


def _satir(g, secili=False, ana=False, parsel_fiyati=''):
    d = gayrimenkul_json(g)
    d.update(secili=secili, ana=ana, parsel_fiyati=parsel_fiyati)
    return d


def _form_sayfasi(ilan, v, gm_satirlari, emsal_satirlari, sahip=None, hata=None, durum_kodu=200):
    sahipler = [sahip] if sahip else []
    baslik = f"{ilan.kod} düzenle" if ilan is not None else 'Yeni ilan'
    return render_template('ilan/form.html', ilan=ilan, v=v, gm_satirlari=gm_satirlari,
                           emsal_satirlari=emsal_satirlari, sahipler=sahipler, sahip=sahip, hata=hata,
                           sorumlular=_sorumlu_secenekleri(ilan), sabit=sabit, title=baslik), durum_kodu


def _sahip_satiri(c):
    return {'id': c.id, 'ad': f"{c.first_name} {c.last_name}".strip(), 'telefon': c.phone or '',
            'hisse': '', 'irtibat': False, 'salt_okunur': False}


def _post_form_sayfasi(ilan, hata):
    """Hatalı POST'ta girilen değerlerle formu yeniden çizer."""
    f = request.form
    v = {alan: f.get(alan, '') for alan in SKALER_ALANLAR}
    secili = [s for s in f.getlist('gayrimenkul_id[]')]
    fiyatlar = parsel_fiyatlari(f)
    ana = f.get('ana_gayrimenkul_id', '')
    sahip = _kontak(f.get('sahip'))
    idler = []
    for s in secili + [str(x) for x in f.getlist('gosterilen_gayrimenkul[]')]:
        if s.isdigit() and int(s) not in idler:
            idler.append(int(s))
    bulunan = {g.id: g for g in gorunur_gayrimenkuller(current_user).filter(ArsaAnaliz.id.in_(idler))} \
        if idler else {}
    if ilan is not None:
        bulunan.update({g.id: g for g in ilan.gayrimenkuller if g.id in idler})
    satirlar = [_satir(bulunan[gid], str(gid) in secili, str(gid) == ana, fiyatlar.get(str(gid)) or '')
                for gid in idler if gid in bulunan]
    emsaller = [e for e in formdan_veri(f)['emsaller'] if any((x or '').strip() for x in e.values())]
    return _form_sayfasi(ilan, v, satirlar, emsaller, _sahip_satiri(sahip) if sahip else None, hata)


# ---------------------------------------------------------------- liste

@ilan_bp.route('/')
@login_required
def liste():
    f = {k: (request.args.get(k) or '').strip()
         for k in ('teklif_tipi', 'durum', 'tur', 'fiyat_min', 'fiyat_max', 'sorumlu')}
    temel = gorunur_ilanlar(current_user)
    sorgu = temel
    if f['teklif_tipi'] in dict(sabit.TEKLIF_TIPLERI):
        sorgu = sorgu.filter(Ilan.teklif_tipi == f['teklif_tipi'])
    else:
        f['teklif_tipi'] = ''
    if f['durum'] in dict(sabit.DURUMLAR):
        sorgu = sorgu.filter(Ilan.durum == f['durum'])
    else:
        f['durum'] = ''
    if f['tur'] in dict(sabit.TURLER):
        sorgu = sorgu.filter(Ilan.baglar.any(and_(IlanGayrimenkul.ana_kayit.is_(True),
                                                  IlanGayrimenkul.gayrimenkul.has(ArsaAnaliz.tur == f['tur']))))
    else:
        f['tur'] = ''
    alt, ust = tutar_ayristir(f['fiyat_min']), tutar_ayristir(f['fiyat_max'])
    if alt is None:
        f['fiyat_min'] = ''
    if ust is None:
        f['fiyat_max'] = ''
    if alt is not None or ust is not None:
        def aralik(sutun):
            kosul = [sutun.isnot(None)]
            if alt is not None:
                kosul.append(sutun >= alt)
            if ust is not None:
                kosul.append(sutun <= ust)
            return and_(*kosul)
        sorgu = sorgu.filter(or_(and_(Ilan.teklif_tipi == 'satilik', aralik(Ilan.fiyat)),
                                 and_(Ilan.teklif_tipi == 'kiralik', aralik(Ilan.kira))))
    if f['sorumlu'].isdigit():
        sorgu = sorgu.filter(Ilan.sorumlu_user_id == int(f['sorumlu']))
    else:
        f['sorumlu'] = ''
    ilanlar = (sorgu.options(selectinload(Ilan.baglar).selectinload(IlanGayrimenkul.gayrimenkul),
                             selectinload(Ilan.sorumlu))
               .order_by(Ilan.created_at.desc(), Ilan.id.desc()).all())
    sorumlu_idleri = [uid for (uid,) in temel.with_entities(Ilan.sorumlu_user_id).distinct() if uid]
    sorumlular = [(u.id, kullanici_adi(u)) for u in
                  User.query.filter(User.id.in_(sorumlu_idleri)).order_by(User.ad, User.email)] \
        if sorumlu_idleri else []
    return render_template('ilan/liste.html', ilanlar=ilanlar, f=f, sorumlular=sorumlular, sabit=sabit,
                           kart_ozeti=kart_ozeti, kullanici_adi=kullanici_adi, title='İlanlar')


# ---------------------------------------------------------------- sahip gayrimenkulleri

@ilan_bp.route('/sahip/<int:contact_id>/gayrimenkuller')
@login_required
def sahip_gayrimenkulleri(contact_id):
    if _kontak(contact_id) is None:
        abort(404)
    return jsonify([gayrimenkul_json(g) for g in _sahip_gayrimenkulleri(contact_id)])


# ---------------------------------------------------------------- oluştur / düzenle

def _kaydet_ve_yonlendir(ilan):
    """ilan None → oluştur. Kod yarışında (benzersiz kod ihlali) bir kez yeni kodla dener."""
    veri = formdan_veri(request.form)
    for deneme in range(2):
        try:
            kaydedilen = ilan_servis.ilan_kaydet(ilan, current_user, veri)
            db.session.commit()
        except IlanHatasi as e:
            db.session.rollback()
            return _post_form_sayfasi(ilan, str(e))
        except IntegrityError as e:
            db.session.rollback()
            if ilan is None and deneme == 0 and _kod_ihlali_mi(e):
                continue
            raise
        flash(f"{kaydedilen.kod} kaydedildi.", 'success')
        return redirect(url_for('ilan.detay', ilan_id=kaydedilen.id))


def _kod_ihlali_mi(hata):
    diag = getattr(getattr(hata, 'orig', None), 'diag', None)
    kisit = getattr(diag, 'constraint_name', None) or str(getattr(hata, 'orig', hata))
    return 'kod' in kisit


@ilan_bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    if request.method == 'POST':
        return _kaydet_ve_yonlendir(None)
    sahip = _kontak(request.args.get('sahip')) if request.args.get('sahip') else None
    secili_idler = [int(x) for x in request.args.getlist('gayrimenkul') if x.isdigit()]
    secililer = (gorunur_gayrimenkuller(current_user).filter(ArsaAnaliz.id.in_(secili_idler))
                 .order_by(ArsaAnaliz.id).all()) if secili_idler else []
    sahibinkiler = _sahip_gayrimenkulleri(sahip.id) if sahip else []
    if sahip is None and secililer:
        # Ön seçilen gayrimenkulün (görünen) ilk sahibini adım 1'e yerleştir
        for g in secililer:
            for s in sorted(g.sahiplikler, key=lambda s: (not s.irtibat, s.id)):
                sahip = _kontak(s.contact_id)
                if sahip:
                    break
            if sahip:
                break
        sahibinkiler = _sahip_gayrimenkulleri(sahip.id) if sahip else []
    ana_id = secililer[0].id if secililer else None
    satirlar = [_satir(g, True, g.id == ana_id) for g in secililer]
    satirlar += [_satir(g) for g in sahibinkiler if g.id not in {s['id'] for s in satirlar}]
    v = {'teklif_tipi': 'satilik', 'durum': 'hazirlaniyor', 'sorumlu_user_id': str(current_user.id)}
    return _form_sayfasi(None, v, satirlar, [], _sahip_satiri(sahip) if sahip else None)


@ilan_bp.route('/<int:ilan_id>/duzenle', methods=['GET', 'POST'])
@login_required
def duzenle(ilan_id):
    i = ilan_or_404(ilan_id, current_user)
    if request.method == 'POST':
        return _kaydet_ve_yonlendir(i)
    satirlar = [_satir(b.gayrimenkul, True, b.ana_kayit, _sayi_yazi(b.parsel_fiyati)) for b in i.baglar]
    sahip = None
    ana = i.ana_gayrimenkul
    if ana is not None:
        for s in sorted(ana.sahiplikler, key=lambda s: (not s.irtibat, s.id)):
            sahip = _kontak(s.contact_id)
            if sahip:
                break
    if sahip is not None:
        mevcut = {s['id'] for s in satirlar}
        satirlar += [_satir(g) for g in _sahip_gayrimenkulleri(sahip.id) if g.id not in mevcut]
    emsaller = [{'konum': e.konum or '', 'm2': _sayi_yazi(e.m2), 'fiyat': _sayi_yazi(e.fiyat),
                 'pay_yuzde': _sayi_yazi(e.pay_yuzde), 'link': e.link or '', 'notlar': e.notlar or ''}
                for e in i.emsaller]
    return _form_sayfasi(i, _ilandan_v(i), satirlar, emsaller, _sahip_satiri(sahip) if sahip else None)


# ---------------------------------------------------------------- detay

@ilan_bp.route('/<int:ilan_id>')
@login_required
def detay(ilan_id):
    i = ilan_or_404(ilan_id, current_user)
    oz = ilan_ozeti(i)
    gorunur_gm = {gid for (gid,) in gorunur_gayrimenkuller(current_user)
                  .filter(ArsaAnaliz.id.in_([g.id for g in i.gayrimenkuller])).with_entities(ArsaAnaliz.id)}
    # Sahipler (ofis içi): tüm gayrimenkullerin sahipleri, kişi başına bir kez
    sahipler, gorulen = [], set()
    for g in i.gayrimenkuller:
        for s in sorted(g.sahiplikler, key=lambda s: (not s.irtibat, s.id)):
            if s.contact_id not in gorulen:
                gorulen.add(s.contact_id)
                sahipler.append(s)
    gorunur_kontak = {cid for (cid,) in gorunur_kontaklar(current_user)
                      .filter(Contact.id.in_(gorulen)).with_entities(Contact.id)} if gorulen else set()
    firsatlar = gorunur_firsatlar(i, current_user)
    return render_template('ilan/detay.html', i=i, oz=oz, gorunur_gm=gorunur_gm, sahipler=sahipler,
                           gorunur_kontak=gorunur_kontak, firsatlar=firsatlar, sabit=sabit,
                           kart_ozeti=kart_ozeti(i), fiyat_metni=fiyat_metni, tur_etiketi=tur_etiketi,
                           kullanici_adi=kullanici_adi, silebilir=silebilir_mi(i, current_user),
                           title=i.kod)


# ---------------------------------------------------------------- durum / sil

@ilan_bp.route('/<int:ilan_id>/durum', methods=['POST'])
@login_required
def durum(ilan_id):
    i = ilan_or_404(ilan_id, current_user)
    yeni_durum = request.form.get('durum')
    if yeni_durum not in dict(sabit.DURUMLAR):
        flash('Geçersiz ilan durumu.', 'danger')
        return redirect(url_for('ilan.detay', ilan_id=i.id))
    if yeni_durum in sabit.AKTIF_DURUMLAR:
        for g in i.gayrimenkuller:
            cakisan = ilan_servis.cakisan_ilan(g.id, i.id)
            if cakisan is not None:
                flash(f"{g.baslik_metni} zaten {cakisan.kod} numaralı aktif ilanda; durum değiştirilmedi.",
                      'danger')
                return redirect(url_for('ilan.detay', ilan_id=i.id))
    i.durum = yeni_durum
    db.session.commit()
    flash(f"Durum: {sabit.etiket(sabit.DURUMLAR, yeni_durum)}.", 'success')
    return redirect(url_for('ilan.detay', ilan_id=i.id))


@ilan_bp.route('/<int:ilan_id>/sil', methods=['POST'])
@login_required
def sil(ilan_id):
    i = ilan_or_404(ilan_id, current_user)
    if not silebilir_mi(i, current_user):
        abort(403)
    kod = i.kod
    # Fırsat bağı kalkar (ilan_id NULL); portföy bağları ve emsaller ilanla birlikte silinir,
    # gayrimenkuller kalır.
    Deal.query.filter(Deal.ilan_id == i.id).update({Deal.ilan_id: None}, synchronize_session='fetch')
    i.portfoyler = []
    db.session.delete(i)
    db.session.commit()
    flash(f"{kod} silindi. Gayrimenkuller kayıtlı kalır.", 'success')
    return redirect(url_for('ilan.liste'))

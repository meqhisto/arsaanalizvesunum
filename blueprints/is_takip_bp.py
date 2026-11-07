# -*- coding: utf-8 -*-
"""İş takip modülü rotaları (/isler)."""
import io
import os
import re
import uuid
import mimetypes
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import (Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify,
                   send_file, current_app)
from flask_login import login_required, current_user

from sqlalchemy.orm import selectinload

from models import db
from models.user_models import User, Portfolio
from models.crm_models import Task, Contact, Deal
from models.arsa_models import ArsaAnaliz
from models.is_takip_models import (
    Is, IsSablonu, IsSablonAdimi, IsBelgesi, IsMasrafi, IsAktivitesi, Bildirim,
    IS_DURUMLARI, IS_ACIK_DURUMLAR, IS_ONCELIKLERI, IS_TURLERI, BELGE_TURLERI, MASRAF_KALEMLERI,
    ODEME_DURUMLARI, GOREV_TAMAMLANDI, GOREV_IPTAL,
)
from modules import is_takip_servis as servis

is_takip_bp = Blueprint('is_takip', __name__, template_folder='../templates')

IZINLI_UZANTILAR = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'zip'}
PANO_DURUMLARI = ['Açık', 'Devam ediyor', 'Beklemede', 'Tamamlandı']


# ---------------------------------------------------------------- yardımcılar
def _belge_klasoru():
    """Belgeler static dışında, doğrudan URL ile erişilemeyen bir klasörde tutulur."""
    kok = current_app.config.get('IS_BELGE_KLASORU') or os.environ.get('IS_BELGE_KLASORU') \
        or os.path.join(current_app.root_path, 'private_uploads', 'isler')
    os.makedirs(kok, exist_ok=True)
    return kok


def _is_or_404(is_id, yonetim=False):
    is_kaydi = db.session.get(Is, is_id)
    if not is_kaydi or not servis.gorebilir(current_user, is_kaydi):
        abort(404)
    if yonetim and not servis.yonetebilir(current_user, is_kaydi):
        abort(403)
    return is_kaydi


def _adim_or_404(is_kaydi, task_id):
    adim = Task.query.filter_by(id=task_id, is_id=is_kaydi.id).first()
    if not adim:
        abort(404)
    return adim


def _tarih(deger):
    try:
        return datetime.strptime(deger, '%Y-%m-%d').date() if deger else None
    except ValueError:
        return None


def _tutar(deger):
    try:
        metin = (deger or '').strip().replace(' ', '').replace('TL', '').replace('₺', '')
        if ',' in metin:  # Türkçe biçim: 1.250,50
            metin = metin.replace('.', '').replace(',', '.')
        elif re.fullmatch(r'\d{1,3}(\.\d{3})+', metin):  # 25.000 / 1.250.000 -> binlik ayırıcı
            metin = metin.replace('.', '')
        sayi = Decimal(metin)
        return sayi if sayi >= 0 else None
    except (InvalidOperation, AttributeError):
        return None


def _int_or_none(deger):
    try:
        return int(deger) if deger not in (None, '') else None
    except (TypeError, ValueError):
        return None


def _sorumlu_gecerli(user_id):
    return user_id in {u.id for u in servis.atanabilir_kullanicilar(current_user)}


def _gorunur_sablonlar():
    q = IsSablonu.query.filter(IsSablonu.aktif.is_(True))
    if current_user.role != 'superadmin':
        q = q.filter(db.or_(IsSablonu.office_id.is_(None), IsSablonu.office_id == current_user.office_id))
    return q.order_by(IsSablonu.ad).all()


def _baglanti_secenekleri():
    """Yeni iş / düzenleme formundaki müşteri, fırsat, analiz, portföy listeleri (kullanıcının kendi kayıtları)."""
    uid = current_user.id
    return {
        'contacts': Contact.query.filter_by(user_id=uid).order_by(Contact.first_name).limit(500).all(),
        'deals': Deal.query.filter_by(user_id=uid).order_by(Deal.created_at.desc()).limit(500).all(),
        'analizler': ArsaAnaliz.query.filter_by(user_id=uid).order_by(ArsaAnaliz.created_at.desc()).limit(500).all(),
        'portfoyler': Portfolio.query.filter_by(user_id=uid).order_by(Portfolio.created_at.desc()).all(),
    }


def _sahiplik_dogrula(model, kayit_id):
    """Formdan gelen bağlantı ID'si kullanıcıya ait değilse yok sayılır."""
    if not kayit_id:
        return None
    kayit = db.session.get(model, kayit_id)
    if not kayit:
        return None
    if current_user.role != 'superadmin' and getattr(kayit, 'user_id', None) != current_user.id:
        return None
    return kayit.id


def _filtreli_isler():
    q = servis.gorunur_isler(current_user)
    f = {k: request.args.get(k, '').strip() for k in ('q', 'tur', 'sorumlu', 'oncelik', 'durum', 'geciken')}
    if f['q']:
        like = f"%{f['q']}%"
        q = q.filter(db.or_(Is.baslik.ilike(like), Is.kod.ilike(like), Is.aciklama.ilike(like)))
    if f['tur']:
        q = q.filter(Is.is_turu == f['tur'])
    if f['oncelik']:
        q = q.filter(Is.oncelik == f['oncelik'])
    if f['durum']:
        q = q.filter(Is.durum == f['durum'])
    if f['sorumlu'].isdigit():
        q = q.filter(Is.sorumlu_user_id == int(f['sorumlu']))
    if f['geciken']:
        q = q.filter(Is.durum.in_(IS_ACIK_DURUMLAR), db.exists().where(db.and_(
            Task.is_id == Is.id, Task.status.notin_([GOREV_TAMAMLANDI, GOREV_IPTAL]),
            Task.due_date < datetime.utcnow())))
    return q, f


# ---------------------------------------------------------------- pano / liste
@is_takip_bp.route('/')
@login_required
def pano():
    q, filtre = _filtreli_isler()
    gorunum = request.args.get('gorunum', 'pano')
    isler = q.options(selectinload(Is.contact), selectinload(Is.sorumlu)).order_by(Is.updated_at.desc()).all()
    # Tüm işlerin adımları tek sorguda (iş başına ayrı sorgu yerine)
    adim_gruplari = {i.id: [] for i in isler}
    if isler:
        for adim in Task.query.filter(Task.is_id.in_(list(adim_gruplari))):
            adim_gruplari[adim.is_id].append(adim)
    ozetler = {i.id: i.adim_ozeti(adim_gruplari[i.id]) for i in isler}
    sutunlar = {d: [i for i in isler if i.durum == d] for d in PANO_DURUMLARI}
    return render_template('is_takip/pano.html', isler=isler, sutunlar=sutunlar, ozetler=ozetler,
                           filtre=filtre, gorunum=gorunum, durumlar=IS_DURUMLARI, pano_durumlari=PANO_DURUMLARI,
                           turler=IS_TURLERI, oncelikler=IS_ONCELIKLERI,
                           kullanicilar=servis.atanabilir_kullanicilar(current_user),
                           yonetici=servis.yonetici_mi(current_user),
                           iptal_sayisi=sum(1 for i in isler if i.durum == 'İptal'))


@is_takip_bp.route('/excel')
@login_required
def excel():
    from openpyxl import Workbook
    from openpyxl.styles import Font
    q, _ = _filtreli_isler()
    wb = Workbook()
    ws = wb.active
    ws.title = 'İşler'
    basliklar = ['Kod', 'Başlık', 'Tür', 'Durum', 'Öncelik', 'Sorumlu', 'Müşteri', 'Başlangıç', 'Hedef bitiş',
                 'Adım (tamam/toplam)', 'Geciken adım', 'Toplam masraf (TL)']
    ws.append(basliklar)
    for h in ws[1]:
        h.font = Font(bold=True)
    for i in q.order_by(Is.kod).all():
        o, m = i.adim_ozeti(), i.masraf_ozeti()
        ws.append([i.kod, i.baslik, i.is_turu, i.durum, i.oncelik, servis.kullanici_adi(i.sorumlu),
                   f"{i.contact.first_name} {i.contact.last_name}" if i.contact else '',
                   i.baslangic_tarihi, i.hedef_bitis_tarihi, f"{o['tamam']}/{o['toplam']}", o['geciken'],
                   round(m['toplam'], 2)])
    for col, w in zip('ABCDEFGHIJKL', [14, 40, 16, 14, 10, 22, 22, 12, 12, 14, 12, 16]):
        ws.column_dimensions[col].width = w
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"isler_{date.today():%Y%m%d}.xlsx",
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ---------------------------------------------------------------- yeni iş
@is_takip_bp.route('/yeni', methods=['GET', 'POST'])
@login_required
def yeni():
    sablonlar = _gorunur_sablonlar()
    kullanicilar = servis.atanabilir_kullanicilar(current_user)
    sablon_bilgisi = {
        'sablon_adimlari': {s.id: [{'baslik': a.baslik, 'gun': a.varsayilan_sure_gun, 'belge': a.gerekli_belge_turu}
                                   for a in s.adimlar] for s in sablonlar},
        'sablon_turleri': {s.id: s.is_turu for s in sablonlar},
    }
    if request.method == 'POST':
        f = request.form
        baslik = (f.get('baslik') or '').strip()
        sorumlu_id = _int_or_none(f.get('sorumlu_user_id')) or current_user.id
        hatalar = []
        if not baslik:
            hatalar.append('İş başlığı zorunludur.')
        if not _sorumlu_gecerli(sorumlu_id):
            hatalar.append('Seçilen sorumlu kişiye iş atama yetkiniz yok.')
        sablon = None
        sablon_id = _int_or_none(f.get('sablon_id'))
        if sablon_id:
            sablon = next((s for s in sablonlar if s.id == sablon_id), None)
        # Önizlemede düzenlenmiş adımlar
        adimlar = []
        for i, (b, t, s) in enumerate(zip(f.getlist('adim_baslik'), f.getlist('adim_tarih'),
                                          f.getlist('adim_sorumlu'))):
            if not b.strip():
                continue
            adim_sorumlu = _int_or_none(s) or sorumlu_id
            if not _sorumlu_gecerli(adim_sorumlu):
                adim_sorumlu = sorumlu_id
            adimlar.append({'baslik': b.strip(), 'son_tarih': _tarih(t), 'sorumlu_id': adim_sorumlu})
        if hatalar:
            for h in hatalar:
                flash(h, 'danger')
            return render_template('is_takip/yeni.html', sablonlar=sablonlar, kullanicilar=kullanicilar,
                                   form=f, turler=IS_TURLERI, oncelikler=IS_ONCELIKLERI,
                                   **sablon_bilgisi, **_baglanti_secenekleri()), 400
        is_kaydi = servis.is_olustur(
            current_user, baslik, f.get('is_turu') if f.get('is_turu') in IS_TURLERI else 'Diğer', sorumlu_id,
            baslangic=_tarih(f.get('baslangic_tarihi')) or date.today(), sablon=sablon,
            adimlar=adimlar if (adimlar or not sablon) else None,
            oncelik=f.get('oncelik') if f.get('oncelik') in IS_ONCELIKLERI else 'Normal',
            aciklama=(f.get('aciklama') or '').strip(),
            contact_id=_sahiplik_dogrula(Contact, _int_or_none(f.get('contact_id'))),
            deal_id=_sahiplik_dogrula(Deal, _int_or_none(f.get('deal_id'))),
            analiz_id=_sahiplik_dogrula(ArsaAnaliz, _int_or_none(f.get('analiz_id'))),
            portfolio_id=_sahiplik_dogrula(Portfolio, _int_or_none(f.get('portfolio_id'))),
            butce=_tutar(f.get('butce')), hedef_bitis=_tarih(f.get('hedef_bitis_tarihi')))
        db.session.commit()
        flash(f'{is_kaydi.kod} numaralı iş oluşturuldu.', 'success')
        return redirect(url_for('is_takip.detay', is_id=is_kaydi.id))

    # GET: analiz / müşteri / fırsat sayfasından "İş başlat" ile gelinmiş olabilir
    form = {k: request.args.get(k, '') for k in ('contact_id', 'deal_id', 'analiz_id', 'portfolio_id', 'is_turu', 'baslik')}
    analiz = db.session.get(ArsaAnaliz, _int_or_none(form['analiz_id']) or 0)
    if analiz and not form['baslik']:
        form['baslik'] = f"{analiz.mahalle} {analiz.ada or ''}/{analiz.parsel or ''} – {analiz.il}/{analiz.ilce}".strip()
    form.setdefault('sorumlu_user_id', str(current_user.id))
    form['baslangic_tarihi'] = date.today().isoformat()
    return render_template('is_takip/yeni.html', sablonlar=sablonlar, kullanicilar=kullanicilar, form=form,
                           turler=IS_TURLERI, oncelikler=IS_ONCELIKLERI, **sablon_bilgisi,
                           **_baglanti_secenekleri())


# ---------------------------------------------------------------- detay ve iş güncelleme
@is_takip_bp.route('/<int:is_id>')
@login_required
def detay(is_id):
    is_kaydi = _is_or_404(is_id)
    adimlar = is_kaydi.adimlar.options(selectinload(Task.assigned_user)).order_by(Task.sira, Task.id).all()
    yonetici = servis.yonetebilir(current_user, is_kaydi)
    belgeler = is_kaydi.belgeler.options(selectinload(IsBelgesi.yukleyen)).all()
    return render_template(
        'is_takip/detay.html', is_kaydi=is_kaydi, adimlar=adimlar, ozet=is_kaydi.adim_ozeti(),
        masraf=is_kaydi.masraf_ozeti(), belgeler=belgeler, masraflar=is_kaydi.masraflar.all(),
        aktiviteler=is_kaydi.aktiviteler.options(selectinload(IsAktivitesi.user)).limit(100).all(), yonetici=yonetici,
        kullanicilar=servis.atanabilir_kullanicilar(current_user) if yonetici else [],
        durumlar=IS_DURUMLARI, oncelikler=IS_ONCELIKLERI, turler=IS_TURLERI, belge_turleri=BELGE_TURLERI,
        masraf_kalemleri=MASRAF_KALEMLERI, odeme_durumlari=ODEME_DURUMLARI,
        simdi=datetime.utcnow(), bugun=date.today(), GOREV_TAMAMLANDI=GOREV_TAMAMLANDI,
        # yonetici bir kez hesaplandı; adım başına yetki sorgusu atma
        adimi_guncelleyebilir=lambda a: yonetici or a.assigned_to_user_id == current_user.id,
        kullanici_adi=servis.kullanici_adi, aktif_sekme=request.args.get('sekme', 'adimlar'),
        **(_baglanti_secenekleri() if yonetici else {}))


@is_takip_bp.route('/<int:is_id>/guncelle', methods=['POST'])
@login_required
def guncelle(is_id):
    is_kaydi = _is_or_404(is_id, yonetim=True)
    f = request.form
    degisiklik = []
    baslik = (f.get('baslik') or '').strip()
    if baslik and baslik != is_kaydi.baslik:
        is_kaydi.baslik = baslik[:200]
        degisiklik.append('başlık')
    for alan, liste in (('is_turu', IS_TURLERI), ('oncelik', IS_ONCELIKLERI)):
        deger = f.get(alan)
        if deger in liste and deger != getattr(is_kaydi, alan):
            setattr(is_kaydi, alan, deger)
            degisiklik.append({'is_turu': 'tür', 'oncelik': 'öncelik'}[alan])
    if f.get('durum') in IS_DURUMLARI:
        servis.is_durumu_degistir(is_kaydi, current_user, f['durum'])
    sorumlu_id = _int_or_none(f.get('sorumlu_user_id'))
    if sorumlu_id and sorumlu_id != is_kaydi.sorumlu_user_id:
        if _sorumlu_gecerli(sorumlu_id):
            eski = servis.kullanici_adi(is_kaydi.sorumlu)
            is_kaydi.sorumlu_user_id = sorumlu_id
            yeni_sorumlu = db.session.get(User, sorumlu_id)
            servis.aktivite(is_kaydi, current_user, 'sorumlu_degisti',
                            f"Sorumlu: {eski} → {servis.kullanici_adi(yeni_sorumlu)}")
            servis.bildirim(sorumlu_id, 'atandi', f"{is_kaydi.kod} – {is_kaydi.baslik} işinin sorumlusu olarak atandınız.",
                            is_kaydi=is_kaydi, url=servis.is_url(is_kaydi))
        else:
            flash('Seçilen kişiye iş atama yetkiniz yok.', 'warning')
    for alan in ('baslangic_tarihi', 'hedef_bitis_tarihi'):
        if alan in f:
            setattr(is_kaydi, alan, _tarih(f.get(alan)))
    if 'aciklama' in f:
        is_kaydi.aciklama = f.get('aciklama', '').strip()
    if 'butce' in f:
        is_kaydi.butce = _tutar(f.get('butce'))
    if 'contact_id' in f:
        for alan, model in (('contact_id', Contact), ('deal_id', Deal), ('analiz_id', ArsaAnaliz),
                            ('portfolio_id', Portfolio)):
            yeni_id = _int_or_none(f.get(alan))
            # Mevcut bağlantı (başka kullanıcının kaydı olsa da) korunur; yeni seçimde sahiplik kontrol edilir
            if yeni_id != getattr(is_kaydi, alan):
                setattr(is_kaydi, alan, _sahiplik_dogrula(model, yeni_id))
    if degisiklik:
        servis.aktivite(is_kaydi, current_user, 'guncellendi', 'Güncellendi: ' + ', '.join(degisiklik))
    db.session.commit()
    flash('İş güncellendi.', 'success')
    return redirect(url_for('is_takip.detay', is_id=is_kaydi.id))


@is_takip_bp.route('/<int:is_id>/durum', methods=['POST'])
@login_required
def durum(is_id):
    """Panoda sürükle-bırak ile durum değişikliği (JSON)."""
    is_kaydi = db.session.get(Is, is_id)
    if not is_kaydi or not servis.gorebilir(current_user, is_kaydi):
        return jsonify({'ok': False, 'hata': 'İş bulunamadı.'}), 404
    if not servis.yonetebilir(current_user, is_kaydi):
        return jsonify({'ok': False, 'hata': 'Bu işin durumunu değiştirme yetkiniz yok.'}), 403
    yeni_durum = (request.get_json(silent=True) or request.form).get('durum')
    if yeni_durum not in IS_DURUMLARI:
        return jsonify({'ok': False, 'hata': 'Geçersiz durum.'}), 400
    servis.is_durumu_degistir(is_kaydi, current_user, yeni_durum)
    db.session.commit()
    return jsonify({'ok': True, 'durum': is_kaydi.durum})


@is_takip_bp.route('/<int:is_id>/sil', methods=['POST'])
@login_required
def sil(is_id):
    is_kaydi = _is_or_404(is_id, yonetim=True)
    if not (servis.yonetici_mi(current_user) or is_kaydi.olusturan_user_id == current_user.id):
        abort(403)
    for b in is_kaydi.belgeler.all():
        _dosyayi_sil(b)
    Task.query.filter_by(is_id=is_kaydi.id).delete(synchronize_session=False)
    Bildirim.query.filter_by(is_id=is_kaydi.id).delete(synchronize_session=False)
    kod = is_kaydi.kod
    db.session.delete(is_kaydi)
    db.session.commit()
    flash(f'{kod} numaralı iş silindi.', 'success')
    return redirect(url_for('is_takip.pano'))


@is_takip_bp.route('/<int:is_id>/not', methods=['POST'])
@login_required
def not_ekle(is_id):
    is_kaydi = _is_or_404(is_id)
    metin = (request.form.get('not') or '').strip()
    if metin:
        servis.aktivite(is_kaydi, current_user, 'not', metin[:2000])
        db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id, sekme='aktivite'))


# ---------------------------------------------------------------- adımlar
@is_takip_bp.route('/<int:is_id>/adim/ekle', methods=['POST'])
@login_required
def adim_ekle(is_id):
    is_kaydi = _is_or_404(is_id, yonetim=True)
    baslik = (request.form.get('baslik') or '').strip()
    if not baslik:
        flash('Adım başlığı zorunludur.', 'danger')
        return redirect(url_for('is_takip.detay', is_id=is_id))
    sorumlu_id = _int_or_none(request.form.get('sorumlu_user_id')) or is_kaydi.sorumlu_user_id
    if not _sorumlu_gecerli(sorumlu_id):
        sorumlu_id = is_kaydi.sorumlu_user_id
    servis.adim_ekle(is_kaydi, current_user, baslik, _tarih(request.form.get('son_tarih')), sorumlu_id,
                     aciklama=(request.form.get('aciklama') or '').strip())
    db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id))


@is_takip_bp.route('/<int:is_id>/adim/<int:task_id>/tamamla', methods=['POST'])
@login_required
def adim_tamamla(is_id, task_id):
    is_kaydi = _is_or_404(is_id)
    adim = _adim_or_404(is_kaydi, task_id)
    if not servis.adimi_guncelleyebilir(current_user, is_kaydi, adim):
        abort(403)
    tamamla = adim.status != GOREV_TAMAMLANDI
    servis.adim_durumunu_degistir(is_kaydi, adim, current_user, tamamla)
    db.session.commit()
    if tamamla:
        eksik = servis.eksik_belge_uyarisi(is_kaydi, adim)
        if eksik:
            flash(f'"{adim.title}" adımı için şablonda "{eksik}" belgesi bekleniyor; henüz yüklenmedi.', 'warning')
        ozet = is_kaydi.adim_ozeti()
        if ozet['toplam'] and ozet['tamam'] == ozet['toplam'] and is_kaydi.durum != 'Tamamlandı':
            flash('Tüm adımlar tamamlandı. İşi "Tamamlandı" durumuna alabilirsiniz.', 'info')
    if request.headers.get('X-Requested-With') == 'fetch':
        return jsonify({'ok': True, 'tamamlandi': tamamla, 'ozet': {k: v for k, v in is_kaydi.adim_ozeti().items() if k != 'siradaki'}})
    return redirect(url_for('is_takip.detay', is_id=is_id))


@is_takip_bp.route('/<int:is_id>/adim/<int:task_id>/guncelle', methods=['POST'])
@login_required
def adim_guncelle(is_id, task_id):
    is_kaydi = _is_or_404(is_id)
    adim = _adim_or_404(is_kaydi, task_id)
    yonetici = servis.yonetebilir(current_user, is_kaydi)
    if not servis.adimi_guncelleyebilir(current_user, is_kaydi, adim):
        abort(403)
    f = request.form
    if yonetici:
        baslik = (f.get('baslik') or '').strip()
        if baslik:
            adim.title = baslik[:200]
        sorumlu_id = _int_or_none(f.get('sorumlu_user_id'))
        if sorumlu_id and sorumlu_id != adim.assigned_to_user_id and _sorumlu_gecerli(sorumlu_id):
            adim.previous_assignee_id = adim.assigned_to_user_id
            adim.assigned_to_user_id = sorumlu_id
            adim.reassigned_at = datetime.utcnow()
            adim.reassigned_by_id = current_user.id
            servis.bildirim(sorumlu_id, 'atandi', f"{is_kaydi.kod}: \"{adim.title}\" adımı size atandı.",
                            is_kaydi=is_kaydi, task=adim, url=servis.is_url(is_kaydi))
    if 'son_tarih' in f:
        yeni = _tarih(f.get('son_tarih'))
        adim.due_date = servis.gun_sonu(yeni) if yeni else None
    if 'aciklama' in f:
        adim.description = f.get('aciklama', '').strip() or None
    servis.aktivite(is_kaydi, current_user, 'adim_guncellendi', f"Adım güncellendi: {adim.title}")
    db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id))


@is_takip_bp.route('/<int:is_id>/adim/<int:task_id>/tasi/<yon>', methods=['POST'])
@login_required
def adim_tasi(is_id, task_id, yon):
    is_kaydi = _is_or_404(is_id, yonetim=True)
    adimlar = is_kaydi.adimlar.order_by(Task.sira, Task.id).all()
    idx = next((i for i, a in enumerate(adimlar) if a.id == task_id), None)
    if idx is None:
        abort(404)
    hedef = idx - 1 if yon == 'yukari' else idx + 1
    if 0 <= hedef < len(adimlar):
        adimlar[idx], adimlar[hedef] = adimlar[hedef], adimlar[idx]
        for sira, a in enumerate(adimlar, start=1):
            a.sira = sira
        db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id))


@is_takip_bp.route('/<int:is_id>/adim/<int:task_id>/sil', methods=['POST'])
@login_required
def adim_sil(is_id, task_id):
    is_kaydi = _is_or_404(is_id, yonetim=True)
    adim = _adim_or_404(is_kaydi, task_id)
    servis.aktivite(is_kaydi, current_user, 'adim_silindi', f"Adım silindi: {adim.title}")
    IsBelgesi.query.filter_by(task_id=adim.id).update({'task_id': None})
    Bildirim.query.filter_by(task_id=adim.id).delete(synchronize_session=False)
    db.session.delete(adim)
    db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id))


# ---------------------------------------------------------------- belgeler
def _dosyayi_sil(belge):
    try:
        yol = os.path.join(_belge_klasoru(), belge.dosya_yolu)
        if os.path.isfile(yol):
            os.remove(yol)
    except OSError:
        current_app.logger.warning(f"Belge dosyası silinemedi: {belge.dosya_yolu}", exc_info=True)


@is_takip_bp.route('/<int:is_id>/belge/yukle', methods=['POST'])
@login_required
def belge_yukle(is_id):
    is_kaydi = _is_or_404(is_id)
    dosyalar = [d for d in request.files.getlist('dosya') if d and d.filename]
    if not dosyalar:
        flash('Yüklenecek dosya seçilmedi.', 'warning')
        return redirect(url_for('is_takip.detay', is_id=is_id, sekme='belgeler'))
    belge_turu = request.form.get('belge_turu') if request.form.get('belge_turu') in BELGE_TURLERI else 'Diğer'
    task_id = _int_or_none(request.form.get('task_id'))
    if task_id and not Task.query.filter_by(id=task_id, is_id=is_kaydi.id).first():
        task_id = None
    klasor = os.path.join(_belge_klasoru(), str(is_kaydi.id))
    os.makedirs(klasor, exist_ok=True)
    eklenen, reddedilen = 0, []
    for d in dosyalar:
        ozgun_ad = d.filename.replace('\\', '/').split('/')[-1][:255]
        uzanti = ozgun_ad.rsplit('.', 1)[-1].lower() if '.' in ozgun_ad else ''
        if uzanti not in IZINLI_UZANTILAR:
            reddedilen.append(ozgun_ad)
            continue
        dosya_adi = f"{uuid.uuid4().hex}.{uzanti}"
        tam_yol = os.path.join(klasor, dosya_adi)
        d.save(tam_yol)
        db.session.add(IsBelgesi(
            is_id=is_kaydi.id, task_id=task_id, belge_turu=belge_turu, dosya_adi=ozgun_ad,
            dosya_yolu=f"{is_kaydi.id}/{dosya_adi}", boyut=os.path.getsize(tam_yol),
            mime_type=d.mimetype or mimetypes.guess_type(ozgun_ad)[0],
            aciklama=(request.form.get('aciklama') or '').strip()[:500] or None,
            yukleyen_user_id=current_user.id))
        servis.aktivite(is_kaydi, current_user, 'belge_eklendi', f"Belge eklendi ({belge_turu}): {ozgun_ad}")
        eklenen += 1
    db.session.commit()
    if eklenen:
        flash(f'{eklenen} belge yüklendi.', 'success')
    if reddedilen:
        flash('Desteklenmeyen dosya türü: ' + ', '.join(reddedilen) +
              '. İzin verilenler: ' + ', '.join(sorted(IZINLI_UZANTILAR)), 'danger')
    return redirect(url_for('is_takip.detay', is_id=is_id, sekme='belgeler'))


@is_takip_bp.route('/<int:is_id>/belge/<int:belge_id>')
@login_required
def belge_indir(is_id, belge_id):
    is_kaydi = _is_or_404(is_id)
    belge = IsBelgesi.query.filter_by(id=belge_id, is_id=is_kaydi.id).first_or_404()
    kok = os.path.realpath(_belge_klasoru())
    yol = os.path.realpath(os.path.join(kok, belge.dosya_yolu))
    if not yol.startswith(kok + os.sep) or not os.path.isfile(yol):
        abort(404)
    # Resim ve PDF'ler tarayıcıda açılabilir, diğerleri indirilir
    tarayicida = (belge.mime_type or '').startswith('image/') or belge.mime_type == 'application/pdf'
    goster = request.args.get('goster') == '1' and tarayicida
    return send_file(yol, as_attachment=not goster, download_name=belge.dosya_adi,
                     mimetype=belge.mime_type or 'application/octet-stream')


@is_takip_bp.route('/<int:is_id>/belge/<int:belge_id>/sil', methods=['POST'])
@login_required
def belge_sil(is_id, belge_id):
    is_kaydi = _is_or_404(is_id)
    belge = IsBelgesi.query.filter_by(id=belge_id, is_id=is_kaydi.id).first_or_404()
    if not (servis.yonetebilir(current_user, is_kaydi) or belge.yukleyen_user_id == current_user.id):
        abort(403)
    IsMasrafi.query.filter_by(belge_id=belge.id).update({'belge_id': None})
    _dosyayi_sil(belge)
    servis.aktivite(is_kaydi, current_user, 'belge_silindi', f"Belge silindi: {belge.dosya_adi}")
    db.session.delete(belge)
    db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id, sekme='belgeler'))


# ---------------------------------------------------------------- masraflar
@is_takip_bp.route('/<int:is_id>/masraf/ekle', methods=['POST'])
@login_required
def masraf_ekle(is_id):
    is_kaydi = _is_or_404(is_id)
    f = request.form
    tutar = _tutar(f.get('tutar'))
    if tutar is None or tutar == 0:
        flash('Geçerli bir tutar girin (örn. 1.250,50).', 'danger')
        return redirect(url_for('is_takip.detay', is_id=is_id, sekme='masraflar'))
    belge_id = _int_or_none(f.get('belge_id'))
    if belge_id and not IsBelgesi.query.filter_by(id=belge_id, is_id=is_kaydi.id).first():
        belge_id = None
    kalem = f.get('kalem') if f.get('kalem') in MASRAF_KALEMLERI else 'Diğer'
    db.session.add(IsMasrafi(
        is_id=is_kaydi.id, kalem=kalem, tutar=tutar, tarih=_tarih(f.get('tarih')) or date.today(),
        odeme_durumu=f.get('odeme_durumu') if f.get('odeme_durumu') in ODEME_DURUMLARI else 'Bekliyor',
        musteriye_yansit=bool(f.get('musteriye_yansit')), belge_id=belge_id,
        aciklama=(f.get('aciklama') or '').strip()[:500] or None, ekleyen_user_id=current_user.id))
    servis.aktivite(is_kaydi, current_user, 'masraf_eklendi', f"Masraf eklendi: {kalem} – {tutar} TL")
    db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id, sekme='masraflar'))


@is_takip_bp.route('/<int:is_id>/masraf/<int:masraf_id>/odeme', methods=['POST'])
@login_required
def masraf_odeme(is_id, masraf_id):
    is_kaydi = _is_or_404(is_id)
    masraf = IsMasrafi.query.filter_by(id=masraf_id, is_id=is_kaydi.id).first_or_404()
    masraf.odeme_durumu = 'Bekliyor' if masraf.odeme_durumu == 'Ödendi' else 'Ödendi'
    servis.aktivite(is_kaydi, current_user, 'masraf_guncellendi', f"{masraf.kalem} masrafı: {masraf.odeme_durumu}")
    db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id, sekme='masraflar'))


@is_takip_bp.route('/<int:is_id>/masraf/<int:masraf_id>/sil', methods=['POST'])
@login_required
def masraf_sil(is_id, masraf_id):
    is_kaydi = _is_or_404(is_id)
    masraf = IsMasrafi.query.filter_by(id=masraf_id, is_id=is_kaydi.id).first_or_404()
    if not (servis.yonetebilir(current_user, is_kaydi) or masraf.ekleyen_user_id == current_user.id):
        abort(403)
    servis.aktivite(is_kaydi, current_user, 'masraf_silindi', f"Masraf silindi: {masraf.kalem} – {masraf.tutar} TL")
    db.session.delete(masraf)
    db.session.commit()
    return redirect(url_for('is_takip.detay', is_id=is_id, sekme='masraflar'))


@is_takip_bp.route('/<int:is_id>/masraf/excel')
@login_required
def masraf_excel(is_id):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    is_kaydi = _is_or_404(is_id)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Masraflar'
    ws.append([f"{is_kaydi.kod} – {is_kaydi.baslik}"])
    ws['A1'].font = Font(bold=True, size=13)
    if is_kaydi.contact:
        ws.append([f"Müşteri: {is_kaydi.contact.first_name} {is_kaydi.contact.last_name}"])
    ws.append([])
    ws.append(['Tarih', 'Kalem', 'Açıklama', 'Tutar (TL)', 'Ödeme', 'Müşteriye yansıtılır'])
    for h in ws[ws.max_row]:
        h.font = Font(bold=True)
    for m in is_kaydi.masraflar.order_by(IsMasrafi.tarih).all():
        ws.append([m.tarih, m.kalem, m.aciklama or '', float(m.tutar), m.odeme_durumu,
                   'Evet' if m.musteriye_yansit else 'Hayır'])
        ws.cell(ws.max_row, 4).number_format = '#,##0.00'
    o = is_kaydi.masraf_ozeti()
    ws.append([])
    for etiket, deger in (('Toplam', o['toplam']), ('Ödenen', o['odenen']), ('Bekleyen', o['bekleyen']),
                          ('Müşteriye yansıtılan', o['musteriye'])):
        ws.append(['', '', etiket, round(deger, 2)])
        ws.cell(ws.max_row, 3).font = Font(bold=True)
        ws.cell(ws.max_row, 4).number_format = '#,##0.00'
    for col, w in zip('ABCDEF', [12, 20, 40, 16, 12, 20]):
        ws.column_dimensions[col].width = w
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{is_kaydi.kod}_masraflar.xlsx",
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# ---------------------------------------------------------------- şablonlar
def _sablon_yetkisi():
    if not servis.sablon_yonetebilir(current_user):
        abort(403)


def _sablon_or_404(sablon_id):
    sablon = db.session.get(IsSablonu, sablon_id)
    if not sablon:
        abort(404)
    if current_user.role != 'superadmin' and sablon.office_id not in (None, current_user.office_id):
        abort(404)
    if current_user.role != 'superadmin' and sablon.office_id is None and request.method == 'POST':
        abort(403)  # hazır (genel) şablonları sadece superadmin düzenler; broker kopyalayabilir
    return sablon


@is_takip_bp.route('/sablonlar')
@login_required
def sablonlar():
    _sablon_yetkisi()
    q = IsSablonu.query
    if current_user.role != 'superadmin':
        q = q.filter(db.or_(IsSablonu.office_id.is_(None), IsSablonu.office_id == current_user.office_id))
    return render_template('is_takip/sablonlar.html', sablonlar=q.order_by(IsSablonu.aktif.desc(), IsSablonu.ad).all(),
                           superadmin=current_user.role == 'superadmin')


def _sablon_formu_kaydet(sablon):
    f = request.form
    sablon.ad = (f.get('ad') or '').strip()[:120]
    sablon.is_turu = f.get('is_turu') if f.get('is_turu') in IS_TURLERI else 'Diğer'
    sablon.aciklama = (f.get('aciklama') or '').strip()
    yeni_adimlar = []
    for b, g, r, belge in zip(f.getlist('adim_baslik'), f.getlist('adim_gun'), f.getlist('adim_rol'),
                              f.getlist('adim_belge')):
        if b.strip():
            yeni_adimlar.append(IsSablonAdimi(
                sira=len(yeni_adimlar) + 1, baslik=b.strip()[:200], varsayilan_sure_gun=max(0, _int_or_none(g) or 0),
                sorumlu_rol=r if r in ('broker', 'danisman') else None,
                gerekli_belge_turu=belge if belge in BELGE_TURLERI else None))
    if not sablon.ad or not yeni_adimlar:
        return 'Şablon adı ve en az bir adım zorunludur.'
    sablon.adimlar = yeni_adimlar
    return None


@is_takip_bp.route('/sablonlar/yeni', methods=['GET', 'POST'])
@login_required
def sablon_yeni():
    _sablon_yetkisi()
    sablon = IsSablonu(office_id=None if current_user.role == 'superadmin' else current_user.office_id,
                       olusturan_user_id=current_user.id)
    kaynak = db.session.get(IsSablonu, _int_or_none(request.args.get('kopya')) or 0)
    if request.method == 'POST':
        hata = _sablon_formu_kaydet(sablon)
        if hata:
            flash(hata, 'danger')
        else:
            db.session.add(sablon)
            db.session.commit()
            flash('Şablon oluşturuldu.', 'success')
            return redirect(url_for('is_takip.sablonlar'))
    elif kaynak:
        sablon.ad, sablon.is_turu, sablon.aciklama = f"{kaynak.ad} (kopya)", kaynak.is_turu, kaynak.aciklama
        sablon.adimlar = [IsSablonAdimi(sira=a.sira, baslik=a.baslik, varsayilan_sure_gun=a.varsayilan_sure_gun,
                                        sorumlu_rol=a.sorumlu_rol, gerekli_belge_turu=a.gerekli_belge_turu)
                          for a in kaynak.adimlar]
    adimlar = list(sablon.adimlar)
    return render_template('is_takip/sablon_form.html', sablon=sablon, adimlar=adimlar, yeni=True,
                           turler=IS_TURLERI, belge_turleri=BELGE_TURLERI)


@is_takip_bp.route('/sablonlar/<int:sablon_id>', methods=['GET', 'POST'])
@login_required
def sablon_duzenle(sablon_id):
    _sablon_yetkisi()
    sablon = _sablon_or_404(sablon_id)
    if request.method == 'POST':
        hata = _sablon_formu_kaydet(sablon)
        if hata:
            db.session.rollback()
            flash(hata, 'danger')
            return redirect(url_for('is_takip.sablon_duzenle', sablon_id=sablon_id))
        db.session.commit()
        flash('Şablon kaydedildi. Değişiklikler yeni açılacak işlerde geçerli olur.', 'success')
        return redirect(url_for('is_takip.sablonlar'))
    salt_okunur = current_user.role != 'superadmin' and sablon.office_id is None
    return render_template('is_takip/sablon_form.html', sablon=sablon, adimlar=sablon.adimlar, yeni=False,
                           salt_okunur=salt_okunur, turler=IS_TURLERI, belge_turleri=BELGE_TURLERI)


@is_takip_bp.route('/sablonlar/<int:sablon_id>/aktif', methods=['POST'])
@login_required
def sablon_aktif(sablon_id):
    _sablon_yetkisi()
    sablon = _sablon_or_404(sablon_id)
    sablon.aktif = not sablon.aktif
    db.session.commit()
    return redirect(url_for('is_takip.sablonlar'))


# ---------------------------------------------------------------- bildirimler
@is_takip_bp.route('/bildirimler')
@login_required
def bildirimler():
    liste = Bildirim.query.filter_by(user_id=current_user.id).order_by(Bildirim.created_at.desc()).limit(200).all()
    return render_template('is_takip/bildirimler.html', bildirimler=liste)


@is_takip_bp.route('/bildirimler/ozet')
@login_required
def bildirim_ozet():
    q = Bildirim.query.filter_by(user_id=current_user.id, okundu=False)
    son = q.order_by(Bildirim.created_at.desc()).limit(8).all()
    return jsonify({'sayi': q.count(), 'son': [
        {'id': b.id, 'mesaj': b.mesaj, 'tur': b.tur, 'url': url_for('is_takip.bildirim_ac', bildirim_id=b.id),
         'tarih': b.created_at.strftime('%d.%m.%Y %H:%M')} for b in son]})


@is_takip_bp.route('/bildirimler/<int:bildirim_id>/ac')
@login_required
def bildirim_ac(bildirim_id):
    b = Bildirim.query.filter_by(id=bildirim_id, user_id=current_user.id).first_or_404()
    b.okundu = True
    db.session.commit()
    hedef = b.url if b.url and b.url.startswith('/') and not b.url.startswith('//') else url_for('is_takip.bildirimler')
    return redirect(hedef)


@is_takip_bp.route('/bildirimler/tumunu-oku', methods=['POST'])
@login_required
def bildirim_tumunu_oku():
    Bildirim.query.filter_by(user_id=current_user.id, okundu=False).update({'okundu': True})
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'fetch':
        return jsonify({'ok': True})
    return redirect(url_for('is_takip.bildirimler'))

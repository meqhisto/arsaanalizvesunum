# -*- coding: utf-8 -*-
"""İlan iş kuralları (spec §4): görünürlük, ilan kodu, çakışma, kaydetme, özet ve sahiplik.

Bu modüldeki fonksiyonlar commit etmez; çağıran commit/rollback eder.
"""
from datetime import datetime
from decimal import Decimal

from flask import abort
from sqlalchemy import or_

from models import db
from models.arsa_models import ArsaAnaliz
from models.crm_models import Contact, Deal
from models.ilan_models import GayrimenkulSahibi, Ilan, IlanEmsal, IlanGayrimenkul
from models.user_models import User
from modules import ilan_hesap
from modules.gayrimenkul_sabitleri import AKTIF_DURUMLAR, DURUMLAR, TEKLIF_TIPLERI


class IlanHatasi(ValueError):
    """Kullanıcıya gösterilebilir doğrulama hatası."""


# ---------------------------------------------------------------- görünürlük

def gorunur_kullanici_idleri(user):
    """Kullanıcının kayıtlarını görebildiği kullanıcı id'leri; superadmin için None (= hepsi).

    Broker: kendisi + astları (manager_id) + (ofisi varsa) aynı ofisteki aktif kullanıcılar.
    """
    if user.role == 'superadmin':
        return None
    if user.role == 'broker':
        kosul = User.manager_id == user.id
        if user.office_id:
            kosul = or_(kosul, User.office_id == user.office_id)
        ekip = db.session.query(User.id).filter(kosul, User.id != user.id, User._is_active.is_(True))
        return [user.id] + [uid for (uid,) in ekip]
    return [user.id]


def _kisitla(sorgu, *sutunlar, user):
    idler = gorunur_kullanici_idleri(user)
    if idler is None:
        return sorgu
    return sorgu.filter(or_(*(s.in_(idler) for s in sutunlar)))


def gorunur_gayrimenkuller(user):
    return _kisitla(ArsaAnaliz.query, ArsaAnaliz.user_id, user=user)


def gorunur_ilanlar(user):
    return _kisitla(Ilan.query, Ilan.user_id, Ilan.sorumlu_user_id, user=user)


def gorunur_kontaklar(user):
    return _kisitla(Contact.query, Contact.user_id, user=user)


def gayrimenkul_or_404(gayrimenkul_id, user):
    g = gorunur_gayrimenkuller(user).filter(ArsaAnaliz.id == gayrimenkul_id).first()
    if g is None:
        abort(404)
    return g


def ilan_or_404(ilan_id, user):
    i = gorunur_ilanlar(user).filter(Ilan.id == ilan_id).first()
    if i is None:
        abort(404)
    return i


# ---------------------------------------------------------------- kod ve çakışma

def yeni_ilan_kodu(yil=None):
    """ILN-YYYY-NNNN: o yılın en büyük sıra numarası + 1."""
    yil = yil or datetime.utcnow().year
    onek = f"ILN-{yil}-"
    en_buyuk = 0
    for (kod,) in db.session.query(Ilan.kod).filter(Ilan.kod.like(f"{onek}%")):
        try:
            en_buyuk = max(en_buyuk, int(kod[len(onek):]))
        except ValueError:
            continue
    return f"{onek}{en_buyuk + 1:04d}"


def cakisan_ilan(gayrimenkul_id, haric_ilan_id=None):
    """Gayrimenkulü içeren, aktif durumdaki (pazarlamada/opsiyonlu) başka bir ilan."""
    sorgu = (Ilan.query.join(IlanGayrimenkul, IlanGayrimenkul.ilan_id == Ilan.id)
             .filter(IlanGayrimenkul.gayrimenkul_id == gayrimenkul_id, Ilan.durum.in_(AKTIF_DURUMLAR)))
    if haric_ilan_id is not None:
        sorgu = sorgu.filter(Ilan.id != haric_ilan_id)
    return sorgu.order_by(Ilan.id).first()


# ---------------------------------------------------------------- kaydetme

SATILIK_ALANLARI = ('fiyat',)
KIRALIK_ALANLARI = ('kira', 'depozito')
KAT_ALANLARI = ('sahip_payi_yuzde', 'ek_nakit', 'teslim_suresi_ay', 'teminat_turu', 'teminat_tutari',
                'tevhid_durumu', 'insaat_alani_elle', 'daire_tercihi_notu', 'bolge_pay_yuzde_elle')
M2_FIYAT_ALANLARI = ('bolge_m2_fiyat_elle',)
TIP_ALANLARI = {
    'satilik': SATILIK_ALANLARI + M2_FIYAT_ALANLARI,
    'kiralik': KIRALIK_ALANLARI + M2_FIYAT_ALANLARI,
    'kat_karsiligi': KAT_ALANLARI,
}
TUM_TIP_ALANLARI = SATILIK_ALANLARI + KIRALIK_ALANLARI + KAT_ALANLARI + M2_FIYAT_ALANLARI
SAYISAL_ALANLAR = {'fiyat', 'kira', 'depozito', 'sahip_payi_yuzde', 'ek_nakit', 'teminat_tutari',
                   'insaat_alani_elle', 'bolge_m2_fiyat_elle', 'bolge_pay_yuzde_elle'}
TAMSAYI_ALANLAR = {'teslim_suresi_ay'}
EMSAL_ALANLARI = ('konum', 'm2', 'fiyat', 'pay_yuzde', 'link', 'notlar')
EMSAL_SAYISAL = {'m2', 'fiyat', 'pay_yuzde'}


def _bos(deger):
    return deger is None or (isinstance(deger, str) and not deger.strip())


def _sayi(deger, alan='Değer'):
    if _bos(deger):
        return None
    if isinstance(deger, bool):
        raise IlanHatasi(f"{alan} geçersiz.")
    if isinstance(deger, (int, float, Decimal)):
        return Decimal(str(deger))
    sonuc = ilan_hesap.tutar_ayristir(deger)
    if sonuc is None:
        raise IlanHatasi(f"{alan} geçersiz.")
    return Decimal(str(sonuc))


def _alan_degeri(alan, deger):
    if alan in SAYISAL_ALANLAR:
        return _sayi(deger, alan)
    if alan in TAMSAYI_ALANLAR:
        s = _sayi(deger, alan)
        return int(s) if s is not None else None
    return None if _bos(deger) else str(deger).strip()


def _kullanici_gorunur_mu(user, hedef_id):
    idler = gorunur_kullanici_idleri(user)
    if idler is None:
        return db.session.get(User, hedef_id) is not None
    return hedef_id in idler


def ilan_kaydet(ilan, user, veri):
    """Yeni ilan oluşturur (ilan None) ya da günceller. Doğrular, IlanHatasi fırlatır. Commit etmez."""
    teklif_tipi = veri.get('teklif_tipi')
    durum = veri.get('durum')
    if teklif_tipi not in {k for k, _ in TEKLIF_TIPLERI}:
        raise IlanHatasi("Geçersiz teklif tipi.")
    if durum not in {k for k, _ in DURUMLAR}:
        raise IlanHatasi("Geçersiz ilan durumu.")

    # Gayrimenkuller: liste sırası = sıra; tekrarlar atlanır
    gm_satirlari, gorulen = [], set()
    for satir in veri.get('gayrimenkuller') or []:
        try:
            gid = int(satir['id'])
        except (KeyError, TypeError, ValueError):
            raise IlanHatasi("Geçersiz gayrimenkul seçimi.")
        if gid not in gorulen:
            gorulen.add(gid)
            gm_satirlari.append((gid, _sayi(satir.get('parsel_fiyati'), 'Parsel fiyatı')))
    if not gm_satirlari:
        raise IlanHatasi("İlana en az bir gayrimenkul eklenmelidir.")
    # Düzenlemede ilana zaten bağlı gayrimenkuller görünürlük şartı olmadan kabul edilir
    # (ör. ilanı yalnız sorumlu olarak gören danışman); yeni eklenenler görünür olmalı.
    gorunurler = {b.gayrimenkul_id: b.gayrimenkul for b in ilan.baglar
                  if b.gayrimenkul_id in gorulen} if ilan is not None else {}
    yeniler = gorulen - set(gorunurler)
    if yeniler:
        gorunurler.update({g.id: g for g in gorunur_gayrimenkuller(user).filter(ArsaAnaliz.id.in_(yeniler))})
    if len(gorunurler) != len(gorulen):
        raise IlanHatasi("Seçilen gayrimenkul bulunamadı.")

    # Teklif tipine ait alanlar; diğerleri None
    degerler = {alan: None for alan in TUM_TIP_ALANLARI}
    for alan in TIP_ALANLARI[teklif_tipi]:
        degerler[alan] = _alan_degeri(alan, veri.get(alan))
    if teklif_tipi == 'satilik' and degerler['fiyat'] is None:
        raise IlanHatasi("Satılık ilanda fiyat zorunludur.")
    if teklif_tipi == 'kiralik' and degerler['kira'] is None:
        raise IlanHatasi("Kiralık ilanda kira zorunludur.")
    if teklif_tipi == 'kat_karsiligi':
        pay = degerler['sahip_payi_yuzde']
        if pay is None or not (0 <= pay <= 100):
            raise IlanHatasi("Kat karşılığında arsa sahibi payı %0–100 arasında olmalıdır.")

    haric = ilan.id if ilan is not None else None
    if durum in AKTIF_DURUMLAR:
        for gid, _ in gm_satirlari:
            cakisan = cakisan_ilan(gid, haric)
            if cakisan is not None:
                raise IlanHatasi(f"{gorunurler[gid].baslik_metni} zaten {cakisan.kod} numaralı aktif ilanda.")

    olusturan_id = ilan.user_id if ilan is not None else user.id
    sorumlu_id = veri.get('sorumlu_user_id')
    if _bos(sorumlu_id):
        sorumlu_id = olusturan_id
    else:
        try:
            sorumlu_id = int(sorumlu_id)
        except (TypeError, ValueError):
            raise IlanHatasi("Seçilen sorumlu bulunamadı.")
        degismedi = ilan is not None and sorumlu_id == ilan.sorumlu_user_id
        if not degismedi and not _kullanici_gorunur_mu(user, sorumlu_id):
            raise IlanHatasi("Seçilen sorumlu bulunamadı.")

    ana_id = veri.get('ana_gayrimenkul_id')
    try:
        ana_id = int(ana_id) if not _bos(ana_id) else None
    except (TypeError, ValueError):
        ana_id = None
    if ana_id not in gorulen:
        ana_id = gm_satirlari[0][0]
    ana = gorunurler[ana_id]

    emsaller = []
    for e in veri.get('emsaller') or []:
        if all(_bos(e.get(k)) for k in EMSAL_ALANLARI):
            continue
        emsaller.append({k: (_sayi(e.get(k), f"Emsal {k}") if k in EMSAL_SAYISAL
                             else (None if _bos(e.get(k)) else str(e.get(k)).strip()))
                         for k in EMSAL_ALANLARI})

    # --- Doğrulama bitti; uygula
    if ilan is None:
        ilan = Ilan(kod=yeni_ilan_kodu(), user_id=user.id)
        db.session.add(ilan)
    ilan.baslik = (str(veri.get('baslik') or '').strip() or ana.baslik_metni)[:200]
    ilan.aciklama = None if _bos(veri.get('aciklama')) else veri.get('aciklama')
    ilan.teklif_tipi = teklif_tipi
    ilan.durum = durum
    ilan.sorumlu_user_id = sorumlu_id
    ilan.office_id = ana.office_id
    for alan, deger in degerler.items():
        setattr(ilan, alan, deger)

    mevcut = {b.gayrimenkul_id: b for b in ilan.baglar}
    yeni_baglar = []
    for sira, (gid, parsel_fiyati) in enumerate(gm_satirlari, start=1):
        bag = mevcut.get(gid) or IlanGayrimenkul(gayrimenkul=gorunurler[gid])
        bag.sira = sira
        bag.parsel_fiyati = parsel_fiyati
        bag.ana_kayit = gid == ana_id
        yeni_baglar.append(bag)
    ilan.baglar = yeni_baglar

    ilan.emsaller = [IlanEmsal(**e) for e in emsaller]
    return ilan


# ---------------------------------------------------------------- özet

def _f(deger):
    return float(deger) if deger is not None else None


def ilan_ozeti(ilan):
    """Task 1 hesaplarını ilanın düz verisiyle çağırır."""
    gayrimenkuller = ilan.gayrimenkuller
    parseller = [{'m2': _f(g.metrekare), 'kaks': _f(g.kaks)} for g in gayrimenkuller]
    toplam = ilan_hesap.toplam_m2(parseller)
    insaat, eksik = ilan_hesap.insaat_hakki(parseller, _f(ilan.insaat_alani_elle))
    pay = _f(ilan.sahip_payi_yuzde)
    istenen = ilan_hesap.istenen_deger(ilan.teklif_tipi, _f(ilan.fiyat), _f(ilan.kira), pay, toplam)
    emsaller = [{'m2': _f(e.m2), 'fiyat': _f(e.fiyat), 'pay_yuzde': _f(e.pay_yuzde)} for e in ilan.emsaller]
    bolge, kaynak = ilan_hesap.bolge_ortalamasi(ilan.teklif_tipi, emsaller, _f(ilan.bolge_m2_fiyat_elle),
                                                _f(ilan.bolge_pay_yuzde_elle))
    fark = ilan_hesap.fark_yuzde(istenen, bolge)
    return {
        'toplam_m2': toplam,
        'insaat_hakki': insaat,
        'kakssiz_parseller': [gayrimenkuller[i].baslik_metni for i in eksik],
        'sahibe_dusen_m2': ilan_hesap.sahibe_dusen_m2(insaat, pay),
        'istenen': istenen,
        'bolge': bolge,
        'bolge_kaynak': kaynak,
        'emsal_sayisi': len(ilan_hesap.gecerli_emsaller(ilan.teklif_tipi, emsaller)) if kaynak == 'emsal' else 0,
        'fark': fark,
        'konum': ilan_hesap.konumlandirma(ilan.teklif_tipi, fark),
    }


# ---------------------------------------------------------------- sahiplik

def sahipleri_kaydet(gayrimenkul, user, sahipler):
    """Gayrimenkulün sahiplerini listeye göre senkronlar. Commit etmez."""
    istenen = {}
    for s in sahipler or []:
        try:
            cid = int(s['contact_id'])
        except (KeyError, TypeError, ValueError):
            raise IlanHatasi("Seçilen müşteri bulunamadı.")
        istenen[cid] = s
    mevcut = {s.contact_id: s for s in gayrimenkul.sahiplikler}
    # Zaten sahip olan kişiler düzenleyen göremese de korunur (ör. broker'ın eklediği kişi);
    # yeni eklenenler görünür olmalı.
    yeniler = set(istenen) - set(mevcut)
    if yeniler:
        bulunan = {cid for (cid,) in gorunur_kontaklar(user).filter(Contact.id.in_(yeniler))
                   .with_entities(Contact.id)}
        if bulunan != yeniler:
            raise IlanHatasi("Seçilen müşteri bulunamadı.")

    yeni = []
    for cid, s in istenen.items():
        kayit = mevcut.get(cid) or GayrimenkulSahibi(contact_id=cid)
        hisse = s.get('hisse')
        kayit.hisse = None if _bos(hisse) else str(hisse).strip()[:20]
        kayit.irtibat = bool(s.get('irtibat'))
        yeni.append(kayit)
    gayrimenkul.sahiplikler = yeni


# ---------------------------------------------------------------- silme politikası

def gayrimenkul_silinirken(gayrimenkul):
    """Gayrimenkul silinmeden önce ilanlarını düzenler (commit etmez).

    Tek gayrimenkullü ilan silinir (emsalleri, portföy bağları gider; fırsatların ilan_id'si NULL olur).
    Çok gayrimenkullü ilandan yalnız bağ çıkarılır; ana kayıtsa sıradaki ana kayıt olur.
    """
    for bag in list(gayrimenkul.ilan_baglari):
        ilan = bag.ilan
        if ilan is None:
            continue
        if len(ilan.baglar) <= 1:
            Deal.query.filter(Deal.ilan_id == ilan.id).update({Deal.ilan_id: None}, synchronize_session='fetch')
            db.session.delete(ilan)
        else:
            ana_miydi = bag.ana_kayit
            ilan.baglar.remove(bag)
            if ana_miydi:
                sonraki = min(ilan.baglar, key=lambda b: b.sira)
                sonraki.ana_kayit = True
                ilan.office_id = sonraki.gayrimenkul.office_id
    db.session.flush()
    db.session.expire(gayrimenkul, ['ilan_baglari'])

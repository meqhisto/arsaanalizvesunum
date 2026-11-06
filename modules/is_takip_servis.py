# -*- coding: utf-8 -*-
"""İş takip modülü iş kuralları: görünürlük/yetki, şablondan iş açma, aktivite ve bildirim."""
import logging
from datetime import datetime, date, timedelta, time

from sqlalchemy import or_, exists, and_
from sqlalchemy.exc import IntegrityError

from models import db
from models.user_models import User
from models.crm_models import Task
from models.is_takip_models import (
    Is, IsAktivitesi, Bildirim, IS_ACIK_DURUMLAR, GOREV_TAMAMLANDI, GOREV_IPTAL,
)

log = logging.getLogger(__name__)

YAKLASAN_GUN = 2  # son tarihine bu kadar gün kalan adım "yaklaşan" sayılır


# ---------------------------------------------------------------- yetkiler
def yonetici_mi(user):
    return user.role in ('superadmin', 'broker')


def _ekip_idleri(user):
    """Broker'ın sorumlu olduğu kullanıcılar: kendisi + astları + (varsa) aynı ofistekiler."""
    ids = {user.id}
    ids.update(u.id for u in user.subordinates)
    if user.office_id:
        ids.update(uid for (uid,) in db.session.query(User.id).filter(User.office_id == user.office_id))
    return ids


def gorunur_isler(user):
    """Kullanıcının görebileceği işlerin sorgusu."""
    q = Is.query
    if user.role == 'superadmin':
        return q
    adimi_bende = exists().where(and_(Task.is_id == Is.id, Task.assigned_to_user_id == user.id))
    if user.role == 'broker':
        ekip = _ekip_idleri(user)
        kosul = or_(Is.sorumlu_user_id.in_(ekip), Is.olusturan_user_id.in_(ekip), adimi_bende)
        if user.office_id:
            kosul = or_(kosul, Is.office_id == user.office_id)
        return q.filter(kosul)
    return q.filter(or_(Is.sorumlu_user_id == user.id, Is.olusturan_user_id == user.id, adimi_bende))


def gorebilir(user, is_kaydi):
    return gorunur_isler(user).filter(Is.id == is_kaydi.id).first() is not None


def yonetebilir(user, is_kaydi):
    """İşi düzenleme, sorumlu değiştirme, adım ekleme/silme, işi silme."""
    if user.role == 'superadmin':
        return True
    if user.role == 'broker':
        return gorebilir(user, is_kaydi)
    return user.id in (is_kaydi.sorumlu_user_id, is_kaydi.olusturan_user_id)


def adimi_guncelleyebilir(user, is_kaydi, adim):
    return yonetebilir(user, is_kaydi) or adim.assigned_to_user_id == user.id


def atanabilir_kullanicilar(user):
    """Sorumlu / adım ataması için seçilebilecek kullanıcılar."""
    if user.role == 'superadmin':
        q = User.query
    elif user.role == 'broker':
        q = User.query.filter(User.id.in_(_ekip_idleri(user)))
    else:
        q = User.query.filter(User.id == user.id)
    return q.filter(User._is_active.is_(True)).order_by(User.ad, User.soyad).all()


def sablon_yonetebilir(user):
    return yonetici_mi(user)


# ---------------------------------------------------------------- yardımcılar
def kullanici_adi(user):
    if not user:
        return '-'
    ad = ' '.join(p for p in [(user.ad or '').strip(), (user.soyad or '').strip()] if p)
    return ad or user.email


def gun_sonu(d):
    """Tarih seçilen adımın son saati: o günün 18:00'i."""
    return datetime.combine(d, time(18, 0))


def aktivite(is_kaydi, user, eylem, detay=''):
    db.session.add(IsAktivitesi(is_id=is_kaydi.id, user_id=user.id if user else None, eylem=eylem, detay=detay))


def bildirim(user_id, tur, mesaj, is_kaydi=None, task=None, url=None, gun=None):
    """Bildirim ekler; aynı kullanıcı + adım + tür için günde bir kez (savepoint ile güvenli)."""
    if not user_id:
        return False
    gun = gun or date.today()
    if task is not None and Bildirim.query.filter_by(user_id=user_id, task_id=task.id, tur=tur, gun=gun).first():
        return False
    try:
        with db.session.begin_nested():
            db.session.add(Bildirim(user_id=user_id, tur=tur, mesaj=mesaj[:500], url=url, gun=gun,
                                    is_id=is_kaydi.id if is_kaydi else None,
                                    task_id=task.id if task is not None else None))
        return True
    except IntegrityError:
        return False


def is_url(is_kaydi):
    return f"/isler/{is_kaydi.id}"


# ---------------------------------------------------------------- iş oluşturma
def is_olustur(olusturan, baslik, is_turu, sorumlu_id, baslangic=None, sablon=None, adimlar=None,
               oncelik='Normal', aciklama='', contact_id=None, deal_id=None, analiz_id=None,
               portfolio_id=None, butce=None, hedef_bitis=None):
    """Yeni iş açar. `adimlar`: [{'baslik', 'son_tarih'(date), 'sorumlu_id', 'aciklama'}] (önizlemeden).
    Verilmezse ve şablon seçildiyse adımlar şablondan üretilir."""
    baslangic = baslangic or date.today()
    sorumlu = db.session.get(User, sorumlu_id) or olusturan
    is_kaydi = Is(kod=Is.yeni_kod(), baslik=baslik.strip()[:200], is_turu=is_turu, oncelik=oncelik,
                  aciklama=aciklama, sorumlu_user_id=sorumlu.id, olusturan_user_id=olusturan.id,
                  office_id=sorumlu.office_id or olusturan.office_id, contact_id=contact_id, deal_id=deal_id,
                  analiz_id=analiz_id, portfolio_id=portfolio_id, sablon_id=sablon.id if sablon else None,
                  baslangic_tarihi=baslangic, butce=butce, durum='Açık')
    db.session.add(is_kaydi)
    db.session.flush()

    if adimlar is None and sablon is not None:
        adimlar = sablondan_adimlar(sablon, baslangic, sorumlu.id)
    for sira, a in enumerate(adimlar or [], start=1):
        adim_ekle(is_kaydi, olusturan, a['baslik'], a.get('son_tarih'), a.get('sorumlu_id') or sorumlu.id,
                  aciklama=a.get('aciklama', ''), sira=sira, aktivite_yaz=False)

    son = max((a.get('son_tarih') for a in (adimlar or []) if a.get('son_tarih')), default=None)
    is_kaydi.hedef_bitis_tarihi = hedef_bitis or son
    aktivite(is_kaydi, olusturan, 'olusturuldu',
             f"İş oluşturuldu{' (' + sablon.ad + ' şablonu)' if sablon else ''}.")
    if sorumlu.id != olusturan.id:
        bildirim(sorumlu.id, 'atandi', f"{is_kaydi.kod} – {is_kaydi.baslik} işinin sorumlusu olarak atandınız.",
                 is_kaydi=is_kaydi, url=is_url(is_kaydi))
    return is_kaydi


def sablondan_adimlar(sablon, baslangic, sorumlu_id):
    gun = baslangic
    sonuc = []
    for adim in sablon.adimlar:
        gun = gun + timedelta(days=adim.varsayilan_sure_gun or 0)
        sonuc.append({'baslik': adim.baslik, 'son_tarih': gun, 'sorumlu_id': sorumlu_id,
                      'aciklama': adim.aciklama or '',
                      'gerekli_belge': adim.gerekli_belge_turu, 'sorumlu_rol': adim.sorumlu_rol})
    return sonuc


def adim_ekle(is_kaydi, ekleyen, baslik, son_tarih, sorumlu_id, aciklama='', sira=None, aktivite_yaz=True):
    if sira is None:
        sira = (db.session.query(db.func.max(Task.sira)).filter(Task.is_id == is_kaydi.id).scalar() or 0) + 1
    adim = Task(user_id=ekleyen.id, assigned_to_user_id=sorumlu_id, assigned_by_user_id=ekleyen.id,
                title=baslik.strip()[:200], description=aciklama or None,
                due_date=gun_sonu(son_tarih) if isinstance(son_tarih, date) else None,
                status='Beklemede', priority=is_kaydi.oncelik if is_kaydi.oncelik in ('Düşük', 'Normal', 'Yüksek', 'Acil') else 'Normal',
                office_id=is_kaydi.office_id, contact_id=is_kaydi.contact_id, deal_id=is_kaydi.deal_id,
                task_type='supervised' if sorumlu_id != ekleyen.id else 'personal',
                is_id=is_kaydi.id, sira=sira)
    db.session.add(adim)
    db.session.flush()
    if aktivite_yaz:
        aktivite(is_kaydi, ekleyen, 'adim_eklendi', f"Adım eklendi: {adim.title}")
    if sorumlu_id and sorumlu_id != ekleyen.id:
        bildirim(sorumlu_id, 'atandi', f"{is_kaydi.kod}: \"{adim.title}\" adımı size atandı.",
                 is_kaydi=is_kaydi, task=adim, url=is_url(is_kaydi))
    return adim


def adim_durumunu_degistir(is_kaydi, adim, user, tamamlandi):
    if tamamlandi:
        adim.status = GOREV_TAMAMLANDI
        adim.completed_at = datetime.utcnow()
        aktivite(is_kaydi, user, 'adim_tamamlandi', f"Adım tamamlandı: {adim.title}")
        if is_kaydi.durum == 'Açık':
            is_kaydi.durum = 'Devam ediyor'
        if is_kaydi.sorumlu_user_id != user.id:
            bildirim(is_kaydi.sorumlu_user_id, 'tamamlandi',
                     f"{is_kaydi.kod}: \"{adim.title}\" adımı {kullanici_adi(user)} tarafından tamamlandı.",
                     is_kaydi=is_kaydi, task=adim, url=is_url(is_kaydi))
    else:
        adim.status = 'Devam Ediyor'
        adim.completed_at = None
        aktivite(is_kaydi, user, 'adim_geri_alindi', f"Adım yeniden açıldı: {adim.title}")


def eksik_belge_uyarisi(is_kaydi, adim):
    """Şablonda bu adım için belge isteniyorsa ve işte o türden belge yoksa türünü döndürür."""
    if not is_kaydi.sablon:
        return None
    for s_adim in is_kaydi.sablon.adimlar:
        if s_adim.baslik == adim.title and s_adim.gerekli_belge_turu:
            if not is_kaydi.belgeler.filter_by(belge_turu=s_adim.gerekli_belge_turu).first():
                return s_adim.gerekli_belge_turu
    return None


def is_durumu_degistir(is_kaydi, user, yeni_durum):
    eski = is_kaydi.durum
    if eski == yeni_durum:
        return
    is_kaydi.durum = yeni_durum
    is_kaydi.tamamlanma_tarihi = datetime.utcnow() if yeni_durum == 'Tamamlandı' else None
    aktivite(is_kaydi, user, 'durum_degisti', f"Durum: {eski} → {yeni_durum}")


# ---------------------------------------------------------------- hatırlatmalar
def hatirlatmalari_uret(bugun=None):
    """Geciken ve yaklaşan adımlar için bildirim üretir. Günde bir kez çalıştırılır (CLI)."""
    bugun = bugun or date.today()
    simdi = datetime.combine(bugun, time(0, 0))
    sinir = gun_sonu(bugun + timedelta(days=YAKLASAN_GUN))
    adimlar = (Task.query.join(Is, Task.is_id == Is.id)
               .filter(Is.durum.in_(IS_ACIK_DURUMLAR), Task.status.notin_([GOREV_TAMAMLANDI, GOREV_IPTAL]),
                       Task.due_date.isnot(None), Task.due_date <= sinir)
               .all())
    sayac = {'geciken': 0, 'yaklasan': 0}
    for adim in adimlar:
        is_kaydi = adim.is_kaydi
        geciken = adim.due_date < simdi
        tur = 'geciken' if geciken else 'yaklasan'
        tarih = adim.due_date.strftime('%d.%m.%Y')
        mesaj = (f"{is_kaydi.kod}: \"{adim.title}\" adımı {tarih} tarihinden beri gecikmede."
                 if geciken else f"{is_kaydi.kod}: \"{adim.title}\" adımının son tarihi {tarih}.")
        alicilar = {adim.assigned_to_user_id or is_kaydi.sorumlu_user_id}
        if geciken:
            alicilar.add(is_kaydi.sorumlu_user_id)
        for uid in alicilar:
            if bildirim(uid, tur, mesaj, is_kaydi=is_kaydi, task=adim, url=is_url(is_kaydi), gun=bugun):
                sayac[tur] += 1
    db.session.commit()
    return sayac


def panel_ozeti(user, gun=7):
    """Ana panel kartları için: kullanıcının geciken ve bu hafta bitecek adımları."""
    simdi = datetime.utcnow()
    is_ids = [i for (i,) in gorunur_isler(user).filter(Is.durum.in_(IS_ACIK_DURUMLAR)).with_entities(Is.id)]
    if not is_ids:
        return {'geciken': [], 'yaklasan': [], 'acik_is': 0}
    q = Task.query.filter(Task.is_id.in_(is_ids), Task.status.notin_([GOREV_TAMAMLANDI, GOREV_IPTAL]),
                          Task.due_date.isnot(None))
    if not yonetici_mi(user):
        q = q.filter(or_(Task.assigned_to_user_id == user.id, Task.assigned_to_user_id.is_(None)))
    geciken = q.filter(Task.due_date < simdi).order_by(Task.due_date).limit(10).all()
    yaklasan = q.filter(Task.due_date >= simdi, Task.due_date <= simdi + timedelta(days=gun)) \
                .order_by(Task.due_date).limit(10).all()
    return {'geciken': geciken, 'yaklasan': yaklasan, 'acik_is': len(is_ids)}

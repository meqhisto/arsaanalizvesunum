"""Sunucu hatalarını superadmin kullanıcılara uygulama içi bildirim (zil) olarak iletir."""
from datetime import date

from flask import current_app

from models import db
from models.is_takip_models import Bildirim
from models.user_models import User

MESAJ_SINIRI = 500  # Bildirim.mesaj sütun uzunluğu


def bildir(yontem, yol, hata):
    """Her etkin superadmin için 'Sunucu hatası: <yöntem> <yol> (<hata türü>)' bildirimi ekler.

    Aynı kullanıcıya aynı gün aynı mesaj ikinci kez eklenmez. Eklenen bildirim sayısını döndürür.
    Hata karşılayıcının içinden çağrıldığı için kendisi asla hata fırlatmaz.
    """
    try:
        db.session.rollback()  # hata, yarım kalmış bir işlemin ortasında oluşmuş olabilir
        mesaj = f"Sunucu hatası: {yontem} {yol}"
        ek = f" ({type(hata).__name__})"
        mesaj = mesaj[:MESAJ_SINIRI - len(ek)] + ek
        bugun = date.today()
        eklenen = 0
        for kullanici in User.query.filter_by(role='superadmin', _is_active=True).all():
            if Bildirim.query.filter_by(user_id=kullanici.id, tur='hata', gun=bugun, mesaj=mesaj).first():
                continue
            db.session.add(Bildirim(user_id=kullanici.id, tur='hata', mesaj=mesaj, url='/admin/dashboard', gun=bugun))
            eklenen += 1
        db.session.commit()
        return eklenen
    except Exception:
        db.session.rollback()
        current_app.logger.warning("Hata bildirimi kaydedilemedi", exc_info=True)
        return 0

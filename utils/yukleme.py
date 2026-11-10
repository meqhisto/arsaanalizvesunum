"""Dosya yükleme ortak yardımcıları: HEIC/webp -> JPEG, benzersiz ad, tablo dosyası okuma."""
import io
import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

RESIM_UZANTILARI = {"png", "jpg", "jpeg", "gif"}
DONUSEN_UZANTILAR = {"heic", "heif", "webp"}  # iPhone/Android biçimleri: JPEG'e çevrilir (tarayıcı ve raporlar açabilsin)
VIDEO_UZANTILARI = {"mp4", "mov", "avi", "m4v"}


def uzanti(dosya_adi):
    return dosya_adi.rsplit('.', 1)[1].lower() if dosya_adi and '.' in dosya_adi else ''


def jpege_cevir(dosya, hedef_yol, en_buyuk_kenar=2400):
    """Resmi (HEIC/HEIF/webp dahil) JPEG olarak kaydeder; başarısızsa False döner."""
    try:
        from PIL import Image, ImageOps
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass
        with Image.open(dosya.stream) as img:
            img = ImageOps.exif_transpose(img).convert('RGB')
            img.thumbnail((en_buyuk_kenar, en_buyuk_kenar))
            img.save(hedef_yol, 'JPEG', quality=85)
        return True
    except Exception as e:
        current_app.logger.warning(f"Fotoğraf JPEG'e çevrilemedi ({dosya.filename}): {e}")
        return False


def resim_kaydet(dosya, klasor, en_buyuk_kenar=None, on_ek=''):
    """Resmi klasöre benzersiz adla kaydeder; kaydedilen dosya adını, tür uygun değilse/bozuksa None döner.

    HEIC/HEIF/webp her zaman JPEG'e çevrilir. en_buyuk_kenar verilirse jpg/jpeg de küçültülür
    (png/gif saydamlık ve animasyon için olduğu gibi kalır).
    """
    if not dosya or not dosya.filename:
        return None
    uz = uzanti(dosya.filename)
    if uz not in RESIM_UZANTILARI | DONUSEN_UZANTILAR:
        return None
    govde = secure_filename(dosya.filename.rsplit('.', 1)[0])[:60] or 'dosya'
    os.makedirs(klasor, exist_ok=True)
    cevir = uz in DONUSEN_UZANTILAR or (en_buyuk_kenar and uz in {'jpg', 'jpeg'})
    ad = f"{on_ek}{uuid.uuid4().hex[:8]}_{govde}.{'jpg' if cevir else uz}"
    hedef = os.path.join(klasor, ad)
    if cevir:
        if not jpege_cevir(dosya, hedef, en_buyuk_kenar or 2400):
            return None
    else:
        # Uzantısı resim olan ama içeriği resim olmayan dosyalar kabul edilmez
        try:
            from PIL import Image
            with Image.open(dosya.stream) as img:
                img.verify()
            dosya.stream.seek(0)
        except Exception:
            return None
        dosya.save(hedef)
    return ad


def tablo_oku(dosya, uz):
    """CSV / Excel dosyasını DataFrame olarak okur.

    CSV'de kodlama (UTF-8, Türkçe Windows) ve ayırıcı (virgül, noktalı virgül, sekme) kendiliğinden
    bulunur: Türkçe Excel'in 'CSV olarak kaydet' çıktısı noktalı virgüllü ve cp1254 kodlamalıdır.
    """
    import pandas as pd
    if uz != 'csv':
        return pd.read_excel(dosya, dtype=object)
    ham = dosya.read()
    for kodlama in ('utf-8-sig', 'cp1254', 'latin-1'):
        try:
            metin = ham.decode(kodlama)
            break
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.StringIO(metin), sep=None, engine='python', dtype=object)

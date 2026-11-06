"""Gayrimenkul / ilan modülü ortak sabitleri."""

TURLER = [('arsa', 'Arsa'), ('tarla', 'Tarla'), ('konut', 'Konut'), ('isyeri', 'İşyeri'), ('bina', 'Bina')]
ALT_TURLER = {
    'konut': [('daire', 'Daire'), ('villa', 'Villa'), ('mustakil', 'Müstakil ev'), ('rezidans', 'Rezidans')],
    'isyeri': [('dukkan', 'Dükkân'), ('ofis', 'Ofis'), ('depo', 'Depo'), ('fabrika', 'Fabrika')],
}
TEKLIF_TIPLERI = [('satilik', 'Satılık'), ('kiralik', 'Kiralık'), ('kat_karsiligi', 'Kat karşılığı')]
DURUMLAR = [('hazirlaniyor', 'Hazırlanıyor'), ('pazarlamada', 'Pazarlamada'), ('opsiyonlu', 'Opsiyonlu'),
            ('anlasildi', 'Anlaşıldı'), ('geri_cekildi', 'Geri çekildi')]
AKTIF_DURUMLAR = ('pazarlamada', 'opsiyonlu')

ISINMA = ['Yok', 'Soba', 'Doğalgaz sobası', 'Kombi (doğalgaz)', 'Merkezi', 'Merkezi (pay ölçer)',
          'Yerden ısıtma', 'Klima', 'Isı pompası', 'Güneş enerjisi']
TAPU_DURUMLARI = ['Kat mülkiyetli', 'Kat irtifaklı', 'Hisseli tapu', 'Müstakil tapulu', 'Arsa tapulu',
                  'Kooperatif', 'Tapu kaydı yok']
TEMINAT_TURLERI = ['Banka teminat mektubu', 'İpotek', 'Çek / senet', 'Teminat yok']
TEVHID = [('yapildi', 'Yapıldı'), ('yapilacak', 'Yapılacak'), ('gerekmiyor', 'Gerekmiyor')]

OZELLIKLER = {
    'ic': ['Asansör', 'Ankastre mutfak', 'Amerikan mutfak', 'Ebeveyn banyosu', 'Giyinme odası', 'Çelik kapı',
           'Görüntülü diyafon', 'Klima', 'Laminat zemin', 'PVC doğrama', 'Şömine', 'Teras'],
    'dis': ['Otopark', 'Kapalı otopark', 'Güvenlik', 'Havuz', 'Bahçe', 'Oyun parkı', 'Spor alanı', 'Jeneratör',
            'Isı yalıtımı', 'Ses yalıtımı', 'Deprem yönetmeliğine uygun'],
    'muhit': ['Okul', 'Hastane', 'Market', 'Alışveriş merkezi', 'Park', 'Cami', 'Belediye', 'Denize yakın',
              'Göle yakın'],
    'ulasim': ['Otobüs durağı', 'Minibüs / dolmuş', 'Ana yol', 'Havalimanı', 'Liman', 'Feribot',
               'Tren istasyonu'],
    'cephe': ['Kuzey', 'Güney', 'Doğu', 'Batı'],
    'altyapi': ['yol', 'elektrik', 'su', 'dogalgaz', 'kanalizasyon', 'telefon', 'internet'],
}
OZELLIK_BASLIKLARI = {'ic': 'İç özellikler', 'dis': 'Dış özellikler', 'muhit': 'Muhit', 'ulasim': 'Ulaşım',
                      'cephe': 'Cephe', 'altyapi': 'Altyapı'}

ALTYAPI_ETIKETLERI = (('yol', 'Yol'), ('elektrik', 'Elektrik'), ('su', 'Su'),
                      ('dogalgaz', 'Doğalgaz'), ('kanalizasyon', 'Kanalizasyon'))


def etiket(liste, kod):
    """(kod, etiket) çiftleri listesinde kodun etiketini döndürür; yoksa kodun kendisi."""
    for k, e in liste:
        if k == kod:
            return e
    return kod

# Arsa Analiz ve Sunum Sistemi

Bu proje, arsa yatırımları için detaylı analiz ve sunum yapabilen bir web uygulamasıdır.

## Özellikler

- Kullanıcı yönetimi (kayıt, giriş, şifre sıfırlama)
- Arsa analizi oluşturma ve yönetme
- Otomatik SWOT analizi
- Fiyat tahmin modeli
- Bölgesel trend analizi
- PDF ve Word formatında rapor oluşturma
- Portföy yönetimi

## Yapılan Son Değişiklikler

### Kullanıcı Yönetimi
- [x] Kayıt formu validasyonları eklendi
- [x] Şifre eşleşme kontrolü eklendi
- [x] Minimum şifre uzunluğu kontrolü eklendi
- [x] E-posta benzersizlik kontrolü eklendi
- [x] Şifre sıfırlama sayfası oluşturuldu
- [x] Flash mesajları iyileştirildi

### Veritabanı
- [x] MySQL veritabanı bağlantısı kuruldu
- [x] Kullanıcı modeli güncellendi
- [x] Arsa analiz modeli güncellendi
- [x] Portföy modeli eklendi

### Analiz Sistemi
- [x] Arsa analiz formu oluşturuldu
- [x] Otomatik SWOT analizi eklendi
- [x] Fiyat tahmin modeli entegre edildi
- [x] Bölgesel trend analizi eklendi

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Veritabanını oluşturun:
```bash
python bootstrap.py
```

3. Uygulamayı başlatın:
```bash
python app.py
```

## Geliştirme Yapılacaklar

- [ ] Daha detaylı bölge analizi
- [ ] Gelişmiş fiyat tahmin modeli
- [ ] Mobil uyumlu arayüz
- [ ] Çoklu dil desteği
- [ ] API entegrasyonu
 

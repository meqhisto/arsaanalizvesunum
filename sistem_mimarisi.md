# Arsa Yatırım Danışmanlığı Sunum Sistemi - Sistem Mimarisi

## Genel Bakış
Bu sistem, arsa yatırım danışmanlarının müşterilerine sunumlar hazırlamasını otomatikleştirmek için tasarlanmıştır. Sistem, kullanıcının girdiği arsa bilgilerini alarak otomatik olarak özet çıkarır ve profesyonel bir sunum dosyası oluşturur.

## Sistem Bileşenleri

### 1. Veri Giriş Modülü
- Web tabanlı form arayüzü
- Arsa bilgilerinin yapılandırılmış şekilde alınması
- Veri doğrulama ve temizleme

### 2. Veri İşleme ve Analiz Modülü
- Arsa değer analizi
- Potansiyel getiri hesaplaması
- Bölgesel karşılaştırma

### 3. Sunum Oluşturma Modülü
- Word şablonu işleme
- PowerPoint şablonu işleme
- Dinamik içerik yerleştirme

### 4. Kullanıcı Arayüzü
- Basit ve kullanıcı dostu web arayüzü
- Sonuçların görüntülenmesi ve indirilmesi

## Teknoloji Seçimleri

### Backend
- Python: Veri işleme ve analiz için
- Flask: Web uygulaması çerçevesi olarak
- pandas: Veri analizi için

### Sunum Oluşturma
- python-docx: Word belgeleri oluşturmak için
- python-pptx: PowerPoint sunumları oluşturmak için

### Frontend
- HTML/CSS/JavaScript: Kullanıcı arayüzü için
- Bootstrap: Duyarlı tasarım için

## Veri Modeli

### Arsa Bilgileri
- konum: Arsanın bulunduğu il, ilçe, mahalle
- metrekare: Arsanın büyüklüğü (m²)
- imar_durumu: Arsanın imar durumu (konut, ticari, karma vb.)
- fiyat: Arsanın güncel fiyatı (TL)
- bolge_fiyat: Bölgedeki emsal metrekare fiyatı (TL/m²)

### Analiz Sonuçları
- metrekare_fiyat: Arsanın metrekare başına fiyatı (TL/m²)
- bolge_karsilastirma: Bölge ortalamasına göre fiyat karşılaştırması (%)
- potansiyel_getiri: Tahmini yıllık getiri oranı (%)
- yatirim_suresi: Tavsiye edilen minimum yatırım süresi (yıl)

## İş Akışı
1. Kullanıcı web arayüzünden arsa bilgilerini girer
2. Sistem verileri doğrular ve analiz eder
3. Potansiyel getiri hesaplanır
4. Seçilen formatta (Word/PowerPoint) sunum oluşturulur
5. Kullanıcı oluşturulan sunumu indirir

## Dosya Yapısı
```
arsa_sunum_sistemi/
├── app.py                  # Ana uygulama dosyası
├── templates/              # HTML şablonları
│   ├── index.html          # Ana sayfa
│   └── sonuc.html          # Sonuç sayfası
├── static/                 # Statik dosyalar
│   ├── css/                # CSS dosyaları
│   ├── js/                 # JavaScript dosyaları
│   └── img/                # Görsel dosyaları
├── modules/                # Python modülleri
│   ├── veri_isleyici.py    # Veri işleme fonksiyonları
│   ├── analiz.py           # Analiz fonksiyonları
│   └── sunum_olusturucu.py # Sunum oluşturma fonksiyonları
└── templates/              # Sunum şablonları
    ├── word_template.docx  # Word şablonu
    └── ppt_template.pptx   # PowerPoint şablonu
```

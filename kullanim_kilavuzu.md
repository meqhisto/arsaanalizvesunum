# Arsa Yatırım Danışmanlığı Sunum Sistemi - Kullanım Kılavuzu

## İçindekiler
1. [Sistem Hakkında](#sistem-hakkında)
2. [Kurulum](#kurulum)
3. [Kullanım](#kullanım)
4. [Sistem Mimarisi](#sistem-mimarisi)
5. [Sorun Giderme](#sorun-giderme)
6. [Sık Sorulan Sorular](#sık-sorulan-sorular)

## Sistem Hakkında

Arsa Yatırım Danışmanlığı Sunum Sistemi, arsa yatırım danışmanlarının müşterilerine sunumlar hazırlamasını otomatikleştirmek için tasarlanmış bir web uygulamasıdır. Bu sistem, kullanıcının girdiği arsa bilgilerini analiz ederek potansiyel getiri hesaplar ve profesyonel Word veya PowerPoint sunumları oluşturur.

### Temel Özellikler

- **Kullanıcı Dostu Arayüz**: Arsa bilgilerini kolayca girebileceğiniz web tabanlı form
- **Otomatik Analiz**: Arsa değeri, bölge karşılaştırması ve potansiyel getiri hesaplama
- **Profesyonel Sunumlar**: Word ve PowerPoint formatlarında otomatik sunum oluşturma
- **Detaylı Raporlama**: Yatırım değerlendirmesi ve tavsiyeler içeren kapsamlı raporlar

## Kurulum

### Sistem Gereksinimleri

- Python 3.6 veya üzeri
- Flask web çerçevesi
- python-docx ve python-pptx kütüphaneleri
- pandas veri analizi kütüphanesi

### Kurulum Adımları

1. Sistemi indirin veya klonlayın:
   ```
   git clone https://github.com/kullanici/arsa_sunum_sistemi.git
   cd arsa_sunum_sistemi
   ```

2. Gerekli Python paketlerini yükleyin:
   ```
   pip install flask python-docx python-pptx pandas
   ```

3. Gerekli dizinleri oluşturun:
   ```
   mkdir -p data output templates/sunum
   ```

4. Uygulamayı başlatın:
   ```
   python app.py
   ```

5. Web tarayıcınızda aşağıdaki adresi açın:
   ```
   http://localhost:5000
   ```

## Kullanım

### Arsa Bilgilerini Girme

1. Ana sayfadaki formu açın.
2. Aşağıdaki bilgileri doldurun:
   - **Konum Bilgileri**: İl, ilçe ve mahalle
   - **Arsa Bilgileri**: Metrekare ve imar durumu
   - **Fiyat Bilgileri**: Arsa fiyatı ve bölge metrekare fiyatı
3. "Analiz Et ve Sunum Oluştur" butonuna tıklayın.

### Analiz Sonuçlarını İnceleme

Analiz sonuçları sayfasında şu bilgileri göreceksiniz:

- **Arsa Bilgileri**: Girdiğiniz temel bilgiler
- **Analiz Sonuçları**: 
  - Bölge karşılaştırması (bölge ortalamasına göre fiyat farkı)
  - Potansiyel getiri oranı
  - Tavsiye edilen minimum yatırım süresi
- **Yatırım Değerlendirmesi**: Arsanın yatırım potansiyeli hakkında genel değerlendirme

### Sunum Oluşturma

Analiz sonuçları sayfasında iki seçenek bulunur:

1. **Word Belgesi Oluştur**: Detaylı bir Word raporu oluşturur
2. **PowerPoint Sunumu Oluştur**: Sunum için PowerPoint dosyası oluşturur

İstediğiniz formatta dosyayı indirmek için ilgili butona tıklayın.

## Sistem Mimarisi

Arsa Yatırım Danışmanlığı Sunum Sistemi, modüler bir yapıda tasarlanmıştır ve aşağıdaki bileşenlerden oluşur:

### 1. Veri Giriş Modülü
- Web tabanlı form arayüzü (HTML/CSS/JavaScript)
- Form validasyonu ve veri temizleme

### 2. Veri İşleme ve Analiz Modülü
- `veri_isleyici.py`: Arsa verilerini kaydetme ve yükleme
- `analiz.py`: Arsa değer analizi ve potansiyel getiri hesaplama

### 3. Sunum Oluşturma Modülü
- `sunum_olusturucu.py`: Word ve PowerPoint sunumları oluşturma
- Şablon yönetimi ve dinamik içerik yerleştirme

### 4. Ana Uygulama
- `app.py`: Flask web uygulaması ve rota yönetimi
- Modüller arası entegrasyon ve kullanıcı arayüzü

### Dosya Yapısı

```
arsa_sunum_sistemi/
├── app.py                  # Ana uygulama dosyası
├── modules/                # Python modülleri
│   ├── veri_isleyici.py    # Veri işleme fonksiyonları
│   ├── analiz.py           # Analiz fonksiyonları
│   └── sunum_olusturucu.py # Sunum oluşturma fonksiyonları
├── templates/              # HTML şablonları
│   ├── index.html          # Ana sayfa
│   ├── sonuc.html          # Sonuç sayfası
│   └── sunum/              # Sunum şablonları
│       ├── word_template.docx  # Word şablonu
│       └── ppt_template.pptx   # PowerPoint şablonu
├── static/                 # Statik dosyalar
│   ├── css/                # CSS dosyaları
│   └── js/                 # JavaScript dosyaları
├── data/                   # Veri dosyaları
└── output/                 # Oluşturulan sunumlar
```

## Sorun Giderme

### Yaygın Sorunlar ve Çözümleri

#### 1. Uygulama Başlatma Sorunları

**Sorun**: Uygulama başlatılırken "Address already in use" hatası alınıyor.

**Çözüm**: Başka bir port kullanın:
```
python app.py --port=5001
```

#### 2. Form Gönderme Sorunları

**Sorun**: Form gönderildiğinde hata alınıyor.

**Çözüm**: 
- Tüm zorunlu alanların doldurulduğundan emin olun
- Sayısal değerlerin doğru formatta olduğunu kontrol edin
- Tarayıcı konsolunda hata mesajlarını kontrol edin

#### 3. Sunum Oluşturma Sorunları

**Sorun**: Sunum dosyaları oluşturulamıyor.

**Çözüm**:
- `output` dizininin yazma izinlerini kontrol edin
- Gerekli kütüphanelerin doğru şekilde yüklendiğinden emin olun
- Uygulama loglarını kontrol edin

#### 4. Dış Erişim Sorunları

**Sorun**: Uygulama dış erişime açık değil veya "ERR_EMPTY_RESPONSE" hatası alınıyor.

**Çözüm**:
- Uygulamayı `--host=0.0.0.0` parametresiyle başlatın
- Güvenlik duvarı ayarlarını kontrol edin
- Proxy ayarlarını kontrol edin
- Gunicorn veya uWSGI gibi bir WSGI sunucusu kullanmayı deneyin

## Sık Sorulan Sorular

### 1. Sistem hangi arsa türleri için kullanılabilir?
Sistem her türlü arsa için kullanılabilir: konut, ticari, karma, sanayi veya diğer imar durumlarına sahip arsalar.

### 2. Potansiyel getiri hesaplaması neye dayanıyor?
Potansiyel getiri hesaplaması, arsa imar durumu, bölge fiyat karşılaştırması ve arsa büyüklüğü gibi faktörlere dayanır. Hesaplama algoritması, farklı imar durumları için farklı katsayılar kullanır ve bölge ortalamasına göre fiyat farkını dikkate alır.

### 3. Sunumları özelleştirebilir miyim?
Şu anki sürümde sunumlar otomatik olarak oluşturulur. Gelecek sürümlerde şablon özelleştirme ve içerik düzenleme özellikleri eklenecektir.

### 4. Sistem çevrimdışı çalışabilir mi?
Evet, sistem tamamen yerel olarak çalışabilir ve internet bağlantısı gerektirmez. Sadece Bootstrap CSS dosyaları için CDN bağlantısı kullanılmaktadır, bu da gerekirse yerel dosyalarla değiştirilebilir.

### 5. Verileri kaydediyor musunuz?
Evet, girilen arsa bilgileri ve analiz sonuçları JSON formatında `data` dizininde saklanır. Bu, geçmiş analizlere erişim sağlar ve karşılaştırma yapmanıza olanak tanır.

---

Bu kullanım kılavuzu, Arsa Yatırım Danışmanlığı Sunum Sistemi'nin temel özelliklerini ve kullanımını açıklamaktadır. Sorularınız veya geri bildirimleriniz için lütfen iletişime geçin.

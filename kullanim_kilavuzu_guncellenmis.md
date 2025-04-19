# Arsa Yatırım Danışmanlığı Sunum Sistemi - Güncellenmiş Kullanım Kılavuzu

## İçindekiler
1. [Sistem Hakkında](#sistem-hakkında)
2. [Yeni Özellikler](#yeni-özellikler)
3. [Kurulum](#kurulum)
4. [Kullanım](#kullanım)
5. [Sistem Mimarisi](#sistem-mimarisi)
6. [Sorun Giderme](#sorun-giderme)
7. [Sık Sorulan Sorular](#sık-sorulan-sorular)

## Sistem Hakkında

Arsa Yatırım Danışmanlığı Sunum Sistemi, arsa yatırım danışmanlarının müşterilerine sunumlar hazırlamasını otomatikleştirmek için tasarlanmış bir web uygulamasıdır. Bu sistem, kullanıcının girdiği arsa bilgilerini analiz ederek potansiyel getiri hesaplar ve profesyonel Word veya PowerPoint sunumları oluşturur.

### Temel Özellikler

- **Kullanıcı Dostu Arayüz**: Arsa bilgilerini kolayca girebileceğiniz web tabanlı form
- **Otomatik Analiz**: Arsa değeri, bölge karşılaştırması ve potansiyel getiri hesaplama
- **Profesyonel Sunumlar**: Word ve PowerPoint formatlarında otomatik sunum oluşturma
- **Detaylı Raporlama**: Yatırım değerlendirmesi ve tavsiyeler içeren kapsamlı raporlar

## Yeni Özellikler

### 1. Parselsorgu.tkgm.gov.tr Entegrasyonu
Sistem artık parselsorgu.tkgm.gov.tr'den otomatik olarak arsa bilgilerini çekebilmektedir:

- **Otomatik Alan Hesaplama**: İl, ilçe, mahalle, ada ve parsel bilgileri girilerek arsanın alanı otomatik olarak hesaplanır
- **Tek Tıkla Veri Çekme**: "Parsel Bilgilerini Getir" butonu ile tek tıklamayla bilgiler alınır
- **Doğru ve Güncel Bilgiler**: Tapu Kadastro Genel Müdürlüğü'nün resmi veritabanından alınan doğru ve güncel bilgiler

### 2. Sahibinden.com Entegrasyonu
Sistem artık sahibinden.com'dan bölge fiyat bilgilerini otomatik olarak çekebilmektedir:

- **Bölge Fiyat Analizi**: Belirtilen bölgedeki emsal arsaların fiyat bilgileri otomatik olarak çekilir
- **Karşılaştırmalı Analiz**: Ortalama, minimum ve maksimum metrekare fiyatları hesaplanır
- **Piyasa Değeri Tespiti**: Bölgedeki benzer arsaların fiyatlarına göre piyasa değeri belirlenir

### 3. TAKS/KAKS Hesaplama
Sistem artık TAKS (Taban Alanı Katsayısı) ve KAKS (Kat Alanı Katsayısı) değerlerine göre inşaat alanı hesaplayabilmektedir:

- **İnşaat Alanı Hesaplama**: TAKS ve KAKS değerlerine göre yapılabilecek inşaat alanı hesaplanır
- **Kat Sayısı Analizi**: Teorik kat sayısı ve tam kat sayısı hesaplanır
- **Yapılaşma Potansiyeli**: Arsanın yapılaşma potansiyeli detaylı olarak analiz edilir

## Kurulum

### Sistem Gereksinimleri

- Python 3.6 veya üzeri
- Flask web çerçevesi
- python-docx ve python-pptx kütüphaneleri
- pandas veri analizi kütüphanesi
- BeautifulSoup4 ve requests kütüphaneleri (web scraping için)

### Kurulum Adımları

1. Sistemi indirin veya klonlayın:
   ```
   git clone https://github.com/kullanici/arsa_sunum_sistemi.git
   cd arsa_sunum_sistemi
   ```

2. Gerekli Python paketlerini yükleyin:
   ```
   pip install flask python-docx python-pptx pandas beautifulsoup4 requests
   ```

3. Gerekli dizinleri oluşturun:
   ```
   mkdir -p data output templates/sunum tests
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
   - **Parsel Bilgileri**: İl, ilçe, mahalle, ada ve parsel numarası
   - **Arsa Bilgileri**: Metrekare ve imar durumu
   - **TAKS/KAKS Bilgileri**: Taban Alanı Katsayısı ve Kat Alanı Katsayısı (arsa niteliğindeki gayrimenkuller için)
   - **Fiyat Bilgileri**: Arsa fiyatı ve bölge metrekare fiyatı

3. Otomatik veri çekme özelliklerini kullanın:
   - **Parsel Bilgilerini Getir**: Parselsorgu.tkgm.gov.tr'den arsa alanı bilgisini otomatik çeker
   - **Bölge Fiyat Bilgilerini Getir**: Sahibinden.com'dan bölge fiyat bilgilerini otomatik çeker

4. "Analiz Et ve Sunum Oluştur" butonuna tıklayın.

### Analiz Sonuçlarını İnceleme

Analiz sonuçları sayfasında şu bilgileri göreceksiniz:

- **Arsa Bilgileri**: Girdiğiniz temel bilgiler ve parsel bilgileri
- **Analiz Sonuçları**: 
  - Bölge karşılaştırması (bölge ortalamasına göre fiyat farkı)
  - Potansiyel getiri oranı
  - Tavsiye edilen minimum yatırım süresi
- **İnşaat Alanı Hesaplaması** (TAKS/KAKS bilgileri girildiyse):
  - Taban alanı
  - Toplam inşaat alanı
  - Teorik kat sayısı
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

### 3. Web Scraping Modülü
- `web_scraping.py`: Parselsorgu.tkgm.gov.tr ve sahibinden.com'dan veri çekme
- `ParselSorgu`: Parsel bilgilerini çekme sınıfı
- `SahibindenScraper`: Bölge fiyat bilgilerini çekme sınıfı
- `InsaatAlaniHesaplayici`: TAKS/KAKS hesaplama sınıfı

### 4. Sunum Oluşturma Modülü
- `sunum_olusturucu.py`: Word ve PowerPoint sunumları oluşturma
- Şablon yönetimi ve dinamik içerik yerleştirme

### 5. Ana Uygulama
- `app.py`: Flask web uygulaması ve rota yönetimi
- Modüller arası entegrasyon ve kullanıcı arayüzü

### Dosya Yapısı

```
arsa_sunum_sistemi/
├── app.py                  # Ana uygulama dosyası
├── modules/                # Python modülleri
│   ├── veri_isleyici.py    # Veri işleme fonksiyonları
│   ├── analiz.py           # Analiz fonksiyonları
│   ├── web_scraping.py     # Web scraping fonksiyonları
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
│       ├── validation.js   # Form validasyon dosyası
│       └── parselsorgu.js  # Parselsorgu ve bölge fiyat işlemleri
├── tests/                  # Test dosyaları
│   ├── test_taks_kaks.py   # TAKS/KAKS testi
│   ├── test_sahibinden.py  # Sahibinden.com testi
│   └── test_entegre_sistem.py # Entegre sistem testi
├── data/                   # Veri dosyaları
└── output/                 # Oluşturulan sunumlar
```

## Sorun Giderme

### Yaygın Sorunlar ve Çözümleri

#### 1. Parselsorgu.tkgm.gov.tr Bağlantı Sorunları

**Sorun**: Parsel bilgileri çekilirken "Bağlantı hatası" alınıyor.

**Çözüm**: 
- İnternet bağlantınızı kontrol edin
- Parselsorgu.tkgm.gov.tr sitesinin çalışır durumda olduğunu doğrulayın
- Girilen il, ilçe, mahalle, ada ve parsel bilgilerinin doğru olduğunu kontrol edin
- Tarayıcınızda manuel olarak parselsorgu.tkgm.gov.tr sitesine erişebildiğinizi doğrulayın

#### 2. Sahibinden.com Veri Çekme Sorunları

**Sorun**: Bölge fiyat bilgileri çekilirken hata alınıyor.

**Çözüm**:
- İnternet bağlantınızı kontrol edin
- Sahibinden.com sitesinin çalışır durumda olduğunu doğrulayın
- Girilen bölge bilgilerinin doğru olduğunu kontrol edin
- Belirtilen bölgede yeterli sayıda ilan olduğunu kontrol edin
- Sahibinden.com'un robot engelleme sistemleri nedeniyle çok sık sorgu yapmaktan kaçının

#### 3. TAKS/KAKS Hesaplama Sorunları

**Sorun**: İnşaat alanı hesaplaması hatalı sonuçlar veriyor.

**Çözüm**:
- TAKS değerinin 0-1 arasında olduğunu kontrol edin
- KAKS değerinin pozitif bir sayı olduğunu kontrol edin
- Arsa alanının doğru girildiğini kontrol edin
- Hesaplamaları manuel olarak doğrulayın (Taban Alanı = Arsa Alanı × TAKS, Toplam İnşaat Alanı = Arsa Alanı × KAKS)

#### 4. Uygulama Başlatma Sorunları

**Sorun**: Uygulama başlatılırken "Address already in use" hatası alınıyor.

**Çözüm**: 
- Başka bir port kullanın:
```
python app.py --port=5001
```

## Sık Sorulan Sorular

### 1. Parselsorgu.tkgm.gov.tr'den çekilen bilgiler ne kadar günceldir?
Parselsorgu.tkgm.gov.tr, Tapu Kadastro Genel Müdürlüğü'nün resmi sitesidir ve en güncel parsel bilgilerini içerir. Ancak, sistemdeki güncellemeler ve bakım çalışmaları nedeniyle bazen bilgiler birkaç gün gecikmeli olabilir.

### 2. Sahibinden.com'dan çekilen fiyat bilgileri ne kadar doğrudur?
Sahibinden.com'dan çekilen fiyat bilgileri, ilan sahiplerinin belirlediği fiyatlardır ve gerçek piyasa değerinden farklı olabilir. Sistem, bu fiyatların ortalamasını alarak daha doğru bir değer sunmaya çalışır, ancak profesyonel bir değerleme için emlak değerleme uzmanlarına danışmanız önerilir.

### 3. TAKS ve KAKS değerlerini nereden bulabilirim?
TAKS ve KAKS değerleri, arsanın bulunduğu bölgenin imar planında belirtilir. Bu bilgileri belediyenin imar müdürlüğünden veya e-imar uygulamalarından öğrenebilirsiniz. Ayrıca, tapu belgelerinde veya imar durum belgesinde de bu bilgiler yer alabilir.

### 4. Sistem hangi arsa türleri için kullanılabilir?
Sistem her türlü arsa için kullanılabilir: konut, ticari, karma, sanayi veya diğer imar durumlarına sahip arsalar. TAKS/KAKS hesaplama özelliği özellikle arsa niteliğindeki gayrimenkuller için faydalıdır.

### 5. Potansiyel getiri hesaplaması neye dayanıyor?
Potansiyel getiri hesaplaması, arsa imar durumu, bölge fiyat karşılaştırması ve arsa büyüklüğü gibi faktörlere dayanır. Hesaplama algoritması, farklı imar durumları için farklı katsayılar kullanır ve bölge ortalamasına göre fiyat farkını dikkate alır.

### 6. Sunumları özelleştirebilir miyim?
Şu anki sürümde sunumlar otomatik olarak oluşturulur. Gelecek sürümlerde şablon özelleştirme ve içerik düzenleme özellikleri eklenecektir.

### 7. Sistem çevrimdışı çalışabilir mi?
Parselsorgu.tkgm.gov.tr ve sahibinden.com entegrasyonları internet bağlantısı gerektirir. Ancak, bu özellikler kullanılmadan, manuel veri girişi ile sistem çevrimdışı olarak da kullanılabilir.

### 8. Verileri kaydediyor musunuz?
Evet, girilen arsa bilgileri ve analiz sonuçları JSON formatında `data` dizininde saklanır. Bu, geçmiş analizlere erişim sağlar ve karşılaştırma yapmanıza olanak tanır.

---

Bu kullanım kılavuzu, Arsa Yatırım Danışmanlığı Sunum Sistemi'nin temel özelliklerini ve kullanımını açıklamaktadır. Sorularınız veya geri bildirimleriniz için lütfen iletişime geçin.

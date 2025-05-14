# Arsa Analiz ve Sunum Platformu

Bu proje, arsa analizleri, CRM yönetimi, portföy takibi ve kullanıcı profili gibi işlevleri bir arada sunan modern bir web uygulamasıdır. Flask tabanlıdır ve Bootstrap ile şık, mobil uyumlu bir arayüze sahiptir.

## Özellikler

- **Arsa Analizleri:** Kullanıcılar arsa analizleri oluşturabilir, detaylarını görüntüleyebilir ve çıktı alabilir.
- **CRM Modülü:** Kişiler, şirketler, fırsatlar ve görevler için kapsamlı bir CRM yönetimi sunar.
- **Portföy Yönetimi:** Portföy ekleme, listeleme ve detay görüntüleme.
- **Kullanıcı Profili:** Profil bilgileri ve ayarları yönetilebilir.
- **Hatırlatıcılar:** Görev ve fırsatlar için bildirim sistemi.
- **Mobil ve Masaüstü Uyumlu:** Sidebar ve menüler tüm cihazlarda tutarlı ve kullanıcı dostu.
- **Gelişmiş Menü Aktiflik Kontrolü:** Sadece aktif sayfa linkinde "active" class'ı bulunur.
- **Güncel Kod Yapısı:** Blueprints, modeller ve modüller ile ölçeklenebilir mimari.

## Kurulum

1. **Gereksinimler:**
   - Python 3.9+
   - pip

2. **Bağımlılıkları Yükleyin:**

   ```pwsh
   pip install -r requirements.txt
   ```

3. **Veritabanı Kurulumu:**

   ```pwsh
   python create_tables.py
   # veya
   python db_update.py
   ```

4. **Uygulamayı Başlatın:**

   ```pwsh
   python app.py
   ```
   Uygulama varsayılan olarak `http://127.0.0.1:5000` adresinde çalışır.

## Proje Yapısı

- `app.py`                : Ana uygulama dosyası
- `models/`               : SQLAlchemy modelleri
- `blueprints/`           : Flask blueprint dosyaları (modüler yapı)
- `templates/`            : Jinja2 HTML şablonları
- `static/`               : CSS, JS ve medya dosyaları
- `modules/`              : Analiz, rapor üretimi ve yardımcı modüller
- `routes/`               : Ek rota dosyaları
- `data/`                 : JSON ve veri dosyaları
- `output/`               : Oluşturulan rapor ve sunum çıktıları
- `instance/config.py`    : Konfigürasyon dosyası

## Kullanım

- Sisteme giriş yaptıktan sonra ana panelden analiz, CRM, portföy ve profil modüllerine erişebilirsiniz.
- CRM modülünde kişiler, şirketler, fırsatlar ve görevler sekmeleri bulunur.
- Analizler bölümünde yeni analiz oluşturabilir veya mevcut analizleri inceleyebilirsiniz.
- Portföyler sekmesinden portföy ekleyebilir ve yönetebilirsiniz.

## Geliştirici Notları

- Menü ve sidebar yapısı Flask'ın `request.endpoint` özelliği ile dinamik olarak aktiflik kontrolü sağlar.
- Kodda blueprint ve modül ayrımı ile ölçeklenebilirlik ve sürdürülebilirlik ön planda tutulmuştur.
- Hatalar ve loglar `app.log` dosyasında tutulur.
- Geliştirme sırasında `requirements.txt` dosyasını güncel tutunuz.

## Sık Karşılaşılan Sorunlar

- **404 Hatası:** Blueprint veya rota tanımlarını ve şablon dosya yollarını kontrol edin.
- **Veritabanı Hataları:** `create_tables.py` veya `db_update.py` ile veritabanı tablolarını oluşturun.
- **Statik Dosya Sorunları:** `static/` klasöründeki dosya yollarını ve referanslarını kontrol edin.

## Katkı ve Lisans

Katkıda bulunmak için fork'layıp pull request gönderebilirsiniz. Proje MIT lisansı ile lisanslanmıştır.

---

Her türlü soru ve destek için proje yöneticisine ulaşabilirsiniz.


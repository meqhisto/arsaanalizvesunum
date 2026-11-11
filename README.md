# Arsa Analiz ve Sunum Platformu

Modern API-driven frontend for Arsa Analiz ve Sunum Platformu. This project is built using Flask for the backend, Node.js + Webpack for the frontend, and PostgreSQL for the database.

## Prerequisites

- Docker
- Docker Compose

## Getting Started with Docker

You can run the entire application using Docker Compose.

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_folder>
    ```

2.  **Build and start the containers:**
    ```bash
    docker-compose up --build
    ```

3.  **Access the application:**
    Open your browser and navigate to `http://localhost:5000`.

## Architecture

- **Web Service (`web`):** Runs the Flask application using Gunicorn and builds the frontend assets with Webpack during the Docker image build.
- **Database Service (`db`):** Uses a PostgreSQL 15 database.

## Environment Variables

The `docker-compose.yml` uses the following environment variables for configuration:

- `FLASK_APP=app.py`
- `FLASK_ENV=development`
- `DATABASE_URL=postgresql://postgres:postgres@db:5432/arsa_analiz`
- `SECRET_KEY=my-secret-key`

If you are running in production, please make sure to override the `SECRET_KEY` and use a secure one.


## Sunucuya (production) kurulum

Geliştirme için olan `docker-compose.yml` yerine `docker-compose.server.yml` kullanılır. Bu dosya gizli bilgileri `.env` dosyasından okur, veritabanı portunu dışarı açmaz ve yüklenen dosyaları kalıcı volume'lerde saklar.

1. `.env` dosyasını oluşturun (değerleri rastgele ve güçlü seçin):
   ```
   POSTGRES_USER=arsa
   POSTGRES_PASSWORD=<guclu-sifre>
   POSTGRES_DB=arsa_analiz
   DATABASE_URL=postgresql://arsa:<guclu-sifre>@db:5432/arsa_analiz
   SECRET_KEY=<rastgele-anahtar>
   JWT_SECRET_KEY=<rastgele-anahtar>
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```
2. Başlatın: `docker compose -f docker-compose.server.yml up -d --build`
3. Güncelleme: `git pull && docker compose -f docker-compose.server.yml up -d --build`

Kayıt sayfası kapalı olduğundan ilk yönetici hesabı uygulama konteyneri içinden oluşturulur
(`User(email=..., role='superadmin')` + `set_password(...)`).

## İş takip modülü

`/isler` altında ofisin yürüttüğü işler (arsa satışı, alım öncesi inceleme, imar/ruhsat, kat karşılığı) adım adım takip edilir.

- İşin adımları CRM görevleridir (`crm_tasks.is_id`). Bu yüzden görev listesi ve hatırlatmalar adımlar için de çalışır.
- Tablolar ve görev tablosuna eklenen `is_id` / `sira` sütunları açılışta otomatik oluşturulur (`modules/is_takip_kurulum.py`). Hazır şablonlar da yalnızca yoksa eklenir.
- Belgeler `private_uploads/isler/` altında tutulur ve yalnızca yetki kontrolü yapan indirme adresinden açılır. Docker'da bu klasör `is_belgeleri` volume'ündedir.

### Günlük hatırlatma

Geciken ve yaklaşan adımlar için bildirimler günde bir kez üretilir. Sunucuda örnek cron satırı (her sabah 08:00):

```
0 8 * * * cd /opt/arsaanalizvesunum && docker compose -f docker-compose.server.yml exec -T web flask --app "app:create_app()" is-takip hatirlat >> /var/log/is-takip-hatirlat.log 2>&1
```

## Gayrimenkul ve İlanlar

Kayıtlar iki katmanlıdır: **gayrimenkul** (fiziksel mülk: arsa, tarla, konut, işyeri, bina; tabloda `arsa_analizleri`)
ve **ilan** (`/ilanlar`; satılık, kiralık ya da kat karşılığı teklif). Bir ilan birden çok gayrimenkulü içerebilir
(ör. aynı sahibin komşu parsellerinden kat karşılığı ilanı); bir gayrimenkul aynı anda yalnız bir aktif
(pazarlamada / opsiyonlu) ilanda olabilir.

- Gayrimenkul ekranları `/analysis` altında kalır (eski bağlantılar çalışır); form türe göre alanları gösterir,
  mal sahipleri CRM müşterilerinden hisseleriyle seçilir ve "Hemen ilana çıkar" ile ilan aynı anda açılabilir.
- Fiyat, kira, bölge m² fiyatı, emsaller ve kat karşılığı şartları ilandadır. Raporlar ilandan üretilir
  (`/ilanlar/<id>/rapor/<pdf|word|pptx>`); eski gayrimenkul rapor adresleri aktif ilan varsa onun raporuna yönlenir,
  yoksa fiyatsız tanıtım raporu üretir. Raporlarda mal sahibi bilgisi yer almaz.
- Portföyler ilan içerir; CRM fırsatları bir ilana bağlanabilir, müşteri detayında sahip olduğu gayrimenkuller görünür.
- Açılışta `modules/ilan_kurulum.py` yeni sütunları ekler ve mevcut veriyi bir kez dönüştürür (her gayrimenkul için
  tek gayrimenkullü satılık ilan, eski bölge fiyatı → m² fiyatı, portföy bağları); işaret `kurulum_isaretleri`
  tablosundaki `ilan_gecisi_v1` satırıdır. Canlıya almadan önce Supabase yedeği alınmalıdır.
- REST API (`/api/v1/analysis`) geriye dönük uyumludur; yanıtlara salt-okunur `tur`, `alt_tur`, `baslik` ve
  `aktif_ilan` (`{kod, teklif_tipi, durum, fiyat}` ya da `null`) eklenmiştir.
- `/api/v1/portfolio*` uç noktaları değiştirilmedi ve hâlâ eski `portfolio_arsalar` tablosunu okur. Web arayüzü bu
  tabloya artık yazmaz; tablo geçiş anındaki portföy içeriğinin anlık görüntüsü olarak kalır (yalnız eski API'nin
  ekleme uç noktası hâlâ yazabilir). Web portföyleri `portfolio_ilanlar` üzerinden ilan içerir; iki görünüm zamanla
  farklılaşabilir.

## Raporlar (PDF / Word / PowerPoint)

Rapor üretimi `modules/rapor/` paketindedir: `model.py` tüm hesapları bir kez yapar, `assets.py` grafik, konum haritası
(OpenStreetMap) ve QR kodları üretir, `pdf.py`, `word.py` ve `pptx_.py` aynı içeriği üç formatta çizer.

Marka bilgileri `.env` üzerinden ayarlanır; boş bırakılırsa raporu indiren kullanıcının profilindeki firma adı kullanılır:

| Değişken | Açıklama |
| --- | --- |
| `REPORT_BRAND_NAME` | Üst bilgi ve kapakta görünen marka adı |
| `REPORT_BRAND_WEB` | Alt bilgideki web adresi (isteğe bağlı) |
| `REPORT_LOGO_PATH` | Logo dosyası (varsayılan `static/logo.png`) |
| `REPORT_PRIMARY_COLOR`, `REPORT_ACCENT_COLOR` | Ana ve vurgu rengi |
| `REPORT_TILE_URL` | Harita karo sunucusu (varsayılan OpenStreetMap) |

Değer projeksiyonu kaldırılmıştır; yerine **Fiyat ve Emsal Analizi** bölümü vardır. İlanın emsallerinden bölge m²
fiyatı (kat karşılığında ortalama arsa sahibi payı) hesaplanır; emsal yoksa ilandaki elle girilen bölge fiyatı
kullanılır. İstenen fiyat/pay bu ortalamayla karşılaştırılır ve konumlandırma (altında / aynı seviyede / üzerinde)
yazılır; emsal tablosu ve kat karşılığı şartları (sahibe düşen inşaat alanı, KAKS eksik parsel uyarısı) aynı
bölümdedir. Fiyatsız tanıtım raporunda bu bölüm boştur.

## Veritabanı: Supabase

Canlı ortam veritabanı olarak Supabase (PostgreSQL 17, Frankfurt) kullanır. Sunucunun IPv6 bağlantısı olmadığından doğrudan bağlantı yerine IPv4 **pooler (session modu, port 5432)** kullanılır:

```
DATABASE_URL=postgresql://<rol>.<proje-ref>:<şifre>@aws-1-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require&keepalives=1&keepalives_idle=30
```

- Uygulama `postgres` süper kullanıcısıyla değil, yalnızca `public` şemasında yetkili ayrı bir rolle (`arsa_app`) bağlanır.
- Supabase `public` şemasını REST API ile dışa açtığı için tüm tablolarda RLS açıktır ve `anon` / `authenticated` rollerinin tablo yetkileri kaldırılmıştır. Uygulama tabloların sahibi olduğu için RLS'den etkilenmez. Yeni tablo eklenirse aynı işlem yapılmalıdır:
  ```sql
  ALTER TABLE public.<tablo> ENABLE ROW LEVEL SECURITY;
  REVOKE ALL ON TABLE public.<tablo> FROM anon, authenticated;
  ```
- Gayrimenkul/ilan yapısının tabloları (`kurulum_isaretleri`, `gayrimenkul_sahipleri`, `ilanlar`, `ilan_gayrimenkulleri`,
  `ilan_emsalleri`, `portfolio_ilanlar`) için bu işlemi açılışta `modules/ilan_kurulum.py` `kur()` yapar (yalnız PostgreSQL):
  RLS kapalı olan tabloda `ALTER TABLE public.<tablo> ENABLE ROW LEVEL SECURITY` çalışır; `anon` / `authenticated` rolleri
  varsa ve bu tablolarda yetkileri kalmışsa `REVOKE ALL ON TABLE public.<tablo> FROM anon, authenticated` çalışır.
  Zaten tamamsa hiçbir şey çalıştırılmaz.
- Bağlantı havuzu `DB_POOL_SIZE` (varsayılan 3), `DB_MAX_OVERFLOW` (2) ve `DB_POOL_RECYCLE` (280 sn) ortam değişkenleriyle ayarlanır. `pool_pre_ping` açıktır.
- Ücretsiz planda Supabase yedekleri indirilemez. Yedek, PostgreSQL 17 istemcisiyle `pg_dump` alınarak sunucuda tutulur.
- Ücretsiz plan projeleri 7 gün düşük aktivitede duraklatılabilir. Duraklatılırsa Supabase panelinden "Resume project" ile açılır.

## Tarayıcı testleri

Ana kullanıcı akışları (giriş, gayrimenkul ve fotoğraf, ilan, müşteri, iş takip belgesi, profil, ofis logosu,
rapor, müşteri içe aktarma) gerçek tarayıcıda, Chromium ve iPhone 13 profilli WebKit ile denenir:

```bash
scripts/tarayici_testi.sh                 # tümü
scripts/tarayici_testi.sh -k fotograf     # ada göre seçerek
```

Betik, `arsaanalizvesunum-web` imajından uygulamanın izole bir kopyasını (SQLite, geçici klasörler) açar ve
depodaki güncel `templates`, `static/js`, `blueprints`, `utils`, `modules`, `models` ve `app.py` dosyalarını
üstüne bağlar. Canlı veritabanına ve canlı kapsayıcıya dokunmaz. Yeni bir Python bağımlılığı eklendiyse
önce imaj yeniden derlenmelidir. Her değişiklik birleştirilmeden önce bu testlerden geçmelidir.

## Yedek ve geri yükleme

`scripts/yedekle.sh` her çalıştığında iki dosya üretir (varsayılan klasör `/opt/arsa-backups`, 14 gün saklanır):

- `supabase_arsa_YYYYMMDD_HHMM.sql.gz`: veritabanı dökümü
- `dosyalar_YYYYMMDD_HHMM.tar.gz`: yüklenen fotoğraflar (`uploads/`), sunumlar (`presentations/`) ve iş belgeleri (`is_belgeleri/`)

Cron satırı:

```
0 0 * * * /opt/arsaanalizvesunum/scripts/yedekle.sh >> /var/log/arsa-yedek.log 2>&1
```

Yedeğin geri yüklenebildiğini doğrulamak için (canlı veriye yazmaz; dökümü geçici bir Postgres kapsayıcısına yükler):

```bash
scripts/yedek_dogrula.sh
```

Geri yükleme:

```bash
# Veritabanı (hedef veritabanı boş olmalı)
gzip -dc /opt/arsa-backups/supabase_arsa_<damga>.sql.gz | psql "$DATABASE_URL"
# Dosyalar: önce geçici bir klasöre açın, sonra ilgili birime kopyalayın
mkdir /tmp/geri && tar xzf /opt/arsa-backups/dosyalar_<damga>.tar.gz -C /tmp/geri
docker cp /tmp/geri/uploads/. arsaanalizvesunum-web-1:/app/static/uploads/
docker cp /tmp/geri/presentations/. arsaanalizvesunum-web-1:/app/static/presentations/
docker cp /tmp/geri/is_belgeleri/. arsaanalizvesunum-web-1:/app/private_uploads/
```

Yedekler şu an yalnızca aynı sunucuda durur; sunucu dışına kopya ayrıca kurulmalıdır.
Betiklerin testi: `tests/test_yedek.sh` (geçici kapsayıcı ve birimlerle çalışır).

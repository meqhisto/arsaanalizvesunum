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

Değer projeksiyonu analizdeki "Yıllık Değer Artış Oranı" alanını kullanır; boşsa model tahmini kullanılır.

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
- Bağlantı havuzu `DB_POOL_SIZE` (varsayılan 3), `DB_MAX_OVERFLOW` (2) ve `DB_POOL_RECYCLE` (280 sn) ortam değişkenleriyle ayarlanır. `pool_pre_ping` açıktır.
- Ücretsiz planda Supabase yedekleri indirilemez. Yedek, PostgreSQL 17 istemcisiyle `pg_dump` alınarak sunucuda tutulur.
- Ücretsiz plan projeleri 7 gün düşük aktivitede duraklatılabilir. Duraklatılırsa Supabase panelinden "Resume project" ile açılır.

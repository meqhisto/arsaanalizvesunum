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

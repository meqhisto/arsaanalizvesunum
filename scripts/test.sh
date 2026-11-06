#!/bin/bash
# Testleri yerel db konteynerindeki arsa_ilan_test veritabanında çalıştırır.
# Üretim (Supabase) DATABASE_URL'si ASLA kullanılmaz.
set -e
COMPOSE=/opt/arsaanalizvesunum/docker-compose.server.yml
cd /opt/arsaanalizvesunum
set -a; . ./.env; set +a
docker compose -f "$COMPOSE" up -d db >/dev/null 2>&1 || true
docker compose -f "$COMPOSE" exec -T db createdb -U "$POSTGRES_USER" arsa_ilan_test 2>/dev/null || true
TEST_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/arsa_ilan_test"
docker compose -f "$COMPOSE" run --rm --no-deps \
  -e DATABASE_URL="$TEST_URL" -e TEST_VERITABANI=1 \
  -v "${KOD:-/opt/arsa-ilan}:/app" -w /app --entrypoint sh web \
  -c "pip install -q -r requirements-dev.txt && python -m pytest $*"

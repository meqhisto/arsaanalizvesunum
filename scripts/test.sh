#!/bin/bash
# Testleri yerel db konteynerindeki arsa_ilan_test veritabanında çalıştırır.
# Üretim (Supabase) DATABASE_URL'si ASLA kullanılmaz.
set -e
# Test edilecek kod: varsayılan olarak bu betiğin bulunduğu depo (KOD ile değiştirilebilir)
KOD="${KOD:-$(cd "$(dirname "$0")/.." && pwd)}"
COMPOSE=/opt/arsaanalizvesunum/docker-compose.server.yml
cd /opt/arsaanalizvesunum
set -a; . ./.env; set +a
# Üretim compose projesinde hiçbir servisi başlatma/yeniden oluşturma; db yalnızca çalışıyorsa kullan
if ! docker compose -f "$COMPOSE" ps --status running --services 2>/dev/null | grep -qx db; then
  echo "HATA: '$COMPOSE' içindeki db servisi çalışmıyor. Testler db konteyneri çalışırken yürütülebilir;" >&2
  echo "      üretim ortamını bu betik başlatmaz, lütfen durumu kontrol edin." >&2
  exit 1
fi
docker compose -f "$COMPOSE" exec -T db createdb -U "$POSTGRES_USER" arsa_ilan_test 2>/dev/null || true
TEST_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/arsa_ilan_test"
docker compose -f "$COMPOSE" run --rm --no-deps \
  -e DATABASE_URL="$TEST_URL" -e TEST_VERITABANI=1 \
  -v "$KOD:/app" -w /app --entrypoint sh web \
  -c "pip install -q -r requirements-dev.txt && python -m pytest $*"

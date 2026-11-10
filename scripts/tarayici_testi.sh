#!/bin/bash
# Gerçek tarayıcı testleri: uygulamanın izole bir kopyasına (SQLite, geçici klasörler) karşı
# Chromium ve iPhone 13 profilli WebKit ile çalışır. Canlı veriye ve canlı kapsayıcıya dokunmaz.
# Kullanım: scripts/tarayici_testi.sh [pytest argümanları]     ör. scripts/tarayici_testi.sh -k test_giris
set -uo pipefail
KOK="$(cd "$(dirname "$0")/.." && pwd)"
IMAJ="${UYGULAMA_IMAJI:-arsaanalizvesunum-web}"
AG=arsa-e2e; UYG=arsa-e2e-app; TEST_IMAJI=arsa-e2e-test

temizle() { docker rm -f "$UYG" >/dev/null 2>&1; docker network rm "$AG" >/dev/null 2>&1; }
trap temizle EXIT
temizle
docker network create "$AG" >/dev/null || exit 2

# Deponun tamamı bağlanmaz: imajdaki webpack çıktısı (static/dist) gizlenmesin.
BAGLAR=()
for yol in templates static/js blueprints utils modules models app.py; do
  BAGLAR+=(-v "$KOK/$yol:/app/$yol:ro")
done
docker run -d --name "$UYG" --network "$AG" \
  -e DATABASE_URL=sqlite:////tmp/t.db -e SECRET_KEY=test -e JWT_SECRET_KEY=test \
  -e UPLOAD_FOLDER=/tmp/uploads_e2e -e IS_BELGE_KLASORU=/tmp/belge_e2e \
  "${BAGLAR[@]}" -v "$KOK/tests/tarayici:/tohum:ro" -w /app --entrypoint sh "$IMAJ" -c \
  "mkdir -p /tmp/uploads_e2e && rm -rf /app/static/uploads && ln -s /tmp/uploads_e2e /app/static/uploads \
   && python /tohum/tohum.py && exec gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 120 'app:create_app()'" >/dev/null || exit 2

docker build -q -t "$TEST_IMAJI" "$KOK/tests/tarayici" >/dev/null || exit 2

docker run --rm --network "$AG" -e TARAYICI_URL="http://$UYG:5000" \
  -v "$KOK/tests/tarayici:/tests/tarayici:ro" "$TEST_IMAJI" \
  python -m pytest /tests/tarayici -p no:cacheprovider "$@"
KOD=$?
if [ $KOD -ne 0 ]; then echo "--- uygulama logu (son 30 satır) ---"; docker logs --tail 30 "$UYG" 2>&1; fi
exit $KOD

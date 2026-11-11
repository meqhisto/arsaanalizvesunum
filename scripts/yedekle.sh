#!/bin/bash
# Gece yedeği: veritabanı dökümü + yüklenen dosyalar (fotoğraflar, sunumlar, iş belgeleri).
# Cron: 0 0 * * * /opt/arsaanalizvesunum/scripts/yedekle.sh >> /var/log/arsa-yedek.log 2>&1
#
# Ortam değişkenleri:
#   YEDEK_DIZINI  yedeklerin yazılacağı klasör            (varsayılan /opt/arsa-backups)
#   SAKLAMA_GUN   bundan eski yedekler silinir             (varsayılan 14)
#   PROJE         compose proje adı; birim adlarının öneki  (varsayılan arsaanalizvesunum)
#   DB_URL        veritabanı adresi                         (varsayılan: depodaki .env içindeki DATABASE_URL)
#   YEDEK_AG      pg_dump kapsayıcısının bağlanacağı Docker ağı (isteğe bağlı; yalnız testte gerekir)
#
# Her dosya önce .tmp olarak yazılır, doğrulanınca yeniden adlandırılır. Herhangi bir adım başarısız
# olursa betik sıfırdan farklı kodla çıkar ve eski yedekler silinmez.
set -euo pipefail
KOK="$(cd "$(dirname "$0")/.." && pwd)"
YEDEK_DIZINI="${YEDEK_DIZINI:-/opt/arsa-backups}"
SAKLAMA_GUN="${SAKLAMA_GUN:-14}"
PROJE="${PROJE:-arsaanalizvesunum}"
if [ -z "${DB_URL:-}" ]; then
  DB_URL=$(grep -E '^DATABASE_URL=' "$KOK/.env" 2>/dev/null | head -1 | cut -d= -f2- || true)
fi
if [ -z "${DB_URL:-}" ]; then echo "$(date -Is) HATA: DATABASE_URL bulunamadı" >&2; exit 1; fi
export DB_URL

DAMGA="$(date +%Y%m%d_%H%M)"
VT_DOSYA="$YEDEK_DIZINI/supabase_arsa_$DAMGA.sql.gz"
DOSYA_ARSIVI="$YEDEK_DIZINI/dosyalar_$DAMGA.tar.gz"
mkdir -p "$YEDEK_DIZINI"
umask 077
trap 'rm -f "$VT_DOSYA.tmp" "$DOSYA_ARSIVI.tmp"' EXIT

# 1) Veritabanı
AG_SECENEGI=(); [ -n "${YEDEK_AG:-}" ] && AG_SECENEGI=(--network "$YEDEK_AG")
docker run --rm "${AG_SECENEGI[@]}" -e DB_URL postgres:17-alpine \
  sh -c 'pg_dump "$DB_URL" --schema=public --no-owner --no-privileges' | gzip > "$VT_DOSYA.tmp"
if [ "$(gzip -dc "$VT_DOSYA.tmp" | grep -c '^CREATE TABLE')" -lt 10 ]; then
  echo "$(date -Is) HATA: veritabanı yedeği eksik görünüyor" >&2; exit 1
fi

# 2) Yüklenen dosyalar: üç birim tek arşivde, kök klasörleri uploads/ presentations/ is_belgeleri/
BIRIM_SECENEKLERI=()
for ad in uploads presentations is_belgeleri; do
  docker volume inspect "${PROJE}_$ad" >/dev/null 2>&1 || { echo "$(date -Is) HATA: ${PROJE}_$ad birimi yok" >&2; exit 1; }
  BIRIM_SECENEKLERI+=(-v "${PROJE}_$ad:/v/$ad:ro")
done
docker run --rm "${BIRIM_SECENEKLERI[@]}" alpine tar czf - -C /v uploads presentations is_belgeleri > "$DOSYA_ARSIVI.tmp"
gzip -t "$DOSYA_ARSIVI.tmp"

# 3) İkisi de sağlam: yerine koy, sonra eskileri sil
mv "$VT_DOSYA.tmp" "$VT_DOSYA"
mv "$DOSYA_ARSIVI.tmp" "$DOSYA_ARSIVI"
find "$YEDEK_DIZINI" \( -name 'supabase_arsa_*.sql.gz' -o -name 'dosyalar_*.tar.gz' \) -mtime +"$SAKLAMA_GUN" -delete
echo "$(date -Is) Yedek alındı: $VT_DOSYA ($(du -h "$VT_DOSYA" | cut -f1)), $DOSYA_ARSIVI ($(du -h "$DOSYA_ARSIVI" | cut -f1))"

#!/bin/bash
# En yeni yedeğin geri yüklenebildiğini doğrular. Canlı veritabanına ve birimlere yazmaz:
#  - veritabanı dökümünü geçici bir Postgres kapsayıcısına yükler, tablo ve kullanıcı sayar;
#  - dosya arşivindeki dosya sayısını birimlerdeki dosya sayısıyla karşılaştırır.
# Ortam değişkenleri: YEDEK_DIZINI (varsayılan /opt/arsa-backups), PROJE (varsayılan arsaanalizvesunum).
set -uo pipefail
YEDEK_DIZINI="${YEDEK_DIZINI:-/opt/arsa-backups}"
PROJE="${PROJE:-arsaanalizvesunum}"
VT="yedek-dogrula-$$"
trap 'docker rm -f "$VT" >/dev/null 2>&1' EXIT

VT_DOSYA=$(ls -t "$YEDEK_DIZINI"/supabase_arsa_*.sql.gz 2>/dev/null | head -1)
ARSIV=$(ls -t "$YEDEK_DIZINI"/dosyalar_*.tar.gz 2>/dev/null | head -1)
[ -n "$VT_DOSYA" ] || { echo "HATA: veritabanı yedeği bulunamadı ($YEDEK_DIZINI)"; exit 1; }
[ -n "$ARSIV" ] || { echo "HATA: dosya yedeği bulunamadı ($YEDEK_DIZINI)"; exit 1; }

docker run -d --name "$VT" -e POSTGRES_PASSWORD=dogrula -e POSTGRES_DB=geri postgres:17-alpine >/dev/null || exit 1
for i in $(seq 1 60); do docker exec "$VT" psql -q -U postgres -d geri -c 'select 1' >/dev/null 2>&1 && break; sleep 1; done
# Dökümde bu sunucuda olmayan roller/eklentiler geçebilir; tek tek hatalar yüklemeyi durdurmaz, sayımlar belirler
gzip -dc "$VT_DOSYA" | docker exec -i "$VT" psql -q -U postgres -d geri >/dev/null 2>&1
TABLO=$(docker exec "$VT" psql -At -U postgres -d geri -c "select count(*) from information_schema.tables where table_schema='public' and table_type='BASE TABLE'" 2>/dev/null)
KULLANICI=$(docker exec "$VT" psql -At -U postgres -d geri -c "select count(*) from users" 2>/dev/null)
TABLO=${TABLO:-0}; KULLANICI=${KULLANICI:-0}

ARSIVDEKI=$(tar tzf "$ARSIV" | grep -c -v '/$')
BIRIMDEKI=$(docker run --rm -v "${PROJE}_uploads:/v/uploads:ro" -v "${PROJE}_presentations:/v/presentations:ro" \
  -v "${PROJE}_is_belgeleri:/v/is_belgeleri:ro" alpine sh -c 'find /v -type f | wc -l')

if [ "$TABLO" -lt 10 ]; then echo "HATA: geri yüklenen tablo sayısı $TABLO (en az 10 bekleniyor) — $VT_DOSYA"; exit 1; fi
if [ "$KULLANICI" -lt 1 ]; then echo "HATA: geri yüklenen kullanıcı yok — $VT_DOSYA"; exit 1; fi
if [ "$ARSIVDEKI" -ne "$BIRIMDEKI" ]; then
  echo "HATA: arşivde $ARSIVDEKI dosya var, birimlerde $BIRIMDEKI (yedekten sonra dosya eklenmiş ya da silinmiş olabilir) — $ARSIV"; exit 1
fi
echo "YEDEK DOĞRULANDI: $TABLO tablo, $KULLANICI kullanıcı, $ARSIVDEKI dosya ($(basename "$VT_DOSYA"), $(basename "$ARSIV"))"

#!/bin/bash
# scripts/yedekle.sh ve scripts/yedek_dogrula.sh testi. Geçici bir Postgres kapsayıcısı ve "yedektest_"
# önekli geçici birimlerle çalışır; canlı veritabanına, canlı birimlere ve /opt/arsa-backups'a dokunmaz.
set -uo pipefail
KOK="$(cd "$(dirname "$0")/.." && pwd)"
AG=yedektest-ag; VT=yedektest-db; PROJE=yedektest
DIZIN="$(mktemp -d)"; HATA=0
BIRIMLER="${PROJE}_uploads ${PROJE}_presentations ${PROJE}_is_belgeleri"

temizle() {
  docker rm -f "$VT" >/dev/null 2>&1
  for b in $BIRIMLER; do docker volume rm -f "$b" >/dev/null 2>&1; done
  docker network rm "$AG" >/dev/null 2>&1
  rm -rf "$DIZIN"
}
trap temizle EXIT
temizle; mkdir -p "$DIZIN"

kontrol() { if eval "$2"; then echo "  OK    $1"; else echo "  HATA  $1"; HATA=1; fi; }

docker network create "$AG" >/dev/null
docker run -d --name "$VT" --network "$AG" -e POSTGRES_PASSWORD=t -e POSTGRES_DB=arsa postgres:17-alpine >/dev/null
for i in $(seq 1 30); do docker exec "$VT" pg_isready -U postgres -d arsa >/dev/null 2>&1 && break; sleep 1; done
sleep 1
SQL="CREATE TABLE users (id serial primary key, email text); INSERT INTO users (email) VALUES ('a@b.c'), ('d@e.f');"
for i in $(seq 1 11); do SQL="$SQL CREATE TABLE t$i (id int);"; done
docker exec "$VT" psql -q -U postgres -d arsa -c "$SQL" >/dev/null
for b in $BIRIMLER; do docker volume create "$b" >/dev/null; done
docker run --rm -v ${PROJE}_uploads:/v alpine sh -c 'mkdir -p /v/1 && echo a > /v/1/a.jpg && echo b > /v/1/b.jpg' 
docker run --rm -v ${PROJE}_is_belgeleri:/v alpine sh -c 'mkdir -p /v/isler/1 && echo c > /v/isler/1/tapu.pdf'
# presentations birimi bilerek boş bırakılır (senaryo c)

URL="postgresql://postgres:t@$VT:5432/arsa"
calistir() { YEDEK_DIZINI="$DIZIN" PROJE="$PROJE" YEDEK_AG="$AG" DB_URL="$1" "$KOK/scripts/yedekle.sh" >"$DIZIN/cikti.log" 2>&1; }

echo "a) normal çalıştırma"
calistir "$URL"; KOD=$?
kontrol "çıkış kodu 0" "[ $KOD -eq 0 ]"
kontrol "veritabanı yedeği oluştu" "ls $DIZIN/supabase_arsa_*.sql.gz >/dev/null 2>&1"
kontrol "dosya yedeği oluştu" "ls $DIZIN/dosyalar_*.tar.gz >/dev/null 2>&1"
TAR=$(ls "$DIZIN"/dosyalar_*.tar.gz 2>/dev/null | tail -1)
kontrol "arşivde 3 dosya var" "[ \"\$(tar tzf '$TAR' 2>/dev/null | grep -c -v '/\$')\" -eq 3 ]"
kontrol "arşivde uploads/1/a.jpg var" "tar tzf '$TAR' 2>/dev/null | grep -q 'uploads/1/a.jpg'"
kontrol "arşivde is_belgeleri/isler/1/tapu.pdf var" "tar tzf '$TAR' 2>/dev/null | grep -q 'is_belgeleri/isler/1/tapu.pdf'"
echo "c) boş birim"
kontrol "boş presentations klasörü arşivde" "tar tzf '$TAR' 2>/dev/null | grep -q 'presentations/\$'"
kontrol ".tmp dosyası kalmadı" "! ls $DIZIN/*.tmp >/dev/null 2>&1"

echo "doğrulama betiği"
YEDEK_DIZINI="$DIZIN" PROJE="$PROJE" "$KOK/scripts/yedek_dogrula.sh" >"$DIZIN/dogrula.log" 2>&1; KOD=$?
kontrol "yedek_dogrula.sh çıkış kodu 0" "[ $KOD -eq 0 ]"
kontrol "sonuç satırı: 12 tablo, 2 kullanıcı, 3 dosya" "grep -q 'YEDEK DOĞRULANDI: 12 tablo, 2 kullanıcı, 3 dosya' $DIZIN/dogrula.log"
docker run --rm -v ${PROJE}_uploads:/v alpine sh -c 'echo yeni > /v/1/yeni.jpg'
YEDEK_DIZINI="$DIZIN" PROJE="$PROJE" "$KOK/scripts/yedek_dogrula.sh" >"$DIZIN/dogrula2.log" 2>&1; KOD=$?
kontrol "birimde yedekte olmayan dosya varken doğrulama başarısız" "[ $KOD -ne 0 ]"

echo "b) veritabanı dökümü başarısız"
ESKI="$DIZIN/supabase_arsa_20000101_0000.sql.gz"; echo eski | gzip > "$ESKI"; touch -d '20 days ago' "$ESKI"
ONCE=$(ls "$DIZIN" | grep -c -E '\.(sql|tar)\.gz$')
calistir "postgresql://postgres:yanlis@$VT:5432/yok"; KOD=$?
kontrol "çıkış kodu sıfırdan farklı" "[ $KOD -ne 0 ]"
kontrol ".tmp dosyası kalmadı" "! ls $DIZIN/*.tmp >/dev/null 2>&1"
kontrol "20 günlük eski yedek silinmedi" "[ -f '$ESKI' ]"
kontrol "yeni yedek dosyası oluşmadı" "[ \"\$(ls $DIZIN | grep -c -E '\.(sql|tar)\.gz\$')\" -eq $ONCE ]"
echo "d) başarılı çalıştırma eski yedeği siler"
calistir "$URL"
kontrol "20 günlük eski yedek silindi" "[ ! -f '$ESKI' ]"

[ $HATA -eq 0 ] && echo "SONUÇ: tüm senaryolar OK" || { echo "SONUÇ: HATA var"; echo "--- son çıktı ---"; cat "$DIZIN/cikti.log" "$DIZIN/dogrula.log" 2>/dev/null | tail -20; }
exit $HATA

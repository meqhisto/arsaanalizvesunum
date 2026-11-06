# Gayrimenkul, İlan ve Mal Sahibi Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Yatırımcı odaklı "arsa analizi"ni; her türü destekleyen gayrimenkul kaydı + hisseli CRM mal sahipleri + çok gayrimenkullü Satılık/Kiralık/Kat karşılığı ilanları + emsal karşılaştırmalı raporlara dönüştürmek.

**Architecture:** `arsa_analizleri` tablosu (sınıf `ArsaAnaliz`) gayrimenkul olarak genişler; yeni `ilanlar`, `ilan_gayrimenkulleri`, `ilan_emsalleri`, `gayrimenkul_sahipleri`, `portfolio_ilanlar` tabloları eklenir. Hesaplar saf fonksiyonlarda (`modules/ilan_hesap.py`), DB'ye dokunan kurallar `modules/ilan_servis.py`'de, ekranlar mevcut `analysis_bp` (gayrimenkul) ve yeni `ilan_bp` (ilan) içinde. Şema ve veri geçişi açılışta idempotent `modules/ilan_kurulum.py` ile.

**Tech Stack:** Flask 2.3, Flask-SQLAlchemy 3, PostgreSQL (canlı: Supabase PG17, test: yerel postgres:15 konteyneri), Jinja2 + Bootstrap 5 (`dashboard_base.html`), reportlab / python-docx / python-pptx, pytest.

**Spec:** `docs/superpowers/specs/2026-11-06-gayrimenkul-ilan-tasarimi-design.md`

## Global Constraints

- Çalışma dizini: worktree `/opt/arsa-ilan`, dal `feat/gayrimenkul-ilan`. `/opt/arsaanalizvesunum` (canlı) dosyalarına dokunulmaz.
- Testler **asla** canlı `DATABASE_URL`'e (Supabase) karşı çalışmaz; yalnız yerel `db` konteynerindeki `arsa_ilan_test` veritabanı.
- Alembic yok. Yeni tablolar `db.create_all()`, mevcut tablolara sütunlar `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (PostgreSQL) ile; her kurulum adımı iki kez çalıştırılınca aynı sonucu verir.
- Eski sütunlar silinmez: `deger_artis_orani`, `fiyat`, `bolge_fiyat`, `altyapi`, `portfolio_arsalar`.
- Mal sahibi bilgisi hiçbir rapor çıktısına (PDF/Word/PPTX) girmez.
- Kullanıcıya görünen tüm metinler Türkçe. Para `tr_currency`, sayılar `tr_number` (`modules/rapor/model.py`) ile biçimlenir.
- Kod/ilan numarası biçimi: `ILN-YYYY-NNNN` (yıl başına sıra, 4 hane).
- Konumlandırma eşiği ±5 (yüzde puan); satılık/kiralıkta düşük = uygun, kat karşılığında yön ters.
- Aktif ilan durumları: `pazarlamada`, `opsiyonlu`. Bir gayrimenkul aynı anda en fazla bir aktif ilanda.
- flake8 `--select=E9,F63,F7,F82` temiz kalmalı (CI).
- Commit mesajları Türkçe ve şu satırla biter: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Review Focus

1. **Eski kayıtta `bolge_fiyat` toplam değer olarak girilmiş** (canlıdaki id=3: 70.000.000 ₺, 10.094 m²). Geçiş bunu m² fiyatına çevirmeli, yoksa rapor "%2.000.000 üstünde" der → Task 2 testi `test_gecis_toplam_bolge_fiyatini_m2ye_cevirir`.
2. **KAKS'ı boş parsel içeren kat karşılığı ilanı**: inşaat hakkı sıfıra düşmemeli, o parsel atlanıp uyarı gösterilmeli; tamamı boşsa "hesaplanamadı" → Task 1 `test_insaat_hakki_kakssiz_parseli_atlar`, Task 6 detay sayfası uyarı testi.
3. **Danışman, başka danışmanın CRM müşterisini sahip olarak POST etmesi** (id elle yazılarak): reddedilmeli → Task 4 `test_baskasinin_kontagi_sahip_secilemez`.
4. **Aynı parsel ikinci bir aktif ilana eklenmesi** (oluşturma ya da durum değişikliği ile): kayıt reddedilip çakışan ilan kodu gösterilmeli → Task 3 `test_cakisma_aktif_ilan`, Task 6 `test_durum_degisikligi_cakisma`.
5. **Türkçe sayı girişi** ("4.250.000", "1.250,50") fiyat/m²/emsal alanlarında: doğru ayrıştırılmalı, 4,25 olarak kaydedilmemeli → Task 1 `test_tutar_ayristir_turkce`.

---

## File Structure

| Dosya | Sorumluluk |
|---|---|
| `modules/gayrimenkul_sabitleri.py` (yeni) | Tür, alt tür, ilan tipi, durum, ısınma, tapu, özellik listeleri — tek kaynak |
| `modules/ilan_hesap.py` (yeni) | Saf hesaplar: toplam m², inşaat hakkı, sahibe düşen m², bölge ortalaması, fark, konumlandırma, tutar ayrıştırma |
| `modules/ilan_servis.py` (yeni) | DB kuralları: görünürlük, ilan kodu, çakışma, ilan kaydetme, sahip kaydetme |
| `modules/ilan_kurulum.py` (yeni) | Sütun ekleme + veri geçişi, idempotent |
| `models/ilan_models.py` (yeni) | `GayrimenkulSahibi`, `Ilan`, `IlanGayrimenkul`, `IlanEmsal`, `portfolio_ilanlar` |
| `models/arsa_models.py` | `ArsaAnaliz` yeni sütunlar + `baslik_metni`/`ozet` yardımcıları |
| `models/crm_models.py` | `Deal.ilan_id` |
| `models/user_models.py` | `Portfolio.ilanlar` ilişkisi |
| `models/__init__.py` | `ilan_models` import + `ilan_kurulum.kur()` |
| `blueprints/analysis_bp.py` | Gayrimenkul oluştur/düzenle/liste/detay, kontak arama/ekleme uçları, tanıtım raporu |
| `blueprints/ilan_bp.py` (yeni) | `/ilanlar`: liste, yeni, detay, düzenle, durum, rapor, sahip gayrimenkulleri JSON |
| `blueprints/crm_bp.py` | Kontak detayına gayrimenkuller, fırsata ilan |
| `blueprints/portfolio_bp.py` | Portföy ↔ ilan |
| `modules/rapor/model.py`, `assets.py`, `pdf.py`, `word.py`, `pptx_.py` | İlan tabanlı rapor modeli ve bölümleri |
| `templates/gayrimenkul/form.html`, `detay.html`, `liste.html`, `_sahipler.html` (yeni) | Gayrimenkul ekranları |
| `templates/ilan/form.html`, `detay.html`, `liste.html`, `_emsaller.html` (yeni) | İlan ekranları |
| `tests/conftest.py`, `tests/test_*.py` (yeni), `scripts/test.sh` (yeni), `requirements-dev.txt` (yeni) | Test altyapısı |

Silinenler: `templates/analysis_form.html`, `templates/analysis_edit.html` (yerine `gayrimenkul/form.html`); `analysis_bp` içindeki yinelenen `list_analyses` (`/list`, ilk kayıtlı olduğu için bugün `analizler`'i gölgeliyor) ve `analiz_detay` (`/<id>`, `view_analysis` tarafından gölgeleniyor). Liste uç adı `analysis.analizler`, detay uç adı `analysis.view_analysis` olarak kalır; şablonlardaki `analysis.analiz_detay` / `analysis.list_analyses` başvuruları bunlarla değiştirilir.

---

### Task 1: Test altyapısı, sabitler ve saf hesaplar

**Files:**
- Create: `requirements-dev.txt` (`pytest==8.3.3`), `scripts/test.sh`, `tests/conftest.py`, `tests/test_ilan_hesap.py`, `modules/gayrimenkul_sabitleri.py`, `modules/ilan_hesap.py`

**Interfaces:**
- Produces (`modules/gayrimenkul_sabitleri.py`):
  - `TURLER = [('arsa','Arsa'),('tarla','Tarla'),('konut','Konut'),('isyeri','İşyeri'),('bina','Bina')]`
  - `ALT_TURLER = {'konut': [('daire','Daire'),('villa','Villa'),('mustakil','Müstakil ev'),('rezidans','Rezidans')], 'isyeri': [('dukkan','Dükkân'),('ofis','Ofis'),('depo','Depo'),('fabrika','Fabrika')]}`
  - `TEKLIF_TIPLERI = [('satilik','Satılık'),('kiralik','Kiralık'),('kat_karsiligi','Kat karşılığı')]`
  - `DURUMLAR = [('hazirlaniyor','Hazırlanıyor'),('pazarlamada','Pazarlamada'),('opsiyonlu','Opsiyonlu'),('anlasildi','Anlaşıldı'),('geri_cekildi','Geri çekildi')]`, `AKTIF_DURUMLAR = ('pazarlamada','opsiyonlu')`
  - `ISINMA = ['Yok','Soba','Doğalgaz sobası','Kombi (doğalgaz)','Merkezi','Merkezi (pay ölçer)','Yerden ısıtma','Klima','Isı pompası','Güneş enerjisi']`
  - `TAPU_DURUMLARI = ['Kat mülkiyetli','Kat irtifaklı','Hisseli tapu','Müstakil tapulu','Arsa tapulu','Kooperatif','Tapu kaydı yok']`
  - `TEMINAT_TURLERI = ['Banka teminat mektubu','İpotek','Çek / senet','Teminat yok']`
  - `TEVHID = [('yapildi','Yapıldı'),('yapilacak','Yapılacak'),('gerekmiyor','Gerekmiyor')]`
  - `OZELLIKLER = {'ic': [...], 'dis': [...], 'muhit': [...], 'ulasim': [...], 'cephe': ['Kuzey','Güney','Doğu','Batı'], 'altyapi': ['yol','elektrik','su','dogalgaz','kanalizasyon','telefon','internet']}`; `ic` en az: Asansör, Ankastre mutfak, Amerikan mutfak, Ebeveyn banyosu, Giyinme odası, Çelik kapı, Görüntülü diyafon, Klima, Laminat zemin, PVC doğrama, Şömine, Teras; `dis`: Otopark, Kapalı otopark, Güvenlik, Havuz, Bahçe, Oyun parkı, Spor alanı, Jeneratör, Isı yalıtımı, Ses yalıtımı, Deprem yönetmeliğine uygun; `muhit`: Okul, Hastane, Market, Alışveriş merkezi, Park, Cami, Belediye, Denize yakın, Göle yakın; `ulasim`: Otobüs durağı, Minibüs / dolmuş, Ana yol, Havalimanı, Liman, Feribot, Tren istasyonu
  - `OZELLIK_BASLIKLARI = {'ic':'İç özellikler','dis':'Dış özellikler','muhit':'Muhit','ulasim':'Ulaşım','cephe':'Cephe','altyapi':'Altyapı'}`, `ALTYAPI_ETIKETLERI` mevcut `modules/rapor/model.py`'deki listeyle aynı (oradan buraya taşınır, model.py buradan import eder)
  - `def etiket(liste, kod) -> str` (bulunmazsa kodu döndürür)
- Produces (`modules/ilan_hesap.py`) — girdiler düz `float|None`/dict, ORM bilmez:
  - `tutar_ayristir(metin: str|None) -> float|None`
  - `toplam_m2(parseller: list[dict]) -> float` (her dict: `{'m2': float, 'kaks': float|None}`)
  - `insaat_hakki(parseller, elle: float|None) -> tuple[float|None, list[int]]` (değer, KAKS'ı eksik parsel indeksleri)
  - `sahibe_dusen_m2(insaat: float|None, pay_yuzde: float|None) -> float|None`
  - `bolge_ortalamasi(teklif_tipi: str, emsaller: list[dict], elle_m2: float|None, elle_pay: float|None) -> tuple[float|None, str]` (değer, kaynak `'emsal'|'elle'|'yok'`); emsal dict: `{'m2','fiyat','pay_yuzde'}`
  - `istenen_deger(teklif_tipi, fiyat, kira, pay_yuzde, toplam_m2) -> float|None` (satılık: fiyat/m², kiralık: kira/m², kat karşılığı: pay %)
  - `fark_yuzde(istenen, bolge) -> float|None`
  - `konumlandirma(teklif_tipi, fark) -> str|None`

- [ ] **Step 1: Test altyapısını kur**

`scripts/test.sh`: `/opt/arsaanalizvesunum/.env`'den `POSTGRES_USER/POSTGRES_PASSWORD` okur; yerel `db` konteynerinde `arsa_ilan_test` yoksa oluşturur (`docker compose -f docker-compose.server.yml exec -T db createdb -U $POSTGRES_USER arsa_ilan_test || true`); ardından `docker compose -f /opt/arsaanalizvesunum/docker-compose.server.yml run --rm --no-deps -e DATABASE_URL=postgresql://…@db:5432/arsa_ilan_test -e TEST_VERITABANI=1 -v ${KOD:-/opt/arsa-ilan}:/app -w /app --entrypoint sh web -c "pip install -q -r requirements-dev.txt && python -m pytest $*"`.

`tests/conftest.py`: `TEST_VERITABANI` env yoksa veya `DATABASE_URL` `supabase` içeriyorsa `pytest.exit("Testler yalnız yerel test veritabanında çalışır")`. Fixture'lar:
- `app` (session): `create_app()`, `WTF_CSRF_ENABLED=False`, `TESTING=True`; başta `db.drop_all(); db.create_all(); ilan_kurulum.kur()` çağırır (Task 2'den sonra; o zamana dek kur satırı yok).
- `db_session` (function): her testten sonra tüm tabloları `TRUNCATE ... RESTART IDENTITY CASCADE` ile temizler.
- `kullanicilar`: ofis + `broker`, `d1` (broker'ın astı, aynı ofis), `d2` (aynı ofis), `dx` (ofissiz yabancı), `sa` (superadmin) — dict id döndürür.
- `giris(client, user_id)`: `session_transaction` ile `_user_id`, `_fresh` yazar; her kullanıcı için **ayrı** `app.test_client()` (aynı app context'te `g` paylaşımı yüzünden ikinci kullanıcı ilkinin kimliğini almasın).

- [ ] **Step 2: Hesap testlerini yaz (`tests/test_ilan_hesap.py`)**

```python
def test_tutar_ayristir_turkce():
    assert tutar_ayristir("4.250.000") == 4250000
    assert tutar_ayristir("1.250,50") == 1250.5
    assert tutar_ayristir("1250.5") == 1250.5
    assert tutar_ayristir("") is None and tutar_ayristir(None) is None and tutar_ayristir("abc") is None

def test_insaat_hakki_toplar():
    p = [{'m2': 1000, 'kaks': 1.5}, {'m2': 800, 'kaks': 2.0}]
    assert toplam_m2(p) == 1800
    assert insaat_hakki(p, None) == (3100, [])

def test_insaat_hakki_kakssiz_parseli_atlar():
    p = [{'m2': 1000, 'kaks': 1.5}, {'m2': 800, 'kaks': None}]
    assert insaat_hakki(p, None) == (1500, [1])
    assert insaat_hakki([{'m2': 800, 'kaks': None}], None) == (None, [0])

def test_insaat_hakki_elle_degeri_kullanir():
    assert insaat_hakki([{'m2': 1000, 'kaks': 1.5}], 4000) == (4000, [])

def test_sahibe_dusen_m2():
    assert sahibe_dusen_m2(3100, 50) == 1550
    assert sahibe_dusen_m2(None, 50) is None and sahibe_dusen_m2(3100, None) is None

def test_bolge_ortalamasi_m2_agirlikli():
    e = [{'m2': 100, 'fiyat': 2_000_000, 'pay_yuzde': None}, {'m2': 300, 'fiyat': 4_500_000, 'pay_yuzde': None}]
    assert bolge_ortalamasi('satilik', e, 99, None) == (16250, 'emsal')
    assert bolge_ortalamasi('satilik', [], 18000, None) == (18000, 'elle')
    assert bolge_ortalamasi('satilik', [], None, None) == (None, 'yok')

def test_bolge_ortalamasi_kat_karsiligi_pay():
    e = [{'m2': None, 'fiyat': None, 'pay_yuzde': 40}, {'m2': None, 'fiyat': None, 'pay_yuzde': 50}]
    assert bolge_ortalamasi('kat_karsiligi', e, None, 30) == (45, 'emsal')

def test_eksik_emsal_satiri_ortalamaya_girmez():
    e = [{'m2': 100, 'fiyat': 2_000_000, 'pay_yuzde': None}, {'m2': None, 'fiyat': 3_000_000, 'pay_yuzde': None}]
    assert bolge_ortalamasi('satilik', e, None, None) == (20000, 'emsal')

def test_fark_ve_konumlandirma():
    assert round(fark_yuzde(19980, 18500), 1) == 8.0
    assert fark_yuzde(100, None) is None and fark_yuzde(100, 0) is None
    assert konumlandirma('satilik', -6) == 'Bölgeye göre uygun'
    assert konumlandirma('satilik', 5) == 'Piyasa seviyesinde'
    assert konumlandirma('satilik', 5.1) == 'Bölgenin üstünde'
    assert konumlandirma('kat_karsiligi', 11.1) == 'Talep bölge ortalamasının üstünde'
    assert konumlandirma('kat_karsiligi', -6) == 'Müteahhit için cazip'
    assert konumlandirma('kat_karsiligi', 0) == 'Piyasa seviyesinde'
    assert konumlandirma('satilik', None) is None

def test_istenen_deger():
    assert istenen_deger('satilik', 4_000_000, None, None, 200) == 20000
    assert istenen_deger('kiralik', None, 30_000, None, 150) == 200
    assert istenen_deger('kat_karsiligi', None, None, 50, 3200) == 50
    assert istenen_deger('satilik', 4_000_000, None, None, 0) is None
```

- [ ] **Step 3: Çalıştır, FAIL gör** — `scripts/test.sh tests/test_ilan_hesap.py -v` → `ModuleNotFoundError: modules.ilan_hesap`.

- [ ] **Step 4: `gayrimenkul_sabitleri.py` ve `ilan_hesap.py`'yi yaz.** `tutar_ayristir`: hem `.` hem `,` varsa `.` binlik, `,` ondalık; yalnız `,` varsa ondalık; yalnız `.` ve son gruptan sonra tam 3 hane ve birden çok grup ya da toplam >3 hane ise binlik ("4.250.000"), aksi halde ondalık ("1250.5"). Konumlandırma etiketleri tam olarak testtekiler; satılık/kiralık: `<-5` "Bölgeye göre uygun", `-5..5` "Piyasa seviyesinde", `>5` "Bölgenin üstünde"; kat karşılığı: `<-5` "Müteahhit için cazip", `-5..5` "Piyasa seviyesinde", `>5` "Talep bölge ortalamasının üstünde". `ALTYAPI_ETIKETLERI`'ni `modules/rapor/model.py`'den taşı, model.py'de `from modules.gayrimenkul_sabitleri import ALTYAPI_ETIKETLERI`.

- [ ] **Step 5: PASS gör** — aynı komut, 10 test geçer.

- [ ] **Step 6: Commit** — `git add requirements-dev.txt scripts/test.sh tests modules/gayrimenkul_sabitleri.py modules/ilan_hesap.py modules/rapor/model.py && git commit -m "İlan hesapları, gayrimenkul sabitleri ve test altyapısı"`

---

### Task 2: Veri modeli ve idempotent geçiş

**Files:**
- Create: `models/ilan_models.py`, `modules/ilan_kurulum.py`, `tests/test_ilan_kurulum.py`
- Modify: `models/arsa_models.py` (ArsaAnaliz), `models/crm_models.py` (Deal), `models/user_models.py` (Portfolio), `models/__init__.py:52-53`, `tests/conftest.py`

**Interfaces:**
- Consumes: `modules.gayrimenkul_sabitleri`
- Produces:
  - `ArsaAnaliz` yeni sütunlar — spec §3.1'deki adlar ve tiplerle birebir: `tur`(default `'arsa'`), `alt_tur`, `baslik`, `brut_m2`, `net_m2`, `oda_sayisi`, `banyo_sayisi`, `bulundugu_kat`, `toplam_kat`, `bina_yasi`, `isinma`, `esyali`, `site_icinde`, `balkon`, `aidat`, `tapu_durumu`, `krediye_uygun`, `takasli`, `kimden`, `ozellikler` (JSON). İlişkiler: `sahiplikler` (→ `GayrimenkulSahibi`, cascade delete-orphan), `ilan_baglari` (→ `IlanGayrimenkul`). Özellik: `baslik_metni -> str` (baslik yoksa `"{alt_tur/tur etiketi} · {mahalle}, {ilce}"`, arsa/tarlada sonuna `" · Ada {ada} / Parsel {parsel}"`), `aktif_ilan -> Ilan|None`.
  - `GayrimenkulSahibi(id, gayrimenkul_id, contact_id, hisse, irtibat, created_at)` — tablo `gayrimenkul_sahipleri`, `UniqueConstraint('gayrimenkul_id','contact_id')`, `contact` ilişkisi + `Contact.sahiplikler` backref.
  - `Ilan` — tablo `ilanlar`, spec §3.3 alanları birebir; ilişkiler `baglar` (→ `IlanGayrimenkul`, `order_by=sira`, cascade), `emsaller` (→ `IlanEmsal`, cascade), `user`, `sorumlu`, `office`. Özellikler: `gayrimenkuller -> list[ArsaAnaliz]` (sıralı), `ana_gayrimenkul -> ArsaAnaliz|None`.
  - `IlanGayrimenkul(ilan_id, gayrimenkul_id [PK], ana_kayit, parsel_fiyati, sira)` — tablo `ilan_gayrimenkulleri`.
  - `IlanEmsal(id, ilan_id, konum, m2, fiyat, pay_yuzde, link, notlar, created_at)` — tablo `ilan_emsalleri`.
  - `portfolio_ilanlar = db.Table(...)` (portfolio_id, ilan_id PK; added_at); `Portfolio.ilanlar` (`lazy='dynamic'`, backref `portfoyler`).
  - `Deal.ilan_id` (FK `ilanlar.id`, `ondelete='SET NULL'`), `Deal.ilan` ilişkisi + `Ilan.firsatlar` backref.
  - `modules.ilan_kurulum.kur() -> None`

- [ ] **Step 1: Geçiş testlerini yaz (`tests/test_ilan_kurulum.py`)** — her test, eski stilde (yalnız eski sütunlar dolu) `ArsaAnaliz` + `portfolio_arsalar` bağı oluşturur, `kur()`'u çağırır:

```python
def test_gecis_ilan_olusturur_ve_iki_kez_calisir(db_session, kullanicilar):
    a = eski_analiz(kullanicilar['broker'], metrekare=2450, fiyat=7_350_000, bolge_fiyat=3200,
                    altyapi=['yol', 'su'])
    kur(); kur()
    ilanlar = Ilan.query.all()
    assert len(ilanlar) == 1
    i = ilanlar[0]
    assert (i.teklif_tipi, i.durum, float(i.fiyat), float(i.bolge_m2_fiyat_elle)) == ('satilik', 'pazarlamada', 7_350_000, 3200)
    assert i.kod.startswith(f"ILN-{datetime.utcnow().year}-") and i.user_id == a.user_id and i.sorumlu_user_id == a.user_id
    assert i.ana_gayrimenkul.id == a.id
    db.session.refresh(a)
    assert a.tur == 'arsa' and a.ozellikler['altyapi'] == ['yol', 'su'] and a.altyapi == ['yol', 'su']

def test_gecis_toplam_bolge_fiyatini_m2ye_cevirir(db_session, kullanicilar):
    eski_analiz(kullanicilar['broker'], metrekare=10094.82, fiyat=35_000_000, bolge_fiyat=70_000_000)
    kur()
    assert round(float(Ilan.query.one().bolge_m2_fiyat_elle)) == 6934

def test_gecis_portfoy_baglarini_kopyalar(db_session, kullanicilar):
    a = eski_analiz(kullanicilar['broker']); p = portfoy(kullanicilar['broker'], [a])
    kur(); kur()
    assert [i.ana_gayrimenkul.id for i in p.ilanlar] == [a.id]

def test_ilani_olan_gayrimenkule_yeni_ilan_acilmaz(db_session, kullanicilar):
    eski_analiz(kullanicilar['broker']); kur()
    Ilan.query.one().durum = 'geri_cekildi'; db.session.commit()
    kur()
    assert Ilan.query.count() == 1
```

- [ ] **Step 2: FAIL gör** — `scripts/test.sh tests/test_ilan_kurulum.py -v` → ImportError `models.ilan_models`.

- [ ] **Step 3: Modelleri yaz** (yukarıdaki Interfaces). `models/__init__.py`'de `ilan_models`'i `create_all`'dan önce import et; `is_takip_kur()`'dan sonra `from modules.ilan_kurulum import kur as ilan_kur; ilan_kur()` (dispose'dan önce).

- [ ] **Step 4: `ilan_kurulum.kur()`'u yaz.** Sıra: (1) PostgreSQL ise `arsa_analizleri`'ye Interfaces'teki her sütun ve `crm_deals.ilan_id` için `ADD COLUMN IF NOT EXISTS` (+ `CREATE INDEX IF NOT EXISTS ix_crm_deals_ilan_id`); değilse uyarı logla ve şema adımını atla. (2) `UPDATE arsa_analizleri SET tur='arsa' WHERE tur IS NULL`. (3) `ozellikler IS NULL` olanlarda `ozellikler = {'altyapi': altyapi or []}` (altyapi string JSON da olabilir — `modules/rapor/model.py: parse_altyapi` ile ayrıştır). (4) Hiç `IlanGayrimenkul` bağı olmayan her gayrimenkul için ilan: `fiyat ← a.fiyat`, `bolge_m2_fiyat_elle ← donustur(a)`, `office_id ← a.office_id`, `user_id = sorumlu_user_id ← a.user_id`, `baslik ← a.baslik_metni`, `ana_kayit=True, sira=1`, `kod` `ilan_servis.yeni_ilan_kodu()` (Task 3'te yazılır; bu task'ta `ilan_kurulum` içinde aynı kuralla yerel `_yeni_kod(yil)` — Task 3 bunu `ilan_servis`'e taşır ve buradan çağırır). `donustur(a)`: `m2f = fiyat/metrekare`; `bolge_fiyat > 10 * m2f` ise `bolge_fiyat / metrekare`, değilse `bolge_fiyat`; `bolge_fiyat` boş/0 ise `None`. (5) `portfolio_arsalar`'daki her (portfolio, arsa) için arsanın ilk ilanı `portfolio_ilanlar`'da yoksa ekle (`INSERT ... ON CONFLICT DO NOTHING`). Hepsi tek `try`; hata → rollback + `log.exception` + raise (is_takip_kurulum deseni).

- [ ] **Step 5: conftest `app` fixture'ına `ilan_kur()` ekle; PASS gör** — `scripts/test.sh tests -v` (Task 1 testleri dahil) yeşil.

- [ ] **Step 6: Commit** — `git commit -m "Gayrimenkul/ilan veri modeli ve mevcut kayıtların idempotent geçişi"`

---

### Task 3: İlan servis kuralları (görünürlük, kod, çakışma, kaydetme)

**Files:**
- Create: `modules/ilan_servis.py`, `tests/test_ilan_servis.py`
- Modify: `modules/ilan_kurulum.py` (kodu servisten al)

**Interfaces:**
- Consumes: Task 1 hesapları, Task 2 modelleri
- Produces (`modules/ilan_servis.py`):
  - `gorunur_kullanici_idleri(user) -> list[int] | None` — superadmin `None` (=hepsi); broker: kendisi + `manager_id == broker.id` olanlar + (broker.office_id varsa) aynı ofisteki aktif kullanıcılar (crm_bp `ekip_kullanicilari_sorgusu` ile aynı kural, burada bağımsız yazılır); diğerleri `[user.id]`.
  - `gorunur_gayrimenkuller(user) -> Query[ArsaAnaliz]`, `gorunur_ilanlar(user) -> Query[Ilan]` (ilan: `user_id` veya `sorumlu_user_id` görünür kümede), `gorunur_kontaklar(user) -> Query[Contact]` (`Contact.user_id` görünür kümede).
  - `gayrimenkul_or_404(id, user) -> ArsaAnaliz`, `ilan_or_404(id, user) -> Ilan` (`abort(404)`).
  - `yeni_ilan_kodu(yil: int|None = None) -> str` — o yılın en büyük sırasından +1.
  - `class IlanHatasi(ValueError)`
  - `cakisan_ilan(gayrimenkul_id: int, haric_ilan_id: int|None) -> Ilan|None`
  - `ilan_kaydet(ilan: Ilan|None, user, veri: dict) -> Ilan` — `veri` anahtarları: `baslik, aciklama, teklif_tipi, durum, sorumlu_user_id, fiyat, kira, depozito, sahip_payi_yuzde, ek_nakit, teslim_suresi_ay, teminat_turu, teminat_tutari, tevhid_durumu, insaat_alani_elle, daire_tercihi_notu, bolge_m2_fiyat_elle, bolge_pay_yuzde_elle`, `gayrimenkuller: list[{'id': int, 'parsel_fiyati': float|None}]` (sıra = liste sırası), `ana_gayrimenkul_id: int|None`, `emsaller: list[dict]` (tamamen boş satırlar atlanır). Doğrular ve `IlanHatasi` fırlatır: geçersiz teklif tipi/durum; en az bir gayrimenkul; her gayrimenkul görünür olmalı; satılıkta `fiyat`, kiralıkta `kira`, kat karşılığında `sahip_payi_yuzde` (0–100) zorunlu; aktif durumdaysa her gayrimenkul için `cakisan_ilan` → `IlanHatasi(f"{baslik_metni} zaten {kod} numaralı aktif ilanda.")`; sorumlu görünür kullanıcılardan olmalı (yoksa oluşturan). Teklif tipine ait olmayan fiyat alanlarını `None` yapar. Ana kayıt verilmezse ilk gayrimenkul. Emsalleri baştan yazar. `office_id` ana gayrimenkulden. Commit etmez; çağıran commit eder.
  - `ilan_ozeti(ilan) -> dict` — anahtarlar: `toplam_m2, insaat_hakki, kakssiz_parseller (baslik_metni listesi), sahibe_dusen_m2, istenen, bolge, bolge_kaynak, fark, konum` (Task 1 fonksiyonlarını ORM'den düz veriye çevirerek çağırır).
  - `sahipleri_kaydet(gayrimenkul, user, sahipler: list[{'contact_id': int, 'hisse': str, 'irtibat': bool}]) -> None` — her contact `gorunur_kontaklar(user)` içinde değilse `IlanHatasi("Seçilen müşteri bulunamadı.")`; mevcut sahiplikleri listeye göre senkronlar.

- [ ] **Step 1: Testleri yaz (`tests/test_ilan_servis.py`)**

```python
def test_gorunurluk(db_session, kullanicilar):  # broker d1'in kaydını görür, d1 broker'ınkini görmez, dx hiçbirini, sa hepsini
def test_yeni_ilan_kodu_yil_icinde_artar(db_session, kullanicilar):
    assert yeni_ilan_kodu(2026) == 'ILN-2026-0001'; ilan_olustur(kod='ILN-2026-0007')
    assert yeni_ilan_kodu(2026) == 'ILN-2026-0008' and yeni_ilan_kodu(2027) == 'ILN-2027-0001'
def test_cakisma_aktif_ilan(db_session, kullanicilar):
    # g1 'pazarlamada' ilanda → ikinci aktif ilan IlanHatasi, mesajda ilk ilanın kodu var;
    # ikinci ilan 'hazirlaniyor' ise kabul; ilk ilan 'geri_cekildi' yapılınca ikinci 'pazarlamada' olabilir
def test_kat_karsiligi_dort_parsel(db_session, kullanicilar):
    # 213 ada 2,3,4,5 (m2: 800, 750, 900, 750; kaks 1.5) → toplam_m2 3200, insaat_hakki 4800,
    # pay 50 → sahibe_dusen_m2 2400; emsal pay 40 ve 50 → bolge 45, fark ≈ 11.1, konum 'Talep bölge ortalamasının üstünde'
def test_teklif_tipine_ait_olmayan_alanlar_temizlenir(db_session, kullanicilar):
    # satilik → kiralik değişince fiyat None, kira dolu
def test_zorunlu_alanlar(db_session, kullanicilar):  # satilik fiyatsız, kat_karsiligi pay 120 → IlanHatasi
def test_gorunmeyen_gayrimenkul_ilana_eklenemez(db_session, kullanicilar):  # d1, broker'ın kaydını ekleyemez
def test_sahipleri_kaydet_hisseli(db_session, kullanicilar):  # iki sahip 1/2 + 1/2, biri irtibat; tekrar çağrı tek sahipe indirir
def test_baskasinin_kontagi_sahip_secilemez_servis(db_session, kullanicilar):  # d1, d2'nin kontağını → IlanHatasi
```

Her testin içi bu satırlardaki değerlerle yazılır; kat karşılığı testi `ilan_ozeti` çıktısını `{'toplam_m2': 3200, 'insaat_hakki': 4800, 'sahibe_dusen_m2': 2400, 'bolge': 45, 'bolge_kaynak': 'emsal'}` alt kümesiyle ve `round(fark,1) == 11.1` ile doğrular.

- [ ] **Step 2: FAIL gör** — `scripts/test.sh tests/test_ilan_servis.py -v`.
- [ ] **Step 3: `ilan_servis.py`'yi yaz; `ilan_kurulum`'daki yerel kod üreticiyi `yeni_ilan_kodu` çağrısıyla değiştir.**
- [ ] **Step 4: PASS gör** — `scripts/test.sh tests -v`.
- [ ] **Step 5: Commit** — `git commit -m "İlan servis kuralları: görünürlük, ilan kodu, çakışma, kaydetme"`

---

### Task 4: Gayrimenkul formu (oluştur/düzenle), sahipler ve "hemen ilana çıkar"

**Files:**
- Create: `templates/gayrimenkul/form.html`, `templates/gayrimenkul/_sahipler.html`, `static/js/gayrimenkul_form.js`, `modules/gayrimenkul_form.py`, `tests/test_gayrimenkul_form.py`
- Modify: `blueprints/analysis_bp.py` (`new_analysis` :43, `edit_analysis` :449, `create_analysis` :714, `duplicate_analysis` :599)
- Delete: `templates/analysis_form.html`, `templates/analysis_edit.html`

**Interfaces:**
- Consumes: sabitler, `ilan_servis.sahipleri_kaydet / ilan_kaydet / gorunur_kontaklar / gayrimenkul_or_404`, `ilan_hesap.tutar_ayristir`
- Produces:
  - `modules/gayrimenkul_form.py`: `formdan_gayrimenkul(form: MultiDict, gayrimenkul: ArsaAnaliz) -> list[str]` (hata listesi; alanları yazar). Kurallar: `tur` ∈ TURLER zorunlu; `il, ilce, mahalle` zorunlu; arsa/tarla: `ada, parsel, metrekare` zorunlu, `imar_durumu, taks (0–1), kaks (0–10)`; konut/işyeri/bina: `brut_m2` zorunlu, `metrekare ← brut_m2`; konutta `oda_sayisi` zorunlu; tür dışı alanlar `None` yapılır (ör. daireye geçilince `ada/parsel/taks/kaks=None`, arsaya geçilince `oda_sayisi..aidat=None`). `ozellikler`: her başlık için `form.getlist(f'oz_{baslik}')` ∩ `OZELLIKLER[baslik]`. SWOT mevcut `strengths/weaknesses/opportunities/threats` hidden JSON alanlarından. Sayılar `tutar_ayristir` ile. Kaldırılan yatırımcı alanları formda yok ve yazılmaz.
  - Form alanı adları: tabloda sütun adıyla aynı (`tur`, `alt_tur`, `brut_m2`, …); sahipler `sahip_contact_id[]`, `sahip_hisse[]`, `sahip_irtibat` (irtibat olan contact_id); "hemen ilana çıkar": `ilana_cikar=1`, `ilan_teklif_tipi`, `ilan_fiyat`, `ilan_kira`, `ilan_depozito`, `ilan_sahip_payi_yuzde`.
  - Rotalar: `GET /analysis/new` (`analysis.new_analysis`), `POST /analysis/create` (`analysis.create_analysis`), `GET|POST /analysis/<id>/edit` (`analysis.edit_analysis`) — hepsi `gayrimenkul/form.html`'i kullanır; oluşturma/düzenleme `gayrimenkul_or_404` ile yetki denetler (düzenleme: sahibi, ekibinin broker'ı, superadmin).
  - `GET /analysis/kontak-ara?q=` (`analysis.kontak_ara`) → `[{"id", "ad", "telefon"}]`, en çok 20, `gorunur_kontaklar` içinden ad/soyad/telefon `ilike`.
  - `POST /analysis/kontak-ekle` (`analysis.kontak_ekle`, JSON `{ad, soyad, telefon}`) → `Contact(user_id=current_user.id, office_id=current_user.office_id, first_name=ad, last_name=soyad or '-', phone=telefon, status='Mal sahibi', source='Portföy')`; ad boşsa 400.
  - Medya yükleme, JSON parsel yükleme ve dashboard istatistik güncellemesi mevcut `create_analysis` davranışından korunur (dashboard `fiyat` alanını kullanıyorsa yeni kayıtta `fiyat` = "hemen ilana çıkar" satış fiyatı ya da 0).

- [ ] **Step 1: Testleri yaz (`tests/test_gayrimenkul_form.py`)** — hepsi test istemcisiyle `POST /analysis/create`:

```python
@pytest.mark.parametrize('tur,alanlar', [
    ('arsa',  {'ada': '213', 'parsel': '2', 'metrekare': '800', 'imar_durumu': 'Konut', 'kaks': '1,5'}),
    ('tarla', {'ada': '101', 'parsel': '7', 'metrekare': '12.000'}),
    ('konut', {'alt_tur': 'daire', 'brut_m2': '120', 'net_m2': '105', 'oda_sayisi': '3+1', 'bulundugu_kat': '4', 'bina_yasi': '5', 'isinma': 'Kombi (doğalgaz)'}),
    ('isyeri',{'alt_tur': 'dukkan', 'brut_m2': '85'}),
    ('bina',  {'brut_m2': '640', 'toplam_kat': '5'}),
])
def test_her_tur_olusturulur(...):  # 302 → /analysis/<id>; tur, metrekare (konutta 120, tarlada 12000) doğru; kaks 1.5
def test_konutta_ada_parsel_zorunlu_degil_arsada_zorunlu(...):  # arsa ada'sız → 200 + "Ada" hata metni; konut ada'sız → 302
def test_tur_degisince_tur_disi_alanlar_temizlenir(...):  # arsa→konut edit sonrası ada/kaks None
def test_ozellikler_listede_olmayani_almaz(...):  # oz_ic=['Asansör','Uydurma'] → ozellikler['ic']==['Asansör']
def test_hisseli_sahipler_ve_yeni_kontak(...):  # kontak-ekle → id; iki sahip 1/2; irtibat doğru
def test_baskasinin_kontagi_sahip_secilemez(...):  # d1, d2'nin contact_id'sini POST → 200 + "Seçilen müşteri bulunamadı.", kayıt oluşmaz
def test_hemen_ilana_cikar(...):  # ilana_cikar=1, satilik, '4.250.000' → 1 ilan, fiyat 4250000, durum 'pazarlamada'
def test_kontak_ara_yalniz_gorunurleri_dondurur(...):  # d1 araması d2'nin kontağını içermez; broker ikisini de bulur
def test_baskasinin_gayrimenkulu_duzenlenemez(...):  # d2 → /analysis/<d1 kaydı>/edit 404
def test_yatirimci_alanlari_formda_yok(...):  # GET /analysis/new HTML'inde 'Alım Tarihi', 'Maliyet', 'Elde Tutma' yok; 'Gayrimenkul türü' var
```

- [ ] **Step 2: FAIL gör** — `scripts/test.sh tests/test_gayrimenkul_form.py -v`.
- [ ] **Step 3: `modules/gayrimenkul_form.py`'yi ve rotaları yaz.** Sahipler + ilan aynı transaction'da: `formdan_gayrimenkul` → `sahipleri_kaydet` → (ilana_cikar ise) `ilan_kaydet(None, user, {..., 'durum': 'pazarlamada', 'gayrimenkuller': [{'id': g.id}]})` → commit; `IlanHatasi` → rollback, formu hata ve girilen değerlerle yeniden çiz (200).
- [ ] **Step 4: Şablonu ve JS'i yaz.** `gayrimenkul/form.html` `dashboard_base.html`'i genişletir; bölümler spec §5.1 sırasıyla; her türe özel blok `data-turler="konut isyeri bina"` gibi işaretli, `gayrimenkul_form.js` seçili türe göre gösterir/gizler ve gizlenen alanlarda `required`'ı kaldırır. JSON parsel yükleme ve SWOT listeleri eski `analysis_form.html`'den taşınır. `_sahipler.html`: arama kutusu (`/analysis/kontak-ara`), seçilen satırlar (hisse, irtibat radyo), "Yeni müşteri ekle" küçük formu (`/analysis/kontak-ekle`).
- [ ] **Step 5: PASS gör + elle kontrol** — `scripts/test.sh tests -v`; ardından `KOD=/opt/arsa-ilan` ile yerel test DB'ye bağlı geçici konteynerde `/analysis/new` sayfasını curl ile çekip `Gayrimenkul türü` ve tüm özellik başlıklarının render edildiğini gör.
- [ ] **Step 6: Eski şablonları sil, `grep -rn "analysis_form.html\|analysis_edit.html" blueprints templates` boş; commit** — `git commit -m "Türe göre gayrimenkul formu, hisseli mal sahipleri ve hemen ilana çıkar"`

---

### Task 5: Gayrimenkul listesi, detayı ve menü

**Files:**
- Create: `templates/gayrimenkul/liste.html`, `templates/gayrimenkul/detay.html`, `tests/test_gayrimenkul_ekranlari.py`
- Modify: `blueprints/analysis_bp.py` (`list_analyses` :49 ve `analiz_detay` :878 silinir; `analizler` :992 ve `view_analysis` :368 yeniden yazılır), `templates/base.html:81-116`, `templates/dashboard_base.html` (menü), şablonlardaki `analysis.analiz_detay`/`analysis.list_analyses` başvuruları

**Interfaces:**
- Consumes: `gorunur_gayrimenkuller`, `gayrimenkul_or_404`, `ArsaAnaliz.baslik_metni/aktif_ilan`, sabitler
- Produces:
  - `GET /analysis/list` (`analysis.analizler`): filtreler `tur`, `il`, `ilce`, `aktif_ilan` (`var`/`yok`), `q` (il/ilçe/mahalle/ada/başlık ilike). Kartta: tür rozeti, `baslik_metni`, özet satırı (`ArsaAnaliz.ozet -> str`: konutta "3+1 · 120 m² · 4. kat", arsada "800 m² · Konut imarlı · KAKS 1,5"), aktif ilan varsa teklif tipi + fiyat.
  - `GET /analysis/<id>` (`analysis.view_analysis`): türe özel bilgiler (yalnız dolu alanlar), özellik grupları, SWOT, fotoğraflar (mevcut medya yükle/sil), sahipler (hisse, irtibat, CRM kontak linki), "Yer aldığı ilanlar" tablosu (kod, tip, durum, tarih) ve "Yeni ilan oluştur" düğmesi (`ilan.yeni` + `gayrimenkul=<id>`), rapor düğmeleri (Task 8 tanıtım raporu). Birim maliyet/güncel değer/değer artışı yok.
  - Menü: "Analizlerim/Analizler" → "Gayrimenkuller" (`analysis.analizler`), altına "İlanlar" (`ilan.liste`, Task 6). `base.html`'deki sidebar endpoint listelerine `ilan.liste`, `ilan.detay` eklenir.

- [ ] **Step 1: Testleri yaz** — `test_liste_tur_filtresi` (arsa + daire kayıtları; `?tur=konut` yalnız daireyi içerir), `test_liste_aktif_ilan_filtresi`, `test_broker_ekibin_kayitlarini_listeler_danisman_digerini_goremez`, `test_detay_konut_alanlari_ve_ilanlar` (HTML'de "3+1", "Kombi (doğalgaz)", ilan kodu; "Birim Maliyet" yok), `test_detay_baskasina_404`, `test_menude_gayrimenkuller_ve_ilanlar` (`/index` HTML'inde "Gayrimenkuller" var, "Analizlerim" yok).
- [ ] **Step 2: FAIL gör.**
- [ ] **Step 3: Rotaları ve şablonları yaz; yinelenen uçları sil; `grep -rn "analiz_detay\|list_analyses" blueprints templates` → yalnız tanım dışı başvuru kalmamalı.**
- [ ] **Step 4: PASS gör** — `scripts/test.sh tests -v`.
- [ ] **Step 5: Commit** — `git commit -m "Gayrimenkul listesi ve detayı; menüde Gayrimenkuller ve İlanlar"`

---

### Task 6: İlan ekranları (`/ilanlar`)

**Files:**
- Create: `blueprints/ilan_bp.py`, `templates/ilan/liste.html`, `templates/ilan/form.html`, `templates/ilan/detay.html`, `templates/ilan/_emsaller.html`, `static/js/ilan_form.js`, `tests/test_ilan_ekranlari.py`
- Modify: `app.py:288-289` (kayıt: `app.register_blueprint(ilan_bp, url_prefix='/ilanlar')`)

**Interfaces:**
- Consumes: `ilan_servis.*`, `ilan_hesap.tutar_ayristir`, sabitler
- Produces (endpoint adları):
  - `ilan.liste` `GET /ilanlar/` — filtreler `teklif_tipi`, `durum`, `tur` (ana gayrimenkulün türü), `fiyat_min`, `fiyat_max` (satılıkta fiyat, kiralıkta kira), `sorumlu`. Kart: kod, tip ve durum rozeti, başlık, özet ("Kat karşılığı · 4 parsel · 3.200 m² · %50" / "Satılık · Daire · 3+1 · 4.250.000 ₺").
  - `ilan.yeni` `GET|POST /ilanlar/yeni` — sorgu parametreleri `sahip=<contact_id>` ve/veya tekrarlanabilir `gayrimenkul=<id>` ön seçim yapar.
  - `ilan.sahip_gayrimenkulleri` `GET /ilanlar/sahip/<contact_id>/gayrimenkuller` → JSON `[{"id","baslik","ozet","m2","kaks","aktif_ilan_kodu"}]` (kontak `gorunur_kontaklar` içinde değilse 404).
  - `ilan.detay` `GET /ilanlar/<id>`, `ilan.duzenle` `GET|POST /ilanlar/<id>/duzenle`, `ilan.durum` `POST /ilanlar/<id>/durum` (form `durum`), `ilan.sil` `POST /ilanlar/<id>/sil` (yalnız oluşturan/broker/superadmin; portföy ve fırsat bağları kalkar, gayrimenkuller silinmez).
  - Form alanları: `ilan_servis.ilan_kaydet` `veri` anahtarlarıyla aynı adlar; gayrimenkuller `gayrimenkul_id[]` + `parsel_fiyati[]`, `ana_gayrimenkul_id`; emsaller `emsal_konum[]`, `emsal_m2[]`, `emsal_fiyat[]`, `emsal_pay[]`, `emsal_link[]`, `emsal_not[]`. Tutarlar `tutar_ayristir`.

- [ ] **Step 1: Testleri yaz (`tests/test_ilan_ekranlari.py`)**

```python
def test_kat_karsiligi_ilani_uctan_uca(...):
    # Hasan Yılmaz (broker'ın kontağı) sahibi; 213/2-3-4-5 gayrimenkulleri (Task 3'teki m2/kaks).
    # GET /ilanlar/sahip/<hasan>/gayrimenkuller → 4 kayıt
    # POST /ilanlar/yeni: kat_karsiligi, pay '50', ek_nakit '2.000.000', teslim 24, teminat 'Banka teminat mektubu',
    #   tevhid 'yapilacak', emsal pay 40 ve 50 → 302 /ilanlar/<id>
    # GET detay: "ILN-", "4 parsel", "3.200", "4.800", "2.400", "%45", "Talep bölge ortalamasının üstünde", "Banka teminat mektubu"
def test_satilik_ilan_emsal_karsilastirma(...):  # emsal 100 m²/2.000.000 ve 300 m²/4.500.000; daire 120 m², fiyat 1.950.000 → "16.250", "Piyasa seviyesinde"
def test_kiralik_ilan(...):  # kira '30.000', depozito '60.000' → detayda "30.000 ₺"
def test_durum_degisikligi_cakisma(...):  # g1 aktif ilan A; ilan B 'hazirlaniyor' → durum 'pazarlamada' POST → flash'ta A'nın kodu, B durumu değişmez
def test_kakssiz_parsel_uyarisi(...):  # bir parsel kaks None → detayda "KAKS bilgisi olmayan parseller hesaba katılmadı" ve parsel başlığı
def test_emsal_yoksa_elle_bolge_fiyati(...):  # bolge_m2_fiyat_elle '18.000' → "18.000" ve "elle girildi"
def test_liste_filtreleri(...):  # ?teklif_tipi=kiralik yalnız kiralık; ?durum=geri_cekildi
def test_ilan_yetki(...):  # d2, d1'in ilanını göremez (404), broker görür; d1 düzenleyebilir
def test_ilan_silinince_gayrimenkul_kalir(...):
```

- [ ] **Step 2: FAIL gör.**
- [ ] **Step 3: `ilan_bp.py`'yi yaz.** POST'ta form → `veri` dict → `ilan_kaydet` → commit → `ilan.detay`; `IlanHatasi` → rollback, form 200 + hata. Detay görünümü `ilan_ozeti(ilan)` sonucunu şablona verir.
- [ ] **Step 4: Şablonları ve `ilan_form.js`'i yaz.** Form adımları spec §5.2: (1) sahip seç (Task 4'teki `_sahipler.html` arama bileşenini tek seçim modunda kullan) → `sahip_gayrimenkulleri` JSON'u ile onay kutulu liste + "Gayrimenkul ekle" (`analysis.new_analysis` yeni sekmede); (2) teklif tipi radyoları, tipe göre alanlar; (3) `_emsaller.html` satır ekle/sil; (4) canlı karşılaştırma kutusu — JS, `ilan_hesap` ile aynı formüllerle (m² ağırlıklı ortalama, ±5 eşiği, kat karşılığı ters yön) hesaplar; sunucu detay sayfası tek doğruluk kaynağıdır. Detay: spec §5.3.
- [ ] **Step 5: PASS gör** — `scripts/test.sh tests -v`.
- [ ] **Step 6: Commit** — `git commit -m "İlan ekranları: çok gayrimenkullü satılık, kiralık ve kat karşılığı ilanları, emsaller"`

---

### Task 7: CRM bağlantıları ve portföyler

**Files:**
- Create: `tests/test_crm_portfoy_baglantilari.py`
- Modify: `blueprints/crm_bp.py` (`crm_contact_detail` :277-290, `deal/new` :635, deal edit ve `deal_detail`), `templates/crm/contact_detail.html`, `templates/crm/deal_detail.html`, `templates/crm/deal_form.html` (crm_bp `template_folder='../templates/crm'`), `blueprints/portfolio_bp.py` (`_portfolio_totals` :22, `portfolio_add_analysis` :157, `portfolio_remove_analysis` :173, detay :111), `templates/portfolio_detail.html`, `templates/new_portfolios.html`

**Interfaces:**
- Consumes: `gorunur_ilanlar`, `ilan_or_404`, `ilan_ozeti`, `Contact.sahiplikler`, `Portfolio.ilanlar`, `Deal.ilan_id`
- Produces:
  - Kontak detayı: "Gayrimenkulleri" sekmesi — her sahiplik: gayrimenkul `baslik_metni` (link), tür, hisse, aktif ilan kodu/durumu; onay kutuları + "Seçilenlerle yeni ilan" düğmesi → `GET ilan.yeni?sahip=<id>&gayrimenkul=..&gayrimenkul=..`.
  - Fırsat formu: `ilan_id` seçimi (`gorunur_ilanlar(current_user)`, etiket `"{kod} · {baslik}"`, boş seçilebilir); geçersiz/görünmeyen id → form hatası "Seçilen ilan bulunamadı."; fırsat detayında ilan linki; ilan detayında (Task 6 şablonu) "Bağlı fırsatlar" listesi.
  - Portföy: `POST /portfolio/<id>/add` artık `ilan_id` alır (eski `analiz_id` gelirse o gayrimenkulün `aktif_ilan`'ı ya da son ilanı eklenir; ikisi de yoksa hata); `POST /portfolio/<id>/remove/<int:ilan_id>`; `_portfolio_totals(ilanlar)` → `{'adet', 'toplam_fiyat' (satılık fiyatları), 'aylik_kira' (kiralık), 'kat_karsiligi_adet'}`; portföy detayında ilan kartları; "Maliyet" metni kalmaz.

- [ ] **Step 1: Testleri yaz** — `test_kontak_detayinda_gayrimenkulleri` (Hasan'ın 4 parseli ve hisse "1/2" görünür; "Seçilenlerle yeni ilan" linki `sahip=` içerir), `test_firsata_ilan_baglanir` (deal/new `ilan_id` → `Deal.ilan_id` dolu; ilan detayında fırsat başlığı), `test_firsata_gorunmeyen_ilan_baglanamaz`, `test_portfoye_ilan_eklenir_ve_toplam` (satılık 4.250.000 + kiralık 30.000 → detayda "4.250.000" ve "30.000", "Maliyet" yok), `test_eski_analiz_id_ile_portfoye_ekleme`.
- [ ] **Step 2: FAIL gör.**
- [ ] **Step 3: Değişiklikleri yaz.**
- [ ] **Step 4: PASS gör** — `scripts/test.sh tests -v`.
- [ ] **Step 5: Commit** — `git commit -m "Mal sahibi ve fırsatların ilanlara bağlanması; portföyler ilan içerir"`

---

### Task 8: İlan tabanlı raporlar (PDF, Word, PowerPoint)

**Files:**
- Create: `tests/test_raporlar.py`
- Modify: `modules/rapor/model.py`, `modules/rapor/assets.py`, `modules/rapor/pdf.py`, `modules/rapor/word.py`, `modules/rapor/pptx_.py`, `modules/rapor/__init__.py`, `blueprints/analysis_bp.py` (`_build_report` :667, `_report_or_redirect`, rapor rotaları :698-712, :1124-1152), `blueprints/ilan_bp.py`

**Interfaces:**
- Consumes: `ilan_ozeti`, sabitler, mevcut `Brand/Advisor`, `_photos_for`, `parse_swot`, `parse_coordinates`
- Produces:
  - `ReportModel`'den çıkarılan alanlar: `yillik_artis`, `artis_kaynagi`, `senaryolar`, `yatirim_ozet`; `Scenario` sınıfı ve `_scenarios` silinir; `assets.projection_chart` silinir.
  - Eklenen alanlar: `teklif_tipi: str|None` (tanıtım raporunda `None`), `teklif_etiketi: str`, `kod: str`, `tur_etiketi: str`, `parseller: list[dict]` (`baslik, ada, parsel, m2, imar, kaks`), `tur_bilgileri: list[tuple[str,str]]` (yalnız dolu türe özel alanlar, etiketli), `ozellik_gruplari: list[tuple[str, list[str]]]`, `fiyat_satirlari: list[tuple[str,str]]` (tipe göre: satılık "İstenen fiyat", "m² fiyatı"; kiralık "Aylık kira", "Depozito", "m² kira"; kat karşılığı "Arsa sahibi payı", "Ek nakit", "Teslim süresi", "Teminat", "Tevhid", "Toplam arsa alanı", "İnşaat hakkı (tahmini)", "Arsa sahibine düşen (tahmini)"), `emsaller: list[dict]`, `bolge: float|None`, `bolge_kaynak: str`, `fark: float|None`, `konum_etiketi: str|None`, `fiyat_ozet: str` (tek paragraf, eski `temel_ozet` yerine).
  - Korunan: `baslik` (satılık "Satılık {tur} Sunum Raporu", kiralık "Kiralık {tur} Sunum Raporu", kat karşılığı "Kat Karşılığı Teklif Raporu", tanıtım "{tur} Tanıtım Raporu"), konum alanları, SWOT, fotoğraflar, harita, QR, danışman, marka, `tavsiyeler`; arsa/tarlada `imar_durumu, taks, kaks, taban_alani, insaat_alani, kat_sayisi, altyapi`, `puan` (yalnız arsa/tarla ve tek parselde, mevcut `ArsaAnalizci` ile).
  - `build_report_model(ilan_or_none, gayrimenkul, user, detail_url='', upload_folder=None, base_dir=None) -> ReportModel` — `ilan_or_none` `None` ise tanıtım raporu (fiyat/emsal bölümü yok). `analiz_id` alanı `gayrimenkul.id`.
  - `assets.price_comparison_chart`: satılık/kiralıkta "Bu ilan" vs "Bölge ortalaması" (m² değeri), kat karşılığında pay % çubukları; `bolge is None` ise üretilmez.
  - Üç renderer: yatırım/senaryo bölümleri yerine "Fiyat ve Emsal Analizi" (fiyat satırları, emsal tablosu [konum, m², fiyat ya da pay, m² fiyatı], bölge ortalaması + kaynak, fark ve konumlandırma, grafik); çok parselde "Parseller" tablosu; türe özel bilgi tablosu; özellik grupları. Mal sahibi alanı hiçbir yerde yok.
  - Rotalar: `ilan.rapor` `GET /ilanlar/<id>/rapor/<fmt>` (`fmt` ∈ pdf/word/pptx), dosya adı `ilan_{kod}_{YYYYMMDD}.{ext}`; `analysis` rapor rotaları: gayrimenkulün `aktif_ilan`'ı varsa `ilan.rapor`'a yönlendirir, yoksa tanıtım raporu üretir (dosya adı `tanitim_{il}_{ilce}_{id}_{YYYYMMDD}`). `generate_pptx` POST'unun renk ayarları korunur.

- [ ] **Step 1: Testleri yaz (`tests/test_raporlar.py`)**

```python
@pytest.mark.parametrize('fmt', ['pdf', 'word', 'pptx'])
@pytest.mark.parametrize('senaryo', ['satilik_daire', 'kiralik_dukkan', 'kat_karsiligi_4_parsel', 'tanitim_arsa'])
def test_rapor_uretilir(fmt, senaryo, ...):  # 200, doğru Content-Type, gövde > 10 KB
def test_rapor_metni_kat_karsiligi(...):  # docx'ten python-docx ile metin: "Kat Karşılığı Teklif Raporu", "%50", "2.400", "213", "Parseller"; "senaryo" ve "değer artışı" yok
def test_rapor_mal_sahibi_icermez(...):  # sahibin adı "Hasan" ve telefonu docx metninde ve pptx slayt metinlerinde yok
def test_rapor_emsal_yoksa_grafik_yok(...):  # build_report_model(...).bolge is None ve build_assets sonucunda price_chart anahtarı yok
def test_gayrimenkul_raporu_aktif_ilana_yonlenir(...):  # /analysis/<id>/report/pdf → 302 /ilanlar/<ilan>/rapor/pdf
```

- [ ] **Step 2: FAIL gör.**
- [ ] **Step 3: `model.py`'yi yeniden yaz** (Interfaces); `fiyat_ozet` metni: satılık/kiralıkta "{konum} konumundaki {ozet} için istenen {fiyat/kira} {tutar}, m² {değer}." + bölge varsa "Bölge ortalaması {bolge} ({emsal sayısı} emsal / elle girildi); ilan bu ortalamanın %{abs(fark)} {altında/üzerinde} — {konum_etiketi}."; kat karşılığında "{n} parsel, toplam {m2} m² arsa için arsa sahibi %{pay} pay talep ediyor; tahmini {sahibe} m² inşaat alanına karşılık gelir." + bölge varsa pay karşılaştırması. Tavsiyeler: mevcut fiyat tavsiyeleri `fark` üzerinden; kat karşılığında `fark > 5` → "Talep edilen pay bölge emsallerinin üzerinde; müteahhit tekliflerinde pazarlık beklenmeli.", tevhid `yapilacak` → "Parsellerin tevhidi (birleştirilmesi) için belediye ve tapu süreci planlanmalı."; tapu/imar teyit tavsiyesi korunur.
- [ ] **Step 4: `assets.py`, `pdf.py`, `word.py`, `pptx_.py`'yi uyarlayıp rotaları bağla.** Her renderer'da senaryo/projeksiyon kodu tamamen silinir (`grep -n "senaryo\|projection\|yatirim_ozet" modules/rapor` boş).
- [ ] **Step 5: PASS gör** — `scripts/test.sh tests -v` (24 rapor testi dahil hepsi yeşil); üretilen bir PDF ve PPTX'i `pdftoppm`/`libreoffice --headless` ile görüntüye çevirip gözle kontrol et (taşan tablo, boş bölüm olmamalı).
- [ ] **Step 6: Commit** — `git commit -m "Raporlar ilan tabanlı: fiyat ve emsal analizi, parseller, kat karşılığı şartları"`

---

### Task 9: API uyumu, demo verisi, işlev testi ve PR

**Files:**
- Modify: `blueprints/api/schemas/analysis_schemas.py`, `blueprints/api/v1/analysis.py`, `/opt/arsa-tests/demo/demo_yukle.py`, `/opt/arsa-tests/demo/demo_temizle.py`, `/opt/arsa-tests/demo/fonksiyon_testi.py` (depo dışı), `README.md` (kısa "Gayrimenkul ve İlanlar" bölümü)
- Create: `tests/test_api_uyum.py`

**Interfaces:**
- Consumes: tüm önceki task'lar
- Produces: API analiz şemasına salt-okunur `tur`, `alt_tur`, `baslik`, `aktif_ilan` (`{kod, teklif_tipi, durum, fiyat}` ya da null); `GUNCELLENEBILIR` listesine dokunulmaz. Demo: spec §8 listesi; `demo_temizle.py` yeni tabloları da siler (sıra: `ilan_emsalleri`, `portfolio_ilanlar`, `crm_deals.ilan_id=NULL`, `ilan_gayrimenkulleri`, `ilanlar`, `gayrimenkul_sahipleri`, sonra mevcut adımlar).

- [ ] **Step 1: `tests/test_api_uyum.py`** — `test_api_analiz_listesi_eski_alanlar_ve_yeni_alanlar` (JWT ile `/api/v1/analysis` → eski alanlar `il, metrekare, fiyat` hâlâ var; `tur`, `aktif_ilan.kod` var). FAIL gör, şemayı güncelle, PASS gör.
- [ ] **Step 2: Demo yükleyiciyi genişlet ve yerel `arsa_demo` kopyasında çalıştır** — `DB=arsa_ilan_demo KOD=/opt/arsa-ilan /opt/arsa-tests/demo/run.sh hazirla.py && … demo_yukle.py`; çıktı: 213 ada 4 parsellik kat karşılığı ilanı, 5 farklı tür, hisseli tarla.
- [ ] **Step 3: `fonksiyon_testi.py`'yi yeni rotalara uyarla ve çalıştır** — tüm satırlar `ok`, `FAIL` sayısı 0. Ayrıca mevcut canlı veritabanının son yedeğini (`/opt/arsa-backups/supabase_arsa_*.sql.gz` en yenisi) yerel `arsa_gecis_provasi` veritabanına yükle, `KOD=/opt/arsa-ilan` ile uygulamayı bir kez başlatıp (`kur()` çalışır) ikinci kez başlat; ilan sayısı = gayrimenkul sayısı, id=3'ün `bolge_m2_fiyat_elle` ≈ 6934, tüm `/analysis/<id>` ve `/ilanlar/<id>` sayfaları 200, eski arsa raporları üç formatta üretilir.
- [ ] **Step 4: flake8** — `docker … python -m flake8 --select=E9,F63,F7,F82 --show-source .` → 0.
- [ ] **Step 5: Commit, push, PR** — `git commit -m "API'ye gayrimenkul/ilan alanları; README"`, `git push`, `gh pr create` (başlık "Gayrimenkul, ilan, kat karşılığı ve mal sahibi yeniden tasarımı"; gövde: özet, geçiş notu, test sonuçları, "canlıya almadan önce Supabase yedeği alınacak"; son satır `🤖 Generated with [Claude Code](https://claude.com/claude-code)`). Birleştirme ve canlıya alma kullanıcı onayıyla, ayrı adım: yedek (`/opt/arsa-backups/yedekle.sh`) → merge → `/opt/arsaanalizvesunum`'da `git pull` + `docker compose -f docker-compose.server.yml up -d --build` → demo yükleyiciyi canlıda yeni türlerle tekrar çalıştır → sayfa kontrolleri.

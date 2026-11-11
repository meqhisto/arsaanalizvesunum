# Aşama 1 — Güven: Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Programı ekibe vermeden önce telefonda ve bilgisayarda güvenilir hale getirmek: gerçek tarayıcı testleri, CSRF koruması, istek kaydı ve hata bildirimi, dosya yedeği, ölü kodun temizliği.

**Architecture:** Tarayıcı testleri, uygulamanın canlı imajından SQLite ile açılan izole bir kopyasına karşı Playwright (Chromium ve iPhone 13 profilli WebKit) ile çalışır. CSRF, Flask-WTF `CSRFProtect` ile sunucuda zorunlu kılınır; token tek bir betikle tüm formlara ve `fetch`/XHR isteklerine eklenir, böylece 39 şablondaki 72 form tek tek değiştirilmez. Hata bildirimi mevcut `Bildirim` tablosunu kullanır, yeni altyapı eklenmez.

**Tech Stack:** Python 3.10, Flask, Flask-WTF 1.2.2, gunicorn, pytest 8.3.3, Playwright 1.48.0 (`mcr.microsoft.com/playwright/python:v1.48.0-jammy`), Docker Compose, bash.

**Spec:** `docs/superpowers/specs/2026-11-10-yol-haritasi-design.md` (Bölüm 4)

## Global Constraints

- Her görev kendi dalında yapılır, PR ile birleştirilir. Canlıya alma yalnızca ofis sahibinin o PR için açık onayıyla yapılır.
- Testler canlı veritabanına (Supabase) asla bağlanmaz. Tarayıcı testleri SQLite, `tests/` altındaki mevcut testler `arsa_ilan_test` veritabanını kullanır.
- Canlıdaki kayıtlara ve yüklenen dosyalara test amacıyla dokunulmaz.
- Kullanıcıya görünen tüm metinler Türkçedir.
- Görev 1 birleştikten sonra her PR, birleşmeden önce `scripts/tarayici_testi.sh` ile geçer.
- İstek kaydına IP adresi ve sorgu dizgisi (query string) yazılmaz.

## Review Focus

1. Sekme saatlerce açık kaldıktan sonra form gönderilir: kullanıcı ham hata sayfası değil, "sayfayı yenileyin" uyarısıyla geldiği sayfayı görmelidir (Görev 3).
2. Sayfa yüklendikten sonra eklenen form veya modal içindeki form gönderilir: CSRF token'ı yine eklenmiş olmalıdır (Görev 3).
3. Gönder düğmesine çift tıklanır: sunucuya tek POST gitmelidir (Görev 1).
4. Aynı sunucu hatası gün içinde 100 kez oluşur: yöneticiye o yol için günde tek bildirim düşmelidir (Görev 4).
5. Yedek sırasında veritabanı dökümü başarısız olur veya bir birim boştur: betik sıfırdan farklı kodla çıkmalı, eski yedekleri silmemelidir (Görev 5).

---

### Task 1: Tarayıcı testleri (yol haritası 1.1)

**Files:**
- Create: `tests/tarayici/Dockerfile`, `tests/tarayici/tohum.py`, `tests/tarayici/conftest.py`, `tests/tarayici/test_akislar.py`, `scripts/tarayici_testi.sh`
- Modify: `README.md` (testlerin nasıl çalıştırılacağı, 5-6 satır)

**Interfaces:**
- Produces: `scripts/tarayici_testi.sh [pytest argümanları]` — çıkış kodu 0 ise tüm akışlar geçti. Sonraki görevler doğrulama için bunu çağırır.
- Produces (conftest): `sayfa` fixture'ı — giriş yapmış `playwright.sync_api.Page`; `motor` parametresi `chromium` ve `webkit-iphone`. Fixture kapanırken sayfada JS hatası (`pageerror`) varsa testi başarısız sayar. `sayfa.post_istekleri` listesi o testteki POST yollarını tutar.
- Produces (conftest): `zorunlulari_doldur(sayfa, form_secici)` yardımcı fonksiyonu.
- Tohum verisi: kullanıcı `t@t.co` / `Abc12345!` (superadmin), ofis "Test Ofis", 1 gayrimenkul (id 1), 1 iş (id 1, kod `IS-1`), 1 müşteri.

- [ ] **Step 1: Çalıştırıcıyı ve tohumu yaz.** `scripts/tarayici_testi.sh` şunları yapar: `arsa-e2e` adlı Docker ağı oluşturur; `arsaanalizvesunum-web` imajından `arsa-e2e-app` kapsayıcısını başlatır (`DATABASE_URL=sqlite:////tmp/t.db`, `SECRET_KEY=test`, `JWT_SECRET_KEY=test`, `UPLOAD_FOLDER=/tmp/uploads_e2e`, `IS_BELGE_KLASORU=/tmp/belge_e2e`); depodaki `templates`, `static/js`, `blueprints`, `utils`, `modules`, `models`, `app.py` salt okunur olarak imajdaki aynı yolların üstüne bağlanır (deponun tamamı bağlanmaz: imajdaki webpack çıktısı gizlenir); `/app/static/uploads` `/tmp/uploads_e2e`'ye sembolik bağlanır; `tests/tarayici/tohum.py` çalışır; gunicorn 1 worker ile başlar. Sonra `tests/tarayici/Dockerfile`'dan `arsa-e2e-test` imajını derler (taban Playwright imajı + `pip install playwright==1.48.0 pytest==8.3.3 pillow`) ve `pytest /tests/tarayici "$@"` çalıştırır. Çıkışta (başarılı ya da başarısız) kapsayıcıyı ve ağı siler, pytest'in çıkış kodunu döndürür.

- [ ] **Step 2: Başarısız olacak ilk testi yaz** (`test_akislar.py`):

```python
def test_giris(sayfa):
    assert '/auth/login' not in sayfa.url
    assert sayfa.locator('text=Çıkış').count() >= 1
```

- [ ] **Step 3: Çalıştır, başarısız olduğunu gör.** `scripts/tarayici_testi.sh -k test_giris` → `fixture 'sayfa' not found`.

- [ ] **Step 4: `conftest.py`'yi yaz.** `sayfa` fixture'ı yukarıdaki arayüze göre. `zorunlulari_doldur` şu algoritmayı kullanır (imza ve testler bunu belirlemediği için burada verildi):

```python
def zorunlulari_doldur(sayfa, form_secici):
    """Formdaki görünür ve etkin zorunlu alanları doldurur; türe göre alan açan formlar için iki tur atar."""
    js = '''(secici) => document.querySelectorAll(secici + ' [required]').forEach(e => {
        if (e.disabled || e.offsetParent === null || e.value) return;
        if (e.tagName === 'SELECT') e.selectedIndex = Math.min(1, e.options.length - 1);
        else e.value = /m2|metre|fiyat|kira|tutar|bedel/i.test(e.name) ? '95' : 'Test';
        e.dispatchEvent(new Event('input', {bubbles: true}));
        e.dispatchEvent(new Event('change', {bubbles: true}));
    })'''
    for _ in range(2):
        sayfa.evaluate(js, form_secici)
        sayfa.wait_for_timeout(300)
```

- [ ] **Step 5: `test_giris`'in her iki motorda geçtiğini gör.** `scripts/tarayici_testi.sh -k test_giris` → `2 passed`.

- [ ] **Step 6: Kalan akış testlerini yaz.** Her test iki motorda çalışır. Fotoğraflar testte Pillow ile 4032x3024 gürültülü JPEG olarak üretilir (yaklaşık 10 MB).

| Test | Yapılan | Doğrulanan |
|---|---|---|
| `test_detaydan_fotograf_yukle` | `/analysis/1`'de 3 fotoğraf seç, "N dosya hazır" yazısını bekle, Yükle | `post_istekleri == ['/analysis/1/media_upload']`; sayfada "3 dosya yüklendi."; `img[src*="/uploads/1/"]` sayısı 3 |
| `test_kucultme_bitmeden_gonder` | 2 fotoğraf seç, beklemeden Yükle | 15 sn içinde "2 dosya yüklendi." |
| `test_cift_tiklama_tek_istek` | 1 fotoğraf seç, hazır olunca Yükle'ye `dblclick` | `post_istekleri` uzunluğu 1 |
| `test_fotografli_gayrimenkul_olustur` | `/analysis/new`, `zorunlulari_doldur`, `#medya`'ya 1 fotoğraf, Kaydet | adres `/analysis/<sayı>`; "Gayrimenkul kaydedildi."; 1 fotoğraf |
| `test_ilan_olustur` | `/ilanlar/yeni`, zorunlu alanlar, kaydet | adres `/ilanlar/<sayı>` |
| `test_musteri_ekle` | CRM yeni kişi formu, ad ve soyad, kaydet | kişi listesinde ad görünür |
| `test_is_belgesi_yukle` | `/isler/1?sekme=belgeler`, PDF + JPEG | "2 belge yüklendi." |
| `test_profil_fotografi` | `/profile`, 1 fotoğraf, kaydet | "Profil başarıyla güncellendi!"; `img[src*="/uploads/profiles/"]` var |
| `test_ofis_logosu` | `/admin/office/create`, ad + PNG | "başarıyla oluşturuldu" |
| `test_rapor_indir` | `/analysis/report/generate/pdf/1` isteği | durum 200, gövde `%PDF` ile başlar |
| `test_crm_iceri_aktar` | İçe aktarma sihirbazına 100 satırlık CSV | 2. adıma geçer, "100" kayıt görünür |

- [ ] **Step 7: Tümünü çalıştır.** `scripts/tarayici_testi.sh` → `24 passed`. Geçmeyen bir akış gerçek bir hataysa testi gevşetme: hatayı ayrı commit ile düzelt, düzeltilemeyecek kadar büyükse testi `xfail(reason=...)` ile işaretleyip PR açıklamasına yaz.

- [ ] **Step 8: Regresyonu kanıtla.** `templates/dashboard_base.html`'de geçici olarak düzeltme öncesi sürümü koyup (`git show de785ba:templates/dashboard_base.html > templates/dashboard_base.html`) `scripts/tarayici_testi.sh -k fotograf_yukle` çalıştır → başarısız olmalı (10 Kasım'daki düğme hatası). Dosyayı geri al (`git checkout templates/dashboard_base.html`), tekrar çalıştır → geçmeli.

- [ ] **Step 9: README'ye bölümü ekle ve commit et.**

```bash
git add tests/tarayici scripts/tarayici_testi.sh README.md
git commit -m "Tarayıcı testleri: ana akışlar Chromium ve iPhone WebKit'te"
```

---

### Task 2: Çalışmayan API kodunu kaldır (1.7)

**Files:**
- Delete: `blueprints/api/v1/crm.py`, `blueprints/api/v1/media.py`, `blueprints/api/v1/portfolio.py`
- Modify: `blueprints/api/api_bp.py:29,38` (yorum satırına alınmış `media_v1` satırları silinir)
- Test: `tests/test_api_uyum.py`

Bu üç dosya kayıtlı değil (kayıtlı olanlar `crm_minimal.py` ve `portfolio_minimal.py`) ve içe aktarılamıyor (`@()` dekoratörü).

- [ ] **Step 1: Başarısız testi yaz** (`tests/test_api_uyum.py` sonuna):

```python
def test_api_v1_modullerinin_hepsi_ice_aktarilir():
    import importlib, pkgutil
    import blueprints.api.v1 as v1
    for m in pkgutil.iter_modules(v1.__path__):
        importlib.import_module(f'blueprints.api.v1.{m.name}')
```

- [ ] **Step 2: Başarısız olduğunu gör.** `/opt/arsa-tests/run.sh -m pytest /app/tests/test_api_uyum.py -k ice_aktarilir` → `TypeError: 'tuple' object is not callable`.
- [ ] **Step 3: Üç dosyayı ve yorum satırlarını sil.**
- [ ] **Step 4: Geçtiğini gör.** Aynı komut → `1 passed`; ardından tüm `tests/` → hepsi geçer.
- [ ] **Step 5: Commit.** `git commit -am "Kayıtlı olmayan ve içe aktarılamayan API modülleri kaldırıldı"`

---

### Task 3: CSRF koruması (1.3)

**Files:**
- Create: `static/js/csrf.js`, `templates/_csrf.html`, `tests/test_csrf.py`
- Modify: `requirements.txt` (`Flask-WTF==1.2.2`), `app.py` (kurulum ve hata karşılayıcı), `<head>` içeren her üst düzey şablon (`grep -L "{% extends" templates -r --include=*.html | xargs grep -l "<head"` ile bulunur; `{% include "_csrf.html" %}` eklenir), `tests/tarayici/conftest.py`

**Interfaces:**
- Produces: `templates/_csrf.html` → `<meta name="csrf-token" content="{{ csrf_token() }}">` ve `csrf.js` yüklemesi.
- Produces: `static/js/csrf.js` — token'ı meta etiketinden okur; (a) `document` üzerinde yakalama aşamasındaki `submit` dinleyicisiyle, yöntemi POST olan ve `csrf_token` alanı olmayan her forma gizli alan ekler; (b) `window.fetch`'i ve `XMLHttpRequest.prototype.send`'i sarar, aynı kökene giden GET/HEAD dışı isteklere `X-CSRFToken` başlığı ekler.
- `app.py`: `csrf = CSRFProtect(app)`; `csrf.exempt(api_bp)` (API JWT kullanır); `WTF_CSRF_TIME_LIMIT = None` (token oturum boyunca geçerli).
- `CSRFError` karşılayıcısı: yol `/api/` içeriyorsa veya istek JSON ise `{"error": "Oturum doğrulanamadı. Sayfayı yenileyip tekrar deneyin."}` ve 400; değilse aynı metinle `flash(..., 'warning')` ve aynı kökenli `Referer`'a yönlendirme (yoksa `/`).

- [ ] **Step 1: Başarısız sunucu testlerini yaz** (`tests/test_csrf.py`). Aynı dosyada tanımlanacak yardımcılar: `csrf_app` fixture'ı (mevcut `app` fixture'ının `WTF_CSRF_ENABLED=True` yapılmış hali; test bitince `False`'a döner), `csrf_istemci` fixture'ı (oturumuna `_user_id` yazılmış test istemcisi), `kullanici() -> User` (o kullanıcıyı veritabanından taze okur), `meta_token(yanit) -> str` (yanıt gövdesindeki `csrf-token` meta etiketinin içeriği, yoksa boş dizge):

```python
def test_tokensiz_form_reddedilir(csrf_istemci):          # giriş yapmış istemci
    r = csrf_istemci.post('/profile', data={'ad': 'X', 'soyad': 'Y', 'timezone': 'UTC'},
                          headers={'Referer': 'http://localhost/profile'})
    assert r.status_code == 302 and r.headers['Location'].endswith('/profile')
    assert kullanici().ad != 'X'

def test_tokenli_form_kabul_edilir(csrf_istemci):
    token = meta_token(csrf_istemci.get('/profile'))
    r = csrf_istemci.post('/profile', data={'ad': 'X', 'soyad': 'Y', 'timezone': 'UTC', 'csrf_token': token})
    assert kullanici().ad == 'X'

def test_tokensiz_json_400_doner(csrf_istemci):
    r = csrf_istemci.post('/crm/api/import/validate', json={'column_mapping': {}})
    assert r.status_code == 400 and 'Sayfayı yenileyip' in r.get_json()['error']

def test_baslikla_json_kabul_edilir(csrf_istemci):
    token = meta_token(csrf_istemci.get('/profile'))
    r = csrf_istemci.post('/crm/api/import/validate', json={'column_mapping': {}}, headers={'X-CSRFToken': token})
    assert r.status_code != 400 or 'Sayfayı yenileyip' not in r.get_data(as_text=True)

def test_jwt_api_muaf(csrf_istemci):
    r = csrf_istemci.post('/api/v1/auth/login', json={'email': 'yok@x.co', 'password': 'x'})
    assert 'Sayfayı yenileyip' not in r.get_data(as_text=True)

def test_giris_sayfasinda_token_var(csrf_app):
    assert meta_token(csrf_app.test_client().get('/auth/login'))
```

- [ ] **Step 2: Başarısız olduklarını gör.** `/opt/arsa-tests/run.sh -m pytest /app/tests/test_csrf.py` → 6 başarısız.
- [ ] **Step 3: `app.py` kurulumunu, hata karşılayıcıyı, `_csrf.html`'i ve `csrf.js`'i yaz; şablonlara include ekle.** Mevcut `{% macro csrf() %}` tanımlarına ve `{{ csrf_token() if csrf_token else '' }}` satırlarına dokunma: zararsızlar.
- [ ] **Step 4: Sunucu testlerinin geçtiğini gör.** → `6 passed`; tüm `tests/` → hepsi geçer.
- [ ] **Step 5: Tarayıcı tarafını sabitle.** `tests/tarayici/conftest.py`'deki `sayfa` fixture'ına ekle: testteki her aynı kökenli POST isteğinin gövdesinde `csrf_token` veya başlığında `x-csrftoken` yoksa test başarısız. `test_akislar.py`'ye ekle:

```python
def test_sonradan_eklenen_form_token_alir(sayfa):
    sayfa.goto(BASE + '/profile')
    sayfa.evaluate('''() => { const f = document.createElement('form'); f.method = 'post'; f.action = '/profile';
        f.innerHTML = '<input name="ad" value="Dinamik"><input name="soyad" value="T"><input name="timezone" value="UTC"><button>g</button>';
        document.body.appendChild(f); f.querySelector('button').click(); }''')
    sayfa.wait_for_load_state('networkidle')
    assert 'Profil başarıyla güncellendi!' in sayfa.content()

def test_bayat_token_uyari_verir(sayfa):
    sayfa.goto(BASE + '/profile')
    sayfa.evaluate("document.querySelector('meta[name=csrf-token]').content = 'gecersiz'")
    sayfa.locator('form[enctype="multipart/form-data"] button[type=submit]').first.click()
    sayfa.wait_for_load_state('networkidle')
    assert 'Sayfayı yenileyip tekrar deneyin' in sayfa.content() and '/profile' in sayfa.url
```

- [ ] **Step 6: `scripts/tarayici_testi.sh`** → Görev 1'in tüm testleri ve iki yeni test iki motorda geçer (`28 passed`). Token'sız POST yakalanan her sayfa için o sayfanın POST yolunu (`$.ajax`, elle kurulan form vb.) `csrf.js` kapsamına al; şablonu tek tek yamalama.
- [ ] **Step 7: Commit.** `git commit -m "CSRF koruması: tüm formlar ve tarayıcı istekleri"`

Canlıya alma notu: yeni bağımlılık imajın yeniden derlenmesini gerektirir. Canlıya alındıktan sonra ofis sahibi bir form kaydedip bir fotoğraf yükleyerek doğrular.

---

### Task 4: İstek kaydı ve hata bildirimi (1.4)

**Files:**
- Modify: `docker-compose.server.yml` (gunicorn komutu ve `logging` bölümü), `app.py` (500 karşılayıcı)
- Create: `modules/hata_bildirimi.py`, `tests/test_hata_bildirimi.py`

**Interfaces:**
- gunicorn'a eklenen bayraklar: `--access-logfile - --access-logformat '%(t)s %(m)s %(U)s %(s)s %(B)sB %(M)sms'` (IP ve sorgu dizgisi yok).
- `web` servisine: `logging: {driver: json-file, options: {max-size: "20m", max-file: "5"}}`.
- Produces: `modules/hata_bildirimi.py::bildir(yontem: str, yol: str, hata: Exception) -> int` — her etkin superadmin için `Bildirim(tur='hata', mesaj=f"Sunucu hatası: {yontem} {yol} ({type(hata).__name__})", url='/admin/dashboard', gun=bugün)` ekler; aynı kullanıcı, aynı gün ve aynı mesaj zaten varsa eklemez; eklenen kayıt sayısını döndürür. Kendi içinde hata olursa yutar ve 0 döndürür (hata karşılayıcı ikinci bir hata üretmemeli).
- `app.py` 500 karşılayıcısı `bildir(request.method, request.path, e)` çağırır.

- [ ] **Step 1: Başarısız testleri yaz** (`tests/test_hata_bildirimi.py`; `superadmin` ve `danisman` fixture'ları aynı dosyada tanımlanır, `db_session` ile birer etkin `User` oluşturur):

```python
def test_hata_superadmine_bildirilir(db_session, superadmin):
    assert bildir('POST', '/x', ValueError('a')) == 1
    b = Bildirim.query.filter_by(user_id=superadmin.id, tur='hata').one()
    assert b.mesaj == 'Sunucu hatası: POST /x (ValueError)'

def test_ayni_hata_gunde_bir_kez(db_session, superadmin):
    for _ in range(100):
        bildir('POST', '/x', ValueError('a'))
    assert Bildirim.query.filter_by(tur='hata').count() == 1

def test_farkli_yol_ayri_bildirim(db_session, superadmin):
    bildir('POST', '/x', ValueError('a')); bildir('GET', '/y', ValueError('a'))
    assert Bildirim.query.filter_by(tur='hata').count() == 2

def test_danismana_bildirilmez(db_session, superadmin, danisman):
    bildir('POST', '/x', ValueError('a'))
    assert Bildirim.query.filter_by(user_id=danisman.id).count() == 0
```

- [ ] **Step 2: Başarısız olduklarını gör** → `ModuleNotFoundError: modules.hata_bildirimi`.
- [ ] **Step 3: `bildir`'i yaz ve 500 karşılayıcısına bağla.** Bildirim zilinin `tur='hata'` kaydını gösterdiğini `templates/dashboard_base.html`'deki zil kodunda doğrula; tür bazlı simge eşlemesi varsa `hata` için uyarı simgesi ekle.
- [ ] **Step 4: Testlerin geçtiğini gör** → `4 passed`.
- [ ] **Step 5: Compose dosyasını güncelle ve yerelde doğrula.** `scripts/tarayici_testi.sh -k test_giris` çalışırken (çalıştırıcıya aynı gunicorn bayraklarını ekle) `docker logs arsa-e2e-app` çıktısında `POST /auth/login 302` biçiminde satır görünür ve satırda IP yoktur.
- [ ] **Step 6: Commit.** `git commit -m "İstek kaydı ve sunucu hatalarının yöneticiye bildirimi"`

---

### Task 5: Dosya yedeği ve geri yükleme denemesi (1.6)

**Files:**
- Create: `scripts/yedekle.sh` (sunucudaki `/opt/arsa-backups/yedekle.sh` depoya alınır ve genişletilir), `scripts/yedek_dogrula.sh`, `tests/test_yedek.sh`
- Modify: `README.md` (yedek ve geri yükleme bölümü)

**Interfaces:**
- `scripts/yedekle.sh` ortam değişkenleri: `YEDEK_DIZINI` (varsayılan `/opt/arsa-backups`), `SAKLAMA_GUN` (14), `PROJE` (compose proje adı, varsayılan `arsaanalizvesunum`), `DB_URL` (verilmezse `.env`'den okunur).
- Çıktılar: `supabase_arsa_YYYYMMDD_HHMM.sql.gz` (bugünkü davranış) ve `dosyalar_YYYYMMDD_HHMM.tar.gz` (`${PROJE}_uploads`, `${PROJE}_presentations`, `${PROJE}_is_belgeleri` birimleri; arşivde `uploads/`, `presentations/`, `is_belgeleri/` kök klasörleri).
- Her dosya önce `.tmp` olarak yazılır, doğrulanınca yeniden adlandırılır. Herhangi bir adım başarısızsa betik sıfırdan farklı kodla çıkar ve eski yedekleri silme adımına ulaşmaz.
- `scripts/yedek_dogrula.sh`: en yeni `.sql.gz`'yi geçici bir `postgres:17-alpine` kapsayıcısına yükler, `CREATE TABLE` sayısı ≥ 10 ve `users` satır sayısı ≥ 1 ise devam eder; en yeni `dosyalar_*.tar.gz` içindeki dosya sayısını birimlerdeki dosya sayısıyla karşılaştırır; sonucu tek satırda yazar (`YEDEK DOĞRULANDI: 31 tablo, 7 kullanıcı, 42 dosya`), uyuşmazlıkta sıfırdan farklı kodla çıkar.

- [ ] **Step 1: Başarısız testi yaz** (`tests/test_yedek.sh`; geçici dizin, geçici postgres kapsayıcısı ve `yedektest_` önekli geçici birimlerle çalışır, canlıya dokunmaz). Senaryolar: (a) normal çalıştırmada iki dosya oluşur ve tar içinde birime konan 3 dosya vardır; (b) `DB_URL` geçersizken çıkış kodu ≠ 0, `YEDEK_DIZINI`'nde `.tmp` kalmaz ve önceden konmuş 20 günlük eski yedek silinmemiştir; (c) birimlerden biri boşken betik başarılı olur ve arşivde o klasör boş olarak bulunur.
- [ ] **Step 2: Başarısız olduğunu gör** → `scripts/yedekle.sh: No such file`.
- [ ] **Step 3: `scripts/yedekle.sh`'yi yaz.** Birimler `docker run --rm -v <birim>:/v/<ad>:ro alpine tar czf - -C /v .` ile arşivlenir.
- [ ] **Step 4: Testin geçtiğini gör** → 3 senaryo `OK`.
- [ ] **Step 5: `scripts/yedek_dogrula.sh`'yi yaz ve test ortamında çalıştır** → `YEDEK DOĞRULANDI` satırı.
- [ ] **Step 6: README bölümünü yaz ve commit et.** `git commit -m "Yedek: yüklenen dosyalar dahil, geri yükleme doğrulaması"`
- [ ] **Step 7 (ofis sahibinin onayıyla, sunucuda):** crontab'daki `/opt/arsa-backups/yedekle.sh` satırını `/opt/arsaanalizvesunum/scripts/yedekle.sh` ile değiştir, bir kez elle çalıştır, `scripts/yedek_dogrula.sh` ile doğrula.

**Sunucu dışı kopya:** hedefi ofis sahibi seçer (ör. Google Drive, S3 uyumlu depo). Seçim yapılınca ayrı küçük bir görev olarak eklenir; bu görev onsuz da birleştirilebilir.

---

### Task 6: Günlük zaman aşımının teşhisi (1.5)

Bu bir araştırma görevidir; çıktısı kod değil, kanıta dayalı bir bulgu ve düzeltme önerisidir. Görev 4 canlıya alındıktan en az 3 gün sonra yapılır.

**Bilinenler:** `WORKER TIMEOUT` ve ardından `SIGKILL` 2026-11-08 14:12, 11-09 05:51 ve 11-10 06:46 UTC'de görüldü. gunicorn `--timeout 120 --workers 3 --preload`. Kapsayıcı belleği 260 MB / 3,8 GB, yani bellek değil. 05:00 UTC'deki hatırlatma cron'u saatlerle örtüşmüyor.

- [ ] **Step 1:** `docker logs arsaanalizvesunum-web-1 2>&1 | grep -n "WORKER TIMEOUT"` ile yeni olayları bul.
- [ ] **Step 2:** Her olay için, olaydan önceki 130 saniyede başlayıp bitiş satırı olmayan isteği bul (istek kaydı satırı ancak istek bitince yazılır; bu yüzden `app.py`'deki istek başlangıcı kaydına da bak, gerekirse başlangıç kaydını `yöntem yol` biçiminde WARNING seviyesinde geçici olarak aç).
- [ ] **Step 3:** Bulguyu `docs/superpowers/specs/` altına kısa bir notla yaz: hangi istek, neden uzun sürüyor (dış servis çağrısı, rapor üretimi, veritabanı bağlantısının kopması), önerilen düzeltme.
- [ ] **Step 4:** Düzeltmeyi ofis sahibine sun. Düzeltme ayrı bir sınırlı değişiklik olarak onaylanır ve yapılır.

3 gün içinde olay tekrarlanmazsa bunu not et ve görevi kapat.

---

### Task 7: Mobil denetim (1.2)

Ofis sahibinden bilgi gerektirir; Görev 1 ile aynı anda başlar.

- [ ] **Step 1:** Ofis sahibinden iPhone'da sorunlu her ekran için sayfa adı, belirti, tarayıcı (Safari/Chrome) ve ekran görüntüsü al.
- [ ] **Step 2:** Her sorunu `webkit-iphone` motorunda yeniden üretmeyi dene. Üretilebilen her sorun için `tests/tarayici/test_mobil.py`'ye önce başarısız olan bir test yaz (ör. öğe ekran genişliğini aşmıyor: `scrollWidth <= clientWidth`; düğme görünür ve tıklanabilir).
- [ ] **Step 3:** Düzelt, testin geçtiğini gör, sorun başına ayrı commit at.
- [ ] **Step 4:** WebKit'te üretilemeyen sorunları listele; bunlar yalnızca gerçek cihazda doğrulanabilir. Düzeltmeyi canlıya aldıktan sonra ofis sahibinden doğrulama iste.
- [ ] **Step 5:** `scripts/tarayici_testi.sh` tümüyle geçer; PR aç.

---

## Sıra ve bağımlılıklar

1 → 2 → 3 → 4 → 5 sırayla; 7, 1 ile aynı anda başlar; 6, 4 canlıya alındıktan 3 gün sonra. Görev 2, 5 ve 7 diğerlerinin arayüzlerine bağlı değildir.

## Aşama 1 bitti ölçütü

`scripts/tarayici_testi.sh` tüm akışlarda geçiyor ve ofis sahibi iPhone'da bir tam günlük işi sorunsuz yapabiliyor.

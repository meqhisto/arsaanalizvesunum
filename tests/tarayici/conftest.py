"""Tarayıcı testleri altyapısı. scripts/tarayici_testi.sh ile çalıştırılır."""
import os
import time
import urllib.request

import pytest
from PIL import Image
from playwright.sync_api import sync_playwright

BASE = os.environ.get('TARAYICI_URL', 'http://arsa-e2e-app:5000')
EPOSTA, SIFRE = 't@t.co', 'Abc12345!'
MOTORLAR = ['chromium', 'webkit-iphone']


@pytest.fixture(scope='session', autouse=True)
def _uygulama_hazir():
    son = None
    for _ in range(60):
        try:
            with urllib.request.urlopen(BASE + '/auth/login', timeout=3) as r:
                if r.status == 200:
                    return
        except Exception as e:  # uygulama henüz açılıyor
            son = e
        time.sleep(1)
    pytest.exit(f'Uygulama 60 sn içinde açılmadı: {son}')


@pytest.fixture(scope='session')
def _playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope='session')
def _tarayicilar(_playwright):
    acik = {'chromium': _playwright.chromium.launch(), 'webkit-iphone': _playwright.webkit.launch()}
    yield acik
    for t in acik.values():
        t.close()


@pytest.fixture(params=MOTORLAR)
def motor(request):
    return request.param


@pytest.fixture
def sayfa(motor, _playwright, _tarayicilar):
    """Giriş yapmış sayfa. `sayfa.post_istekleri`: testteki POST yolları. JS hatası testi başarısız sayar."""
    ayar = dict(_playwright.devices['iPhone 13']) if motor == 'webkit-iphone' else {}
    # Bootstrap, hareket azaltma kapalıyken sayfayı yumuşak kaydırır. Playwright tıklamadan önce öğeyi
    # görünür alana kaydırdığı için animasyon bitmeden basıp bırakıyor, bırakma düğmenin dışına düşüyor ve
    # tıklama kayboluyordu (iPhone profilinde 8 denemede 3). Kullanıcı sayfa dururken dokunur; testte
    # animasyon kapatılır.
    baglam = _tarayicilar[motor].new_context(reduced_motion='reduce', **ayar)
    pg = baglam.new_page()
    pg.set_default_timeout(20000)
    js_hatalari = []
    pg.on('pageerror', lambda e: js_hatalari.append(str(e)[:200]))
    pg.post_istekleri = []
    pg.on('request', lambda r: pg.post_istekleri.append(r.url.replace(BASE, '').split('?')[0]) if r.method == 'POST' else None)
    pg.goto(BASE + '/auth/login')
    pg.fill('input[name=email]', EPOSTA)
    pg.fill('input[name=password]', SIFRE)
    pg.click('button[type=submit]')
    pg.wait_for_load_state('networkidle')
    pg.post_istekleri.clear()
    yield pg
    baglam.close()
    assert not js_hatalari, f'Sayfada JavaScript hatası: {js_hatalari}'


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


@pytest.fixture(scope='session')
def fotograflar(tmp_path_factory):
    """Telefon fotoğrafı büyüklüğünde (4032x3024, ~10 MB) üç JPEG."""
    klasor = tmp_path_factory.mktemp('foto')
    yollar = []
    for i in range(3):
        yol = klasor / f'IMG_{i}.jpg'
        Image.effect_noise((4032, 3024), 80).convert('RGB').save(yol, quality=92)
        yollar.append(str(yol))
    return yollar

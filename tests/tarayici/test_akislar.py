"""Ana kullanıcı akışları: gerçek tarayıcıda, Chromium ve iPhone 13 profilli WebKit'te."""


def test_giris(sayfa):
    assert '/auth/login' not in sayfa.url
    assert sayfa.locator('text=Çıkış').count() >= 1


import re

from conftest import BASE, zorunlulari_doldur

DETAY_FOTO = 'img[src*="/uploads/1/"]'
YUKLE = 'form[action*="media_upload"] button[type=submit]'


def _hazir_bekle(sayfa, adet):
    sayfa.wait_for_function(
        "n => [...document.querySelectorAll('.foto-kucult-bilgi')].some(e => e.textContent.startsWith(n + ' dosya hazır'))",
        arg=str(adet), timeout=60000)


def test_detaydan_fotograf_yukle(sayfa, fotograflar):
    sayfa.goto(BASE + '/analysis/1')
    once = sayfa.locator(DETAY_FOTO).count()
    sayfa.locator('input[name=medya]').set_input_files(fotograflar)
    _hazir_bekle(sayfa, 3)
    sayfa.locator(YUKLE).click()
    sayfa.wait_for_selector('text=3 dosya yüklendi.')
    assert sayfa.post_istekleri == ['/analysis/1/media_upload']
    assert sayfa.locator(DETAY_FOTO).count() == once + 3


def test_kucultme_bitmeden_gonder(sayfa, fotograflar):
    sayfa.goto(BASE + '/analysis/1')
    sayfa.locator('input[name=medya]').set_input_files(fotograflar[:2])
    sayfa.locator(YUKLE).click()
    sayfa.wait_for_selector('text=2 dosya yüklendi.', timeout=60000)


def test_cift_tiklama_tek_istek(sayfa, fotograflar):
    sayfa.goto(BASE + '/analysis/1')
    sayfa.locator('input[name=medya]').set_input_files(fotograflar[:1])
    _hazir_bekle(sayfa, 1)
    sayfa.locator(YUKLE).dblclick()
    sayfa.wait_for_selector('text=1 dosya yüklendi.')
    assert len(sayfa.post_istekleri) == 1


def test_fotografli_gayrimenkul_olustur(sayfa, fotograflar):
    sayfa.goto(BASE + '/analysis/new')
    zorunlulari_doldur(sayfa, '#gayrimenkulForm')
    sayfa.locator('#medya').set_input_files(fotograflar[:1])
    _hazir_bekle(sayfa, 1)
    sayfa.locator('#gayrimenkulForm button[type=submit]').last.click()
    sayfa.wait_for_selector('text=Gayrimenkul kaydedildi.')
    assert re.search(r'/analysis/\d+$', sayfa.url)
    assert sayfa.locator('img[src*="/uploads/"]').count() == 1


def test_ilan_olustur(sayfa):
    # Gayrimenkul detayındaki "ilana çıkar" bağlantısının açtığı adres
    sayfa.goto(BASE + '/ilanlar/yeni?gayrimenkul=1')
    sayfa.locator('input[name="gayrimenkul_id[]"]').first.check()
    sayfa.locator('input[name=teklif_tipi][value=satilik]').check()
    sayfa.wait_for_timeout(300)
    sayfa.locator('#ilanForm input[name=fiyat]:visible').first.fill('1500000')
    zorunlulari_doldur(sayfa, '#ilanForm')
    sayfa.locator('#ilanForm button[type=submit]').last.click()
    sayfa.wait_for_url(re.compile(r'/ilanlar/\d+$'))


def test_musteri_ekle(sayfa, motor):
    ad = f'Tarayici{motor.replace("-", "")}'
    sayfa.goto(BASE + '/crm/contact/new')
    sayfa.fill('input[name=first_name]', ad)
    sayfa.fill('input[name=last_name]', 'Testoglu')
    sayfa.locator('form[method=POST] button[type=submit]').first.click()
    sayfa.wait_for_url(lambda adres: not adres.endswith('/crm/contact/new'))  # kayıt bitip yönlendirme gelsin
    sayfa.goto(BASE + '/crm/contacts')
    sayfa.wait_for_selector(f'text={ad}')  # liste sayfa açıldıktan sonra doluyor


def test_is_belgesi_yukle(sayfa, fotograflar, tmp_path):
    pdf = tmp_path / 'tapu.pdf'
    pdf.write_bytes(b'%PDF-1.4 test')
    sayfa.goto(BASE + '/isler/1?sekme=belgeler')
    sayfa.locator('#dosya').set_input_files([str(pdf), fotograflar[0]])
    sayfa.locator('form[action*="belge/yukle"] button').click()
    sayfa.wait_for_selector('text=2 belge yüklendi.')


def test_profil_fotografi(sayfa, fotograflar):
    sayfa.goto(BASE + '/profile')
    sayfa.locator('input[name=profil_foto]').set_input_files(fotograflar[0])
    _hazir_bekle(sayfa, 1)
    sayfa.locator('form[enctype="multipart/form-data"] button[type=submit]').first.click()
    sayfa.wait_for_selector('text=Profil başarıyla güncellendi!')
    assert sayfa.locator('img[src*="/uploads/profiles/"]').count() >= 1


def test_ofis_logosu(sayfa, motor, tmp_path):
    from PIL import Image
    logo = tmp_path / 'logo.png'
    Image.new('RGBA', (600, 200), (0, 90, 200, 120)).save(logo)
    sayfa.goto(BASE + '/admin/office/create')
    sayfa.fill('#name', f'Ofis {motor}')
    sayfa.locator('#logo_path').set_input_files(str(logo))
    sayfa.locator('form[enctype="multipart/form-data"] button[type=submit]').first.click()
    sayfa.wait_for_selector('text=başarıyla oluşturuldu')


def test_rapor_indir(sayfa):
    yanit = sayfa.request.get(BASE + '/analysis/report/generate/pdf/1')
    assert yanit.status == 200
    assert yanit.body()[:4] == b'%PDF'


def test_crm_iceri_aktar(sayfa, tmp_path):
    csv = tmp_path / 'kisiler.csv'
    csv.write_text('Ad,Soyad,Email\n' + ''.join(f'Ad{i},Soyad{i},k{i}@ornek.com\n' for i in range(100)), encoding='utf-8')
    sayfa.goto(BASE + '/crm/import')
    sayfa.locator('#file-input').set_input_files(str(csv))
    sayfa.locator('#upload-btn').click()
    sayfa.wait_for_selector('#step-content-2', state='visible')
    assert '100' in sayfa.locator('#preview-info').inner_text()


def test_sonradan_eklenen_form_token_alir(sayfa):
    sayfa.goto(BASE + '/profile')
    sayfa.evaluate("""() => { const f = document.createElement('form'); f.method = 'post'; f.action = '/profile';
        f.innerHTML = '<input name="ad" value="Dinamik"><input name="soyad" value="T"><input name="timezone" value="UTC"><button>g</button>';
        document.body.appendChild(f); f.querySelector('button').click(); }""")
    sayfa.wait_for_selector('text=Profil başarıyla güncellendi!')


def test_bayat_token_uyari_verir(sayfa):
    sayfa.goto(BASE + '/profile')
    sayfa.evaluate("document.querySelector('meta[name=csrf-token]').content = 'gecersiz'")
    sayfa.locator('form[enctype="multipart/form-data"] button[type=submit]').first.click()
    sayfa.wait_for_selector('text=Sayfayı yenileyip tekrar deneyin')
    assert '/profile' in sayfa.url

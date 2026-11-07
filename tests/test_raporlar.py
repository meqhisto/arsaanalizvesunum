"""İlan tabanlı raporlar: PDF, Word, PowerPoint (spec §6)."""
import io
import re
from datetime import datetime

import pytest
from docx import Document
from pptx import Presentation

from models import db
from models.arsa_models import ArsaAnaliz
from models.crm_models import Contact
from models.ilan_models import GayrimenkulSahibi, Ilan, IlanEmsal, IlanGayrimenkul
from models.user_models import User
from conftest import giris

MIME = {
    'pdf': 'application/pdf',
    'word': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}
UZANTI = {'pdf': 'pdf', 'word': 'docx', 'pptx': 'pptx'}


def istemci(app, user_id):
    return giris(app.test_client(), user_id)


def gayrimenkul(user_id, **kw):
    v = dict(user_id=user_id, il='Çanakkale', ilce='Merkez', mahalle='Kepez', fiyat=0)
    v.update(kw)
    g = ArsaAnaliz(**v)
    db.session.add(g)
    db.session.commit()
    return g


def arsa(user_id, parsel='2', metrekare=800, kaks=1.5, **kw):
    return gayrimenkul(user_id, ada='213', parsel=parsel, metrekare=metrekare, kaks=kaks, taks=0.3,
                       imar_durumu='Konut', tur='arsa', altyapi=['yol', 'elektrik'], **kw)


def ilan(gler, kod='ILN-2026-0001', teklif_tipi='satilik', emsaller=(), **kw):
    user_id = gler[0].user_id
    i = Ilan(kod=kod, baslik=kw.pop('baslik', kod), user_id=user_id, sorumlu_user_id=user_id,
             teklif_tipi=teklif_tipi, durum=kw.pop('durum', 'pazarlamada'), **kw)
    for sira, g in enumerate(gler, start=1):
        i.baglar.append(IlanGayrimenkul(gayrimenkul=g, ana_kayit=(sira == 1), sira=sira))
    for e in emsaller:
        i.emsaller.append(IlanEmsal(**e))
    db.session.add(i)
    db.session.commit()
    return i


def sahip_ekle(gler, user_id):
    hasan = Contact(user_id=user_id, first_name='Hasan', last_name='Yılmazoğlu', phone='05551112233',
                    email='hasan@sahip.com')
    db.session.add(hasan)
    db.session.commit()
    for g in gler:
        db.session.add(GayrimenkulSahibi(gayrimenkul_id=g.id, contact_id=hasan.id, hisse='1/2', irtibat=True))
    db.session.commit()
    return hasan


def kur_satilik_daire(br):
    d = gayrimenkul(br, mahalle='Barbaros', tur='konut', alt_tur='daire', metrekare=120, brut_m2=120, net_m2=105,
                    oda_sayisi='3+1', bulundugu_kat='4', toplam_kat=6, bina_yasi=5, isinma='Kombi (doğalgaz)',
                    balkon=True, ozellikler={'ic': ['Asansör', 'Çelik kapı'], 'dis': ['Otopark']},
                    swot_analizi={'strengths': ['Merkezi konum']})
    sahip_ekle([d], br)
    i = ilan([d], fiyat=4_250_000, emsaller=[
        {'konum': 'Barbaros 1', 'm2': 100, 'fiyat': 3_000_000},
        {'konum': 'Barbaros 2', 'm2': 140, 'fiyat': 4_900_000}])
    return f'/ilanlar/{i.id}/rapor', i


def kur_kiralik_dukkan(br):
    d = gayrimenkul(br, tur='isyeri', alt_tur='dukkan', metrekare=80, brut_m2=80)
    i = ilan([d], teklif_tipi='kiralik', kira=25_000, depozito=50_000, bolge_m2_fiyat_elle=250)
    return f'/ilanlar/{i.id}/rapor', i


def kur_kat_karsiligi(br):
    gler = [arsa(br, parsel=str(p), metrekare=m2) for p, m2 in ((2, 800), (3, 750), (4, 900), (5, 750))]
    sahip_ekle(gler, br)
    i = ilan(gler, teklif_tipi='kat_karsiligi', sahip_payi_yuzde=50, ek_nakit=2_000_000, teslim_suresi_ay=24,
             teminat_turu='Banka teminat mektubu', teminat_tutari=5_000_000, tevhid_durumu='yapilacak',
             emsaller=[{'konum': 'Kepez A', 'pay_yuzde': 40}, {'konum': 'Kepez B', 'pay_yuzde': 50}])
    return f'/ilanlar/{i.id}/rapor', i


def kur_tanitim_arsa(br):
    g = arsa(br)
    sahip_ekle([g], br)
    return f'/analysis/{g.id}/report', g


SENARYOLAR = {'satilik_daire': kur_satilik_daire, 'kiralik_dukkan': kur_kiralik_dukkan,
              'kat_karsiligi_4_parsel': kur_kat_karsiligi, 'tanitim_arsa': kur_tanitim_arsa}


def indir(app, user_id, url):
    r = istemci(app, user_id).get(url)
    assert r.status_code == 200, (r.status_code, r.headers.get('Location'))
    return r


def docx_metni(data):
    doc = Document(io.BytesIO(data))
    parcalar = [p.text for p in doc.paragraphs]

    def tablolar(tables):
        for t in tables:
            for row in t.rows:
                for cell in row.cells:
                    parcalar.extend(p.text for p in cell.paragraphs)
                    tablolar(cell.tables)
    tablolar(doc.tables)
    for sec in doc.sections:
        parcalar.extend(p.text for p in sec.header.paragraphs)
        parcalar.extend(p.text for p in sec.footer.paragraphs)
    return '\n'.join(parcalar)


def pdf_metni(data):
    pypdf = pytest.importorskip('pypdf', reason='PDF metin çıkarma için pypdf gerekli (requirements-dev.txt)')
    return '\n'.join(page.extract_text() or '' for page in pypdf.PdfReader(io.BytesIO(data)).pages)


def pptx_metni(data):
    prs = Presentation(io.BytesIO(data))
    parcalar = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                parcalar.append(shape.text_frame.text)
            if getattr(shape, 'has_table', False) and shape.has_table:
                for row in shape.table.rows:
                    parcalar.extend(c.text for c in row.cells)
    return '\n'.join(parcalar)


# ---------------------------------------------------------------- üretim

@pytest.mark.parametrize('fmt', ['pdf', 'word', 'pptx'])
@pytest.mark.parametrize('senaryo', list(SENARYOLAR))
def test_rapor_uretilir(app, kullanicilar, fmt, senaryo):
    yol, _ = SENARYOLAR[senaryo](kullanicilar['broker'])
    r = indir(app, kullanicilar['broker'], f'{yol}/{fmt}')
    assert r.headers['Content-Type'] == MIME[fmt]
    assert len(r.data) > 10 * 1024
    assert r.headers['Content-Disposition'].endswith(f'.{UZANTI[fmt]}"')


def test_rapor_dosya_adlari(app, kullanicilar):
    br = kullanicilar['broker']
    yol, i = kur_satilik_daire(br)
    bugun = datetime.now().strftime('%Y%m%d')
    r = indir(app, br, f'{yol}/word')
    assert f'filename="ilan_{i.kod}_{bugun}.docx"' in r.headers['Content-Disposition']
    g = arsa(br, parsel='9')
    r = indir(app, br, f'/analysis/{g.id}/report/pdf')
    assert f'filename="tanitim_Canakkale_Merkez_{g.id}_{bugun}.pdf"' in r.headers['Content-Disposition']


def test_rapor_metni_kat_karsiligi(app, kullanicilar):
    yol, _ = kur_kat_karsiligi(kullanicilar['broker'])
    metin = docx_metni(indir(app, kullanicilar['broker'], f'{yol}/word').data)
    for parca in ('Kat Karşılığı Teklif Raporu', '%50', '2.400', '213', 'Parseller', 'Fiyat ve Emsal Analizi',
                  '3.200', '4.800', 'Banka teminat mektubu', '2.000.000 TL', 'Yapılacak', 'Kepez A',
                  'Parsellerin tevhidi', 'Talep edilen pay bölge emsallerinin üzerinde'):
        assert parca in metin, parca
    kucuk = metin.lower()
    assert 'senaryo' not in kucuk and 'değer artışı' not in kucuk and 'projeksiyon' not in kucuk


def test_rapor_metni_satilik(app, kullanicilar):
    yol, _ = kur_satilik_daire(kullanicilar['broker'])
    metin = docx_metni(indir(app, kullanicilar['broker'], f'{yol}/word').data)
    for parca in ('Satılık Daire Sunum Raporu', 'İstenen fiyat', '4.250.000 TL', 'm² fiyatı', '35.417 TL',
                  'Bölge ortalaması', '2 emsal', 'Barbaros 2', 'Oda sayısı', '3+1', 'İç özellikler', 'Asansör',
                  'Fiyat ve Emsal Analizi'):
        assert parca in metin, parca
    assert 'Parseller' not in metin and '₺' not in metin
    pptx = pptx_metni(indir(app, kullanicilar['broker'], f'{yol}/pptx').data)
    for parca in ('Satılık Daire Sunum Raporu', 'Fiyat ve Emsal Analizi', '4.250.000 TL', 'Barbaros 2'):
        assert parca in pptx, parca


def test_rapor_metni_kiralik(app, kullanicilar):
    yol, _ = kur_kiralik_dukkan(kullanicilar['broker'])
    metin = docx_metni(indir(app, kullanicilar['broker'], f'{yol}/word').data)
    for parca in ('Kiralık Dükkân Sunum Raporu', 'Aylık kira', '25.000 TL', 'Depozito', '50.000 TL', 'm² kira',
                  'elle girildi'):
        assert parca in metin, parca


def test_tanitim_raporu_fiyatsiz(app, kullanicilar):
    yol, _ = kur_tanitim_arsa(kullanicilar['broker'])
    metin = docx_metni(indir(app, kullanicilar['broker'], f'{yol}/word').data)
    assert 'Arsa Tanıtım Raporu' in metin and 'TAKS' in metin and 'Uygunluk puanı' in metin
    assert 'Fiyat ve Emsal Analizi' not in metin and 'İstenen fiyat' not in metin
    pptx = pptx_metni(indir(app, kullanicilar['broker'], f'{yol}/pptx').data)
    assert 'Arsa Tanıtım Raporu' in pptx and 'Fiyat ve Emsal Analizi' not in pptx


@pytest.mark.parametrize('senaryo', ['satilik_daire', 'kat_karsiligi_4_parsel', 'tanitim_arsa'])
def test_rapor_mal_sahibi_icermez(app, kullanicilar, senaryo):
    yol, _ = SENARYOLAR[senaryo](kullanicilar['broker'])
    for fmt, cikar in (('word', docx_metni), ('pptx', pptx_metni), ('pdf', pdf_metni)):
        metin = cikar(indir(app, kullanicilar['broker'], f'{yol}/{fmt}').data)
        for yasak in ('Hasan', 'Yılmazoğlu', '05551112233', '555 111', 'hasan@sahip.com'):
            assert yasak not in metin, (fmt, yasak)


# ---------------------------------------------------------------- model / görseller

def test_rapor_emsal_yoksa_grafik_yok(app, kullanicilar, tmp_path):
    from modules.rapor import build_assets, build_report_model
    br = kullanicilar['broker']
    d = gayrimenkul(br, tur='konut', alt_tur='daire', metrekare=120, brut_m2=120)
    i = ilan([d], fiyat=4_000_000)
    user = db.session.get(User, br)
    m = build_report_model(i, i.ana_gayrimenkul, user)
    assert m.bolge is None and m.fark is None and m.bolge_kaynak == 'yok'
    assets = build_assets(m, str(tmp_path))
    assert 'price_chart' not in assets


def test_rapor_modeli_kat_karsiligi(app, kullanicilar, tmp_path):
    from modules.rapor import build_assets, build_report_model
    br = kullanicilar['broker']
    _, i = kur_kat_karsiligi(br)
    m = build_report_model(i, i.ana_gayrimenkul, db.session.get(User, br))
    assert m.teklif_tipi == 'kat_karsiligi' and m.kod == i.kod and m.baslik == 'Kat Karşılığı Teklif Raporu'
    assert [p['parsel'] for p in m.parseller] == ['2', '3', '4', '5']
    assert set(m.parseller[0]) >= {'baslik', 'ada', 'parsel', 'm2', 'imar', 'kaks'}
    satirlar = dict(m.fiyat_satirlari)
    assert satirlar['Arsa sahibi payı'] == '%50' and satirlar['Arsa sahibine düşen (tahmini)'] == '2.400 m²'
    assert satirlar['Toplam arsa alanı'] == '3.200 m²' and satirlar['Tevhid'] == 'Yapılacak'
    assert m.bolge == pytest.approx(45) and m.konum_etiketi == 'Talep bölge ortalamasının üstünde'
    assert m.puan == 0 and not m.puan_detay  # çok parselde puan yok
    assert 'price_chart' in build_assets(m, str(tmp_path))
    assert re.search(r'4 parsel, toplam 3\.200 m² arsa için arsa sahibi %50 pay talep ediyor', m.fiyat_ozet)


def test_rapor_modeli_tanitim(app, kullanicilar):
    from modules.rapor import build_report_model
    br = kullanicilar['broker']
    g = arsa(br)
    m = build_report_model(None, g, db.session.get(User, br))
    assert m.teklif_tipi is None and m.analiz_id == g.id and m.baslik == 'Arsa Tanıtım Raporu'
    assert m.fiyat_satirlari == [] and m.emsaller == [] and m.bolge is None
    assert m.puan > 0 and m.puan_detay
    for alan in ('yillik_artis', 'senaryolar', 'yatirim_ozet', 'artis_kaynagi'):
        assert not hasattr(m, alan)


# ---------------------------------------------------------------- rotalar ve erişim

def test_gayrimenkul_raporu_aktif_ilana_yonlenir(app, kullanicilar):
    br = kullanicilar['broker']
    _, i = kur_satilik_daire(br)
    g = i.ana_gayrimenkul
    c = istemci(app, br)
    r = c.get(f'/analysis/{g.id}/report/pdf')
    assert r.status_code == 302 and r.headers['Location'].endswith(f'/ilanlar/{i.id}/rapor/pdf')
    r = c.get(f'/analysis/report/generate/word/{g.id}')
    assert r.status_code == 302 and r.headers['Location'].endswith(f'/ilanlar/{i.id}/rapor/word')
    r = c.post(f'/analysis/report/generate_pptx/{g.id}', data={'color_scheme': 'blue'})
    assert r.status_code == 302 and r.headers['Location'].endswith(f'/ilanlar/{i.id}/rapor/pptx')


def test_pasif_ilanli_gayrimenkul_tanitim_raporu_verir(app, kullanicilar):
    br = kullanicilar['broker']
    d = gayrimenkul(br, tur='konut', alt_tur='daire', metrekare=120)
    ilan([d], fiyat=1_000_000, durum='geri_cekildi')
    r = indir(app, br, f'/analysis/{d.id}/report/word')
    assert 'Daire Tanıtım Raporu' in docx_metni(r.data)


def test_rapor_erisim(app, kullanicilar):
    k = kullanicilar
    g = arsa(k['d1'])
    i = ilan([g], fiyat=3_000_000, durum='hazirlaniyor')
    # ekibin broker'ı ve superadmin indirebilir; ofis dışı danışman göremez
    for uid in (k['d1'], k['broker'], k['sa']):
        indir(app, uid, f'/ilanlar/{i.id}/rapor/pdf')
        indir(app, uid, f'/analysis/{g.id}/report/word')
    assert istemci(app, k['dx']).get(f'/ilanlar/{i.id}/rapor/pdf').status_code == 404
    assert istemci(app, k['dx']).get(f'/analysis/{g.id}/report/pdf').status_code == 404
    assert istemci(app, k['dx']).post(f'/analysis/report/generate_pptx/{g.id}').status_code == 404
    assert istemci(app, k['dx']).get(f'/analysis/{g.id}/share').status_code == 404
    assert istemci(app, k['broker']).get(f'/analysis/{g.id}/share').status_code == 200
    assert istemci(app, k['d1']).get(f'/ilanlar/{i.id}/rapor/xls').status_code == 404


def test_rapor_butonlari(app, kullanicilar):
    k = kullanicilar
    g = arsa(k['d1'])
    i = ilan([g], fiyat=3_000_000)
    sayfa = istemci(app, k['broker']).get(f'/analysis/{g.id}').get_data(as_text=True)
    assert f'/analysis/{g.id}/report/pdf' in sayfa and f'/analysis/report/generate_pptx/{g.id}' in sayfa
    sayfa = istemci(app, k['broker']).get(f'/ilanlar/{i.id}').get_data(as_text=True)
    for fmt in ('pdf', 'word', 'pptx'):
        assert f'/ilanlar/{i.id}/rapor/{fmt}' in sayfa


def test_pdf_metni_okunur(app, kullanicilar):
    """PDF metin çıkarma gerçekten çalışıyor (mal sahibi kontrolü boşuna geçmesin)."""
    yol, _ = kur_kat_karsiligi(kullanicilar['broker'])
    metin = pdf_metni(indir(app, kullanicilar['broker'], f'{yol}/pdf').data)
    assert 'Kat Karşılığı Teklif Raporu' in metin and '2.400' in metin


def test_tanitim_raporu_ic_notlari_icermez(app, kullanicilar):
    br = kullanicilar['broker']
    g = arsa(br, notlar='Sahibi Hasan Yılmazoğlu, tel 05551112233; acele satmak istiyor')
    for fmt, cikar in (('word', docx_metni), ('pptx', pptx_metni), ('pdf', pdf_metni)):
        metin = cikar(indir(app, br, f'/analysis/{g.id}/report/{fmt}').data)
        assert 'Arsa Tanıtım Raporu' in metin
        for yasak in ('Hasan', 'Yılmazoğlu', '05551112233', 'acele', 'Danışman notu'):
            assert yasak not in metin, (fmt, yasak)


@pytest.mark.parametrize('fiyat, etiket, tavsiye', [
    (1_070_000, 'Bölgenin üstünde', 'Fiyat bölge ortalamasının üzerinde; pazarlık payı değerlendirilmeli.'),
    (1_030_000, 'Piyasa seviyesinde', 'Fiyat piyasa seviyesinde, bölge ortalamasına yakın'),
    (970_000, 'Piyasa seviyesinde', 'Fiyat piyasa seviyesinde, bölge ortalamasına yakın'),
    (930_000, 'Bölgeye göre uygun', 'Fiyat bölge ortalamasının altında; bölgeye göre uygun'),
    (1_150_000, 'Bölgenin üstünde', 'Fiyat bölge ortalamasının belirgin şekilde üzerinde'),
    (850_000, 'Bölgeye göre uygun', 'Fiyat bölge ortalamasının belirgin şekilde altında'),
])
def test_fiyat_tavsiyesi_konumlandirmayla_tutarli(app, kullanicilar, fiyat, etiket, tavsiye):
    from modules.rapor import build_report_model
    br = kullanicilar['broker']
    d = gayrimenkul(br, tur='konut', alt_tur='daire', metrekare=100, brut_m2=100)
    i = ilan([d], fiyat=fiyat, emsaller=[{'konum': 'E', 'm2': 100, 'fiyat': 1_000_000}])
    m = build_report_model(i, d, db.session.get(User, br))
    assert m.konum_etiketi == etiket
    fiyat_tavsiyeleri = [t for t in m.tavsiyeler if t.startswith('Fiyat')]
    assert len(fiyat_tavsiyeleri) == 1 and fiyat_tavsiyeleri[0].startswith(tavsiye), fiyat_tavsiyeleri


def test_kat_karsiligi_kaks_eksik_uyarisi(app, kullanicilar):
    br = kullanicilar['broker']
    gler = [arsa(br, parsel='2', metrekare=800), arsa(br, parsel='3', metrekare=750, kaks=None),
            arsa(br, parsel='4', metrekare=900)]
    i = ilan(gler, teklif_tipi='kat_karsiligi', sahip_payi_yuzde=50)
    metin = docx_metni(indir(app, br, f'/ilanlar/{i.id}/rapor/word').data)
    assert '2.550 m² (KAKS bilgisi eksik 1 parsel hesaba katılmadı)' in metin  # (800+900)*1,5
    assert '1.275 m² (KAKS bilgisi eksik 1 parsel hesaba katılmadı)' in metin
    pptx = pptx_metni(indir(app, br, f'/ilanlar/{i.id}/rapor/pptx').data)
    assert 'KAKS bilgisi eksik 1 parsel hesaba katılmadı' in pptx


def test_kat_karsiligi_kaks_hic_yok(app, kullanicilar):
    br = kullanicilar['broker']
    gler = [arsa(br, parsel='2', kaks=None), arsa(br, parsel='3', kaks=None)]
    i = ilan(gler, teklif_tipi='kat_karsiligi', sahip_payi_yuzde=None)
    from modules.rapor import build_report_model
    m = build_report_model(i, gler[0], db.session.get(User, br))
    satir = dict(m.fiyat_satirlari)
    assert satir['İnşaat hakkı (tahmini)'] == 'Hesaplanamadı (KAKS bilgisi yok)'
    assert satir['Arsa sahibine düşen (tahmini)'] == 'Hesaplanamadı (KAKS bilgisi yok)'
    assert 'hesaplanamadı' in m.fiyat_ozet and '%-' not in m.fiyat_ozet and '2 parsel' in m.fiyat_ozet
    metin = docx_metni(indir(app, br, f'/ilanlar/{i.id}/rapor/word').data)
    assert 'Hesaplanamadı (KAKS bilgisi yok)' in metin and '%-' not in metin


def test_aktif_ilani_gormeyen_tanitim_raporu_alir(app, kullanicilar):
    """d1 kendi gayrimenkulünü görür; broker'ın açtığı (sorumlusu broker) aktif ilanı göremez."""
    k = kullanicilar
    g = arsa(k['d1'])
    i = Ilan(kod='ILN-2026-0099', baslik='Broker ilanı', user_id=k['broker'], sorumlu_user_id=k['broker'],
             teklif_tipi='satilik', durum='pazarlamada', fiyat=5_000_000)
    i.baglar.append(IlanGayrimenkul(gayrimenkul=g, ana_kayit=True, sira=1))
    db.session.add(i)
    db.session.commit()
    c = istemci(app, k['d1'])
    assert c.get(f'/ilanlar/{i.id}').status_code == 404
    r = c.get(f'/analysis/{g.id}/report/word')
    assert r.status_code == 200
    metin = docx_metni(r.data)
    assert 'Arsa Tanıtım Raporu' in metin and '5.000.000' not in metin
    r = istemci(app, k['d1']).post(f'/analysis/report/generate_pptx/{g.id}')
    assert r.status_code == 200 and 'tanitim_' in r.headers['Content-Disposition']

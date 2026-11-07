# Gayrimenkul, İlan ve Mal Sahibi Yeniden Tasarımı

Tarih: 2026-11-06 · Durum: Onaylandı (tasarım), uygulama planı bekleniyor

## 1. Amaç

Program bir emlak ofisinin portföy ve pazarlama aracıdır. Bugünkü "Arsa Analiz Formu" yatırımcı
gözüyle yazılmış (maliyet, alım tarihi, değer artışı, elde tutma süresi). Ofisi ilgilendiren ise
mal sahibinin **kaça satmak / kiralamak / kat karşılığı vermek istediği** ve **bölge emsalleri**dir.

Hedefler:

- Yatırımcı alanlarını kaldırmak; istenen fiyat ve emsal karşılaştırmasını öne çıkarmak.
- Arsa dışındaki tüm gayrimenkul türlerini (konut, işyeri, tarla, bina) sahibinden.com düzeyinde
  detayla desteklemek.
- Satılık, Kiralık ve **Kat karşılığı** teklif tiplerini desteklemek.
- Aynı mal sahibinin birden fazla gayrimenkulünü **tek teklif** olarak pazarlayabilmek
  (ör. 213 ada 2-3-4-5 parsellerin birlikte kat karşılığı verilmesi).
- Gayrimenkulleri CRM müşterilerine (mal sahiplerine, hisseli olarak) ve CRM fırsatlarına bağlamak.

Başarı ölçütü: Bir danışman, CRM'deki mal sahibini seçip onun dört parselini tek bir kat karşılığı
ilanında toplayabilmeli, pay oranını ve şartları girebilmeli, emsal oranlarla karşılaştırmayı
görebilmeli ve bunu müşteriye PDF/Word/PowerPoint rapor olarak sunabilmeli. Mevcut kayıtlar
bozulmadan yeni yapıya geçmeli.

Kapsam dışı: ilan sitelerine otomatik yayın, emsallerin internetten otomatik çekilmesi.

## 2. Kavramlar

| Kavram | Ne tutar |
|---|---|
| **Gayrimenkul** | Fiziksel varlık: tür, konum, ada/parsel, m², imar, türe özel alanlar, özellikler, SWOT, fotoğraflar, sahipler |
| **Sahiplik** | Gayrimenkul ↔ CRM müşterisi (çoktan çoğa), hisse oranı, irtibat/yetki veren işareti |
| **İlan** | Pazarlama teklifi: bir veya daha çok gayrimenkul, teklif tipi, fiyat/şartlar, emsaller, durum, sorumlu danışman |
| **Emsal** | İlana bağlı karşılaştırma kaydı (m² fiyatı veya kat karşılığı pay oranı) |
| **Portföy** | Mevcut koleksiyon özelliği; artık ilanlardan oluşur, müşteriye toplu sunum için |

## 3. Veri modeli

Tablolar `db.create_all()` ile, mevcut tablolara eklenen sütunlar `ADD COLUMN IF NOT EXISTS` ile
başlangıçta idempotent olarak oluşturulur (`modules/is_takip_kurulum.py` deseni). Alembic kullanılmaz.

### 3.1 `arsa_analizleri` (Gayrimenkul) — genişletilir

Tablo adı ve `ArsaAnaliz` sınıfı korunur (raporlar, medya, API bağımlı). Yeni sütunlar:

- `tur` (varchar 20, varsayılan `arsa`): `arsa`, `tarla`, `konut`, `isyeri`, `bina`
- `alt_tur` (varchar 30): konut → `daire`/`villa`/`mustakil`/`rezidans`; işyeri → `dukkan`/`ofis`/`depo`/`fabrika`
- `baslik` (varchar 200, boş olabilir; boşsa konumdan üretilir)
- Konut/işyeri/bina ortak: `brut_m2`, `net_m2` (Numeric 10,2), `oda_sayisi` (varchar 10, ör. "3+1"),
  `banyo_sayisi`, `bulundugu_kat` (varchar 10, "Bahçe", "Zemin", "5"), `toplam_kat`, `bina_yasi` (int),
  `isinma` (varchar 30), `esyali`, `site_icinde`, `balkon` (bool), `aidat` (Numeric 10,2)
- Ortak: `tapu_durumu` (varchar 30: kat mülkiyeti, kat irtifakı, hisseli tapu, müstakil tapu, arsa tapusu),
  `krediye_uygun`, `takasli` (bool), `kimden` (varchar 20: sahibinden, emlak ofisinden)
- `ozellikler` (JSON): `{ "ic": [...], "dis": [...], "muhit": [...], "ulasim": [...], "cephe": [...], "altyapi": [...] }`
- Arsa/tarla alanları (`ada`, `parsel`, `pafta`, `imar_durumu`, `taks`, `kaks`) aynen kalır.
- `metrekare` arsa/tarla için arsa alanı, diğer türlerde brüt m² ile doldurulur (raporlar ve
  istatistikler tek alana bakabilsin diye). `nullable=False` korunur.
- `il`, `ilce`, `mahalle` zorunlu kalır; `ada`/`parsel` yalnız arsa/tarla için zorunlu.

Formdan ve ekranlardan kaldırılanlar (sütunlar veri kaybı olmasın diye **silinmez**):
`deger_artis_orani`, alım tarihi, güncel değer, risk değerlendirmesi, elde tutma süresi, uzun vadeli strateji.
`fiyat` ve `bolge_fiyat` gayrimenkulde artık düzenlenmez; geçişte ilana taşınır, eski kodun kırılmaması
için okunabilir kalır.

### 3.2 `gayrimenkul_sahipleri` — yeni

`id`, `gayrimenkul_id` → arsa_analizleri, `contact_id` → crm_contacts, `hisse` (varchar 20, ör. "1/2", boş olabilir),
`irtibat` (bool), `created_at`. Benzersiz: (`gayrimenkul_id`, `contact_id`).

### 3.3 `ilanlar` — yeni

- `id`, `kod` (`ILN-YYYY-NNNN`, benzersiz), `baslik`, `aciklama`
- `user_id` (oluşturan), `sorumlu_user_id`, `office_id`
- `teklif_tipi`: `satilik`, `kiralik`, `kat_karsiligi`
- `durum`: `hazirlaniyor`, `pazarlamada`, `opsiyonlu`, `anlasildi`, `geri_cekildi`
- Satılık: `fiyat` (Numeric 15,2)
- Kiralık: `kira` (Numeric 12,2), `depozito` (Numeric 12,2)
- Kat karşılığı: `sahip_payi_yuzde` (Numeric 5,2), `ek_nakit` (Numeric 15,2), `teslim_suresi_ay` (int),
  `teminat_turu` (varchar 40), `teminat_tutari` (Numeric 15,2), `tevhid_durumu` (`yapildi`/`yapilacak`/`gerekmiyor`),
  `insaat_alani_elle` (Numeric 12,2, boşsa hesaplanır), `daire_tercihi_notu` (Text)
- `bolge_m2_fiyat_elle` (Numeric 15,2) — emsal yoksa kullanılan elle girilmiş bölge m² fiyatı
- `bolge_pay_yuzde_elle` (Numeric 5,2) — kat karşılığında emsal yoksa elle bölge pay oranı
- `created_at`, `updated_at`

### 3.4 `ilan_gayrimenkulleri` — yeni

`ilan_id`, `gayrimenkul_id` (birleşik birincil anahtar), `ana_kayit` (bool), `parsel_fiyati` (Numeric 15,2, isteğe bağlı), `sira`.

### 3.5 `ilan_emsalleri` — yeni

`id`, `ilan_id`, `konum` (varchar 200), `m2` (Numeric 10,2), `fiyat` (Numeric 15,2; satılık/kiralık),
`pay_yuzde` (Numeric 5,2; kat karşılığı), `link` (varchar 500), `notlar` (Text), `created_at`.

### 3.6 Mevcut tablolara eklemeler

- `crm_deals.ilan_id` → ilanlar (nullable)
- `portfolio_ilanlar` (portfolio_id, ilan_id, added_at) — portföyler ilan içerir. `portfolio_arsalar`
  geçiş sonrası okunur ama yeni bağlantı oluşturulmaz.

## 4. İş kuralları ve hesaplar (`modules/ilan_servis.py`)

Saf fonksiyonlar halinde, birim testli:

- `toplam_m2(ilan)` = ilandaki gayrimenkullerin `metrekare` toplamı
- `insaat_hakki(ilan)` = Σ (`metrekare` × `kaks`), KAKS'ı olmayan parsel atlanır ve uyarı döner;
  `insaat_alani_elle` doluysa o kullanılır
- `sahibe_dusen_m2(ilan)` = insaat_hakki × sahip_payi_yuzde / 100
- `istenen_m2_fiyati(ilan)` = fiyat (veya kira) / toplam_m2
- `bolge_ortalamasi(ilan)`: emsal varsa satılık/kiralıkta Σfiyat/Σm2 (m² ağırlıklı), kat karşılığında
  pay_yuzde ortalaması; emsal yoksa ilgili `_elle` alanı; ikisi de yoksa `None`
- `fark_yuzde(ilan)` = (istenen − bölge) / bölge × 100
- `konumlandirma(fark)`: < −5 → "Bölgeye göre uygun", −5…+5 → "Piyasa seviyesinde", > +5 → "Bölgenin üstünde".
  Kat karşılığında yön terstir (yüksek pay, müteahhit için daha az cazip): etiketler buna göre.
- **Çakışma kuralı:** Bir gayrimenkul aynı anda yalnız bir ilanda `durum ∈ {pazarlamada, opsiyonlu}` olabilir.
  İhlalde kayıt reddedilir ve çakışan ilan kodu ile mesaj gösterilir.
- **Ana kayıt:** her ilanda tam bir ana kayıt; belirtilmezse ilk eklenen.
- **Görünürlük/yetki:** ilanlar ve gayrimenkuller mevcut analiz görünürlüğünü izler (sahibi, broker için ekibi,
  superadmin hepsi). Sahip olarak yalnız kullanıcının görebildiği CRM müşterileri seçilebilir.

## 5. Ekranlar

### 5.1 Gayrimenkul formu (oluştur ve düzenle — tek şablon)

1. Tür ve alt tür seçimi; form yalnız ilgili alanları gösterir (JS ile, sunucu tarafı doğrulama da türe göre).
2. Konum (il/ilçe/mahalle; arsa/tarlada ada/parsel/pafta, JSON ile parsel yükleme korunur).
3. Temel bilgiler (türe göre).
4. Özellikler: iç/dış/muhit/ulaşım/cephe/altyapı onay kutuları.
5. SWOT.
6. Açıklama, fotoğraflar.
7. Mal sahipleri: CRM müşterisi arama + seçme, hisse, irtibat; "Yeni müşteri ekle" (ad, telefon) ile anında oluşturma.
8. "Bunu hemen ilana çıkar" seçeneği: işaretlenirse teklif tipi ve fiyat alanları açılır, kayıtla birlikte tek
   gayrimenkullü ilan oluşur.

Mevcut `analysis_form.html` ve `analysis_edit.html` tek `gayrimenkul_form.html`'de birleşir.

### 5.2 İlan formu

1. Mal sahibi seç (CRM).
2. Sahibin gayrimenkulleri listelenir; ilana katılacaklar işaretlenir, ana kayıt seçilir, "Gayrimenkul ekle" kısayolu.
3. Teklif tipi ve şartlar (tipe göre alanlar). Toplam m², inşaat hakkı, sahibe düşen m² canlı gösterilir.
4. Emsaller: satır ekle/sil; altında canlı karşılaştırma kutusu ("Bölge ort. 18.500 ₺/m², talep %8 üstünde").
5. Durum, sorumlu danışman, açıklama.

### 5.3 Detay sayfaları

- **İlan detayı:** kod, tip ve durum rozetleri; fiyat/şartlar; parsel tablosu; emsal karşılaştırma kartı;
  bağlı CRM fırsatları; sahipler (ofis içi); rapor düğmeleri; portföye ekle.
- **Gayrimenkul detayı:** türe özel bilgiler, özellikler, SWOT, fotoğraflar, sahipler, yer aldığı ilanlar (geçmiş dahil).
  "Birim maliyet", "güncel değer", "değer artışı" kutuları kalkar.
- **CRM müşteri detayı:** "Gayrimenkulleri" sekmesi (tür, hisse, aktif ilan durumu); seçilenlerle "Yeni ilan oluştur".

### 5.4 Listeler

- **İlanlar:** teklif tipi, durum, tür, fiyat aralığı, sorumlu filtreleri; kartta "Kat karşılığı · 4 parsel · 3.200 m² · %50".
- **Gayrimenkuller:** tür, il/ilçe, aktif ilanı var/yok filtreleri.
- Menüde "Analizler" yerine **Gayrimenkuller** ve **İlanlar**.

### 5.5 CRM fırsatları

Fırsat formuna isteğe bağlı "İlgili ilan" seçimi; fırsat detayında ilan bağlantısı.

## 6. Raporlar (PDF, Word, PowerPoint)

- Rapor **ilan** üzerinden üretilir (`build_report_model` ilan alır; tek gayrimenkullü ilanda bugünkü düzen korunur).
- Kaldırılanlar: yatırım senaryoları, değer artışı projeksiyonu, getiri.
- Eklenen "Fiyat ve Emsal Analizi" bölümü: istenen fiyat/m², emsal tablosu, bölge ortalaması, fark ve konumlandırma.
- Çok parselli ilan: parsel tablosu (ada/parsel/m²/imar/KAKS), toplam m², inşaat hakkı.
- Kat karşılığı: şartlar tablosu (pay %, ek nakit, teslim süresi, teminat, tevhid) ve sahibe düşen tahmini m².
- Türe özel bilgi tablosu ve özellikler; arsada imar/TAKS/KAKS korunur.
- Mal sahibi bilgisi rapora **girmez**.
- Gayrimenkul detayından rapor istenirse, o gayrimenkulün aktif ilanı varsa onunla, yoksa fiyatsız
  "tanıtım" raporu üretilir.

## 7. Geçiş (mevcut veri)

Başlangıçta idempotent kurulum fonksiyonu (`modules/ilan_kurulum.py`):

1. Yeni sütun ve tabloları ekler.
2. `tur` boş kayıtları `arsa` yapar.
3. `altyapi` JSON'unu `ozellikler.altyapi`'ya kopyalar (altyapi sütunu silinmez).
4. İlanı olmayan her gayrimenkul için tek gayrimenkullü, `satilik`, `pazarlamada` ilan oluşturur:
   `fiyat` ← gayrimenkul.fiyat, `bolge_m2_fiyat_elle` ← gayrimenkul.bolge_fiyat, sahibi ve ofisi aynen.
5. `portfolio_arsalar` bağlantılarını `portfolio_ilanlar`'a kopyalar.

Canlıya almadan önce Supabase yedeği alınır (`/opt/arsa-backups/yedekle.sh`).

API (`/api/v1/analysis`) geriye dönük uyumlu kalır; yeni alanlar okunur alan olarak eklenir. İlan API'si bu kapsamda yoktur.

## 8. Demo verisi

Demo yükleyici genişletilir: daire (satılık), villa (satılık), dükkân (kiralık), ofis (kiralık),
hisseli tarla, ve aynı sahibin 213 ada 2-3-4-5 parsellerinden oluşan kat karşılığı ilanı (emsal pay oranlarıyla);
CRM fırsatlarından bazıları ilanlara bağlanır.

## 9. Test

- Birim: `ilan_servis` hesapları (m² ağırlıklı ortalama, KAKS eksik parsel, elle değerler, fark ve konumlandırma
  her iki yönde), çakışma kuralı, ilan kodu üretimi.
- Entegrasyon (Flask test istemcisi, ayrı test veritabanı): her tür × her teklif tipi için oluşturma, düzenleme,
  detay; çok parselli kat karşılığı ilanı; hisseli sahip ekleme ve "Yeni müşteri ekle"; yetkisiz kullanıcının
  başkasının müşterisini sahip seçememesi; üç rapor formatının her teklif tipiyle üretilmesi.
- Geçiş: mevcut demo veritabanının bir kopyasında kurulum iki kez çalıştırılır; kayıt sayıları, fiyatlar ve
  portföy bağlantıları korunur, eski arsa raporları üretilmeye devam eder.
- Mevcut işlev testi (`fonksiyon_testi.py`) yeni yapıya uyarlanıp tam geçer.

## 10. Kapsam dışı / sonraya

- İlan sitelerine yayın, emsal otomatik çekme
- İlan API'si
- Kullanılmayan eski sütunların (deger_artis_orani vb.) silinmesi — geçiş birkaç hafta sorunsuz çalıştıktan sonra ayrı iş

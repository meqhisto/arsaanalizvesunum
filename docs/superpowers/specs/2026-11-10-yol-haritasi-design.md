# Arsa Analiz Yol Haritası

Tarih: 2026-11-10 · Durum: Taslak, gözden geçirme bekliyor

## 1. Amaç

Program önce kendi ofisimizde günlük işte gerçekten kullanılacak, ardından başka emlak
ofislerine ürün olarak sunulacak. Bu belge işlerin sırasını ve her aşamanın ne zaman bitmiş
sayılacağını belirler. Tek tek işlerin ayrıntılı tasarımı burada yoktur; her iş başlamadan önce
kendi tasarımından ve onayından geçer.

## 2. Bugünkü durum (2026-11-10)

- Modüller: gayrimenkul, ilan, CRM, iş takip, portföy, raporlar (PDF, Word, PowerPoint), yönetim paneli.
- Canlıda yalnızca demo verisi var: 1 gerçek kullanıcı, 18 gayrimenkul, 15 ilan, 10 müşteri.
- Sunucu İstanbul'da, veritabanı Supabase Frankfurt'ta. Sayfa hızı şimdilik kabul edildi.
- Otomatik testler sunucu tarafını kapsıyor, gerçek tarayıcıyı kapsamıyor. Gönder düğmesinin
  formu engellediği hata bu yüzden 2025'ten 2026-11-10'a kadar fark edilmedi.
- Formlarda CSRF koruması yok.
- İstek kaydı (access log) tutulmuyor.
- Uygulama süreci günde bir kez zaman aşımıyla yeniden başlıyor (8, 9 ve 10 Kasım logları).
- Gece yedeği yalnızca veritabanını alıyor ve aynı sunucuda saklıyor. Yüklenen fotoğraf ve
  belgeler yedeklenmiyor.
- `blueprints/api/v1` altında kayıtlı olmayan ve çalışmayan kod var (`media.py`, `portfolio.py`).

Gerçek kullanımı engelleyen dört şey: hatalar, mobil kullanım, eksik özellikler, gerçek verinin
içeri alınması.

## 3. Sıralama kararı

Önce sağlamlık, sonra özellik. Dört engelden üçü özellik değil sağlamlık konusudur. Ekip
programı ilk hafta hatasız görürse kullanmaya devam eder; hata görürse Excel'e döner.

Elenen seçenekler:
- Önce özellik: yeni özellikler test edilmemiş tarayıcı davranışının üstüne biner.
- Tek iş akışını uçtan uca yapmak: CRM ve iş takip bir süre denetimsiz kalır.

## 4. Aşama 1 — Güven

Amaç: ekibe vermeden önce programın telefonda ve bilgisayarda sorunsuz çalıştığından emin olmak.

| # | İş | Kapsam |
|---|---|---|
| 1.1 | Tarayıcı testleri | Playwright ile Chromium ve iPhone profilli WebKit. Giriş, gayrimenkul ekle/düzenle, fotoğraf yükleme, ilan, müşteri, iş takip ve rapor indirme akışları. Testler depoda durur ve her değişiklikten önce çalıştırılır. |
| 1.2 | Mobil denetim | Gerçek iPhone'da görülen sorunların sayfa, belirti ve ekran görüntüsüyle toplanıp kapatılması. |
| 1.3 | CSRF koruması | Tüm formlar ve tarayıcıdan yapılan POST istekleri. |
| 1.4 | Görünürlük | İstek kaydı ve sunucu hatalarının bildirimi. |
| 1.5 | Kararlılık | Günlük zaman aşımının sebebinin bulunup giderilmesi. |
| 1.6 | Yedek | Yüklenen dosyaların yedeğe eklenmesi, yedeğin sunucu dışında bir yere kopyalanması, geri yükleme denemesi. |
| 1.7 | Temizlik | Çalışmayan API kodunun kaldırılması. |

Bitti ölçütü: tarayıcı testleri tüm ana akışlarda geçiyor ve ofis sahibi iPhone'da bir tam günlük
işi sorunsuz yapabiliyor.

Sıra: 1.1 ilk yapılır, çünkü sonraki her değişikliği o korur. 1.2 kullanıcıdan bilgi beklediği
için 1.1 ile aynı anda başlar.

## 5. Aşama 2 — Gerçek veriye geçiş

| # | İş | Kapsam |
|---|---|---|
| 2.1 | Toplu içe aktarma | Gayrimenkul ve ilanların Excel'den aktarılması. Müşteri aktarımı var. |
| 2.2 | Demo temizliği | Demo kayıtlarının ve demo ofislerin silinmesi. Öncesinde yedek alınır. |
| 2.3 | Ekip kurulumu | Gerçek ofis, logo, kullanıcı hesapları ve yetkiler. |
| 2.4 | İlk hafta desteği | Ekibin ilk haftasında çıkan sorunların öncelikle kapatılması. |

Bitti ölçütü: ekip bir hafta boyunca yeni kayıtları yalnızca programa giriyor.

Açık soru: mevcut kayıtlar nerede ve hangi biçimde duruyor (Excel, portal, defter)? 2.1'in
kapsamını bu belirler.

## 6. Aşama 3 — Özellikler

Sıra günlük işe etkisine göredir.

| # | Özellik | Kapsam | Bugün var olan |
|---|---|---|---|
| 3.1 | Paylaşılabilir ilan sayfası | Giriş gerektirmeyen, fotoğraflı, WhatsApp'tan gönderilebilen ilan linki. Link kapatılabilir. | İlan detay sayfası ve raporlar |
| 3.2 | Alıcı talebi eşleştirme | Talep kaydı (bölge, bütçe, tür, teklif tipi). Yeni ilan girilince uygun taleplerin, yeni talep girilince uygun ilanların listelenmesi. | Müşteri ve fırsat kayıtları; talep için veri alanı yok |
| 3.3 | Hatırlatma ve bildirim | Yetki bitiş tarihi, kira artışı, müşteri arama hatırlatmaları. Uygulama içi bildirim ve e-posta. | İş takipte uygulama içi bildirim ve günlük hatırlatma görevi; e-posta altyapısı yok |
| 3.4 | Sözleşme ve belgeler | Yetki belgesi, yer gösterme formu, kapora ve kira sözleşmesinin kayıttaki bilgilerle doldurulup PDF üretilmesi. | Rapor üretim altyapısı |
| 3.5 | Portal için dışa aktarma | İlan metni ve fotoğraflarının portala girmeye hazır paket olarak indirilmesi. | - |

Kapsam sınırları:
- 3.5 otomatik yayın değildir. Portalların ofis hesabımıza otomatik yayın bağlantısı sunup
  sunmadığı araştırılacak; sunuyorsa ayrı bir iş olarak eklenir.
- 3.3'ün ilk sürümünde otomatik WhatsApp mesajı yoktur; ücretli ve onaylı iş hesabı gerektirir.
  Yerine "WhatsApp'ta paylaş" düğmesi konur.
- 3.4 için sözleşme şablon metinleri ofisten alınır.

Bitti ölçütü (her özellik için ayrı): ekip özelliği bir hafta günlük işte kullandı ve engelleyici
sorun bildirmedi.

## 7. Aşama 4 — Satışa hazırlık

Kendi ofisimizde en az birkaç haftalık kullanımdan sonra ayrıca tasarlanır. Konu başlıkları:
ofislerin birbirinden tam yalıtımı, kayıt ve deneme süreci, abonelik ve ödeme, tanıtım sayfası,
KVKK metinleri. Kendi kullanımımızdan çıkan dersler bu aşamayı değiştireceği için şimdiden
ayrıntılandırılmadı.

## 8. Çalışma biçimi

- Her iş kendi dalında yapılır, PR ile birleştirilir, canlıya ofis sahibinin onayıyla alınır.
- Aşama 1.1'den sonra her PR tarayıcı testlerinden geçer.
- Aşama 3'teki her özellik başlamadan önce kısa bir tasarım yazılır ve onaylanır.
- Sayfa hızı konusu veri büyüdükçe yeniden değerlendirilir (2026-11-07 kararı).

## 9. Kapsam dışı

- Mobil uygulama (App Store / Play Store).
- Veritabanının taşınması.
- Yapay zekâ ile fiyat tahmini iyileştirmeleri.

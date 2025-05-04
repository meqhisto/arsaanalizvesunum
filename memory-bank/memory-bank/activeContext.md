# Aktif Bağlam (activeContext.md)

Bu belge, Arsa Analiz ve Sunum Sistemi projesi için mevcut proje durumunun bir anlık görüntüsünü sunar. Aktif sprint, devam eden görevler, bilinen sorunlar, öncelikler ve sonraki adımlara odaklanır.

## Mevcut Sprint Hedefleri

Sprint Hedefi: **Temel arsa analiz işlevselliğini uygulamak ve sunum katmanını iyileştirmek.**

Özellikle, bu sprint şunları amaçlamaktadır:


*   **Temel analiz algoritmalarını uygulamak:** Temel arsa metriklerini (örn. alan, boyutlar, önceden tanımlanmış kriterlere göre uygunluk puanları) hesaplamak için algoritmalar geliştirmek ve test etmek.
*   **Analiz sonuçlarını sunmak için kullanıcı arayüzünü iyileştirmek:** Veri görselleştirme ve rapor oluşturmaya odaklanarak sunum katmanının netliğini ve kullanılabilirliğini artırmak.
*   **Veri yükleme sürecindeki performans darboğazlarını gidermek:** Duyarlı bir kullanıcı deneyimi sağlamak için veri alma ve işleme süreçlerini optimize etmek.

## Devam Eden Görevler



*   **Sunum Katmanı İyileştirme (Mehmet):** Veri görselleştirme bileşenlerini, özellikle etkileşimli harita ve grafik ekranlarını iyileştirme. Yeni analiz sonuçlarını sunuma entegre etme üzerinde çalışıyor. Tahmini tamamlanma: 03.05.2025.

*   **Dokümantasyon Güncelleme (Elif):** Kullanıcı dokümantasyonunu analiz ve sunum katmanlarındaki en son değişiklikleri yansıtacak şekilde güncelleme. Tahmini tamamlanma: 09.05.2025

*   **SWOT Analizi Geliştirmeleri:** SWOT analizi verilerinin daha etkili bir şekilde işlenmesi ve önceden tanımlanmış SWOT seçenekleri sunmak. Swot analizlerinin güven skoruna etkisi için bir puanlama sistemi yapmak 
*   **Raporlama Özellikleri:** Analiz sonuçlarının PDF veya Excel formatında dışa aktarılması ve grafikler/görselleştirmeler oluşturulması.
*   **Kullanıcı Deneyimi İyileştirmeleri:** Form doldurma sürecini daha kullanıcı dostu hale getirmek, adım adım form doldurma ve otomatik kaydetme özelliği eklemek.

*   **Performans Optimizasyonu (Ek):** Sayfa yükleme hızını artırmak ve JavaScript kodunu optimize etmek.
*   **Güvenlik Geliştirmeleri:** CSRF koruması eklemek, XSS saldırılarına karşı koruma sağlamak ve veri girişi sanitizasyonu yapmak.

## Bilinen Sorunlar


.
*   **Sınırlı Hata Yönetimi:** Sistem şu anda sağlam hata yönetimine sahip değil, bu da beklenmedik çökmelere ve veri kaybına yol açabilir.

## Öncelikler


4.  **Temel Hata Yönetimi Uygulama:** Çökmeleri ve veri kaybını önlemek için temel hata yönetimi ekleyin.

## Sonraki Adımlar


*   **Kod İncelemesi:** Veri entegrasyonu ve analiz algoritması modülleri için 06.05.2025 tarihine kadar kod incelemeleri yapın.
*   **Performans Testi:** Önbellekleme stratejileri uygulandıktan sonra veri yükleme sürecinin kapsamlı performans testini yapın.
*   **Hata Yönetimi Uygulama:** 08.05.2025 tarihine kadar temel hata yönetimi uygulayın.

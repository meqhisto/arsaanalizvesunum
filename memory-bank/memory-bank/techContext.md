```markdown
# Teknik Bağlam (techContext.md)

Bu belge, Arsa Analiz ve Sunum Sistemi projesi için teknolojik bağlamı özetlemektedir. Geliştirme yaşam döngüsü boyunca kullanılan teknolojileri, araçları, ortamları ve süreçleri detaylandırır.

## Kullanılan Teknolojiler

*   **Programlama Dilleri:**
    *   Python (Backend, Veri Analizi, Betikleme)
    *   JavaScript (Frontend)
    *   HTML (Frontend)
    *   CSS (Frontend)

*   **Backend Çerçevesi:**
    *   Django (REST API, Kullanıcı Kimlik Doğrulama, Veri Yönetimi)

*   **Frontend Çerçevesi:**
    *   React (Kullanıcı Arayüzü, Bileşen Yönetimi)

*   **Veritabanı:**
    *   PostgreSQL (Veri Depolama, Mekansal Veri Desteği)
    *   PostGIS (Mekansal veri yönetimi için PostgreSQL uzantısı)

*   **Jeo-uzamsal Kütüphaneler:**
    *   GeoPandas (Python - Mekansal Veri Manipülasyonu ve Analizi)
    *   Shapely (Python - Geometrik İşlemler)
    *   Leaflet (JavaScript - Etkileşimli Haritalar)

*   **Veri Görselleştirme Kütüphaneleri:**
    *   Matplotlib (Python - Statik Çizimler ve Grafikler)
    *   Seaborn (Python - İstatistiksel Veri Görselleştirme)
    *   Chart.js (JavaScript - Dinamik Çizimler ve Grafikler)

*   **Bulut Platformu:**
    *   AWS (Amazon Web Services) veya Google Cloud Platform (GCP) (Altyapı, Barındırma, Hizmetler - *Maliyet ve ölçeklenebilirlik analizine göre kesin platform seçimi yapılacaktır*)

## Yazılım Geliştirme Araçları

*   **IDE (Entegre Geliştirme Ortamı):**
    *   Visual Studio Code (Kod Düzenleme, Hata Ayıklama, Sürüm Kontrol Entegrasyonu)
    *   PyCharm (Python IDE - Kod Tamamlama, Yeniden Düzenleme, Hata Ayıklama)

*   **Sürüm Kontrol Sistemi:**
    *   Git (Dağıtılmış Sürüm Kontrolü)

*   **Sürüm Kontrol Deposu:**
    *   GitHub veya GitLab (Kod Barındırma, İşbirliği, Sorun Takibi)

*   **Paket Yöneticisi:**
    *   pip (Python Paket Kurulumu)
    *   npm (Node Paket Yöneticisi - JavaScript Paket Kurulumu)

*   **Derleme Aracı:**
    *   Webpack (Frontend Varlık Paketleme)

*   **Konteynerleştirme:**
    *   Docker (Uygulamaların Konteynerleştirilmesi)

*   **Orkestrasyon:**
    *   Docker Compose (Çoklu Konteyner Uygulama Yönetimi)
    *   Kubernetes (Konteyner Orkestrasyonu - *Gelecekteki ölçeklenebilirlik için düşünülüyor, başlangıçta uygulanmayabilir*)

*   **Proje Yönetimi:**
    *   Jira (Sorun Takibi, Çevik Proje Yönetimi)
    *   Confluence (Dokümantasyon, İşbirliği)

## Geliştirme Ortamı

*   **İşletim Sistemi:**
    *   Linux (Backend geliştirme ve dağıtım için tercih edilir)
    *   macOS (Frontend ve bazı backend geliştirme için kabul edilebilir)
    *   Windows (Frontend ve bazı backend geliştirme için kabul edilebilir)

*   **Sanal Ortam:**
    *   venv (Python Sanal Ortamları)
    *   Node.js sürüm yöneticisi (nvm)

*   **Veritabanı Sunucusu:**
    *   PostGIS uzantısı etkinleştirilmiş yerel PostgreSQL örneği.

*   **Bulut Ortamı:**
    *   Geliştirme ve hazırlık ortamları, üretim ortamını yansıtmak için AWS veya GCP'de (nihai platform kararına bağlı olarak) sağlanacaktır.

## Test Stratejisi

*   **Birim Testi:**
    *   Bireysel fonksiyonların ve bileşenlerin test edilmesi.
    *   Python: `unittest` veya `pytest` çerçeveleri
    *   JavaScript: Jest veya Mocha

*   **Entegrasyon Testi:**
    *   Farklı modüller veya servisler arasındaki etkileşimlerin test edilmesi.

*   **API Testi:**
    *   REST API uç noktalarının işlevsellik ve performans açısından test edilmesi.
    *   Araçlar: `requests` kütüphanesi ile `pytest` (Python), Postman

*   **Uçtan Uca (E2E) Testi:**
    *   Kullanıcı etkileşiminden veritabanı etkileşimine kadar tüm uygulama akışının test edilmesi.
    *   Araçlar: Cypress veya Selenium

*   **Jeo-uzamsal Veri Doğrulama:**
    *   Jeo-uzamsal verilerin bütünlüğünün ve doğruluğunun doğrulanması.
    *   Geometrik doğrulama için GeoPandas ve Shapely kullanılması.

*   **Performans Testi:**
    *   Sistemin beklenen trafiği kaldırabildiğinden emin olmak için yük testi.
    *   Araçlar: Locust veya JMeter

*   **Kullanıcı Kabul Testi (UAT):**
    *   Sistemin gereksinimlerini karşıladığından emin olmak için son kullanıcılar tarafından test edilmesi.

## Dağıtım Süreci

*   **Konteynerleştirme:** Her servis için (backend, frontend) Docker imajları oluşturulacaktır.
*   **Kod Olarak Altyapı (IaC):** Altyapıyı sağlamak için Terraform veya CloudFormation (AWS/GCP'ye özel) kullanılacaktır.
*   **Dağıtım Otomasyonu:** Dağıtım adımlarını otomatikleştirmek için Ansible veya benzeri bir yapılandırma yönetim aracı kullanılacaktır.
*   **Dağıtım Stratejisi:** Güncellemeler sırasında kesinti süresini en aza indirmek için Blue/Green dağıtımı veya Rolling dağıtımı kullanılacaktır.
*   **Veritabanı Migrasyonları:** Veritabanı şema değişikliklerini yönetmek için Alembic (Python/Django için) veya benzeri bir araç kullanılacaktır.
*   **İzleme:** Sistem izleme ve uyarı için Prometheus ve Grafana.

## Sürekli Entegrasyon Yaklaşımı

*   **CI/CD Hattı:**
    *   Derleme, test ve dağıtım sürecini otomatikleştirmek için GitHub Actions veya GitLab CI/CD kullanılacaktır.

*   **Otomatik Test:**
    *   Tüm birim, entegrasyon ve API testleri her kod commitinde otomatik olarak çalıştırılacaktır.

*   **Kod Kalitesi Kontrolleri:**
    *   Kod stili ve kalitesini zorlamak için linterlar ve kod formatlayıcılar (örn. `flake8`, `pylint`, `prettier`) kullanılacaktır.

*   **Otomatik Dağıtım:**
    *   Testlerin ve kod kalitesi kontrollerinin başarıyla tamamlanmasının ardından, uygulama otomatik olarak hazırlık veya üretim ortamına dağıtılacaktır.

Oluşturulma Tarihi: 30.04.2025
```
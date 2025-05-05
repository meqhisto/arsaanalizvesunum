```markdown
# Arsa Analiz ve Sunum Sistemi - Sistem Kalıpları

Bu belge, Arsa Analiz ve Sunum Sistemi'nde kullanılan sistem kalıplarını özetlemektedir. Mimari tasarımı, veri modellerini, API tanımlarını, bileşen yapısını, entegrasyon noktalarını ve ölçeklenebilirlik stratejisini kapsar.

## 1. Mimari Tasarım: Mikroservis Mimarisi

Mikroservis mimarisini kullanacağız. Bu yaklaşım aşağıdaki faydaları sunar:

*   **Bağımsız Dağıtım:** Her servis bağımsız olarak dağıtılabilir ve ölçeklendirilebilir.
*   **Teknoloji Çeşitliliği:** Farklı servisler, belirli görevleri için en uygun farklı teknolojiler kullanılarak oluşturulabilir.
*   **Hata İzolasyonu:** Bir servisteki hata, tüm sistemi çökertmez.
*   **Geliştirilmiş Ölçeklenebilirlik:** Bireysel servisler, belirli yük gereksinimlerine göre ölçeklendirilebilir.
*   **Daha Kolay Bakım:** Daha küçük kod tabanları daha kolay anlaşılır ve bakımı yapılır.

Çekirdek servisler şunlar olacaktır:

*   **Arsa Veri Servisi:** Arsa verilerinin depolanmasını ve alınmasını yönetir.
*   **Analiz Servisi:** Arsa verileri üzerinde analitik hesaplamalar yapar (örn. uygunluk analizi, imar uyumluluğu).
*   **Sunum Servisi:** Analiz edilmiş arsa verilerine dayalı sunumlar ve görselleştirmeler oluşturur.
*   **Kullanıcı Yönetimi Servisi:** Kullanıcı kimlik doğrulama ve yetkilendirmeyi yönetir.
*   **API Ağ Geçidi:** Tüm istemci istekleri için tek bir giriş noktası görevi görür ve bunları uygun servislere yönlendirir.

## 2. Veri Modelleri

Kalıcı veri depolama için ilişkisel bir veritabanı (PostgreSQL) ve gerekirse belirli analitik veriler için potansiyel olarak bir NoSQL veritabanı (örn. MongoDB) kullanacağız. İşte temel veri modellerine basitleştirilmiş bir genel bakış:

**2.1. Arsa Veri Modeli (İlişkisel):**

*   `arsa_id` (UUID, Birincil Anahtar): Arsa parseli için benzersiz tanımlayıcı.
*   `parsel_no` (VARCHAR): Parsel numarası.
*   `ada_no` (VARCHAR): Ada numarası.
*   `mevki` (VARCHAR): Konum.
*   `alan` (NUMERIC): Alan (metrekare cinsinden).
*   `koordinatlar` (GEOMETRY): Coğrafi koordinatlar (örn. PostGIS kullanarak).
*   `imar_durumu` (VARCHAR): İmar durumu.
*   `tapu_kaydi` (VARCHAR): Tapu kaydı.
*   `created_at` (TIMESTAMP): Oluşturulma zaman damgası.
*   `updated_at` (TIMESTAMP): Son güncelleme zaman damgası.

**2.2. Analiz Sonucu Veri Modeli (İlişkisel/NoSQL):**

*   `analiz_id` (UUID, Birincil Anahtar): Analiz sonucu için benzersiz tanımlayıcı.
*   `arsa_id` (UUID, Arsa'ya referans veren Yabancı Anahtar): Analizin yapıldığı arsa parseli.
*   `analiz_tipi` (VARCHAR): Yapılan analiz türü (örn. "Uygunluk Analizi", "İmar Uyumluluğu").
*   `sonuc` (JSONB/Belge): Analiz sonuçları, esneklik için potansiyel olarak bir JSON belgesi olarak depolanır.
*   `created_at` (TIMESTAMP): Oluşturulma zaman damgası.

**2.3. Kullanıcı Veri Modeli (İlişkisel):**

*   `kullanici_id` (UUID, Birincil Anahtar): Kullanıcı için benzersiz tanımlayıcı.
*   `kullanici_adi` (VARCHAR): Kullanıcı adı.
*   `sifre` (VARCHAR): Şifre (hashlenmiş).
*   `eposta` (VARCHAR): E-posta adresi.
*   `rol` (VARCHAR): Kullanıcı rolü (örn. "Admin", "Analist", "Görüntüleyici").
*   `created_at` (TIMESTAMP): Oluşturulma zaman damgası.
*   `updated_at` (TIMESTAMP): Son güncelleme zaman damgası.

## 3. API Tanımları

Servisler arasında ve harici istemcilerle iletişim için RESTful API'ler kullanacağız. JSON standart veri formatı olacaktır.

**3.1. Arsa Veri Servisi API:**

*   `GET /arsalar`: Tüm arsaları al (sayfalama ile).
*   `GET /arsalar/{arsa_id}`: Kimliğe göre belirli bir arsayı al.
*   `POST /arsalar`: Yeni bir arsa oluştur.
*   `PUT /arsalar/{arsa_id}`: Mevcut bir arsayı güncelle.
*   `DELETE /arsalar/{arsa_id}`: Bir arsayı sil.

**3.2. Analiz Servisi API:**

*   `POST /analizler/{arsa_id}`: Belirli bir arsa üzerinde analizi tetikle. İstek gövdesinde analiz türünü kabul eder (örn. `{"analiz_tipi": "Uygunluk Analizi"}`).
*   `GET /analizler/{analiz_id}`: Belirli bir analiz sonucunu al.
*   `GET /analizler/arsa/{arsa_id}`: Belirli bir arsa için tüm analiz sonuçlarını al.

**3.3. Sunum Servisi API:**

*   `GET /sunumlar/{arsa_id}`: En son analiz sonuçlarını kullanarak belirli bir arsa için sunum oluştur.
*   `GET /sunumlar/{arsa_id}/pdf`: Belirli bir arsa için PDF sunumu oluştur.

**3.4. Kullanıcı Yönetimi Servisi API:**

*   `POST /kullanicilar/kayit`: Yeni bir kullanıcı kaydet.
*   `POST /kullanicilar/giris`: Bir kullanıcıyı kimlik doğrula ve bir JWT belirteci al.
*   `GET /kullanicilar/profil`: Mevcut kullanıcının profilini al (kimlik doğrulama gerektirir).

## 4. Bileşen Yapısı

Her mikroservis aşağıdaki gibi yapılandırılacaktır:

*   **API Katmanı:** Gelen istekleri yönetir, giriş doğrulamasını yapar ve iş mantığı katmanını çağırır.
*   **İş Mantığı Katmanı:** Servisin çekirdek mantığını uygular.
*   **Veri Erişim Katmanı:** Veritabanı veya diğer veri kaynaklarıyla etkileşim kurar.
*   **Yardımcılar/Araçlar:** Servis boyunca kullanılan ortak fonksiyonlar ve yardımcı programlar.

Örnek: **Arsa Veri Servisi Bileşen Yapısı**

*   `ArsaDataService/`
    *   `api/`
        *   `arsa_controller.py` (Arsalarla ilgili HTTP isteklerini yönetir)
    *   `business_logic/`
        *   `arsa_manager.py` (Arsa oluşturma, alma, güncelleme ve silme işlemlerini yönetir)
    *   `data_access/`
        *   `arsa_repository.py` (Arsa verileri üzerinde CRUD işlemleri yapmak için veritabanıyla etkileşim kurar)
    *   `models/`
        *   `arsa.py` (Arsa veri modelini tanımlar)
    *   `utils/`
        *   `exceptions.py` (Özel istisnalar)

## 5. Entegrasyon Noktaları

*   **API Ağ Geçidi:** Tüm istemci istekleri API Ağ Geçidi üzerinden yönlendirilecektir. Bu, sistem için tek bir giriş noktası sağlar ve merkezi kimlik doğrulama, yetkilendirme ve hız sınırlama imkanı sunar. API Ağ Geçidi olarak Kong veya Tyk kullanabiliriz.
*   **Mesaj Kuyruğu (RabbitMQ/Kafka):** Servisler arasındaki eşzamansız iletişim bir mesaj kuyruğu kullanılarak yönetilecektir. Örneğin, yeni bir arsa oluşturulduğunda, Arsa Veri Servisi kuyruğa bir mesaj yayınlayabilir ve bu mesaj Analiz Servisi tarafından alınarak ilk analizi tetikleyebilir.
*   **Veritabanı:** Tüm servisler, kendi Veri Erişim Katmanları aracılığıyla PostgreSQL veritabanıyla etkileşim kuracaktır.
*   **Harici API'ler:** Analiz Servisi, veri zenginleştirme için harici API'lerle entegre olabilir (örn. belirli bir konum için demografik verileri alma).

## 6. Ölçeklenebilirlik Stratejisi

*   **Yatay Ölçeklendirme:** Mikroservisler, her servisin daha fazla örneği eklenerek yatay olarak ölçeklendirilebilir. Bu, Kubernetes gibi bir konteyner düzenleme platformu kullanılarak yönetilecektir.
*   **Yük Dengeleme:** API Ağ Geçidi ve Kubernetes, her servisin birden çok örneği arasında yük dengelemeyi yönetecektir.
*   **Veritabanı Ölçeklendirme:** PostgreSQL veritabanını ölçeklendirmek için veritabanı replikasyonu ve parçalama kullanabiliriz.
*   **Önbellekleme:** Veritabanı yükünü azaltmak ve sık erişilen veriler için yanıt sürelerini iyileştirmek amacıyla önbellekleme mekanizmaları (örn. Redis) uygulayın. Analiz sonuçlarını önbelleğe almayı düşünün.
*   **Eşzamansız İşleme:** Uzun süren görevleri arka plan çalışanlarına yüklemek için mesaj kuyrukları kullanın, ana uygulama iş parçacıklarının engellenmesini önleyin.

Oluşturulma Tarihi: 30.04.2025
```
# Arsa Analiz ve Sunum API Dokümantasyonu

## Genel Bakış

Bu API, arsa analizi ve CRM sistemi için RESTful web servisleri sağlar. JWT tabanlı kimlik doğrulama kullanır ve JSON formatında veri alışverişi yapar.

## Base URL
http://localhost:5000/api/v1/

## Kimlik Doğrulama

API, JWT (JSON Web Token) tabanlı kimlik doğrulama kullanır. Korumalı endpoint'lere erişim için Authorization header'ında Bearer token gönderilmelidir.

```
Authorization: Bearer <access_token>
```

## Standart Yanıt Formatı

### Başarılı Yanıt
```json
{
  "success": true,
  "message": "İşlem başarılı",
  "data": { ... },
  "meta": { ... }
}
```

### Hata Yanıtı
```json
{
  "success": false,
  "message": "Hata mesajı",
  "errors": { ... },
  "error_code": "ERROR_CODE"
}
```

### Sayfalanmış Yanıt
```json
{
  "success": true,
  "message": "Veriler getirildi",
  "data": [ ... ],
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## Endpoint'ler

### 1. Kimlik Doğrulama (Authentication)

#### Kullanıcı Kaydı
```
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "ad": "Ahmet",
  "soyad": "Yılmaz",
  "telefon": "05551234567",
  "firma": "ABC Şirketi",
  "unvan": "Emlak Uzmanı",
  "adres": "İstanbul, Türkiye"
}
```

#### Kullanıcı Girişi
```
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "remember_me": false
}
```

#### Token Yenileme
```
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

#### Çıkış
```
POST /auth/logout
Authorization: Bearer <access_token>
```

#### Parola Sıfırlama İsteği
```
POST /auth/forgot-password
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

### 2. Kullanıcı Yönetimi (Users)

#### Profil Bilgileri
```
GET /users/profile
Authorization: Bearer <access_token>
```

#### Profil Güncelleme
```
PUT /users/profile
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "ad": "Ahmet",
  "soyad": "Yılmaz",
  "telefon": "05551234567",
  "firma": "ABC Şirketi",
  "unvan": "Emlak Uzmanı",
  "adres": "İstanbul, Türkiye",
  "timezone": "Europe/Istanbul"
}
```

#### Parola Değiştirme
```
POST /users/change-password
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword123",
  "confirm_password": "NewPassword123"
}
```

#### Kullanıcı Listesi (Admin)
```
GET /users?page=1&per_page=20&search=ahmet&role=danisman&active=true
Authorization: Bearer <access_token>
```

### 3. Arsa Analizi (Analysis)

#### Analiz Listesi
```
GET /analysis?page=1&per_page=20&il=İstanbul&ilce=Kadıköy&min_price=1000000&max_price=5000000
Authorization: Bearer <access_token>
```

#### Yeni Analiz Oluşturma
```
POST /analysis
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "il": "İstanbul",
  "ilce": "Kadıköy",
  "mahalle": "Moda",
  "ada": "123",
  "parsel": "45",
  "koordinatlar": "40.9876,29.1234",
  "pafta": "H23d1a",
  "metrekare": 1000.0,
  "imar_durumu": "Konut",
  "taks": 0.30,
  "kaks": 1.20,
  "yaklasik_deger": 5000000.0,
  "tahmini_deger_m2": 5000.0,
  "yatirim_getirisi": 15.5,
  "risk_skoru": 3,
  "notlar": "Analiz notları",
  "konum_skoru": 8,
  "ulasim_skoru": 7,
  "cevre_skoru": 9,
  "gelecek_potansiyeli": 8
}
```

#### Analiz Detayı
```
GET /analysis/{id}
Authorization: Bearer <access_token>
```

#### Analiz Güncelleme
```
PUT /analysis/{id}
Authorization: Bearer <access_token>
```

#### Analiz Silme
```
DELETE /analysis/{id}
Authorization: Bearer <access_token>
```

#### Analiz İstatistikleri
```
GET /analysis/stats
Authorization: Bearer <access_token>
```

#### Toplu Analiz Oluşturma
```
POST /analysis/bulk
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "analyses": [
    {
      "il": "İstanbul",
      "ilce": "Kadıköy",
      "mahalle": "Moda",
      "metrekare": 1000.0,
      "imar_durumu": "Konut",
      "yaklasik_deger": 5000000.0
    }
  ],
  "portfolio_id": 1
}
```

### 4. CRM Sistemi

#### Kişiler (Contacts)

##### Kişi Listesi
```
GET /crm/contacts?page=1&per_page=20&search=ahmet&status=Lead&company_id=1
Authorization: Bearer <access_token>
```

##### Yeni Kişi Oluşturma
```
POST /crm/contacts
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "ad": "Ahmet",
  "soyad": "Yılmaz",
  "email": "ahmet@example.com",
  "telefon": "05551234567",
  "company_id": 1,
  "pozisyon": "Müdür",
  "adres": "İstanbul",
  "notlar": "Önemli müşteri",
  "status": "Lead",
  "kaynak": "Web sitesi"
}
```

##### Kişi Detayı
```
GET /crm/contacts/{id}
Authorization: Bearer <access_token>
```

##### Kişi Güncelleme
```
PUT /crm/contacts/{id}
Authorization: Bearer <access_token>
```

##### Kişi Silme
```
DELETE /crm/contacts/{id}
Authorization: Bearer <access_token>
```

#### Şirketler (Companies)

##### Şirket Listesi
```
GET /crm/companies?page=1&per_page=20&search=abc
Authorization: Bearer <access_token>
```

##### Yeni Şirket Oluşturma
```
POST /crm/companies
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "ABC Şirketi",
  "industry": "Emlak",
  "website": "https://abc.com",
  "telefon": "02121234567",
  "email": "info@abc.com",
  "adres": "İstanbul",
  "notlar": "Büyük şirket"
}
```

#### Fırsatlar (Deals)

##### Fırsat Listesi
```
GET /crm/deals?page=1&per_page=20&stage=Potansiyel&contact_id=1
Authorization: Bearer <access_token>
```

##### Yeni Fırsat Oluşturma
```
POST /crm/deals
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "title": "Arsa Satışı",
  "contact_id": 1,
  "company_id": 1,
  "value": 5000000.0,
  "stage": "Potansiyel",
  "expected_close_date": "2024-12-31",
  "probability": 50,
  "notes": "Büyük fırsat"
}
```

#### CRM İstatistikleri
```
GET /crm/stats
Authorization: Bearer <access_token>
```

### 5. Portfolio Yönetimi

#### Portfolio Listesi
```
GET /portfolio?page=1&per_page=20&visibility=public
Authorization: Bearer <access_token>
```

#### Yeni Portfolio Oluşturma
```
POST /portfolio
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "title": "İstanbul Portfolyosu",
  "description": "İstanbul'daki arsalar",
  "visibility": "private"
}
```

#### Portfolio Detayı
```
GET /portfolio/{id}
Authorization: Bearer <access_token>
```

#### Portfolio'ya Analiz Ekleme
```
POST /portfolio/{id}/analyses
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "analysis_ids": [1, 2, 3]
}
```

#### Portfolio İstatistikleri
```
GET /portfolio/{id}/stats
Authorization: Bearer <access_token>
```

### 6. Medya Yönetimi

#### Dosya Yükleme
```
POST /media/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Yüklenecek dosya
- `analysis_id`: Analiz ID (opsiyonel)
- `description`: Dosya açıklaması (opsiyonel)

#### Dosya İndirme
```
GET /media/{id}
Authorization: Bearer <access_token>
```

#### Dosya Bilgileri
```
GET /media/{id}/info
Authorization: Bearer <access_token>
```

#### Dosya Silme
```
DELETE /media/{id}
Authorization: Bearer <access_token>
```

#### Analiz Dosyaları
```
GET /media/analysis/{analysis_id}
Authorization: Bearer <access_token>
```

## HTTP Status Kodları

- `200 OK`: İşlem başarılı
- `201 Created`: Kaynak oluşturuldu
- `400 Bad Request`: Geçersiz istek
- `401 Unauthorized`: Kimlik doğrulama gerekli
- `403 Forbidden`: Erişim izni yok
- `404 Not Found`: Kaynak bulunamadı
- `409 Conflict`: Çakışma (örn: email zaten var)
- `413 Payload Too Large`: Dosya çok büyük
- `422 Unprocessable Entity`: Validasyon hatası
- `429 Too Many Requests`: Rate limit aşıldı
- `500 Internal Server Error`: Sunucu hatası

## Rate Limiting

API, rate limiting kullanır. Aşırı istek durumunda `429 Too Many Requests` yanıtı döner.

## CORS

API, CORS desteği sağlar. Aşağıdaki origin'lerden gelen isteklere izin verir:
- `http://localhost:3000`
- `http://localhost:5000`

## Swagger Dokümantasyonu

Interaktif API dokümantasyonu için:
```
http://localhost:5000/api/docs/
```

## Test Etme

API'yi test etmek için `test_api.py` scriptini kullanabilirsiniz:

```bash
python test_api.py
```

## Hata Kodları

| Kod | Açıklama |
|-----|----------|
| `VALIDATION_ERROR` | Validasyon hatası |
| `NOT_FOUND` | Kaynak bulunamadı |
| `UNAUTHORIZED` | Kimlik doğrulama hatası |
| `FORBIDDEN` | Erişim izni yok |
| `INTERNAL_SERVER_ERROR` | Sunucu hatası |

## Güvenlik

- Tüm şifreler hash'lenerek saklanır
- JWT token'ları güvenli şekilde imzalanır
- Input validation ve sanitization uygulanır
- Rate limiting ile DDoS koruması
- CORS yapılandırması ile güvenli erişim

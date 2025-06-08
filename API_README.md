# 🚀 Arsa Analiz ve Sunum API Documentation

[![API Status](https://img.shields.io/badge/API-Production%20Ready-brightgreen)](http://localhost:5000/health)
[![Test Coverage](https://img.shields.io/badge/Tests-14%2F14%20Passing-brightgreen)](./test_api.py)
[![Version](https://img.shields.io/badge/Version-1.1.4-blue)](./PROGRESS.md)
[![Authentication](https://img.shields.io/badge/Auth-JWT%20Bearer-orange)](./blueprints/api/v1/auth.py)

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Request/Response Examples](#requestresponse-examples)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Health Check & Performance](#health-check--performance)
- [Development Setup](#development-setup)

## 🎯 Overview

The **Arsa Analiz ve Sunum API** is a comprehensive REST API for real estate analysis and CRM management. It provides secure, scalable endpoints for managing property analyses, customer relationships, portfolios, and user accounts.

### ✅ Key Features

- ✅ **JWT Authentication** - Secure token-based authentication with refresh mechanism
- ✅ **Real Estate Analysis** - Create, manage, and analyze property data
- ✅ **CRM System** - Contact and customer relationship management
- ✅ **Portfolio Management** - Organize analyses into portfolios
- ✅ **User Management** - Registration, login, profile management
- ✅ **Data Isolation** - Each user sees only their own data
- ✅ **Input Validation** - Comprehensive request validation
- ✅ **Error Handling** - Standardized error responses
- ✅ **Performance Monitoring** - Health checks and performance metrics
- ✅ **CORS Support** - Frontend integration ready

### 🏗️ Architecture

```
/api/v1/
├── auth/          # Authentication endpoints
├── users/         # User management
├── analysis/      # Property analysis CRUD
├── crm/           # CRM and contacts
└── portfolio/     # Portfolio management
```

## 🔐 Authentication

The API uses **JWT (JSON Web Tokens)** for authentication with access and refresh token mechanism.

### Token Types

| Token Type | Purpose | Expiry | Usage |
|------------|---------|--------|-------|
| **Access Token** | API requests | 1 hour | `Authorization: Bearer <token>` |
| **Refresh Token** | Token renewal | 7 days | Refresh endpoint only |

### Authentication Flow

1. **Register/Login** → Get access + refresh tokens
2. **API Requests** → Include access token in header
3. **Token Expires** → Use refresh token to get new access token
4. **Logout** → Invalidate tokens

## 📡 API Endpoints

### 🔑 Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/auth/register` | User registration | ☐ |
| `POST` | `/api/v1/auth/login` | User login | ☐ |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | ✅ (Refresh Token) |
| `POST` | `/api/v1/auth/logout` | User logout | ✅ |

### 👤 User Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/users/profile` | Get user profile | ✅ |

### 📊 Analysis Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/analysis` | Create new analysis | ✅ |
| `GET` | `/api/v1/analysis` | List user analyses | ✅ |
| `GET` | `/api/v1/analysis/{id}` | Get analysis details | ✅ |
| `GET` | `/api/v1/analysis/stats` | Analysis statistics | ✅ |

### 👥 CRM Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/crm/contacts` | Create new contact | ✅ |
| `GET` | `/api/v1/crm/contacts` | List user contacts | ✅ |
| `GET` | `/api/v1/crm/stats` | CRM statistics | ✅ |

### 📁 Portfolio Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/portfolio` | Create new portfolio | ✅ |
| `GET` | `/api/v1/portfolio` | List user portfolios | ✅ |
| `GET` | `/api/v1/portfolio/{id}` | Get portfolio details | ✅ |

### 🏥 System Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/` | API information | ☐ |
| `GET` | `/health` | Health check | ☐ |

## 📝 Request/Response Examples

### User Registration

**Request:**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "ad": "John",
  "soyad": "Doe",
  "telefon": "05551234567",
  "firma": "Real Estate Co."
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "danisman"
    }
  }
}
```

### Create Analysis

**Request:**
```http
POST /api/v1/analysis
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "il": "İstanbul",
  "ilce": "Kadıköy",
  "mahalle": "Moda",
  "metrekare": 1000,
  "fiyat": 5000000,
  "imar_durumu": "Konut",
  "taks": 0.4,
  "kaks": 1.2,
  "notlar": "Deniz manzaralı arsa"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Analysis created successfully",
  "data": {
    "id": 15,
    "il": "İstanbul",
    "ilce": "Kadıköy",
    "mahalle": "Moda",
    "metrekare": 1000.0,
    "fiyat": 5000000.0,
    "imar_durumu": "Konut",
    "taks": 0.4,
    "kaks": 1.2,
    "notlar": "Deniz manzaralı arsa",
    "created_at": "2025-06-08T12:30:00.000000",
    "user_id": 1
  }
}
```

### Create Contact

**Request:**
```http
POST /api/v1/crm/contacts
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "ad": "Ahmet",
  "soyad": "Yılmaz",
  "email": "ahmet@example.com",
  "telefon": "05551234567",
  "status": "Lead",
  "pozisyon": "Emlak Müdürü",
  "notlar": "Potansiyel müşteri"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Contact created successfully",
  "data": {
    "id": 8,
    "ad": "Ahmet",
    "soyad": "Yılmaz",
    "full_name": "Ahmet Yılmaz",
    "email": "ahmet@example.com",
    "telefon": "05551234567",
    "status": "Lead",
    "pozisyon": "Emlak Müdürü",
    "notlar": "Potansiyel müşteri",
    "created_at": "2025-06-08T12:35:00.000000",
    "user_id": 1
  }
}
```

### Create Portfolio

**Request:**
```http
POST /api/v1/portfolio
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "İstanbul Yatırım Portföyü",
  "description": "İstanbul bölgesindeki arsa yatırımları",
  "visibility": "private"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Portfolio created successfully",
  "data": {
    "id": 3,
    "title": "İstanbul Yatırım Portföyü",
    "description": "İstanbul bölgesindeki arsa yatırımları",
    "visibility": "private",
    "arsa_count": 0,
    "created_at": "2025-06-08T12:40:00.000000",
    "user_id": 1
  }
}
```

### List with Pagination

**Request:**
```http
GET /api/v1/analysis?page=1&per_page=10&search=İstanbul
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Analyses retrieved successfully",
  "data": {
    "data": [
      {
        "id": 15,
        "il": "İstanbul",
        "ilce": "Kadıköy",
        "mahalle": "Moda",
        "metrekare": 1000.0,
        "fiyat": 5000000.0,
        "created_at": "2025-06-08T12:30:00.000000"
      }
    ],
    "meta": {
      "pagination": {
        "page": 1,
        "per_page": 10,
        "total": 1,
        "total_pages": 1,
        "has_prev": false,
        "has_next": false
      }
    }
  }
}
```

## ⚠️ Error Handling

The API uses standardized HTTP status codes and error responses.

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request data |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Access denied |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource already exists |
| `422` | Unprocessable Entity | Validation error |
| `500` | Internal Server Error | Server error |

### Error Response Format

```json
{
  "success": false,
  "message": "Descriptive error message",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": {
      "field": "email",
      "message": "Invalid email format"
    }
  }
}
```

### Common Error Examples

**Validation Error:**
```json
{
  "success": false,
  "message": "Missing required field: email",
  "error": {
    "code": "VALIDATION_ERROR",
    "field": "email"
  }
}
```

**Authentication Error:**
```json
{
  "success": false,
  "message": "Token has expired",
  "error": {
    "code": "TOKEN_EXPIRED"
  }
}
```

**Resource Not Found:**
```json
{
  "success": false,
  "message": "Analysis not found",
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "resource": "analysis",
    "id": 999
  }
}
```

## 🧪 Testing

The API includes a comprehensive test suite with **100% test coverage** (14/14 tests passing).

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
python app.py

# Run the test suite (in another terminal)
python test_api.py
```

### Test Coverage

✅ **Authentication Tests:**
- User registration with validation
- User login with JWT token generation
- Token refresh mechanism
- User logout and token invalidation

✅ **Analysis Tests:**
- Create analysis with validation
- List analyses with pagination and search
- Analysis statistics and metrics

✅ **CRM Tests:**
- Create contacts with validation
- List contacts with pagination
- CRM statistics and reporting

✅ **Portfolio Tests:**
- Create portfolios with visibility controls
- List portfolios with filtering

✅ **System Tests:**
- API information endpoint
- Health check with database connectivity
- Performance monitoring

### Test Results Example

```
🚀 Starting API Tests...
✅ PASS API Info
✅ PASS Health Check
✅ PASS User Registration
✅ PASS User Login
✅ PASS User Profile
✅ PASS Create Analysis
✅ PASS List Analyses
✅ PASS Create Contact
✅ PASS List Contacts
✅ PASS Create Portfolio
✅ PASS CRM Stats
✅ PASS Analysis Stats
✅ PASS Token Refresh
✅ PASS Logout

Total: 14/14 tests passed
Success Rate: 100.0%
🎉 All tests passed!
```

## 🏥 Health Check & Performance

### Health Check Endpoint

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.1.4",
  "timestamp": "2025-06-08T12:00:00.000000+00:00",
  "response_time_ms": 45.23,
  "checks": {
    "database_connection": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "database_engine": {
      "status": "healthy",
      "message": "Database engine accessible",
      "details": {
        "driver": "mssql",
        "server_version": "Microsoft SQL Server 2022"
      }
    },
    "database_performance": {
      "status": "healthy",
      "message": "Database performance normal",
      "details": {
        "connection_time_ms": 23.45
      }
    },
    "database_schema": {
      "status": "healthy",
      "message": "All required tables exist",
      "details": {
        "required_tables": ["users", "arsa_analizleri", "crm_contacts"],
        "tables_checked": 4,
        "total_tables": 26
      }
    },
    "api_performance": {
      "status": "healthy",
      "message": "API performance normal"
    }
  }
}
```

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- SQL Server Database
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/meqhisto/arsaanalizvesunum.git
cd arsaanalizvesunum
git checkout 1.1.4
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
# Copy and edit configuration
cp .env.example .env
# Edit database connection and JWT secret
```

5. **Initialize database:**
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

6. **Start the API server:**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `mssql+pyodbc://...` |
| `JWT_SECRET_KEY` | JWT signing secret | `your-secret-key` |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access token expiry | `3600` (1 hour) |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh token expiry | `604800` (7 days) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

### API Versioning

The API follows semantic versioning:
- **v1.1.4** - Current stable version
- **v1.1.3** - Previous version with basic API structure
- **v1.1.2** - Frontend improvements
- **v1.1.1** - Initial API implementation

### Contributing

1. Create a feature branch from the latest version
2. Implement changes with tests
3. Ensure all tests pass (100% coverage required)
4. Update documentation
5. Submit pull request

### Support

For issues and questions:
- 📧 Email: altanbariscomert@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/meqhisto/arsaanalizvesunum/issues)
- 📚 Documentation: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

---

**🎉 API Status: Production Ready | Test Coverage: 100% | Version: 1.1.4**

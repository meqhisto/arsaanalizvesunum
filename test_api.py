#!/usr/bin/env python3
"""
API Test Script
Bu script, oluşturulan REST API'nin temel endpoint'lerini test eder.
"""

import requests
import json
import sys
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:5000/api/v1"

# Test kullanıcı bilgileri - benzersiz email ile
import time
timestamp = int(time.time())
TEST_USER = {
    "email": f"apitest{timestamp}@example.com",
    "password": "TestPassword123",
    "ad": "Test",
    "soyad": "User",
    "telefon": "05551234567",
    "firma": "Test Company"
}

# Global token storage
access_token = None
refresh_token = None

def print_response(response, title="Response"):
    """API yanıtını güzel bir şekilde yazdırır."""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        print(f"Body: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Body: {response.text}")
    print(f"{'='*50}\n")

def get_auth_headers():
    """Authorization header'ını döner."""
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}

def test_api_info():
    """API bilgi endpoint'ini test eder."""
    print("🔍 Testing API Info...")
    response = requests.get(f"{BASE_URL.replace('/v1', '')}/")
    print_response(response, "API Info")
    return response.status_code == 200

def test_health_check():
    """Health check endpoint'ini test eder."""
    print("🏥 Testing Health Check...")
    response = requests.get(f"{BASE_URL.replace('/v1', '')}/health")
    print_response(response, "Health Check")
    return response.status_code == 200

def test_user_registration():
    """Kullanıcı kaydı endpoint'ini test eder."""
    print("📝 Testing User Registration...")
    response = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
    print_response(response, "User Registration")
    
    if response.status_code == 201:
        data = response.json()
        global access_token, refresh_token
        access_token = data.get("data", {}).get("access_token")
        refresh_token = data.get("data", {}).get("refresh_token")
        return True
    return False

def test_user_login():
    """Kullanıcı girişi endpoint'ini test eder."""
    print("🔐 Testing User Login...")
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_response(response, "User Login")
    
    if response.status_code == 200:
        data = response.json()
        global access_token, refresh_token
        access_token = data.get("data", {}).get("access_token")
        refresh_token = data.get("data", {}).get("refresh_token")
        return True
    return False

def test_user_profile():
    """Kullanıcı profili endpoint'ini test eder."""
    print("👤 Testing User Profile...")
    response = requests.get(f"{BASE_URL}/users/profile", headers=get_auth_headers())
    print_response(response, "User Profile")
    return response.status_code == 200

def test_create_analysis():
    """Analiz oluşturma endpoint'ini test eder."""
    print("📊 Testing Create Analysis...")
    analysis_data = {
        "il": "İstanbul",
        "ilce": "Kadıköy",
        "mahalle": "Moda",
        "metrekare": 1000.0,
        "fiyat": 5000000.0,
        "imar_durumu": "Konut",
        "taks": 0.4,
        "kaks": 1.2,
        "notlar": "Test analizi"
    }
    response = requests.post(f"{BASE_URL}/analysis", json=analysis_data, headers=get_auth_headers())
    print_response(response, "Create Analysis")
    
    if response.status_code == 201:
        return response.json().get("data", {}).get("id")
    return None

def test_list_analyses():
    """Analiz listesi endpoint'ini test eder."""
    print("📋 Testing List Analyses...")
    response = requests.get(f"{BASE_URL}/analysis", headers=get_auth_headers())
    print_response(response, "List Analyses")
    return response.status_code == 200

def test_create_contact():
    """Kişi oluşturma endpoint'ini test eder."""
    print("👥 Testing Create Contact...")
    import time
    timestamp = int(time.time())
    contact_data = {
        "ad": "Ahmet",
        "soyad": "Yılmaz",
        "email": f"ahmet{timestamp}@example.com",
        "telefon": "05551234567",
        "status": "Lead",
        "notlar": "Test kişisi"
    }
    response = requests.post(f"{BASE_URL}/crm/contacts", json=contact_data, headers=get_auth_headers())
    print_response(response, "Create Contact")
    
    if response.status_code == 201:
        return response.json().get("data", {}).get("id")
    return None

def test_list_contacts():
    """Kişi listesi endpoint'ini test eder."""
    print("📞 Testing List Contacts...")
    response = requests.get(f"{BASE_URL}/crm/contacts", headers=get_auth_headers())
    print_response(response, "List Contacts")
    return response.status_code == 200

def test_create_portfolio():
    """Portfolio oluşturma endpoint'ini test eder."""
    print("📁 Testing Create Portfolio...")
    portfolio_data = {
        "title": "Test Portfolio",
        "description": "Bu bir test portfolyosudur",
        "visibility": "private"
    }
    response = requests.post(f"{BASE_URL}/portfolio", json=portfolio_data, headers=get_auth_headers())
    print_response(response, "Create Portfolio")
    
    if response.status_code == 201:
        return response.json().get("data", {}).get("id")
    return None

def test_crm_stats():
    """CRM istatistikleri endpoint'ini test eder."""
    print("📈 Testing CRM Stats...")
    response = requests.get(f"{BASE_URL}/crm/stats", headers=get_auth_headers())
    print_response(response, "CRM Stats")
    return response.status_code == 200

def test_analysis_stats():
    """Analiz istatistikleri endpoint'ini test eder."""
    print("📊 Testing Analysis Stats...")
    response = requests.get(f"{BASE_URL}/analysis/stats", headers=get_auth_headers())
    print_response(response, "Analysis Stats")
    return response.status_code == 200

def test_token_refresh():
    """Token yenileme endpoint'ini test eder."""
    print("🔄 Testing Token Refresh...")
    if not refresh_token:
        print("❌ No refresh token available")
        return False
    
    headers = {"Authorization": f"Bearer {refresh_token}"}
    response = requests.post(f"{BASE_URL}/auth/refresh", headers=headers)
    print_response(response, "Token Refresh")
    
    if response.status_code == 200:
        data = response.json()
        global access_token
        access_token = data.get("data", {}).get("access_token")
        return True
    return False

def test_logout():
    """Çıkış endpoint'ini test eder."""
    print("🚪 Testing Logout...")
    response = requests.post(f"{BASE_URL}/auth/logout", headers=get_auth_headers())
    print_response(response, "Logout")
    return response.status_code == 200

def run_all_tests():
    """Tüm testleri çalıştırır."""
    print("🚀 Starting API Tests...")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now()}")
    
    tests = [
        ("API Info", test_api_info),
        ("Health Check", test_health_check),
        ("User Registration", test_user_registration),
        ("User Login", test_user_login),
        ("User Profile", test_user_profile),
        ("Create Analysis", test_create_analysis),
        ("List Analyses", test_list_analyses),
        ("Create Contact", test_create_contact),
        ("List Contacts", test_list_contacts),
        ("Create Portfolio", test_create_portfolio),
        ("CRM Stats", test_crm_stats),
        ("Analysis Stats", test_analysis_stats),
        ("Token Refresh", test_token_refresh),
        ("Logout", test_logout)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            results.append((test_name, result))
            print(f"{status} {test_name}")
        except Exception as e:
            print(f"❌ ERROR {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Sonuçları özetle
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

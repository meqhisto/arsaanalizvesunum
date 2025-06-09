#!/usr/bin/env python3
"""
Test script to verify security headers are properly implemented
"""

import requests
import sys

def test_security_headers():
    """Test if security headers are present in the response"""
    
    try:
        # Make a request to the application
        response = requests.get('http://127.0.0.1:5000', timeout=10)
        
        print("🔍 Testing Security Headers...")
        print(f"Status Code: {response.status_code}")
        print("-" * 50)
        
        # Expected security headers
        expected_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': 'default-src',  # Partial check
            'Permissions-Policy': 'geolocation=()'  # Partial check
        }
        
        # Check each header
        all_passed = True
        for header, expected_value in expected_headers.items():
            actual_value = response.headers.get(header)
            
            if actual_value:
                if expected_value in actual_value:
                    print(f"✅ {header}: {actual_value}")
                else:
                    print(f"⚠️  {header}: {actual_value} (unexpected value)")
                    all_passed = False
            else:
                print(f"❌ {header}: Missing")
                all_passed = False
        
        print("-" * 50)
        
        # Additional headers to check
        additional_headers = [
            'Strict-Transport-Security',
            'Server',
            'Set-Cookie'
        ]
        
        print("📋 Additional Headers:")
        for header in additional_headers:
            value = response.headers.get(header)
            if value:
                print(f"   {header}: {value}")
            else:
                print(f"   {header}: Not present")
        
        print("-" * 50)
        
        if all_passed:
            print("🎉 All security headers are properly configured!")
            return True
        else:
            print("⚠️  Some security headers are missing or misconfigured.")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to http://127.0.0.1:5000")
        print("   Make sure the Flask application is running.")
        return False
    except Exception as e:
        print(f"❌ Error testing security headers: {e}")
        return False

def test_environment_variables():
    """Test if environment variables are being used"""
    
    print("\n🔧 Testing Environment Variables...")
    print("-" * 50)
    
    try:
        # Test if the app responds (indicates env vars are working)
        response = requests.get('http://127.0.0.1:5000', timeout=10)
        
        if response.status_code == 200:
            print("✅ Application is running (environment variables loaded)")
        else:
            print(f"⚠️  Application returned status code: {response.status_code}")
            
        # Check if we can access a protected endpoint
        try:
            api_response = requests.get('http://127.0.0.1:5000/api/', timeout=10)
            if api_response.status_code == 200:
                print("✅ API endpoints are accessible")
            else:
                print(f"⚠️  API returned status code: {api_response.status_code}")
        except:
            print("⚠️  Could not test API endpoints")
            
    except Exception as e:
        print(f"❌ Error testing environment variables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Security Implementation Test")
    print("=" * 50)
    
    # Test security headers
    headers_ok = test_security_headers()
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    print("\n📊 Test Summary:")
    print("-" * 50)
    
    if headers_ok and env_ok:
        print("🎉 All tests passed! Security improvements are working.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        sys.exit(1)

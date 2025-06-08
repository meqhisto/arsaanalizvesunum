#!/usr/bin/env python3
"""
Test script to verify that the /login route now properly redirects to /auth/login
"""

import requests
import sys

def test_login_redirect():
    """Test that /login redirects to /auth/login"""
    try:
        # Test the redirect
        response = requests.get('http://localhost:5000/login', allow_redirects=False)
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if '/auth/login' in location:
                print("✅ SUCCESS: /login correctly redirects to /auth/login")
                return True
            else:
                print(f"❌ FAIL: /login redirects to {location}, expected /auth/login")
                return False
        else:
            print(f"❌ FAIL: Expected 302 redirect, got {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FAIL: Could not connect to Flask app. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False

def test_auth_login_works():
    """Test that /auth/login works properly"""
    try:
        response = requests.get('http://localhost:5000/auth/login')
        
        if response.status_code == 200:
            if 'Giriş Yap' in response.text or 'login' in response.text.lower():
                print("✅ SUCCESS: /auth/login returns login page")
                return True
            else:
                print("❌ FAIL: /auth/login doesn't return login page")
                return False
        else:
            print(f"❌ FAIL: /auth/login returned {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FAIL: Could not connect to Flask app. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing login route fix...")
    print("=" * 50)
    
    # Test both routes
    test1 = test_login_redirect()
    test2 = test_auth_login_works()
    
    print("=" * 50)
    if test1 and test2:
        print("🎉 All tests passed! The login route fix is working.")
        sys.exit(0)
    else:
        print("💥 Some tests failed. Check the Flask application.")
        sys.exit(1)

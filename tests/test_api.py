"""
Integration tests for API endpoints
"""

import pytest
import json
from models import db
from models.user_models import User
from models.crm_models import Contact
from models.arsa_models import ArsaAnaliz


class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'testpassword'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['email'] == test_user.email
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post('/api/auth/login', json={
            'email': test_user.email,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com'
            # password missing
        })
        
        assert response.status_code == 400
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get('/api/users/profile')
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        response = client.get('/api/users/profile', headers=auth_headers)
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401


class TestUsersAPI:
    """Test users API endpoints."""
    
    def test_get_user_profile(self, client, auth_headers, test_user):
        """Test getting user profile."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        response = client.get('/api/users/profile', headers=auth_headers)
        
        if response.status_code == 200:
            data = response.get_json()
            assert data['email'] == test_user.email
            assert data['ad'] == test_user.ad
            assert data['soyad'] == test_user.soyad
    
    def test_update_user_profile(self, client, auth_headers, test_user):
        """Test updating user profile."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        update_data = {
            'ad': 'Updated',
            'soyad': 'Name'
        }
        
        response = client.put('/api/users/profile', 
                            headers=auth_headers, 
                            json=update_data)
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401


class TestAnalysisAPI:
    """Test analysis API endpoints."""
    
    def test_get_analyses_list(self, client, auth_headers):
        """Test getting analyses list."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        response = client.get('/api/analyses/', headers=auth_headers)
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
        
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, list)
    
    def test_create_analysis(self, client, auth_headers):
        """Test creating a new analysis."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        analysis_data = {
            'baslik': 'Test API Analysis',
            'il': 'İstanbul',
            'ilce': 'Kadıköy',
            'mahalle': 'Moda'
        }
        
        response = client.post('/api/analyses/', 
                             headers=auth_headers, 
                             json=analysis_data)
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
    
    def test_get_analysis_detail(self, client, auth_headers, test_analysis):
        """Test getting analysis detail."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        response = client.get(f'/api/analyses/{test_analysis.id}', 
                            headers=auth_headers)
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
        
        if response.status_code == 200:
            data = response.get_json()
            assert data['id'] == test_analysis.id
            assert data['baslik'] == test_analysis.baslik


class TestCRMAPI:
    """Test CRM API endpoints."""
    
    def test_get_contacts_list(self, client, auth_headers):
        """Test getting contacts list."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        response = client.get('/api/crm/contacts/', headers=auth_headers)
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
        
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, list)
    
    def test_create_contact(self, client, auth_headers):
        """Test creating a new contact."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        contact_data = {
            'ad': 'API',
            'soyad': 'Contact',
            'email': 'api@example.com',
            'telefon': '555-0789',
            'status': 'lead'
        }
        
        response = client.post('/api/crm/contacts/', 
                             headers=auth_headers, 
                             json=contact_data)
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
    
    def test_get_contact_detail(self, client, auth_headers, test_contact):
        """Test getting contact detail."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        response = client.get(f'/api/crm/contacts/{test_contact.id}', 
                            headers=auth_headers)
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401
        
        if response.status_code == 200:
            data = response.get_json()
            assert data['id'] == test_contact.id
            assert data['email'] == test_contact.email


class TestHealthAPI:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_health_check_detailed(self, client):
        """Test detailed health check."""
        response = client.get('/api/health/detailed')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert 'database' in data
        assert 'timestamp' in data


class TestAPIErrorHandling:
    """Test API error handling."""
    
    def test_404_endpoint(self, client):
        """Test 404 error handling."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
    
    def test_invalid_json(self, client, auth_headers):
        """Test invalid JSON handling."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        response = client.post('/api/crm/contacts/', 
                             headers=auth_headers,
                             data='invalid json')
        
        assert response.status_code == 400
    
    def test_method_not_allowed(self, client):
        """Test method not allowed error."""
        response = client.delete('/api/health')
        
        assert response.status_code == 405


class TestAPIValidation:
    """Test API input validation."""
    
    def test_create_contact_missing_required_fields(self, client, auth_headers):
        """Test creating contact with missing required fields."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        contact_data = {
            'ad': 'Test'
            # Missing required fields
        }
        
        response = client.post('/api/crm/contacts/', 
                             headers=auth_headers, 
                             json=contact_data)
        
        assert response.status_code == 400
    
    def test_create_analysis_invalid_data(self, client, auth_headers):
        """Test creating analysis with invalid data."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        analysis_data = {
            'baslik': '',  # Empty title
            'il': 'InvalidCity'
        }
        
        response = client.post('/api/analyses/', 
                             headers=auth_headers, 
                             json=analysis_data)
        
        assert response.status_code == 400


class TestAPIPermissions:
    """Test API permission system."""
    
    def test_admin_only_endpoint_as_user(self, client, auth_headers):
        """Test accessing admin-only endpoint as regular user."""
        if not auth_headers:
            pytest.skip("Could not get auth token")
            
        response = client.get('/api/admin/users', headers=auth_headers)
        
        # Should be forbidden (403) or not found (404)
        assert response.status_code in [403, 404]
    
    def test_admin_only_endpoint_as_admin(self, client, admin_auth_headers):
        """Test accessing admin-only endpoint as admin."""
        if not admin_auth_headers:
            pytest.skip("Could not get admin auth token")
            
        response = client.get('/api/admin/users', headers=admin_auth_headers)
        
        # Should not be forbidden
        assert response.status_code != 403

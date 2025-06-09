"""
Test configuration and fixtures for the Flask application
"""

import os
import pytest
import tempfile
from app import create_app
from models import db
from models.user_models import User, Office
from models.crm_models import Contact, Task, Deal
from models.arsa_models import ArsaAnaliz
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""

    # Use in-memory SQLite database for testing
    test_db_uri = 'sqlite:///:memory:'

    # Set test environment variables
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
    os.environ['DATABASE_URL'] = test_db_uri
    os.environ['FLASK_ENV'] = 'testing'

    # Create the app with testing config
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": test_db_uri,
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        "LOGIN_DISABLED": False,
        "SERVER_NAME": "localhost:5000",  # Fix URL generation in tests
        "APPLICATION_ROOT": "/",
        "PREFERRED_URL_SCHEME": "http"
    })

    # Create the database and the database table
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def test_office(app):
    """Create a test office."""
    with app.app_context():
        office = Office(
            name="Test Ofis",
            address="Test Adres",
            phone="555-0123"
        )
        db.session.add(office)
        db.session.commit()

        # Return the office object
        return office


@pytest.fixture
def test_user(app):
    """Create a test user with office."""
    with app.app_context():
        # Create office first
        office = Office(
            name="Test Ofis",
            address="Test Adres",
            phone="555-0123"
        )
        db.session.add(office)
        db.session.flush()  # Get ID without committing

        # Create user
        user = User(
            ad="Test",
            soyad="User",
            email="test@example.com",
            password_hash=generate_password_hash("testpassword"),
            role="danisman",
            office_id=office.id
        )
        db.session.add(user)
        db.session.commit()

        # Return the user object
        return user


@pytest.fixture
def test_admin_user(app):
    """Create a test admin user with office."""
    with app.app_context():
        # Create office first
        office = Office(
            name="Admin Ofis",
            address="Admin Adres",
            phone="555-0456"
        )
        db.session.add(office)
        db.session.flush()  # Get ID without committing

        # Create admin user
        admin = User(
            ad="Admin",
            soyad="User",
            email="admin@example.com",
            password_hash=generate_password_hash("adminpassword"),
            role="superadmin",
            office_id=office.id
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def test_broker_user(app, test_office):
    """Create a test broker user."""
    with app.app_context():
        broker = User(
            ad="Broker",
            soyad="User",
            email="broker@example.com",
            password_hash=generate_password_hash("brokerpassword"),
            role="broker",
            office_id=test_office.id
        )
        db.session.add(broker)
        db.session.commit()
        return broker


# test_contact and test_analysis fixtures removed - tests now create their own data


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for API requests."""
    # Login to get JWT token
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',  # test_user fixture'ının email'i
        'password': 'testpassword'
    })

    if response.status_code == 200:
        data = response.get_json()
        token = data['data']['access_token']
        return {'Authorization': f'Bearer {token}'}
    else:
        return {}


@pytest.fixture
def admin_auth_headers(client, test_admin_user):
    """Get admin authentication headers for API requests."""
    # Login to get JWT token
    response = client.post('/api/v1/auth/login', json={
        'email': 'admin@example.com',  # test_admin_user fixture'ının email'i
        'password': 'adminpassword'
    })

    if response.status_code == 200:
        data = response.get_json()
        token = data['data']['access_token']
        return {'Authorization': f'Bearer {token}'}
    else:
        return {}


@pytest.fixture
def logged_in_user(client, test_user):
    """Log in a test user for session-based tests."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return test_user


@pytest.fixture
def logged_in_admin(client, test_admin_user):
    """Log in an admin user for session-based tests."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_admin_user.id)
        sess['_fresh'] = True
    return test_admin_user


# Test data factories
class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def create(app, office_id, **kwargs):
        defaults = {
            'ad': 'Test',
            'soyad': 'User',
            'email': 'test@example.com',
            'password_hash': generate_password_hash('testpassword'),
            'role': 'danisman',
            'office_id': office_id
        }
        defaults.update(kwargs)
        
        with app.app_context():
            user = User(**defaults)
            db.session.add(user)
            db.session.commit()
            return user


class ContactFactory:
    """Factory for creating test contacts."""
    
    @staticmethod
    def create(app, user_id, **kwargs):
        defaults = {
            'ad': 'Test',
            'soyad': 'Contact',
            'email': 'contact@example.com',
            'telefon': '555-0123',
            'user_id': user_id,
            'status': 'lead'
        }
        defaults.update(kwargs)
        
        with app.app_context():
            contact = Contact(**defaults)
            db.session.add(contact)
            db.session.commit()
            return contact


class AnalysisFactory:
    """Factory for creating test analyses."""
    
    @staticmethod
    def create(app, user_id, **kwargs):
        defaults = {
            'baslik': 'Test Analiz',
            'il': 'İstanbul',
            'ilce': 'Kadıköy',
            'mahalle': 'Test Mahalle',
            'user_id': user_id,
            'durum': 'tamamlandi'
        }
        defaults.update(kwargs)
        
        with app.app_context():
            analysis = ArsaAnaliz(**defaults)
            db.session.add(analysis)
            db.session.commit()
            return analysis

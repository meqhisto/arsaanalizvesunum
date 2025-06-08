import pytest
from app import create_app
from models import db
from models.user_models import User

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Test kullanıcı ekle
            user = User(ad='testuser', email='test@example.com')
            user.set_password('123456')
            db.session.add(user)
            db.session.commit()
        yield client

def login(client, username, password):
    return client.post('/auth/login', data={
        'email': username,
        'password': password
    }, follow_redirects=True)

def test_index_page(client):
    # Önce giriş yap
    login(client, 'test@example.com', '123456')
    response = client.get('/index')
    assert response.status_code == 200
    assert b'Ana Sayfa' in response.data

def test_check_reminders_endpoint(client):
    login(client, 'test@example.com', '123456')
    response = client.get('/crm/tasks/check-reminders')
    assert response.status_code == 200
    assert b'reminders' in response.data
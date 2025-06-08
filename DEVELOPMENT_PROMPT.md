# 🚀 Arsa Analiz ve Sunum Platformu - Kapsamlı Geliştirme Rehberi

Bu dokümant, "Arsa Analiz ve Sunum Platformu" uygulamasını sıfırdan yeniden oluşturmak veya genişletmek için gereken tüm teknik detayları içerir.

## 📋 Proje Genel Bakış

### Uygulama Tanımı
Gayrimenkul sektörü için geliştirilmiş kapsamlı bir Flask web uygulaması. Arsa analizi, CRM yönetimi, portföy takibi ve profesyonel rapor üretimi özelliklerini tek platformda birleştirir.

### Temel Özellikler
- **Arsa Analizi:** ML tabanlı fiyat tahmini, SWOT analizi, TAKS/KAKS hesaplamaları
- **CRM Sistemi:** Müşteri yönetimi, satış pipeline'ı, görev takibi
- **Portföy Yönetimi:** Arsa gruplandırma, performans analizi
- **Rapor Sistemi:** Word/PDF/PowerPoint otomatik rapor üretimi
- **REST API:** Comprehensive API with JWT authentication
- **Multi-tenant:** Ofis bazlı kullanıcı yönetimi

## 🏗️ Teknik Mimari

### Backend Architecture

#### Core Framework
```python
# Flask Application Structure
Flask 2.3.3
├── Blueprint-based modular architecture
├── SQLAlchemy 2.0.41 ORM
├── Flask-Migrate for database migrations
├── Flask-Login for session management
├── Flask-JWT-Extended for API authentication
└── Marshmallow for API serialization
```

#### Database Design
```sql
-- Core Tables Structure
Users (id, email, password_hash, role, office_id, manager_id)
├── Offices (id, name, address, phone, logo_path)
├── ArsaAnaliz (id, user_id, office_id, il, ilce, metrekare, fiyat, swot_analizi)
├── CRM_Contacts (id, user_id, office_id, ad, soyad, email, telefon, company_id)
├── CRM_Companies (id, user_id, name, industry, website)
├── CRM_Deals (id, user_id, contact_id, title, value, stage, probability)
├── CRM_Tasks (id, user_id, contact_id, deal_id, title, priority, status)
├── CRM_Interactions (id, user_id, contact_id, type, notes, date)
├── Portfolios (id, user_id, title, description, visibility)
└── Portfolio_Arsalar (portfolio_id, arsa_id, added_at)
```

#### API Structure
```
/api/v1/
├── /auth (login, register, refresh, logout)
├── /users (profile, change-password, list)
├── /analysis (CRUD operations, stats, bulk)
├── /crm/contacts (CRUD, search, filter)
├── /crm/companies (CRUD, search)
├── /crm/deals (CRUD, stage updates, pipeline)
├── /crm/tasks (CRUD, status updates)
├── /crm/interactions (CRUD, timeline)
├── /portfolio (CRUD, add/remove analyses)
└── /media (upload, download, delete)
```

### Frontend Architecture

#### Technology Stack
```javascript
// Frontend Build System
Webpack 5.89.0
├── Bootstrap 5.3.6 (UI Framework)
├── Chart.js 4.4.0 (Data Visualization)
├── Axios 1.6.0 (HTTP Client)
├── SCSS/Sass (Styling)
├── Babel (ES6+ Transpilation)
└── ESLint + Prettier (Code Quality)
```

#### Template Structure
```
templates/
├── base.html (Main layout with navigation)
├── auth/ (Login, register, forgot password)
├── analysis/ (Analysis forms, list, detail)
├── crm/ (Contacts, companies, deals, tasks)
├── portfolio/ (Portfolio management)
└── components/ (Reusable UI components)
```

## 🔧 Detaylı Implementasyon Rehberi

### 1. Proje Kurulumu

#### Environment Setup
```bash
# Project initialization
mkdir arsaanalizvesunum && cd arsaanalizvesunum
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Core dependencies
pip install flask==2.3.3 sqlalchemy==2.0.41 flask-sqlalchemy==3.1.1
pip install flask-migrate==4.0.5 flask-login==0.6.3 flask-jwt-extended==4.7.1
pip install marshmallow==4.0.0 marshmallow-sqlalchemy==1.4.2
pip install flask-cors==4.0.0 flasgger==0.9.7.1
pip install pyodbc==5.2.0  # SQL Server driver

# ML and data processing
pip install xgboost==3.0.2 scikit-learn==1.7.0 pandas==2.3.0 numpy==2.3.0

# Document generation
pip install python-docx==1.1.2 reportlab==4.4.1 python-pptx==1.0.2
pip install pillow==11.2.1 qrcode==8.2 xlsxwriter==3.2.3

# Frontend build tools
npm init -y
npm install webpack webpack-cli webpack-dev-server
npm install bootstrap@5.3.6 @popperjs/core chart.js axios
npm install sass sass-loader css-loader style-loader mini-css-extract-plugin
```

#### Application Factory Pattern
```python
# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_cors import CORS

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://...'
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Register blueprints
    from blueprints.auth_bp import auth_bp
    from blueprints.main_bp import main_bp
    from blueprints.analysis_bp import analysis_bp
    from blueprints.crm_bp import crm_bp
    from blueprints.portfolio_bp import portfolio_bp
    from blueprints.api.api_bp import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(crm_bp, url_prefix='/crm')
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
```

### 2. Database Models

#### User Management Models
```python
# models/user_models.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    ad = db.Column(db.String(50))
    soyad = db.Column(db.String(50))
    telefon = db.Column(db.String(20))
    firma = db.Column(db.String(100))
    unvan = db.Column(db.String(100))
    role = db.Column(db.String(20), default='danisman')  # superadmin, broker, danisman, calisan
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    failed_attempts = db.Column(db.Integer, default=0)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Office(db.Model):
    __tablename__ = "offices"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(30))
    logo_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
```

#### Analysis Models
```python
# models/arsa_models.py
class ArsaAnaliz(db.Model):
    __tablename__ = "arsa_analizleri"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.id"))
    
    # Location data
    il = db.Column(db.String(50), nullable=False)
    ilce = db.Column(db.String(50), nullable=False)
    mahalle = db.Column(db.String(100), nullable=False)
    ada = db.Column(db.String(20))
    parsel = db.Column(db.String(20))
    koordinatlar = db.Column(db.String(100))
    
    # Property data
    metrekare = db.Column(db.Numeric(10, 2), nullable=False)
    imar_durumu = db.Column(db.String(50))
    taks = db.Column(db.Numeric(4, 2))
    kaks = db.Column(db.Numeric(4, 2))
    fiyat = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Analysis data
    swot_analizi = db.Column(db.JSON)
    altyapi = db.Column(db.JSON)
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="analizler")
    office = db.relationship("Office", backref="analizler")
```

#### CRM Models
```python
# models/crm_models.py
class Contact(db.Model):
    __tablename__ = "crm_contacts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.id"))
    company_id = db.Column(db.Integer, db.ForeignKey("crm_companies.id"))
    
    ad = db.Column(db.String(50), nullable=False)
    soyad = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(20))
    pozisyon = db.Column(db.String(100))
    adres = db.Column(db.Text)
    notlar = db.Column(db.Text)
    status = db.Column(db.String(20), default="Lead")  # Lead, Prospect, Customer
    kaynak = db.Column(db.String(50))  # Web, Referral, Cold Call, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Deal(db.Model):
    __tablename__ = "crm_deals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("crm_companies.id"))
    
    title = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Numeric(15, 2), default=0.00)
    currency = db.Column(db.String(10), default="TRY")
    stage = db.Column(db.String(50), default="Potansiyel")  # Potansiyel, Görüşme, Teklif, Müzakere, Kazanıldı, Kaybedildi
    expected_close_date = db.Column(db.Date)
    probability = db.Column(db.Integer, default=0)  # 0-100
    notes = db.Column(db.Text)
```

### 3. API Implementation

#### Authentication System
```python
# blueprints/api/v1/auth.py
from flask_jwt_extended import create_access_token, create_refresh_token

@auth_api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password) and user.is_active:
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return success_response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': UserSchema().dump(user)
        })
    
    return unauthorized_response("Invalid credentials")
```

#### CRUD Operations Pattern
```python
# blueprints/api/v1/analysis.py
@analysis_api.route('', methods=['GET'])
@jwt_required()
def get_analyses():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = ArsaAnaliz.query.filter_by(user_id=user_id)
    
    # Filtering
    if request.args.get('il'):
        query = query.filter(ArsaAnaliz.il == request.args.get('il'))
    
    paginated = query.paginate(page=page, per_page=per_page)
    
    return success_response(
        data=ArsaAnalizSchema(many=True).dump(paginated.items),
        meta={'pagination': pagination_meta(paginated)}
    )

@analysis_api.route('', methods=['POST'])
@jwt_required()
def create_analysis():
    user_id = get_jwt_identity()
    schema = ArsaAnalizCreateSchema()
    
    try:
        data = schema.load(request.get_json())
        data['user_id'] = user_id
        
        analysis = ArsaAnaliz(**data)
        db.session.add(analysis)
        db.session.commit()
        
        return success_response(
            data=ArsaAnalizSchema().dump(analysis),
            message="Analysis created successfully",
            status_code=201
        )
    except ValidationError as e:
        return validation_error_response(e.messages)
```

### 4. Machine Learning Integration

#### Price Prediction Model
```python
# modules/fiyat_tahmini.py
import xgboost as xgb
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

class FiyatTahminiModel:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.feature_columns = [
            'il', 'ilce', 'metrekare', 'imar_durumu', 
            'taks', 'kaks', 'konum_skoru', 'ulasim_skoru'
        ]
    
    def prepare_data(self, df):
        """Prepare data for training/prediction"""
        # Handle categorical variables
        categorical_cols = ['il', 'ilce', 'imar_durumu']
        
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col])
            else:
                df[col] = self.label_encoders[col].transform(df[col])
        
        return df[self.feature_columns]
    
    def train(self, training_data):
        """Train the XGBoost model"""
        X = self.prepare_data(training_data)
        y = training_data['fiyat']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        score = self.model.score(X_test, y_test)
        return score
    
    def predict(self, analysis_data):
        """Predict price for new analysis"""
        if not self.model:
            raise ValueError("Model not trained")
        
        df = pd.DataFrame([analysis_data])
        X = self.prepare_data(df)
        
        prediction = self.model.predict(X)[0]
        return float(prediction)
```

### 5. Document Generation

#### Report Generation System
```python
# modules/document_generator.py
from docx import Document
from docx.shared import Inches
from reportlab.pdfgen import canvas
from pptx import Presentation

class ReportGenerator:
    def __init__(self, analysis_data, template_type="default"):
        self.analysis = analysis_data
        self.template_type = template_type
    
    def generate_word_report(self):
        """Generate Word document report"""
        doc = Document()
        
        # Title
        title = doc.add_heading(f'Arsa Analiz Raporu - {self.analysis.il}/{self.analysis.ilce}', 0)
        
        # Basic Information
        doc.add_heading('Temel Bilgiler', level=1)
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        info_data = [
            ('Lokasyon', f'{self.analysis.il}, {self.analysis.ilce}, {self.analysis.mahalle}'),
            ('Metrekare', f'{self.analysis.metrekare} m²'),
            ('İmar Durumu', self.analysis.imar_durumu),
            ('TAKS', f'{self.analysis.taks}'),
            ('KAKS', f'{self.analysis.kaks}'),
            ('Tahmini Değer', f'{self.analysis.fiyat:,.2f} TL')
        ]
        
        for key, value in info_data:
            row_cells = table.add_row().cells
            row_cells[0].text = key
            row_cells[1].text = str(value)
        
        # SWOT Analysis
        if self.analysis.swot_analizi:
            doc.add_heading('SWOT Analizi', level=1)
            swot = self.analysis.swot_analizi
            
            for category in ['Güçlü Yönler', 'Zayıf Yönler', 'Fırsatlar', 'Tehditler']:
                doc.add_heading(category, level=2)
                if category.lower().replace(' ', '_') in swot:
                    for item in swot[category.lower().replace(' ', '_')]:
                        doc.add_paragraph(f'• {item}', style='List Bullet')
        
        # Save document
        filename = f'arsa_analiz_{self.analysis.il}_{self.analysis.ilce}_{datetime.now().strftime("%Y%m%d%H%M%S")}.docx'
        doc.save(f'output/{filename}')
        
        return filename
    
    def generate_pdf_report(self):
        """Generate PDF report"""
        filename = f'arsa_analiz_{self.analysis.il}_{self.analysis.ilce}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
        
        c = canvas.Canvas(f'output/{filename}')
        width, height = c._pagesize
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f'Arsa Analiz Raporu - {self.analysis.il}/{self.analysis.ilce}')
        
        # Content
        y_position = height - 100
        c.setFont("Helvetica", 12)
        
        content = [
            f'Lokasyon: {self.analysis.il}, {self.analysis.ilce}, {self.analysis.mahalle}',
            f'Metrekare: {self.analysis.metrekare} m²',
            f'İmar Durumu: {self.analysis.imar_durumu}',
            f'Tahmini Değer: {self.analysis.fiyat:,.2f} TL'
        ]
        
        for line in content:
            c.drawString(50, y_position, line)
            y_position -= 20
        
        c.save()
        return filename
```

### 6. Frontend Implementation

#### Modern JavaScript Structure
```javascript
// static/js/main.js
class AnalysisManager {
    constructor() {
        this.apiClient = new ApiClient();
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadAnalyses();
    }
    
    bindEvents() {
        document.getElementById('create-analysis-btn').addEventListener('click', () => {
            this.showCreateModal();
        });
        
        document.getElementById('analysis-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createAnalysis();
        });
    }
    
    async loadAnalyses() {
        try {
            const response = await this.apiClient.get('/api/v1/analysis');
            this.renderAnalysesList(response.data);
        } catch (error) {
            console.error('Error loading analyses:', error);
            this.showError('Analizler yüklenirken hata oluştu');
        }
    }
    
    async createAnalysis() {
        const formData = new FormData(document.getElementById('analysis-form'));
        const data = Object.fromEntries(formData);
        
        try {
            const response = await this.apiClient.post('/api/v1/analysis', data);
            this.hideCreateModal();
            this.loadAnalyses();
            this.showSuccess('Analiz başarıyla oluşturuldu');
        } catch (error) {
            this.showError('Analiz oluşturulurken hata oluştu');
        }
    }
}

class ApiClient {
    constructor() {
        this.baseURL = '/api/v1';
        this.token = localStorage.getItem('access_token');
    }
    
    async request(method, url, data = null) {
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            }
        };
        
        if (data) {
            config.body = JSON.stringify(data);
        }
        
        const response = await fetch(this.baseURL + url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    get(url) { return this.request('GET', url); }
    post(url, data) { return this.request('POST', url, data); }
    put(url, data) { return this.request('PUT', url, data); }
    delete(url) { return this.request('DELETE', url); }
}
```

### 7. Testing Strategy

#### Unit Testing Setup
```python
# tests/test_models.py
import pytest
from app import create_app, db
from models.user_models import User
from models.arsa_models import ArsaAnaliz

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user(app):
    user = User(email='test@example.com', ad='Test', soyad='User')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

def test_user_creation(app, user):
    assert user.email == 'test@example.com'
    assert user.check_password('password123')
    assert not user.check_password('wrongpassword')

def test_analysis_creation(app, user):
    analysis = ArsaAnaliz(
        user_id=user.id,
        il='İstanbul',
        ilce='Kadıköy',
        mahalle='Moda',
        metrekare=1000,
        fiyat=5000000
    )
    db.session.add(analysis)
    db.session.commit()
    
    assert analysis.id is not None
    assert analysis.user_id == user.id
```

#### API Testing
```python
# tests/test_api.py
def test_login_api(client):
    # Create test user
    user = User(email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    # Test login
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'refresh_token' in data

def test_create_analysis_api(client, auth_headers):
    response = client.post('/api/v1/analysis', 
        headers=auth_headers,
        json={
            'il': 'İstanbul',
            'ilce': 'Kadıköy',
            'mahalle': 'Moda',
            'metrekare': 1000,
            'fiyat': 5000000
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
```

## 🚀 Deployment ve Production

### Environment Configuration
```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Security Considerations
- JWT token expiration and refresh mechanism
- Rate limiting on API endpoints
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration for production
- HTTPS enforcement
- Environment variable management
- Database connection security

### Performance Optimization
- Database indexing strategy
- Query optimization
- Caching implementation (Redis)
- CDN for static assets
- Image optimization
- Bundle size optimization
- Lazy loading implementation

## 🔐 Security Implementation

### Authentication & Authorization
```python
# Security decorators
from functools import wraps
from flask_login import current_user

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@main_bp.route('/admin')
@role_required(['superadmin'])
def admin_dashboard():
    return render_template('admin/dashboard.html')
```

### Input Validation
```python
# Custom validators
from marshmallow import validates, ValidationError

class ArsaAnalizSchema(Schema):
    il = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    metrekare = fields.Decimal(required=True, validate=validate.Range(min=1))
    fiyat = fields.Decimal(required=True, validate=validate.Range(min=0))

    @validates('email')
    def validate_email(self, value):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError('Invalid email format')
```

### Rate Limiting
```python
# Rate limiting implementation
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login logic
    pass
```

## 📊 Advanced Features Implementation

### Real-time Notifications
```python
# WebSocket integration for real-time updates
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('join_room')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'User joined room {room}'}, room=room)

# Trigger notifications
def notify_deal_update(deal_id, user_id):
    socketio.emit('deal_updated', {
        'deal_id': deal_id,
        'message': 'Deal has been updated'
    }, room=f'user_{user_id}')
```

### Advanced Search & Filtering
```python
# Elasticsearch integration for advanced search
from elasticsearch import Elasticsearch

class SearchService:
    def __init__(self):
        self.es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

    def index_analysis(self, analysis):
        doc = {
            'id': analysis.id,
            'il': analysis.il,
            'ilce': analysis.ilce,
            'mahalle': analysis.mahalle,
            'metrekare': float(analysis.metrekare),
            'fiyat': float(analysis.fiyat),
            'created_at': analysis.created_at.isoformat()
        }
        self.es.index(index='analyses', id=analysis.id, body=doc)

    def search_analyses(self, query, filters=None):
        search_body = {
            'query': {
                'bool': {
                    'must': [
                        {'multi_match': {
                            'query': query,
                            'fields': ['il', 'ilce', 'mahalle']
                        }}
                    ]
                }
            }
        }

        if filters:
            search_body['query']['bool']['filter'] = []
            if 'price_range' in filters:
                search_body['query']['bool']['filter'].append({
                    'range': {
                        'fiyat': {
                            'gte': filters['price_range']['min'],
                            'lte': filters['price_range']['max']
                        }
                    }
                })

        return self.es.search(index='analyses', body=search_body)
```

### Caching Strategy
```python
# Redis caching implementation
import redis
from flask import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_key(prefix, *args):
    return f"{prefix}:{':'.join(map(str, args))}"

def cached_analysis_stats(user_id):
    key = cache_key('analysis_stats', user_id)
    cached = redis_client.get(key)

    if cached:
        return json.loads(cached)

    # Calculate stats
    stats = calculate_analysis_stats(user_id)

    # Cache for 1 hour
    redis_client.setex(key, 3600, json.dumps(stats))
    return stats
```

## 🧪 Testing & Quality Assurance

### Comprehensive Test Suite
```python
# Integration tests
class TestAnalysisAPI:
    def test_analysis_crud_workflow(self, client, auth_headers):
        # Create
        create_response = client.post('/api/v1/analysis',
            headers=auth_headers,
            json=self.sample_analysis_data
        )
        assert create_response.status_code == 201
        analysis_id = create_response.json['data']['id']

        # Read
        get_response = client.get(f'/api/v1/analysis/{analysis_id}',
            headers=auth_headers
        )
        assert get_response.status_code == 200

        # Update
        update_response = client.put(f'/api/v1/analysis/{analysis_id}',
            headers=auth_headers,
            json={'fiyat': 6000000}
        )
        assert update_response.status_code == 200

        # Delete
        delete_response = client.delete(f'/api/v1/analysis/{analysis_id}',
            headers=auth_headers
        )
        assert delete_response.status_code == 204

# Performance tests
def test_api_performance(client, auth_headers):
    import time

    start_time = time.time()
    response = client.get('/api/v1/analysis', headers=auth_headers)
    end_time = time.time()

    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Should respond within 1 second
```

### Load Testing
```python
# locustfile.py for load testing
from locust import HttpUser, task, between

class AnalysisUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def get_analyses(self):
        self.client.get("/api/v1/analysis", headers=self.headers)

    @task(1)
    def create_analysis(self):
        self.client.post("/api/v1/analysis",
            headers=self.headers,
            json={
                "il": "İstanbul",
                "ilce": "Kadıköy",
                "mahalle": "Moda",
                "metrekare": 1000,
                "fiyat": 5000000
            }
        )
```

## 🚀 DevOps & Deployment

### CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v1

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - name: Deploy to production
      run: |
        # Deployment script
        echo "Deploying to production..."
```

### Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://user:password@db:5432/arsaanaliz
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: arsaanaliz
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - web

volumes:
  postgres_data:
```

### Monitoring & Logging
```python
# Structured logging
import structlog
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
            'level': 'INFO'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = structlog.get_logger()

# Usage in application
@analysis_bp.route('/create', methods=['POST'])
def create_analysis():
    logger.info("Analysis creation started",
                user_id=current_user.id,
                request_id=request.headers.get('X-Request-ID'))
    try:
        # Analysis creation logic
        logger.info("Analysis created successfully",
                    analysis_id=analysis.id,
                    user_id=current_user.id)
    except Exception as e:
        logger.error("Analysis creation failed",
                     error=str(e),
                     user_id=current_user.id)
        raise
```

## 📈 Scalability Considerations

### Database Optimization
```sql
-- Essential indexes for performance
CREATE INDEX idx_arsa_user_il ON arsa_analizleri(user_id, il);
CREATE INDEX idx_arsa_created_at ON arsa_analizleri(created_at DESC);
CREATE INDEX idx_crm_contacts_user_status ON crm_contacts(user_id, status);
CREATE INDEX idx_crm_deals_user_stage ON crm_deals(user_id, stage);
CREATE INDEX idx_crm_tasks_user_status ON crm_tasks(user_id, status, priority);

-- Partitioning for large datasets
CREATE TABLE arsa_analizleri_2024 PARTITION OF arsa_analizleri
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### Microservices Architecture
```python
# Service separation example
# auth_service.py
class AuthService:
    def __init__(self):
        self.db = get_auth_db()

    def authenticate_user(self, email, password):
        # Authentication logic
        pass

    def generate_tokens(self, user_id):
        # Token generation
        pass

# analysis_service.py
class AnalysisService:
    def __init__(self):
        self.db = get_analysis_db()
        self.ml_service = MLService()

    def create_analysis(self, data):
        # Analysis creation with ML prediction
        predicted_price = self.ml_service.predict_price(data)
        data['predicted_price'] = predicted_price
        return self.db.create_analysis(data)

# API Gateway pattern
class APIGateway:
    def __init__(self):
        self.auth_service = AuthService()
        self.analysis_service = AnalysisService()
        self.crm_service = CRMService()

    def route_request(self, request):
        if request.path.startswith('/auth'):
            return self.auth_service.handle(request)
        elif request.path.startswith('/analysis'):
            return self.analysis_service.handle(request)
        elif request.path.startswith('/crm'):
            return self.crm_service.handle(request)
```

---

Bu kapsamlı rehber, enterprise-grade bir gayrimenkul analiz platformu geliştirmek için gereken tüm teknik detayları, best practice'leri ve scalability çözümlerini içerir. Modern web development standartlarına uygun, güvenli ve performanslı bir uygulama oluşturmak için gerekli tüm bilgiler sağlanmıştır.

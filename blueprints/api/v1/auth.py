# blueprints/api/v1/auth.py
from flask import Blueprint, request, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import secrets
import traceback

from models import db
from models.user_models import User
from ..schemas.user_schemas import (
    UserLoginSchema, UserRegistrationSchema, TokenResponseSchema,
    RefreshTokenSchema, PasswordResetRequestSchema, PasswordResetSchema,
    UserSchema
)
from ..utils.decorators import validate_json, log_api_call, handle_db_errors
from ..utils.responses import (
    success_response, error_response, validation_error_response,
    unauthorized_response, not_found_response
)

auth_v1 = Blueprint('auth_v1', __name__)


@auth_v1.route('/test-token', methods=['POST'])
@log_api_call
def test_token():
    """Test token creation with string identity"""
    try:
        # Test kullanıcısı
        user = User.query.filter_by(email='apitest@example.com').first()
        if not user:
            return error_response("Test user not found", 404)

        # String identity ile token oluştur
        test_token = create_access_token(identity=str(user.id))

        return success_response(
            data={
                'token': test_token,
                'user_id': str(user.id),
                'message': 'Token created with string identity'
            },
            message="Test token created successfully"
        )
    except Exception as e:
        return error_response(f"Token creation failed: {str(e)}", 500)

# Token blacklist (production'da Redis kullanılmalı)
blacklisted_tokens = set()


@auth_v1.route('/register', methods=['POST'])
@log_api_call
def register():
    """
    Kullanıcı kaydı
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: user
        description: User registration data
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - ad
            - soyad
          properties:
            email:
              type: string
              format: email
            password:
              type: string
              minLength: 8
            ad:
              type: string
              minLength: 2
            soyad:
              type: string
              minLength: 2
            telefon:
              type: string
            firma:
              type: string
            unvan:
              type: string
            adres:
              type: string
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              $ref: '#/definitions/TokenResponse'
      400:
        description: Validation error
      409:
        description: Email already exists
    """
    try:
        # JSON verilerini al
        data = request.get_json()
        if not data:
            return error_response("No JSON data provided", 400)

        # Temel validasyonlar
        required_fields = ['email', 'password', 'ad', 'soyad']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(f"Missing required field: {field}", 400)

        # Email benzersizlik kontrolü
        if User.query.filter_by(email=data['email']).first():
            return error_response("Email already exists", 409)

        # Parola uzunluk kontrolü
        if len(data['password']) < 8:
            return error_response("Password must be at least 8 characters long", 400)

        # Kullanıcı oluştur
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            ad=data['ad'],
            soyad=data['soyad'],
            telefon=data.get('telefon'),
            firma=data.get('firma'),
            unvan=data.get('unvan'),
            adres=data.get('adres'),
            role='danisman'  # Varsayılan rol
        )

        db.session.add(user)
        db.session.commit()

        # Token'ları oluştur
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )

        # Kullanıcı bilgilerini serialize et
        user_schema = UserSchema()
        user_data = user_schema.dump(user)

        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 86400,  # 24 saat
            'token_type': 'Bearer',
            'user': user_data
        }

        current_app.logger.info(f"New user registered: {user.email}")
        return success_response(
            data=response_data,
            message="User registered successfully",
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return error_response("Registration failed", 500)


@auth_v1.route('/login', methods=['POST'])
def login():
    """
    Kullanıcı girişi
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: credentials
        description: User login credentials
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
            password:
              type: string
            remember_me:
              type: boolean
              default: false
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              $ref: '#/definitions/TokenResponse'
      401:
        description: Invalid credentials
      423:
        description: Account locked
    """
    try:
        # JSON verilerini al
        data = request.get_json()
        current_app.logger.info(f"Raw request data: {data}")
        current_app.logger.info(f"Request headers: {dict(request.headers)}")
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Request content type: {request.content_type}")

        if not data:
            current_app.logger.error("No JSON data provided in request")
            return error_response("No JSON data provided", 400)

        current_app.logger.info(f"Login attempt for data: {data}")

        email = data.get('email')
        password = data.get('password')
        remember_me = data.get('remember_me', False)

        if not email or not password:
            current_app.logger.error(f"Missing email or password: email={email}, password={'***' if password else None}")
            return error_response("Email and password are required", 400)

        current_app.logger.info(f"Login attempt for email: {email}")

        # Kullanıcıyı bul
        user = User.query.filter_by(email=email).first()

        if not user:
            current_app.logger.warning(f"User not found: {email}")
            return unauthorized_response("Invalid email or password")

        current_app.logger.info(f"User found: {user.email}, active: {user.is_active}, failed_attempts: {user.failed_attempts}")

        # Hesap kilidi kontrolü
        if user.failed_attempts >= 5:
            current_app.logger.warning(f"Account locked: {email}")
            return error_response("Account locked due to too many failed attempts", 423)

        # Aktif kullanıcı kontrolü
        if not user.is_active:
            current_app.logger.warning(f"Account deactivated: {email}")
            return unauthorized_response("Account is deactivated")

        # Parola kontrolü
        password_check = user.check_password(password)
        current_app.logger.info(f"Password check result for {email}: {password_check}")

        if not password_check:
            # Başarısız deneme sayısını artır
            user.failed_attempts += 1
            db.session.commit()
            current_app.logger.warning(f"Invalid password for: {email}")
            return unauthorized_response("Invalid email or password")

        # Başarılı giriş - failed_attempts'i sıfırla
        user.failed_attempts = 0
        user.son_giris = datetime.utcnow()
        db.session.commit()

        # Token süreleri
        access_expires = timedelta(hours=24 if remember_me else 1)
        refresh_expires = timedelta(days=30 if remember_me else 7)

        # Token'ları oluştur
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=access_expires
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=refresh_expires
        )

        # Kullanıcı bilgilerini serialize et
        user_schema = UserSchema()
        user_data = user_schema.dump(user)

        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(access_expires.total_seconds()),
            'token_type': 'Bearer',
            'user': user_data
        }

        current_app.logger.info(f"User logged in: {user.email}")
        return success_response(
            data=response_data,
            message="Login successful"
        )

    except Exception as e:
        current_app.logger.error(f"Login endpoint error: {str(e)}")
        current_app.logger.error(f"Login endpoint traceback: {traceback.format_exc()}")
        return error_response("Login failed due to server error", 500)


@auth_v1.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@log_api_call
def refresh():
    """
    Token yenileme
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Token refreshed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: object
              properties:
                access_token:
                  type: string
                expires_in:
                  type: integer
                token_type:
                  type: string
      401:
        description: Invalid refresh token
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return unauthorized_response("User not found or inactive")
        
        # Yeni access token oluştur
        new_access_token = create_access_token(
            identity=str(current_user_id),
            expires_delta=timedelta(hours=1)
        )
        
        response_data = {
            'access_token': new_access_token,
            'expires_in': 3600,  # 1 saat
            'token_type': 'Bearer'
        }
        
        return success_response(
            data=response_data,
            message="Token refreshed successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return unauthorized_response("Token refresh failed")


@auth_v1.route('/logout', methods=['POST'])
@jwt_required()
@log_api_call
def logout():
    """
    Kullanıcı çıkışı
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Logout successful
      401:
        description: Invalid token
    """
    try:
        # Token'ı blacklist'e ekle
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        current_app.logger.info(f"User logged out: {get_jwt_identity()}")
        return success_response(message="Logout successful")
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return error_response("Logout failed", 500)


@auth_v1.route('/forgot-password', methods=['POST'])
@log_api_call
@handle_db_errors
@validate_json(PasswordResetRequestSchema)
def forgot_password(data):
    """
    Parola sıfırlama isteği
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: email
        description: User email for password reset
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email
    responses:
      200:
        description: Password reset email sent
      404:
        description: Email not found
    """
    email = data['email']
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Güvenlik için her zaman başarılı yanıt ver
        return success_response(
            message="If the email exists, a password reset link has been sent"
        )
    
    # Reset token oluştur
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    
    db.session.commit()
    
    # TODO: E-posta gönderme işlemi burada yapılacak
    current_app.logger.info(f"Password reset requested for: {email}")
    
    return success_response(
        message="If the email exists, a password reset link has been sent"
    )


@auth_v1.route('/reset-password', methods=['POST'])
@log_api_call
@handle_db_errors
@validate_json(PasswordResetSchema)
def reset_password(data):
    """
    Parola sıfırlama
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: reset_data
        description: Password reset data
        required: true
        schema:
          type: object
          required:
            - token
            - new_password
            - confirm_password
          properties:
            token:
              type: string
            new_password:
              type: string
              minLength: 8
            confirm_password:
              type: string
    responses:
      200:
        description: Password reset successful
      400:
        description: Invalid or expired token
    """
    token = data['token']
    new_password = data['new_password']
    
    # Token'ı kontrol et
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        return error_response("Invalid or expired reset token", 400)
    
    # Parolayı güncelle
    user.password_hash = generate_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.failed_attempts = 0
    
    db.session.commit()
    
    current_app.logger.info(f"Password reset successful for: {user.email}")
    return success_response(message="Password reset successful")


# JWT token blacklist kontrolü
@auth_v1.before_app_request
def check_if_token_revoked():
    """Token'ın blacklist'te olup olmadığını kontrol eder."""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        verify_jwt_in_request(optional=True)
        jti = get_jwt().get('jti')
        if jti in blacklisted_tokens:
            return unauthorized_response("Token has been revoked")
    except:
        pass

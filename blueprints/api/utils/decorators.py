# blueprints/api/utils/decorators.py
from functools import wraps
from flask import request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from marshmallow import ValidationError
from .responses import validation_error_response, unauthorized_response, forbidden_response
from models.user_models import User
from models import db


def validate_json(schema_class):
    """JSON verilerini Marshmallow şeması ile doğrular."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()
                data = schema.load(request.get_json() or {})
                return f(data, *args, **kwargs)
            except ValidationError as err:
                return validation_error_response(err.messages)
        return decorated_function
    return decorator


def jwt_required_api():
    """API için JWT token doğrulaması yapar."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                return f(*args, **kwargs)
            except Exception as e:
                return unauthorized_response("Invalid or missing token")
        return decorated_function
    return decorator


def get_current_user():
    """JWT token'dan mevcut kullanıcıyı getirir."""
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        return User.query.get(user_id)
    except:
        return None


def role_required(*allowed_roles):
    """Belirli rollere sahip kullanıcılar için erişim kontrolü."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                
                if not user:
                    return unauthorized_response("User not found")
                
                if user.role not in allowed_roles:
                    return forbidden_response("Insufficient permissions")
                
                return f(*args, **kwargs)
            except Exception as e:
                return unauthorized_response("Invalid or missing token")
        return decorated_function
    return decorator


def admin_required():
    """Admin rolü gerektirir."""
    return role_required('admin')


def broker_required():
    """Broker rolü gerektirir."""
    return role_required('admin', 'broker')


def handle_db_errors(f):
    """Veritabanı hatalarını yakalar ve uygun yanıt döner."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in {f.__name__}: {str(e)}")
            from .responses import internal_server_error_response
            return internal_server_error_response("Database operation failed")
    return decorated_function


def paginate_query(default_per_page=20, max_per_page=100):
    """Query'leri sayfalama parametreleri ile donatır."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            page = request.args.get('page', 1, type=int)
            per_page = min(
                request.args.get('per_page', default_per_page, type=int),
                max_per_page
            )
            
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = default_per_page
                
            return f(page=page, per_page=per_page, *args, **kwargs)
        return decorated_function
    return decorator


def log_api_call(f):
    """API çağrılarını loglar."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
            
        current_app.logger.info(
            f"API Call: {request.method} {request.path} - "
            f"User: {user_id} - IP: {request.remote_addr}"
        )
        
        return f(*args, **kwargs)
    return decorated_function

# blueprints/api/api_bp.py
from flask import Blueprint, jsonify, current_app
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from .utils.responses import error_response, internal_server_error_response
import traceback

# Ana API Blueprint'i oluştur
api_bp = Blueprint('api', __name__, url_prefix='/api')

# CORS yapılandırması
CORS(api_bp, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True
    }
})

# API versiyonlarını import et
from .v1.auth import auth_v1
from .v1.users import users_v1
from .v1.crm_minimal import crm_v1
from .v1.analysis import analysis_v1
from .v1.portfolio_minimal import portfolio_v1
# from .v1.media import media_v1

# V1 endpoint'lerini kaydet
api_bp.register_blueprint(auth_v1, url_prefix='/v1/auth')
api_bp.register_blueprint(users_v1, url_prefix='/v1/users')
api_bp.register_blueprint(crm_v1, url_prefix='/v1/crm')
api_bp.register_blueprint(analysis_v1, url_prefix='/v1/analysis')
api_bp.register_blueprint(portfolio_v1, url_prefix='/v1/portfolio')
# api_bp.register_blueprint(media_v1, url_prefix='/v1/media')


@api_bp.route('/')
def api_info():
    """API bilgileri."""
    return jsonify({
        "name": "Arsa Analiz ve Sunum API",
        "version": "1.0.0",
        "description": "Real estate analysis and CRM API",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "crm": "/api/v1/crm",
            "analysis": "/api/v1/analysis",
            "portfolio": "/api/v1/portfolio",
            "media": "/api/v1/media",
            "docs": "/api/docs"
        },
        "documentation": "/api/docs"
    })


@api_bp.route('/health')
def health_check():
    """
    Kapsamlı API sağlık kontrolü.

    Kontrol edilen bileşenler:
    - Veritabanı bağlantısı ve performansı
    - Connection pool durumu
    - Temel tablo erişimi
    - API response time
    """
    import time
    from datetime import datetime, timezone
    from models import db
    from sqlalchemy.sql import text
    from sqlalchemy import inspect

    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.1.3",
        "checks": {}
    }

    overall_healthy = True

    # 1. Temel veritabanı bağlantı testi (sorgu olmadan)
    try:
        # Sadece bağlantı aç/kapat - hiç sorgu çalıştırmadan
        with db.engine.connect() as connection:
            # Bağlantı başarılı, connection objesi var mı kontrol et
            if connection:
                health_status["checks"]["database_connection"] = {
                    "status": "healthy",
                    "message": "Database connection successful"
                }
            else:
                health_status["checks"]["database_connection"] = {
                    "status": "unhealthy",
                    "message": "Database connection returned None"
                }
                overall_healthy = False
    except Exception as e:
        current_app.logger.error(f"Database connection failed: {str(e)}")
        health_status["checks"]["database_connection"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        overall_healthy = False

    # 2. Database engine ve connection durumu
    try:
        engine = db.engine

        # Engine bilgileri
        engine_info = {
            "driver": str(engine.dialect.name),
            "server_version": "unknown"
        }

        # Basit bağlantı testi ve server version
        with engine.connect() as connection:
            try:
                # Server version bilgisi al
                if engine.dialect.name == 'mssql':
                    result = connection.execute(text('SELECT @@VERSION'))
                    row = result.fetchone()
                    if row and row[0]:
                        version_info = str(row[0])
                        engine_info["server_version"] = version_info.split('\n')[0][:100]  # İlk satır, max 100 karakter
                    else:
                        engine_info["server_version"] = "MSSQL - Version unknown"
                elif engine.dialect.name == 'postgresql':
                    result = connection.execute(text('SELECT version()'))
                    row = result.fetchone()
                    if row and row[0]:
                        engine_info["server_version"] = str(row[0])[:100]
                    else:
                        engine_info["server_version"] = "PostgreSQL - Version unknown"
                elif engine.dialect.name == 'mysql':
                    result = connection.execute(text('SELECT VERSION()'))
                    row = result.fetchone()
                    if row and row[0]:
                        engine_info["server_version"] = str(row[0])
                    else:
                        engine_info["server_version"] = "MySQL - Version unknown"
                else:
                    result = connection.execute(text('SELECT 1'))
                    engine_info["server_version"] = "Connected successfully"
            except Exception as version_error:
                current_app.logger.warning(f"Could not get server version: {str(version_error)}")
                engine_info["server_version"] = "Version check failed"

        # Pool durumu (basit kontrol)
        pool_healthy = True
        pool_messages = ["Database engine accessible"]

        # Pool var mı kontrol et
        if hasattr(engine, 'pool'):
            pool_messages.append("Connection pool available")

            # Pool'dan bağlantı alabilir miyiz test et
            try:
                test_conn = engine.connect()
                test_conn.close()
                pool_messages.append("Pool connection test successful")
            except Exception as pool_error:
                pool_healthy = False
                pool_messages.append(f"Pool connection failed: {str(pool_error)}")
        else:
            pool_messages.append("No connection pool detected")

        health_status["checks"]["database_engine"] = {
            "status": "healthy" if pool_healthy else "warning",
            "message": "; ".join(pool_messages),
            "details": engine_info
        }

        if not pool_healthy:
            overall_healthy = False

    except Exception as e:
        current_app.logger.error(f"Database engine check failed: {str(e)}")
        health_status["checks"]["database_engine"] = {
            "status": "unhealthy",
            "message": f"Database engine check failed: {str(e)}"
        }
        overall_healthy = False

    # 3. Temel tablo varlığı kontrolü (metadata ile)
    try:
        # Kritik tabloların varlığını kontrol et
        inspector = inspect(db.engine)
        required_tables = ['users', 'arsa_analizleri', 'crm_contacts', 'crm_deals']
        missing_tables = []

        existing_tables = inspector.get_table_names()

        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)

        if missing_tables:
            health_status["checks"]["database_schema"] = {
                "status": "unhealthy",
                "message": f"Missing tables: {', '.join(missing_tables)}",
                "details": {
                    "required_tables": required_tables,
                    "existing_tables": len(existing_tables),
                    "missing_tables": missing_tables
                }
            }
            overall_healthy = False
        else:
            health_status["checks"]["database_schema"] = {
                "status": "healthy",
                "message": "All required tables exist",
                "details": {
                    "tables_checked": len(required_tables),
                    "total_tables": len(existing_tables),
                    "required_tables": required_tables
                }
            }

    except Exception as e:
        current_app.logger.error(f"Database schema check failed: {str(e)}")
        health_status["checks"]["database_schema"] = {
            "status": "unhealthy",
            "message": f"Database schema check failed: {str(e)}"
        }
        overall_healthy = False

    # 4. Database connection performance testi
    try:
        # Bağlantı kurma performansını ölç
        connection_start = time.time()
        with db.engine.connect() as connection:
            # Bağlantı kuruldu, şimdi basit bir işlem yap
            connection.execute(text('SELECT 1'))
        connection_time = (time.time() - connection_start) * 1000  # milliseconds

        if connection_time > 5000:  # 5 saniyeden fazla
            health_status["checks"]["database_performance"] = {
                "status": "unhealthy",
                "message": f"Very slow database response: {connection_time:.2f}ms",
                "details": {"connection_time_ms": round(connection_time, 2)}
            }
            overall_healthy = False
        elif connection_time > 1000:  # 1 saniyeden fazla
            health_status["checks"]["database_performance"] = {
                "status": "warning",
                "message": f"Slow database response: {connection_time:.2f}ms",
                "details": {"connection_time_ms": round(connection_time, 2)}
            }
        else:
            health_status["checks"]["database_performance"] = {
                "status": "healthy",
                "message": "Database performance normal",
                "details": {"connection_time_ms": round(connection_time, 2)}
            }

    except Exception as e:
        current_app.logger.error(f"Database performance check failed: {str(e)}")
        health_status["checks"]["database_performance"] = {
            "status": "unhealthy",
            "message": f"Database performance check failed: {str(e)}"
        }
        overall_healthy = False

    # 5. API response time
    total_time = (time.time() - start_time) * 1000  # milliseconds
    health_status["response_time_ms"] = round(total_time, 2)

    if total_time > 5000:  # 5 saniyeden fazla
        health_status["checks"]["api_performance"] = {
            "status": "unhealthy",
            "message": f"Very slow API response: {total_time:.2f}ms"
        }
        overall_healthy = False
    elif total_time > 2000:  # 2 saniyeden fazla
        health_status["checks"]["api_performance"] = {
            "status": "warning",
            "message": f"Slow API response: {total_time:.2f}ms"
        }
    else:
        health_status["checks"]["api_performance"] = {
            "status": "healthy",
            "message": "API performance normal"
        }

    # Genel durum belirleme
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"

    # HTTP status code belirleme
    status_code = 200 if overall_healthy else 503

    # Başarısız kontroller varsa loglama
    if not overall_healthy:
        failed_checks = [name for name, check in health_status["checks"].items()
                        if check["status"] == "unhealthy"]
        current_app.logger.warning(f"Health check failed. Failed checks: {', '.join(failed_checks)}")

    return jsonify(health_status), status_code


@api_bp.route('/health/detailed')
def health_check_detailed():
    """
    Detaylı API sağlık kontrolü.
    /api/health ile aynı işlevi görür ama daha detaylı bilgi verir.
    """
    return health_check()  # Aynı fonksiyonu kullan


@api_bp.route('/v1')
def api_v1_info():
    """API v1 bilgileri."""
    return jsonify({
        "version": "1.0.0",
        "endpoints": {
            "authentication": {
                "login": "POST /api/v1/auth/login",
                "register": "POST /api/v1/auth/register",
                "refresh": "POST /api/v1/auth/refresh",
                "logout": "POST /api/v1/auth/logout"
            },
            "users": {
                "profile": "GET /api/v1/users/profile",
                "update": "PUT /api/v1/users/profile",
                "list": "GET /api/v1/users",
                "change_password": "POST /api/v1/users/change-password"
            },
            "crm": {
                "contacts": "GET,POST /api/v1/crm/contacts",
                "companies": "GET,POST /api/v1/crm/companies",
                "deals": "GET,POST /api/v1/crm/deals",
                "tasks": "GET,POST /api/v1/crm/tasks",
                "interactions": "GET,POST /api/v1/crm/interactions",
                "stats": "GET /api/v1/crm/stats"
            },
            "analysis": {
                "list": "GET /api/v1/analysis",
                "create": "POST /api/v1/analysis",
                "detail": "GET /api/v1/analysis/{id}",
                "update": "PUT /api/v1/analysis/{id}",
                "delete": "DELETE /api/v1/analysis/{id}",
                "stats": "GET /api/v1/analysis/stats",
                "reports": "POST /api/v1/analysis/{id}/report"
            },
            "portfolio": {
                "list": "GET /api/v1/portfolio",
                "create": "POST /api/v1/portfolio",
                "detail": "GET /api/v1/portfolio/{id}",
                "update": "PUT /api/v1/portfolio/{id}",
                "delete": "DELETE /api/v1/portfolio/{id}"
            },
            "media": {
                "upload": "POST /api/v1/media/upload",
                "download": "GET /api/v1/media/{id}",
                "delete": "DELETE /api/v1/media/{id}"
            }
        }
    })


# Global error handlers
@api_bp.errorhandler(400)
def bad_request(error):
    """400 Bad Request handler."""
    return error_response("Bad request", 400)


@api_bp.errorhandler(401)
def unauthorized(error):
    """401 Unauthorized handler."""
    return error_response("Unauthorized", 401)


@api_bp.errorhandler(403)
def forbidden(error):
    """403 Forbidden handler."""
    return error_response("Forbidden", 403)


@api_bp.errorhandler(404)
def not_found(error):
    """404 Not Found handler."""
    return error_response("Resource not found", 404)


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """405 Method Not Allowed handler."""
    return error_response("Method not allowed", 405)


@api_bp.errorhandler(422)
def unprocessable_entity(error):
    """422 Unprocessable Entity handler."""
    return error_response("Validation failed", 422)


@api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    """429 Rate Limit Exceeded handler."""
    return error_response("Rate limit exceeded", 429)


@api_bp.errorhandler(500)
def internal_server_error(error):
    """500 Internal Server Error handler."""
    current_app.logger.error(f"Internal server error: {str(error)}")
    current_app.logger.error(traceback.format_exc())
    return internal_server_error_response()


@api_bp.errorhandler(Exception)
def handle_unexpected_error(error):
    """Beklenmeyen hataları yakalar."""
    current_app.logger.error(f"Unexpected error: {str(error)}")
    current_app.logger.error(traceback.format_exc())
    return internal_server_error_response("An unexpected error occurred")


# JWT error handlers
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError, JWTDecodeError

@api_bp.errorhandler(NoAuthorizationError)
def handle_no_authorization_error(error):
    """JWT authorization header eksik."""
    return error_response("Missing Authorization Header", 401)

@api_bp.errorhandler(InvalidHeaderError)
def handle_invalid_header_error(error):
    """JWT header geçersiz."""
    return error_response("Invalid Authorization Header", 401)

@api_bp.errorhandler(JWTDecodeError)
def handle_jwt_decode_error(error):
    """JWT decode hatası."""
    return error_response("Invalid token", 401)

@api_bp.errorhandler(422)
def handle_jwt_exceptions(error):
    """JWT hatalarını yakalar."""
    return error_response("Invalid token", 422)


def init_swagger(app):
    """Swagger dokümantasyonunu başlatır."""
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/api/docs/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/api/docs/static",
        "swagger_ui": True,
        "specs_route": "/api/docs/"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Arsa Analiz ve Sunum API",
            "description": "Real estate analysis and CRM API documentation",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            }
        },
        "host": "localhost:5000",
        "basePath": "/api/v1",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
            }
        },
        "security": [{"Bearer": []}],
        "consumes": ["application/json"],
        "produces": ["application/json"]
    }
    
    return Swagger(app, config=swagger_config, template=swagger_template)

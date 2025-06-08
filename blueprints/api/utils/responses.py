# blueprints/api/utils/responses.py
from flask import jsonify
from typing import Any, Dict, Optional, Union


def success_response(
    data: Any = None, 
    message: str = "Success", 
    status_code: int = 200,
    meta: Optional[Dict] = None
) -> tuple:
    """Başarılı API yanıtı oluşturur."""
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    
    if meta:
        response["meta"] = meta
        
    return jsonify(response), status_code


def error_response(
    message: str = "An error occurred",
    status_code: int = 400,
    errors: Optional[Dict] = None,
    error_code: Optional[str] = None
) -> tuple:
    """Hata API yanıtı oluşturur."""
    response = {
        "success": False,
        "message": message
    }
    
    if errors:
        response["errors"] = errors
        
    if error_code:
        response["error_code"] = error_code
        
    return jsonify(response), status_code


def paginated_response(
    data: list,
    page: int,
    per_page: int,
    total: int,
    message: str = "Success"
) -> tuple:
    """Sayfalanmış API yanıtı oluşturur."""
    total_pages = (total + per_page - 1) // per_page
    
    meta = {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
    
    return success_response(data=data, message=message, meta=meta)


def validation_error_response(errors: Dict) -> tuple:
    """Validasyon hatası yanıtı oluşturur."""
    return error_response(
        message="Validation failed",
        status_code=422,
        errors=errors,
        error_code="VALIDATION_ERROR"
    )


def not_found_response(message: str = "Resource not found") -> tuple:
    """404 Not Found yanıtı oluşturur."""
    return error_response(
        message=message,
        status_code=404,
        error_code="NOT_FOUND"
    )


def unauthorized_response(message: str = "Unauthorized") -> tuple:
    """401 Unauthorized yanıtı oluşturur."""
    return error_response(
        message=message,
        status_code=401,
        error_code="UNAUTHORIZED"
    )


def forbidden_response(message: str = "Forbidden") -> tuple:
    """403 Forbidden yanıtı oluşturur."""
    return error_response(
        message=message,
        status_code=403,
        error_code="FORBIDDEN"
    )


def internal_server_error_response(message: str = "Internal server error") -> tuple:
    """500 Internal Server Error yanıtı oluşturur."""
    return error_response(
        message=message,
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR"
    )

"""
Security headers module for Flask application
Provides security headers to protect against common web vulnerabilities
"""

import os
from flask import request, current_app

# Debug import
print("Security headers module loaded!")


def add_security_headers(response):
    """
    Add security headers to all responses

    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables XSS filtering
    - Strict-Transport-Security: Enforces HTTPS (production only)
    - Content-Security-Policy: Prevents XSS and data injection
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """

    print("Adding security headers to response...")  # Debug
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Enable XSS filtering
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Control referrer information
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Control browser features
    response.headers['Permissions-Policy'] = (
        'geolocation=(), '
        'microphone=(), '
        'camera=(), '
        'payment=(), '
        'usb=(), '
        'magnetometer=(), '
        'gyroscope=(), '
        'speaker=()'
    )
    
    # HTTPS enforcement (production only)
    if os.environ.get('FORCE_HTTPS', 'False').lower() == 'true':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
        "https://cdn.jsdelivr.net "
        "https://cdnjs.cloudflare.com "
        "https://code.jquery.com "
        "https://stackpath.bootstrapcdn.com; "
        "style-src 'self' 'unsafe-inline' "
        "https://cdn.jsdelivr.net "
        "https://cdnjs.cloudflare.com "
        "https://stackpath.bootstrapcdn.com "
        "https://fonts.googleapis.com; "
        "font-src 'self' "
        "https://fonts.gstatic.com "
        "https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob: "
        "https://via.placeholder.com; "
        "connect-src 'self' "
        "https://api.openai.com "
        "https://maps.googleapis.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    
    return response


def configure_session_security(app):
    """
    Configure secure session settings
    """
    # Session cookie security
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Remember me cookie security
    app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_DURATION'] = 86400 * 30  # 30 days


def log_security_event(event_type, details=None, user_id=None):
    """
    Log security-related events
    
    Args:
        event_type (str): Type of security event
        details (dict): Additional details about the event
        user_id (int): User ID if applicable
    """
    log_data = {
        'event_type': event_type,
        'ip_address': request.remote_addr if request else 'unknown',
        'user_agent': request.headers.get('User-Agent') if request else 'unknown',
        'user_id': user_id,
        'details': details or {}
    }
    
    current_app.logger.warning(f"Security Event: {event_type} - {log_data}")


def is_safe_url(target):
    """
    Check if a URL is safe for redirects
    Prevents open redirect vulnerabilities
    
    Args:
        target (str): URL to check
        
    Returns:
        bool: True if URL is safe, False otherwise
    """
    if not target:
        return False
        
    # Check for absolute URLs
    if target.startswith('http://') or target.startswith('https://'):
        return False
        
    # Check for protocol-relative URLs
    if target.startswith('//'):
        return False
        
    # Check for javascript: or data: URLs
    if target.lower().startswith(('javascript:', 'data:', 'vbscript:')):
        return False
        
    return True


def validate_file_upload(file, allowed_extensions=None, max_size=None):
    """
    Validate uploaded files for security
    
    Args:
        file: Flask file object
        allowed_extensions (set): Set of allowed file extensions
        max_size (int): Maximum file size in bytes
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file selected"
    
    # Check file extension
    if allowed_extensions:
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size
    if max_size:
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            return False, f"File too large. Maximum size: {max_size // (1024*1024)}MB"
    
    # Check for potentially dangerous filenames
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    if any(char in file.filename for char in dangerous_chars):
        return False, "Invalid filename"
    
    return True, None


def sanitize_filename(filename):
    """
    Sanitize filename for safe storage
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    import re
    import uuid
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 50:
        name = name[:50]
    
    # Add UUID to prevent conflicts
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{name}_{unique_id}{ext}"

# blueprints/auth_decorators.py
from functools import wraps
from flask_login import current_user
from flask import flash, redirect, url_for, request # request'i import et

def role_required(*roles): # Birden fazla rol kabul edebilmesi için *roles
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in roles:
                flash(f'Bu sayfaya erişim için gerekli yetkiye sahip değilsiniz ({", ".join(roles)}).', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

superadmin_required = role_required('superadmin')
broker_required = role_required('broker')
# Örnek: Hem broker hem superadmin erişebilsin
# admin_or_broker_required = role_required('superadmin', 'broker')
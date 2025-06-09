# blueprints/permission_helpers.py
from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from models.permission_models import PermissionManager
from datetime import datetime

def permission_required(permission_key):
    """Belirli bir yetki gerektiren route'lar için decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'error')
                return redirect(url_for('auth.login'))
            
            if not PermissionManager.has_permission(current_user, permission_key):
                flash(f'Bu sayfaya erişim için gerekli yetkiye sahip değilsiniz ({permission_key}).', 'error')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def any_permission_required(*permission_keys):
    """Birden fazla yetkiden herhangi birine sahip olmayı gerektiren decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'error')
                return redirect(url_for('auth.login'))
            
            has_any_permission = any(
                PermissionManager.has_permission(current_user, perm) 
                for perm in permission_keys
            )
            
            if not has_any_permission:
                flash(f'Bu sayfaya erişim için gerekli yetkilerden birine sahip değilsiniz.', 'error')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def broker_or_admin_required(f):
    """Broker veya admin yetkisi gerektiren decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.role not in ['broker', 'superadmin']:
            flash('Bu sayfaya erişim için broker veya admin yetkisi gereklidir.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def can_manage_user_permissions(manager_user, target_user):
    """Bir kullanıcının başka bir kullanıcının yetkilerini yönetip yönetemeyeceğini kontrol eder"""
    
    # Superadmin herkesin yetkilerini yönetebilir
    if manager_user.role == 'superadmin':
        return True
    
    # Broker sadece kendi ofisindeki kullanıcıların yetkilerini yönetebilir
    if manager_user.role == 'broker':
        # Aynı ofiste olmalılar
        if manager_user.office_id and manager_user.office_id == target_user.office_id:
            # Broker sadece danışman ve çalışanların yetkilerini yönetebilir
            if target_user.role in ['danisman', 'calisan']:
                return True
    
    return False

def get_manageable_users(manager_user):
    """Bir kullanıcının yetki yönetebileceği kullanıcıları getirir"""
    from models import User
    
    if manager_user.role == 'superadmin':
        # Superadmin tüm kullanıcıları yönetebilir
        return User.query.all()
    
    elif manager_user.role == 'broker':
        # Broker sadece kendi ofisindeki danışman ve çalışanları yönetebilir
        if manager_user.office_id:
            return User.query.filter(
                User.office_id == manager_user.office_id,
                User.role.in_(['danisman', 'calisan']),
                User.id != manager_user.id
            ).all()
    
    return []

def get_available_permissions_for_role(role):
    """Belirli bir rol için atanabilir yetkiler listesini getirir"""
    
    if role == 'superadmin':
        return list(PermissionManager.PERMISSIONS.keys())
    
    elif role == 'broker':
        # Broker'lar admin yetkilerini veremez
        return [
            perm for perm in PermissionManager.PERMISSIONS.keys() 
            if not perm.startswith('admin.')
        ]
    
    elif role == 'danisman':
        # Danışmanlar için uygun yetkiler
        return [
            'analysis.view', 'analysis.create', 'analysis.edit', 'analysis.export',
            'crm.view', 'crm.create', 'crm.edit', 'crm.export',
            'portfolio.view', 'portfolio.create', 'portfolio.edit', 'portfolio.share'
        ]
    
    elif role == 'calisan':
        # Çalışanlar için temel yetkiler
        return [
            'analysis.view', 'analysis.create',
            'crm.view', 'crm.create',
            'portfolio.view'
        ]
    
    return []

def initialize_default_permissions():
    """Sistem ilk kurulumunda varsayılan yetki şablonlarını oluşturur"""
    from models import db
    from models.permission_models import PermissionTemplate
    
    for role, permissions in PermissionManager.DEFAULT_PERMISSIONS.items():
        # Mevcut şablon var mı kontrol et
        existing_template = PermissionTemplate.query.filter_by(role=role).first()
        
        if not existing_template:
            template = PermissionTemplate(
                role=role,
                permissions=permissions,
                description=f'{role.title()} rolü için varsayılan yetkiler'
            )
            db.session.add(template)
    
    try:
        db.session.commit()
        print("Varsayılan yetki şablonları oluşturuldu.")
    except Exception as e:
        db.session.rollback()
        print(f"Yetki şablonları oluşturulurken hata: {e}")

def sync_user_permissions_with_role(user):
    """Kullanıcının rolü değiştiğinde yetkilerini senkronize eder"""
    from models import db
    from models.permission_models import UserPermission
    
    # Kullanıcının mevcut özel yetkilerini temizle (rol değişikliği durumunda)
    UserPermission.query.filter_by(user_id=user.id).delete()
    
    # Yeni rol için varsayılan yetkiler otomatik olarak PermissionManager.get_user_permissions() 
    # fonksiyonu tarafından sağlanacak
    
    try:
        db.session.commit()
        print(f"Kullanıcı {user.email} için yetkiler senkronize edildi.")
    except Exception as e:
        db.session.rollback()
        print(f"Yetki senkronizasyonu hatası: {e}")

class PermissionService:
    """Yetki yönetimi için servis sınıfı"""
    
    @staticmethod
    def grant_permission(user_id, permission_key, granted_by_user_id, reason=None):
        """Kullanıcıya yetki ver"""
        from models import db
        from models.permission_models import UserPermission, PermissionLog
        
        # Mevcut yetki var mı kontrol et
        existing_perm = UserPermission.query.filter_by(
            user_id=user_id, 
            permission_key=permission_key
        ).first()
        
        old_value = existing_perm.permission_value if existing_perm else None
        
        if existing_perm:
            existing_perm.permission_value = True
            existing_perm.granted_by = granted_by_user_id
            existing_perm.granted_at = datetime.utcnow()
            existing_perm.is_active = True
        else:
            new_perm = UserPermission(
                user_id=user_id,
                permission_key=permission_key,
                permission_value=True,
                granted_by=granted_by_user_id
            )
            db.session.add(new_perm)
        
        # Log kaydı oluştur
        log_entry = PermissionLog(
            user_id=user_id,
            permission_key=permission_key,
            old_value=old_value,
            new_value=True,
            changed_by=granted_by_user_id,
            change_reason=reason,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(log_entry)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Yetki verme hatası: {e}")
            return False
    
    @staticmethod
    def revoke_permission(user_id, permission_key, revoked_by_user_id, reason=None):
        """Kullanıcıdan yetki al"""
        from models import db
        from models.permission_models import UserPermission, PermissionLog
        
        # Mevcut yetki var mı kontrol et
        existing_perm = UserPermission.query.filter_by(
            user_id=user_id, 
            permission_key=permission_key
        ).first()
        
        old_value = existing_perm.permission_value if existing_perm else None
        
        if existing_perm:
            existing_perm.permission_value = False
            existing_perm.granted_by = revoked_by_user_id
            existing_perm.granted_at = datetime.utcnow()
            existing_perm.is_active = True
        else:
            # Yetki yoksa, yasaklama yetkisi oluştur
            new_perm = UserPermission(
                user_id=user_id,
                permission_key=permission_key,
                permission_value=False,
                granted_by=revoked_by_user_id
            )
            db.session.add(new_perm)
        
        # Log kaydı oluştur
        log_entry = PermissionLog(
            user_id=user_id,
            permission_key=permission_key,
            old_value=old_value,
            new_value=False,
            changed_by=revoked_by_user_id,
            change_reason=reason,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(log_entry)
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Yetki alma hatası: {e}")
            return False
    
    @staticmethod
    def bulk_update_permissions(user_id, permissions_dict, updated_by_user_id, reason=None):
        """Kullanıcının birden fazla yetkisini toplu güncelle"""
        success_count = 0
        
        for permission_key, permission_value in permissions_dict.items():
            if permission_value:
                success = PermissionService.grant_permission(
                    user_id, permission_key, updated_by_user_id, reason
                )
            else:
                success = PermissionService.revoke_permission(
                    user_id, permission_key, updated_by_user_id, reason
                )
            
            if success:
                success_count += 1
        
        return success_count == len(permissions_dict)

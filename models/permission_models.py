# models/permission_models.py
from models import db
from datetime import datetime

class PermissionTemplate(db.Model):
    """Rol bazlı yetki şablonları"""
    __tablename__ = 'permission_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, unique=True)  # superadmin, broker, danisman, calisan
    permissions = db.Column(db.JSON, nullable=False)  # JSON formatında yetki listesi
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PermissionTemplate {self.role}>'


class UserPermission(db.Model):
    """Kullanıcı bazlı özel yetkiler"""
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_key = db.Column(db.String(100), nullable=False)  # Örn: 'analysis.create', 'crm.view'
    permission_value = db.Column(db.Boolean, default=True)  # True: izin var, False: yasaklı
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Kim tarafından verildi
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Opsiyonel: yetki sona erme tarihi
    is_active = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    user = db.relationship('User', foreign_keys=[user_id], backref='custom_permissions')
    granted_by_user = db.relationship('User', foreign_keys=[granted_by])
    
    # Unique constraint: Bir kullanıcı için aynı yetki sadece bir kez tanımlanabilir
    __table_args__ = (db.UniqueConstraint('user_id', 'permission_key', name='unique_user_permission'),)
    
    def __repr__(self):
        return f'<UserPermission {self.user_id}:{self.permission_key}={self.permission_value}>'


class OfficePermission(db.Model):
    """Ofis bazlı varsayılan yetkiler"""
    __tablename__ = 'office_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # danisman, calisan
    permission_key = db.Column(db.String(100), nullable=False)
    permission_value = db.Column(db.Boolean, default=True)
    set_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Hangi broker tarafından ayarlandı
    set_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # İlişkiler
    office = db.relationship('Office', backref='office_permissions')
    set_by_user = db.relationship('User', foreign_keys=[set_by])
    
    # Unique constraint: Bir ofiste aynı rol için aynı yetki sadece bir kez tanımlanabilir
    __table_args__ = (db.UniqueConstraint('office_id', 'role', 'permission_key', name='unique_office_permission'),)
    
    def __repr__(self):
        return f'<OfficePermission {self.office_id}:{self.role}:{self.permission_key}={self.permission_value}>'


class PermissionLog(db.Model):
    """Yetki değişikliklerinin log'u"""
    __tablename__ = 'permission_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_key = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.Boolean)
    new_value = db.Column(db.Boolean)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    change_reason = db.Column(db.String(255))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv6 desteği için
    
    # İlişkiler
    user = db.relationship('User', foreign_keys=[user_id])
    changed_by_user = db.relationship('User', foreign_keys=[changed_by])
    
    def __repr__(self):
        return f'<PermissionLog {self.user_id}:{self.permission_key} {self.old_value}->{self.new_value}>'


# Yetki sistemi için yardımcı sınıflar
class PermissionManager:
    """Yetki yönetimi için yardımcı sınıf"""
    
    # Sistem genelindeki tüm yetkiler
    PERMISSIONS = {
        # Analiz yetkiler
        'analysis.view': 'Analizleri görüntüleme',
        'analysis.create': 'Yeni analiz oluşturma',
        'analysis.edit': 'Analiz düzenleme',
        'analysis.delete': 'Analiz silme',
        'analysis.export': 'Analiz dışa aktarma',
        
        # CRM yetkiler
        'crm.view': 'CRM görüntüleme',
        'crm.create': 'Yeni kişi/şirket ekleme',
        'crm.edit': 'CRM düzenleme',
        'crm.delete': 'CRM silme',
        'crm.export': 'CRM dışa aktarma',
        
        # Portföy yetkiler
        'portfolio.view': 'Portföy görüntüleme',
        'portfolio.create': 'Yeni portföy oluşturma',
        'portfolio.edit': 'Portföy düzenleme',
        'portfolio.delete': 'Portföy silme',
        'portfolio.share': 'Portföy paylaşma',
        
        # Ofis yönetimi yetkiler
        'office.view': 'Ofis bilgilerini görüntüleme',
        'office.edit': 'Ofis bilgilerini düzenleme',
        'office.manage_users': 'Ofis kullanıcılarını yönetme',
        'office.manage_permissions': 'Ofis yetkilerini yönetme',
        
        # Admin yetkiler
        'admin.users': 'Kullanıcı yönetimi',
        'admin.offices': 'Ofis yönetimi',
        'admin.system': 'Sistem ayarları',
        'admin.reports': 'Sistem raporları',
        
        # Broker yetkiler
        'broker.dashboard': 'Broker dashboard erişimi',
        'broker.team_management': 'Ekip yönetimi',
        'broker.permission_management': 'Yetki yönetimi',
        'broker.reports': 'Broker raporları',
    }
    
    # Rol bazlı varsayılan yetkiler
    DEFAULT_PERMISSIONS = {
        'superadmin': list(PERMISSIONS.keys()),  # Tüm yetkiler
        'broker': [
            'analysis.view', 'analysis.create', 'analysis.edit', 'analysis.export',
            'crm.view', 'crm.create', 'crm.edit', 'crm.export',
            'portfolio.view', 'portfolio.create', 'portfolio.edit', 'portfolio.share',
            'office.view', 'office.edit', 'office.manage_users', 'office.manage_permissions',
            'broker.dashboard', 'broker.team_management', 'broker.permission_management', 'broker.reports'
        ],
        'danisman': [
            'analysis.view', 'analysis.create', 'analysis.edit', 'analysis.export',
            'crm.view', 'crm.create', 'crm.edit',
            'portfolio.view', 'portfolio.create', 'portfolio.edit'
        ],
        'calisan': [
            'analysis.view', 'analysis.create',
            'crm.view', 'crm.create',
            'portfolio.view'
        ]
    }
    
    @staticmethod
    def get_user_permissions(user):
        """Kullanıcının tüm yetkilerini getir"""
        # Rol bazlı varsayılan yetkiler
        default_perms = set(PermissionManager.DEFAULT_PERMISSIONS.get(user.role, []))
        
        # Kullanıcı bazlı özel yetkiler
        custom_perms = UserPermission.query.filter_by(
            user_id=user.id, 
            is_active=True
        ).all()
        
        # Ofis bazlı yetkiler (eğer kullanıcı bir ofise bağlıysa)
        office_perms = []
        if user.office_id:
            office_perms = OfficePermission.query.filter_by(
                office_id=user.office_id,
                role=user.role,
                is_active=True
            ).all()
        
        # Yetkileri birleştir
        final_permissions = default_perms.copy()
        
        # Ofis yetkilerini ekle/çıkar
        for perm in office_perms:
            if perm.permission_value:
                final_permissions.add(perm.permission_key)
            else:
                final_permissions.discard(perm.permission_key)
        
        # Kullanıcı özel yetkilerini ekle/çıkar (en yüksek öncelik)
        for perm in custom_perms:
            if perm.permission_value:
                final_permissions.add(perm.permission_key)
            else:
                final_permissions.discard(perm.permission_key)
        
        return list(final_permissions)
    
    @staticmethod
    def has_permission(user, permission_key):
        """Kullanıcının belirli bir yetkisi var mı kontrol et"""
        user_permissions = PermissionManager.get_user_permissions(user)
        return permission_key in user_permissions
    
    @staticmethod
    def get_sidebar_menu(user):
        """Kullanıcının yetkilerine göre sidebar menüsünü oluştur"""
        permissions = PermissionManager.get_user_permissions(user)
        menu_items = []
        
        # Ana Sayfa - herkes için
        menu_items.append({
            'title': 'Ana Sayfa',
            'icon': 'fas fa-home',
            'url': '/index',
            'active': True
        })
        
        # Analizler
        if any(p.startswith('analysis.') for p in permissions):
            menu_items.append({
                'title': 'Analizlerim',
                'icon': 'fas fa-chart-line',
                'url': '/analysis/list',
                'active': True
            })
        
        # CRM
        if any(p.startswith('crm.') for p in permissions):
            menu_items.append({
                'title': 'CRM',
                'icon': 'fas fa-users',
                'url': '/crm/new_contacts_list',
                'active': True
            })
        
        # Portföyler
        if any(p.startswith('portfolio.') for p in permissions):
            menu_items.append({
                'title': 'Portföyler',
                'icon': 'fas fa-briefcase',
                'url': '/portfolio/portfolios',
                'active': True
            })
        
        # Broker Dashboard
        if 'broker.dashboard' in permissions:
            menu_items.append({
                'title': 'Broker Dashboard',
                'icon': 'fas fa-user-tie',
                'url': '/broker/dashboard',
                'active': True
            })
        
        # Admin Panel
        if any(p.startswith('admin.') for p in permissions):
            menu_items.append({
                'title': 'Admin Panel',
                'icon': 'fas fa-crown',
                'url': '/admin/dashboard',
                'active': True
            })
        
        # Profil - herkes için
        menu_items.append({
            'title': 'Profil',
            'icon': 'fas fa-user',
            'url': '/profile',
            'active': True
        })
        
        return menu_items

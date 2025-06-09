# blueprints/broker_bp.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Office
from models.permission_models import PermissionManager, UserPermission, OfficePermission
from blueprints.permission_helpers import (
    broker_or_admin_required, 
    can_manage_user_permissions, 
    get_manageable_users,
    get_available_permissions_for_role,
    PermissionService
)
from datetime import datetime

broker_bp = Blueprint('broker', __name__, url_prefix='/broker', template_folder='../templates')

@broker_bp.route('/dashboard')
@login_required
@broker_or_admin_required
def dashboard():
    """Broker Dashboard"""

    # Broker'ın ofis bilgilerini al
    office = current_user.office if current_user.office_id else None

    # Ofis istatistikleri
    office_consultants = 0
    monthly_analyses = 0
    active_customers = 0
    pending_tasks = 0
    team_members = []

    if office:
        # Ofis danışmanları
        office_consultants = User.query.filter_by(office_id=office.id, role='danisman').count()

        # Bu ay yapılan analizler (ofis bazlı)
        from models.arsa_models import ArsaAnaliz
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_analyses = ArsaAnaliz.query.filter(
            ArsaAnaliz.user_id.in_(
                db.session.query(User.id).filter_by(office_id=office.id)
            ),
            ArsaAnaliz.created_at >= start_of_month
        ).count()

        # Aktif müşteriler (ofis bazlı)
        from models.crm_models import Contact
        active_customers = Contact.query.filter(
            Contact.user_id.in_(
                db.session.query(User.id).filter_by(office_id=office.id)
            )
        ).count()

        # Bekleyen görevler (ofis bazlı)
        from models.crm_models import Task
        pending_tasks = Task.query.filter(
            Task.user_id.in_(
                db.session.query(User.id).filter_by(office_id=office.id)
            ),
            Task.status.in_(['pending', 'in_progress'])
        ).count()

        # Ekip üyeleri
        team_members = User.query.filter(
            User.office_id == office.id,
            User.id != current_user.id
        ).limit(5).all()

    return render_template('dashboard_base.html',
                         show_broker_content=True,
                         office=office,
                         stats={
                             'office_consultants': office_consultants,
                             'monthly_analyses': monthly_analyses,
                             'active_customers': active_customers,
                             'pending_tasks': pending_tasks
                         },
                         team_members=team_members)


    """Gelişmiş Broker Dashboard"""

    # Broker'ın ofis bilgilerini al
    office = current_user.office if current_user.office_id else None

    # Temel istatistikler
    stats = {
        'office_consultants': 0,
        'office_employees': 0,
        'monthly_analyses': 0,
        'weekly_analyses': 0,
        'active_customers': 0,
        'pending_tasks': 0,
        'completed_tasks': 0,
        'total_revenue': 0,
        'monthly_revenue': 0
    }

    # Performans verileri
    performance_data = {
        'top_performers': [],
        'recent_activities': [],
        'monthly_trends': [],
        'team_comparison': []
    }

    team_members = []
    office_users = []

    if office:
        # Ofis kullanıcıları
        office_users = User.query.filter_by(office_id=office.id).all()
        office_user_ids = [user.id for user in office_users]

        # Temel sayılar
        stats['office_consultants'] = User.query.filter_by(office_id=office.id, role='danisman').count()
        stats['office_employees'] = User.query.filter_by(office_id=office.id, role='calisan').count()

        # Zaman aralıkları
        from datetime import datetime, timedelta
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        # Analiz istatistikleri
        from models.arsa_models import ArsaAnaliz
        if office_user_ids:
            stats['monthly_analyses'] = ArsaAnaliz.query.filter(
                ArsaAnaliz.user_id.in_(office_user_ids),
                ArsaAnaliz.created_at >= start_of_month
            ).count()

            stats['weekly_analyses'] = ArsaAnaliz.query.filter(
                ArsaAnaliz.user_id.in_(office_user_ids),
                ArsaAnaliz.created_at >= start_of_week
            ).count()

        # CRM istatistikleri
        from models.crm_models import Contact, Task
        if office_user_ids:
            stats['active_customers'] = Contact.query.filter(
                Contact.user_id.in_(office_user_ids)
            ).count()

            stats['pending_tasks'] = Task.query.filter(
                Task.user_id.in_(office_user_ids),
                Task.status.in_(['pending', 'in_progress'])
            ).count()

            stats['completed_tasks'] = Task.query.filter(
                Task.user_id.in_(office_user_ids),
                Task.status == 'completed',
                Task.updated_at >= start_of_month
            ).count()

        # En iyi performans gösterenler
        for user in office_users:
            if user.id != current_user.id:
                user_analyses = ArsaAnaliz.query.filter(
                    ArsaAnaliz.user_id == user.id,
                    ArsaAnaliz.created_at >= start_of_month
                ).count()

                user_customers = Contact.query.filter_by(user_id=user.id).count()

                performance_data['top_performers'].append({
                    'user': user,
                    'monthly_analyses': user_analyses,
                    'total_customers': user_customers,
                    'score': user_analyses * 2 + user_customers  # Basit skor hesaplama
                })

        # Performansa göre sırala
        performance_data['top_performers'].sort(key=lambda x: x['score'], reverse=True)
        performance_data['top_performers'] = performance_data['top_performers'][:5]

        # Son aktiviteler
        recent_analyses = ArsaAnaliz.query.filter(
            ArsaAnaliz.user_id.in_(office_user_ids)
        ).order_by(ArsaAnaliz.created_at.desc()).limit(5).all()

        for analysis in recent_analyses:
            performance_data['recent_activities'].append({
                'type': 'analysis',
                'user': analysis.user,
                'title': analysis.baslik,
                'date': analysis.created_at,
                'icon': 'fas fa-chart-line',
                'color': 'primary'
            })

        # Son müşteriler
        recent_contacts = Contact.query.filter(
            Contact.user_id.in_(office_user_ids)
        ).order_by(Contact.created_at.desc()).limit(3).all()

        for contact in recent_contacts:
            performance_data['recent_activities'].append({
                'type': 'contact',
                'user': contact.user,
                'title': f"{contact.ad} {contact.soyad}",
                'date': contact.created_at,
                'icon': 'fas fa-user-plus',
                'color': 'success'
            })

        # Aktiviteleri tarihe göre sırala
        performance_data['recent_activities'].sort(key=lambda x: x['date'], reverse=True)
        performance_data['recent_activities'] = performance_data['recent_activities'][:8]

        # Ekip üyeleri (detaylı)
        team_members = User.query.filter(
            User.office_id == office.id,
            User.id != current_user.id
        ).all()

    return render_template('broker_dashboard_enhanced.html',
                         office=office,
                         stats=stats,
                         performance_data=performance_data,
                         team_members=team_members,
                         office_users=office_users)

@broker_bp.route('/team')
@login_required
@broker_or_admin_required
def team_management():
    """Ekip Yönetimi"""
    
    team_members = get_manageable_users(current_user)
    
    return render_template('dashboard_base.html',
                         show_team_content=True,
                         team_members=team_members)

@broker_bp.route('/permissions')
@login_required
@broker_or_admin_required
def permission_management():
    """Yetki Yönetimi"""
    
    # URL'den user_id parametresi al
    user_id = request.args.get('user_id', type=int)
    selected_user = None
    
    if user_id:
        selected_user = User.query.get(user_id)
        # Kullanıcıyı yönetme yetkisi var mı kontrol et
        if not selected_user or not can_manage_user_permissions(current_user, selected_user):
            flash('Bu kullanıcının yetkilerini yönetme izniniz yok.', 'error')
            return redirect(url_for('broker.permission_management'))
    
    team_members = get_manageable_users(current_user)
    
    # Seçili kullanıcının mevcut yetkilerini al
    user_permissions = {}
    available_permissions = {}
    
    if selected_user:
        user_permissions = PermissionManager.get_user_permissions(selected_user)
        available_permissions = get_available_permissions_for_role(selected_user.role)
    
    return render_template('dashboard_base.html',
                         show_permissions_content=True,
                         team_members=team_members,
                         selected_user=selected_user,
                         user_permissions=user_permissions,
                         available_permissions=available_permissions,
                         permission_descriptions=PermissionManager.PERMISSIONS)

@broker_bp.route('/permissions/update', methods=['POST'])
@login_required
@broker_or_admin_required
def update_permissions():
    """Kullanıcı yetkilerini güncelle"""
    
    user_id = request.form.get('user_id', type=int)
    if not user_id:
        flash('Kullanıcı ID gerekli.', 'error')
        return redirect(url_for('broker.permission_management'))
    
    target_user = User.query.get(user_id)
    if not target_user or not can_manage_user_permissions(current_user, target_user):
        flash('Bu kullanıcının yetkilerini yönetme izniniz yok.', 'error')
        return redirect(url_for('broker.permission_management'))
    
    # Form'dan gelen yetki değişikliklerini al
    permissions_to_update = {}
    available_permissions = get_available_permissions_for_role(target_user.role)
    
    for permission_key in available_permissions:
        # Checkbox değeri varsa True, yoksa False
        permission_value = permission_key in request.form
        permissions_to_update[permission_key] = permission_value
    
    # Yetkileri toplu güncelle
    reason = f"Broker {current_user.email} tarafından güncellendi"
    success = PermissionService.bulk_update_permissions(
        user_id, permissions_to_update, current_user.id, reason
    )
    
    if success:
        flash(f'{target_user.ad} {target_user.soyad} kullanıcısının yetkileri başarıyla güncellendi.', 'success')
    else:
        flash('Yetki güncellemesi sırasında bir hata oluştu.', 'error')
    
    return redirect(url_for('broker.permission_management', user_id=user_id))

@broker_bp.route('/permissions/reset/<int:user_id>')
@login_required
@broker_or_admin_required
def reset_permissions(user_id):
    """Kullanıcının yetkilerini rol varsayılanlarına sıfırla"""
    
    target_user = User.query.get(user_id)
    if not target_user or not can_manage_user_permissions(current_user, target_user):
        flash('Bu kullanıcının yetkilerini yönetme izniniz yok.', 'error')
        return redirect(url_for('broker.permission_management'))
    
    # Kullanıcının özel yetkilerini temizle
    UserPermission.query.filter_by(user_id=user_id).delete()
    
    try:
        db.session.commit()
        flash(f'{target_user.ad} {target_user.soyad} kullanıcısının yetkileri varsayılan değerlere sıfırlandı.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Yetki sıfırlama sırasında bir hata oluştu.', 'error')
    
    return redirect(url_for('broker.permission_management', user_id=user_id))

@broker_bp.route('/reports')
@login_required
@broker_or_admin_required
def reports():
    """Performans Raporları"""
    
    return render_template('dashboard_base.html',
                         show_reports_content=True)

@broker_bp.route('/api/user-permissions/<int:user_id>')
@login_required
@broker_or_admin_required
def get_user_permissions_api(user_id):
    """Kullanıcının yetkilerini JSON olarak döndür (AJAX için)"""
    
    target_user = User.query.get(user_id)
    if not target_user or not can_manage_user_permissions(current_user, target_user):
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    
    user_permissions = PermissionManager.get_user_permissions(target_user)
    available_permissions = get_available_permissions_for_role(target_user.role)
    
    # Yetki durumlarını hazırla
    permission_status = {}
    for perm in available_permissions:
        permission_status[perm] = {
            'has_permission': perm in user_permissions,
            'description': PermissionManager.PERMISSIONS.get(perm, perm)
        }
    
    return jsonify({
        'user': {
            'id': target_user.id,
            'name': f"{target_user.ad} {target_user.soyad}",
            'email': target_user.email,
            'role': target_user.role
        },
        'permissions': permission_status
    })

@broker_bp.route('/api/bulk-permissions', methods=['POST'])
@login_required
@broker_or_admin_required
def bulk_update_permissions_api():
    """Birden fazla kullanıcının yetkilerini toplu güncelle (AJAX için)"""
    
    data = request.get_json()
    if not data or 'updates' not in data:
        return jsonify({'error': 'Geçersiz veri'}), 400
    
    success_count = 0
    error_count = 0
    
    for update in data['updates']:
        user_id = update.get('user_id')
        permissions = update.get('permissions', {})
        
        target_user = User.query.get(user_id)
        if not target_user or not can_manage_user_permissions(current_user, target_user):
            error_count += 1
            continue
        
        reason = f"Broker {current_user.email} tarafından toplu güncelleme"
        success = PermissionService.bulk_update_permissions(
            user_id, permissions, current_user.id, reason
        )
        
        if success:
            success_count += 1
        else:
            error_count += 1
    
    return jsonify({
        'success': True,
        'message': f'{success_count} kullanıcı güncellendi, {error_count} hata oluştu.',
        'success_count': success_count,
        'error_count': error_count
    })

# Broker blueprint'ini app.py'ye kaydetmeyi unutma!
# app.register_blueprint(broker_bp)

# blueprints/api/v1/users.py
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_

from models import db
from models.user_models import User, Portfolio
from ..schemas.user_schemas import (
    UserSchema, UserUpdateSchema, PasswordChangeSchema,
    UserListSchema, PortfolioSchema
)
from ..utils.decorators import (
    validate_json, log_api_call, handle_db_errors,
    paginate_query, admin_required
)
from ..utils.responses import (
    success_response, error_response, not_found_response,
    unauthorized_response, paginated_response
)

users_v1 = Blueprint('users_v1', __name__)


@users_v1.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint without JWT"""
    return success_response(message="Test endpoint works!")


@users_v1.route('/test-jwt', methods=['GET'])
@jwt_required()
def test_jwt_endpoint():
    """Test endpoint with JWT"""
    user_id = get_jwt_identity()
    return success_response(data={"user_id": user_id}, message="JWT test works!")


@users_v1.route('/profile', methods=['GET'])
@jwt_required()
@log_api_call
def get_profile():
    """
    Kullanıcı profili getir
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: User profile retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              $ref: '#/definitions/User'
      401:
        description: Unauthorized
      404:
        description: User not found
    """
    user_id = get_jwt_identity()
    # Integer veya string olabilir
    if isinstance(user_id, str):
        user_id = int(user_id)
    current_user = User.query.get(user_id)
    if not current_user:
        return not_found_response("User not found")
    
    user_schema = UserSchema()
    user_data = user_schema.dump(current_user)
    
    return success_response(
        data=user_data,
        message="Profile retrieved successfully"
    )


@users_v1.route('/profile', methods=['PUT'])
@jwt_required()
@log_api_call
@handle_db_errors
@validate_json(UserUpdateSchema)
def update_profile(data):
    """
    Kullanıcı profilini güncelle
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: body
        name: profile
        description: Updated profile data
        required: true
        schema:
          type: object
          properties:
            ad:
              type: string
            soyad:
              type: string
            telefon:
              type: string
            firma:
              type: string
            unvan:
              type: string
            adres:
              type: string
            timezone:
              type: string
    responses:
      200:
        description: Profile updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              $ref: '#/definitions/User'
      401:
        description: Unauthorized
      404:
        description: User not found
    """
    user_id = int(get_jwt_identity())
    current_user = User.query.get(user_id)
    if not current_user:
        return not_found_response("User not found")
    
    # Profil bilgilerini güncelle
    for field, value in data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.session.commit()
    
    user_schema = UserSchema()
    user_data = user_schema.dump(current_user)
    
    current_app.logger.info(f"Profile updated for user: {current_user.email}")
    return success_response(
        data=user_data,
        message="Profile updated successfully"
    )


@users_v1.route('/change-password', methods=['POST'])
@jwt_required()
@log_api_call
@handle_db_errors
@validate_json(PasswordChangeSchema)
def change_password(data):
    """
    Parola değiştir
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: body
        name: password_data
        description: Password change data
        required: true
        schema:
          type: object
          required:
            - current_password
            - new_password
            - confirm_password
          properties:
            current_password:
              type: string
            new_password:
              type: string
              minLength: 8
            confirm_password:
              type: string
    responses:
      200:
        description: Password changed successfully
      400:
        description: Invalid current password or passwords don't match
      401:
        description: Unauthorized
    """
    user_id = int(get_jwt_identity())
    current_user = User.query.get(user_id)
    if not current_user:
        return not_found_response("User not found")
    
    # Mevcut parolayı kontrol et
    if not check_password_hash(current_user.password_hash, data['current_password']):
        return error_response("Current password is incorrect", 400)
    
    # Yeni parolaları kontrol et
    if data['new_password'] != data['confirm_password']:
        return error_response("New passwords do not match", 400)
    
    # Parolayı güncelle
    current_user.password_hash = generate_password_hash(data['new_password'])
    db.session.commit()
    
    current_app.logger.info(f"Password changed for user: {current_user.email}")
    return success_response(message="Password changed successfully")


@users_v1.route('', methods=['GET'])
@jwt_required()
@admin_required()
@log_api_call
@paginate_query()
def list_users(page, per_page):
    """
    Kullanıcı listesi (Admin)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number
      - in: query
        name: per_page
        type: integer
        default: 20
        description: Items per page
      - in: query
        name: search
        type: string
        description: Search in name, email, or company
      - in: query
        name: role
        type: string
        description: Filter by role
      - in: query
        name: active
        type: boolean
        description: Filter by active status
    responses:
      200:
        description: Users retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: array
              items:
                $ref: '#/definitions/UserList'
            meta:
              $ref: '#/definitions/Pagination'
      401:
        description: Unauthorized
      403:
        description: Forbidden
    """
    # Filtreleme parametreleri
    search = request.args.get('search', '').strip()
    role = request.args.get('role', '').strip()
    active = request.args.get('active')
    
    # Base query
    query = User.query
    
    # Arama filtresi
    if search:
        search_filter = or_(
            User.ad.ilike(f'%{search}%'),
            User.soyad.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%'),
            User.firma.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    # Rol filtresi
    if role:
        query = query.filter(User.role == role)
    
    # Aktiflik filtresi
    if active is not None:
        is_active = active.lower() in ['true', '1', 'yes']
        query = query.filter(User._is_active == is_active)
    
    # Sıralama
    query = query.order_by(User.registered_on.desc())
    
    # Sayfalama
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Serialize
    user_schema = UserListSchema(many=True)
    users_data = user_schema.dump(pagination.items)
    
    return paginated_response(
        data=users_data,
        page=page,
        per_page=per_page,
        total=pagination.total,
        message="Users retrieved successfully"
    )


@users_v1.route('/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required()
@log_api_call
def get_user(user_id):
    """
    Kullanıcı detayı (Admin)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: User retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              $ref: '#/definitions/User'
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: User not found
    """
    user = User.query.get(user_id)
    if not user:
        return not_found_response("User not found")
    
    user_schema = UserSchema()
    user_data = user_schema.dump(user)
    
    return success_response(
        data=user_data,
        message="User retrieved successfully"
    )


@users_v1.route('/<int:user_id>/activate', methods=['POST'])
@jwt_required()
@admin_required()
@log_api_call
@handle_db_errors
def activate_user(user_id):
    """
    Kullanıcıyı aktifleştir (Admin)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: User activated successfully
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: User not found
    """
    user = User.query.get(user_id)
    if not user:
        return not_found_response("User not found")
    
    user._is_active = True
    user.failed_attempts = 0
    db.session.commit()
    
    current_app.logger.info(f"User activated: {user.email}")
    return success_response(message="User activated successfully")


@users_v1.route('/<int:user_id>/deactivate', methods=['POST'])
@jwt_required()
@admin_required()
@log_api_call
@handle_db_errors
def deactivate_user(user_id):
    """
    Kullanıcıyı deaktifleştir (Admin)
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: User deactivated successfully
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: User not found
    """
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    user = User.query.get(user_id)

    if not user:
        return not_found_response("User not found")

    # Kendi hesabını deaktifleştirmeyi engelle
    if user.id == current_user_id:
        return error_response("Cannot deactivate your own account", 400)
    
    user._is_active = False
    db.session.commit()
    
    current_app.logger.info(f"User deactivated: {user.email}")
    return success_response(message="User deactivated successfully")


@users_v1.route('/portfolios', methods=['GET'])
@jwt_required()
@log_api_call
def get_user_portfolios():
    """
    Kullanıcının portfolyolarını getir
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Portfolios retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: array
              items:
                $ref: '#/definitions/Portfolio'
      401:
        description: Unauthorized
    """
    user_id = int(get_jwt_identity())
    current_user = User.query.get(user_id)
    if not current_user:
        return not_found_response("User not found")
    
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).order_by(Portfolio.created_at.desc()).all()
    
    portfolio_schema = PortfolioSchema(many=True)
    portfolios_data = portfolio_schema.dump(portfolios)
    
    return success_response(
        data=portfolios_data,
        message="Portfolios retrieved successfully"
    )


@users_v1.route('/stats', methods=['GET'])
@jwt_required()
@log_api_call
def get_user_stats():
    """
    Kullanıcı istatistikleri
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: User statistics retrieved successfully
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
                total_analyses:
                  type: integer
                total_portfolios:
                  type: integer
                total_contacts:
                  type: integer
                total_deals:
                  type: integer
                recent_activity:
                  type: array
      401:
        description: Unauthorized
    """
    user_id = int(get_jwt_identity())
    current_user = User.query.get(user_id)
    if not current_user:
        return not_found_response("User not found")
    
    # İstatistikleri hesapla
    from models.arsa_models import ArsaAnaliz
    from models.crm_models import Contact, Deal
    
    stats = {
        'total_analyses': ArsaAnaliz.query.filter_by(user_id=current_user.id).count(),
        'total_portfolios': Portfolio.query.filter_by(user_id=current_user.id).count(),
        'total_contacts': Contact.query.filter_by(user_id=current_user.id).count(),
        'total_deals': Deal.query.filter_by(user_id=current_user.id).count(),
        'recent_activity': []  # TODO: Son aktiviteleri ekle
    }
    
    return success_response(
        data=stats,
        message="User statistics retrieved successfully"
    )

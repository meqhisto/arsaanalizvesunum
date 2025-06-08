# blueprints/api/v1/crm_minimal.py
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.crm_models import Contact, Company
from ..utils.decorators import log_api_call
from ..utils.responses import success_response, error_response, not_found_response

# CRM Blueprint
crm_v1 = Blueprint('crm_v1', __name__)


@crm_v1.route('/contacts', methods=['POST'])
@jwt_required()
@log_api_call
def create_contact():
    """
    Yeni kişi oluştur
    ---
    tags:
      - CRM - Contacts
    security:
      - Bearer: []
    parameters:
      - in: body
        name: contact
        description: Contact data
        required: true
        schema:
          type: object
          required:
            - ad
            - soyad
          properties:
            ad:
              type: string
              minLength: 1
              maxLength: 100
            soyad:
              type: string
              minLength: 1
              maxLength: 100
            email:
              type: string
              format: email
            telefon:
              type: string
              maxLength: 30
            company_id:
              type: integer
            pozisyon:
              type: string
              maxLength: 100
            adres:
              type: string
            notlar:
              type: string
            status:
              type: string
              enum: ['Lead', 'Prospect', 'Customer', 'Inactive']
              default: 'Lead'
            kaynak:
              type: string
              maxLength: 100
    responses:
      201:
        description: Contact created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    try:
        # Kullanıcı bilgisini al
        user_id = get_jwt_identity()
        from models.user_models import User
        current_user = User.query.get(user_id)
        
        if not current_user:
            return not_found_response("User not found")
        
        # JSON verilerini al
        data = request.get_json()
        if not data:
            return error_response("No JSON data provided", 400)
        
        # Temel validasyonlar
        required_fields = ['ad', 'soyad']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(f"Missing required field: {field}", 400)
        
        # Email format kontrolü (opsiyonel)
        if data.get('email'):
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return error_response("Invalid email format", 400)
        
        # Company kontrolü (opsiyonel)
        if data.get('company_id'):
            company = Company.query.filter_by(
                id=data['company_id'],
                user_id=current_user.id
            ).first()
            if not company:
                return error_response("Company not found", 404)
        
        # Contact oluştur
        contact = Contact(
            user_id=current_user.id,
            office_id=getattr(current_user, 'office_id', None),
            first_name=data['ad'],
            last_name=data['soyad'],
            email=data.get('email'),
            phone=data.get('telefon'),
            company_id=data.get('company_id'),
            role=data.get('pozisyon'),
            status=data.get('status', 'Lead'),
            source=data.get('kaynak'),
            notes=data.get('notlar')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        # Response data hazırla
        contact_data = {
            'id': contact.id,
            'ad': contact.first_name,
            'soyad': contact.last_name,
            'full_name': f"{contact.first_name} {contact.last_name}",
            'email': contact.email,
            'telefon': contact.phone,
            'company_id': contact.company_id,
            'pozisyon': contact.role,
            'status': contact.status,
            'kaynak': contact.source,
            'notlar': contact.notes,
            'created_at': contact.created_at.isoformat() if contact.created_at else None,
            'user_id': contact.user_id
        }
        
        current_app.logger.info(f"Contact created: {contact.first_name} {contact.last_name} by user {current_user.id}")
        return success_response(
            data=contact_data,
            message="Contact created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Contact creation error: {str(e)}")
        return error_response("Contact creation failed", 500)


@crm_v1.route('/contacts', methods=['GET'])
@jwt_required()
@log_api_call
def list_contacts():
    """
    Kişi listesi
    ---
    tags:
      - CRM - Contacts
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
      - in: query
        name: search
        type: string
        description: Search in name, email, or phone
    responses:
      200:
        description: Contacts retrieved successfully
      401:
        description: Unauthorized
    """
    try:
        # Kullanıcı bilgisini al
        user_id = get_jwt_identity()
        from models.user_models import User
        current_user = User.query.get(user_id)
        
        if not current_user:
            return not_found_response("User not found")
        
        # Parametreler
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        
        # Base query
        query = Contact.query.filter_by(user_id=current_user.id)
        
        # Arama filtresi
        if search:
            from sqlalchemy import or_
            search_filter = or_(
                Contact.first_name.ilike(f'%{search}%'),
                Contact.last_name.ilike(f'%{search}%'),
                Contact.email.ilike(f'%{search}%'),
                Contact.phone.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Sıralama
        query = query.order_by(Contact.created_at.desc())
        
        # Sayfalama
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Response data hazırla
        contacts_data = []
        for contact in pagination.items:
            contact_data = {
                'id': contact.id,
                'ad': contact.first_name,
                'soyad': contact.last_name,
                'full_name': f"{contact.first_name} {contact.last_name}",
                'email': contact.email,
                'telefon': contact.phone,
                'company_id': contact.company_id,
                'pozisyon': contact.role,
                'status': contact.status,
                'kaynak': contact.source,
                'notlar': contact.notes,
                'created_at': contact.created_at.isoformat() if contact.created_at else None,
                'user_id': contact.user_id
            }
            contacts_data.append(contact_data)
        
        response_data = {
            'data': contacts_data,
            'meta': {
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'total_pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        }
        
        return success_response(
            data=response_data,
            message="Contacts retrieved successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"List contacts error: {str(e)}")
        return error_response("Failed to retrieve contacts", 500)


@crm_v1.route('/stats', methods=['GET'])
@jwt_required()
@log_api_call
def get_crm_stats():
    """
    CRM istatistikleri
    ---
    tags:
      - CRM - Stats
    security:
      - Bearer: []
    responses:
      200:
        description: CRM stats retrieved successfully
      401:
        description: Unauthorized
    """
    try:
        # Kullanıcı bilgisini al
        user_id = get_jwt_identity()
        from models.user_models import User
        current_user = User.query.get(user_id)

        if not current_user:
            return not_found_response("User not found")

        # Contact istatistikleri
        total_contacts = Contact.query.filter_by(user_id=current_user.id).count()

        # Status'a göre dağılım
        from sqlalchemy import func
        status_stats = db.session.query(
            Contact.status,
            func.count(Contact.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Contact.status).all()

        status_distribution = {}
        for status, count in status_stats:
            status_distribution[status or 'Unknown'] = count

        # Son 30 günde eklenen contact'lar
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_contacts = Contact.query.filter(
            Contact.user_id == current_user.id,
            Contact.created_at >= thirty_days_ago
        ).count()

        stats_data = {
            'total_contacts': total_contacts,
            'status_distribution': status_distribution,
            'recent_contacts_30_days': recent_contacts,
            'generated_at': datetime.utcnow().isoformat()
        }

        return success_response(
            data=stats_data,
            message="CRM stats retrieved successfully"
        )

    except Exception as e:
        current_app.logger.error(f"CRM stats error: {str(e)}")
        return error_response("Failed to retrieve CRM stats", 500)

# blueprints/api/v1/crm.py
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_, func
from datetime import datetime, date

from models import db
from models.crm_models import Contact, Company, Deal, Task, Interaction
from ..schemas.crm_schemas import (
    ContactSchema, ContactCreateSchema, ContactUpdateSchema,
    CompanySchema, CompanyCreateSchema, CompanyUpdateSchema,
    DealSchema, DealCreateSchema, DealUpdateSchema,
    TaskSchema, TaskCreateSchema, TaskUpdateSchema,
    InteractionSchema, InteractionCreateSchema,
    CRMStatsSchema
)
from ..utils.decorators import (
    validate_json, log_api_call, handle_db_errors,
    paginate_query, )
from ..utils.responses import (
    success_response, error_response, not_found_response,
    paginated_response
)

crm_v1 = Blueprint('crm_v1', __name__)


# CONTACTS ENDPOINTS
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
      - in: query
        name: status
        type: string
        description: Filter by status
      - in: query
        name: company_id
        type: integer
        description: Filter by company
    responses:
      200:
        description: Contacts retrieved successfully
      401:
        description: Unauthorized
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    # Filtreleme parametreleri
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    company_id = request.args.get('company_id', type=int)
    
    # Base query
    query = Contact.query.filter_by(user_id=current_user.id)
    
    # Arama filtresi
    if search:
        search_filter = or_(
            Contact.ad.ilike(f'%{search}%'),
            Contact.soyad.ilike(f'%{search}%'),
            Contact.email.ilike(f'%{search}%'),
            Contact.telefon.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    # Status filtresi
    if status:
        query = query.filter(Contact.status == status)
    
    # Company filtresi
    if company_id:
        query = query.filter(Contact.company_id == company_id)
    
    # Sıralama
    query = query.order_by(Contact.created_at.desc())
    
    # Sayfalama
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Serialize
    contact_schema = ContactSchema(many=True)
    contacts_data = contact_schema.dump(pagination.items)
    
    return paginated_response(
        data=contacts_data,
        page=page,
        per_page=per_page,
        total=pagination.total,
        message="Contacts retrieved successfully"
    )


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


# @crm_v1.route('/contacts/<int:contact_id>', methods=['GET'])
# @jwt_required()
# @log_api_call
def get_contact_disabled(contact_id):
    """
    Kişi detayı
    ---
    tags:
      - CRM - Contacts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: contact_id
        type: integer
        required: true
    responses:
      200:
        description: Contact retrieved successfully
      401:
        description: Unauthorized
      404:
        description: Contact not found
    """
    current_user = ()
    contact = Contact.query.filter_by(
        id=contact_id,
        user_id=current_user.id
    ).first()
    
    if not contact:
        return not_found_response("Contact not found")
    
    contact_schema = ContactSchema()
    contact_data = contact_schema.dump(contact)
    
    return success_response(
        data=contact_data,
        message="Contact retrieved successfully"
    )


# @crm_v1.route('/contacts/<int:contact_id>', methods=['PUT'])
# @jwt_required()
# @log_api_call
def update_contact_disabled(contact_id, data):
    """
    Kişi güncelle
    ---
    tags:
      - CRM - Contacts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: contact_id
        type: integer
        required: true
      - in: body
        name: contact
        description: Updated contact data
        required: true
        schema:
          $ref: '#/definitions/ContactUpdate'
    responses:
      200:
        description: Contact updated successfully
      401:
        description: Unauthorized
      404:
        description: Contact not found
    """
    current_user = ()
    contact = Contact.query.filter_by(
        id=contact_id,
        user_id=current_user.id
    ).first()
    
    if not contact:
        return not_found_response("Contact not found")
    
    # Company kontrolü
    if data.get('company_id'):
        company = Company.query.filter_by(
            id=data['company_id'],
            user_id=current_user.id
        ).first()
        if not company:
            return error_response("Company not found", 404)
    
    # Contact güncelle
    for field, value in data.items():
        if hasattr(contact, field):
            setattr(contact, field, value)
    
    contact.updated_at = datetime.utcnow()
    db.session.commit()
    
    contact_schema = ContactSchema()
    contact_data = contact_schema.dump(contact)
    
    current_app.logger.info(f"Contact updated: {contact.ad} {contact.soyad}")
    return success_response(
        data=contact_data,
        message="Contact updated successfully"
    )


# @crm_v1.route('/contacts/<int:contact_id>', methods=['DELETE'])
# @jwt_required()
# @log_api_call
def delete_contact_disabled(contact_id):
    """
    Kişi sil
    ---
    tags:
      - CRM - Contacts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: contact_id
        type: integer
        required: true
    responses:
      200:
        description: Contact deleted successfully
      401:
        description: Unauthorized
      404:
        description: Contact not found
    """
    current_user = ()
    contact = Contact.query.filter_by(
        id=contact_id,
        user_id=current_user.id
    ).first()
    
    if not contact:
        return not_found_response("Contact not found")
    
    db.session.delete(contact)
    db.session.commit()
    
    current_app.logger.info(f"Contact deleted: {contact.ad} {contact.soyad}")
    return success_response(message="Contact deleted successfully")


# COMPANIES ENDPOINTS - DISABLED FOR NOW
# @crm_v1.route('/companies', methods=['GET'])
# @jwt_required()
# @log_api_call
def list_companies_disabled(page, per_page):
    """
    Şirket listesi
    ---
    tags:
      - CRM - Companies
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
        description: Search in company name or industry
    responses:
      200:
        description: Companies retrieved successfully
      401:
        description: Unauthorized
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    # Filtreleme parametreleri
    search = request.args.get('search', '').strip()
    
    # Base query
    query = Company.query.filter_by(user_id=current_user.id)
    
    # Arama filtresi
    if search:
        search_filter = or_(
            Company.name.ilike(f'%{search}%'),
            Company.industry.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    # Sıralama
    query = query.order_by(Company.created_at.desc())
    
    # Sayfalama
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Serialize
    company_schema = CompanySchema(many=True)
    companies_data = company_schema.dump(pagination.items)
    
    return paginated_response(
        data=companies_data,
        page=page,
        per_page=per_page,
        total=pagination.total,
        message="Companies retrieved successfully"
    )


@crm_v1.route('/companies', methods=['POST'])
@()
@log_api_call
@handle_db_errors
@validate_json(CompanyCreateSchema)
def create_company(data):
    """
    Yeni şirket oluştur
    ---
    tags:
      - CRM - Companies
    security:
      - Bearer: []
    parameters:
      - in: body
        name: company
        description: Company data
        required: true
        schema:
          $ref: '#/definitions/CompanyCreate'
    responses:
      201:
        description: Company created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    # Aynı isimde şirket kontrolü
    existing_company = Company.query.filter_by(
        name=data['name'],
        user_id=current_user.id
    ).first()
    
    if existing_company:
        return error_response("Company with this name already exists", 409)
    
    # Company oluştur
    company = Company(
        user_id=current_user.id,
        **data
    )
    
    db.session.add(company)
    db.session.commit()
    
    company_schema = CompanySchema()
    company_data = company_schema.dump(company)
    
    current_app.logger.info(f"Company created: {company.name}")
    return success_response(
        data=company_data,
        message="Company created successfully",
        status_code=201
    )


# DEALS ENDPOINTS
@crm_v1.route('/deals', methods=['GET'])
@()
@log_api_call
@paginate_query()
def list_deals(page, per_page):
    """
    Fırsat listesi
    ---
    tags:
      - CRM - Deals
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
        name: stage
        type: string
        description: Filter by stage
      - in: query
        name: contact_id
        type: integer
        description: Filter by contact
    responses:
      200:
        description: Deals retrieved successfully
      401:
        description: Unauthorized
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    # Filtreleme parametreleri
    stage = request.args.get('stage', '').strip()
    contact_id = request.args.get('contact_id', type=int)
    
    # Base query
    query = Deal.query.filter_by(user_id=current_user.id)
    
    # Stage filtresi
    if stage:
        query = query.filter(Deal.stage == stage)
    
    # Contact filtresi
    if contact_id:
        query = query.filter(Deal.contact_id == contact_id)
    
    # Sıralama
    query = query.order_by(Deal.created_at.desc())
    
    # Sayfalama
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Serialize
    deal_schema = DealSchema(many=True)
    deals_data = deal_schema.dump(pagination.items)
    
    return paginated_response(
        data=deals_data,
        page=page,
        per_page=per_page,
        total=pagination.total,
        message="Deals retrieved successfully"
    )


@crm_v1.route('/stats', methods=['GET'])
@()
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
        description: CRM statistics retrieved successfully
      401:
        description: Unauthorized
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    # İstatistikleri hesapla
    stats = {
        'total_contacts': Contact.query.filter_by(user_id=current_user.id).count(),
        'total_companies': Company.query.filter_by(user_id=current_user.id).count(),
        'total_deals': Deal.query.filter_by(user_id=current_user.id).count(),
        'total_tasks': Task.query.filter_by(user_id=current_user.id).count(),
        'active_deals_value': db.session.query(func.sum(Deal.value)).filter(
            Deal.user_id == current_user.id,
            Deal.stage.notin_(['Kazanıldı', 'Kaybedildi'])
        ).scalar() or 0,
        'won_deals_value': db.session.query(func.sum(Deal.value)).filter(
            Deal.user_id == current_user.id,
            Deal.stage == 'Kazanıldı'
        ).scalar() or 0,
        'overdue_tasks': Task.query.filter(
            Task.user_id == current_user.id,
            Task.due_date < date.today(),
            Task.status != 'Tamamlandı'
        ).count(),
        'recent_interactions': Interaction.query.filter_by(user_id=current_user.id).count()
    }
    
    return success_response(
        data=stats,
        message="CRM statistics retrieved successfully"
    )

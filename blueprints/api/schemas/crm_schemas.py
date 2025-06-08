# blueprints/api/schemas/crm_schemas.py
from marshmallow import Schema, fields, validate, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.crm_models import Contact, Company, Deal, Task, Interaction
from models import db
from ..utils.validators import validate_email, validate_phone


class ContactSchema(SQLAlchemyAutoSchema):
    """Contact şeması."""
    class Meta:
        model = Contact
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    full_name = fields.Method("get_full_name")
    company_name = fields.Method("get_company_name")
    
    def get_full_name(self, obj):
        return f"{obj.ad or ''} {obj.soyad or ''}".strip()
    
    def get_company_name(self, obj):
        return obj.company.name if obj.company else None


class ContactCreateSchema(Schema):
    """Contact oluşturma şeması."""
    ad = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    soyad = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(allow_none=True, validate=validate_email)
    telefon = fields.Str(allow_none=True, validate=validate_phone)
    company_id = fields.Int(allow_none=True)
    pozisyon = fields.Str(allow_none=True, validate=validate.Length(max=100))
    adres = fields.Str(allow_none=True)
    notlar = fields.Str(allow_none=True)
    status = fields.Str(
        validate=validate.OneOf(['Lead', 'Prospect', 'Customer', 'Inactive']),
        load_default='Lead'
    )
    kaynak = fields.Str(allow_none=True, validate=validate.Length(max=100))


class ContactUpdateSchema(Schema):
    """Contact güncelleme şeması."""
    ad = fields.Str(validate=validate.Length(min=1, max=100))
    soyad = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email(allow_none=True, validate=validate_email)
    telefon = fields.Str(allow_none=True, validate=validate_phone)
    company_id = fields.Int(allow_none=True)
    pozisyon = fields.Str(allow_none=True, validate=validate.Length(max=100))
    adres = fields.Str(allow_none=True)
    notlar = fields.Str(allow_none=True)
    status = fields.Str(validate=validate.OneOf(['Lead', 'Prospect', 'Customer', 'Inactive']))
    kaynak = fields.Str(allow_none=True, validate=validate.Length(max=100))


class CompanySchema(SQLAlchemyAutoSchema):
    """Company şeması."""
    class Meta:
        model = Company
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    contact_count = fields.Method("get_contact_count")
    deal_count = fields.Method("get_deal_count")
    
    def get_contact_count(self, obj):
        return obj.contacts.count() if obj.contacts else 0
    
    def get_deal_count(self, obj):
        return obj.deals.count() if obj.deals else 0


class CompanyCreateSchema(Schema):
    """Company oluşturma şeması."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    industry = fields.Str(allow_none=True, validate=validate.Length(max=100))
    website = fields.Url(allow_none=True)
    telefon = fields.Str(allow_none=True, validate=validate_phone)
    email = fields.Email(allow_none=True, validate=validate_email)
    adres = fields.Str(allow_none=True)
    notlar = fields.Str(allow_none=True)


class CompanyUpdateSchema(Schema):
    """Company güncelleme şeması."""
    name = fields.Str(validate=validate.Length(min=1, max=200))
    industry = fields.Str(allow_none=True, validate=validate.Length(max=100))
    website = fields.Url(allow_none=True)
    telefon = fields.Str(allow_none=True, validate=validate_phone)
    email = fields.Email(allow_none=True, validate=validate_email)
    adres = fields.Str(allow_none=True)
    notlar = fields.Str(allow_none=True)


class DealSchema(SQLAlchemyAutoSchema):
    """Deal şeması."""
    class Meta:
        model = Deal
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    contact_name = fields.Method("get_contact_name")
    company_name = fields.Method("get_company_name")
    days_to_close = fields.Method("get_days_to_close")
    
    def get_contact_name(self, obj):
        if obj.contact:
            return f"{obj.contact.ad or ''} {obj.contact.soyad or ''}".strip()
        return None
    
    def get_company_name(self, obj):
        return obj.company.name if obj.company else None
    
    def get_days_to_close(self, obj):
        if obj.expected_close_date:
            from datetime import date
            today = date.today()
            return (obj.expected_close_date - today).days
        return None


class DealCreateSchema(Schema):
    """Deal oluşturma şeması."""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    contact_id = fields.Int(allow_none=True)
    company_id = fields.Int(allow_none=True)
    value = fields.Decimal(allow_none=True, places=2)
    stage = fields.Str(
        validate=validate.OneOf(['Potansiyel', 'İlk Görüşme', 'Teklif', 'Müzakere', 'Kazanıldı', 'Kaybedildi']),
        load_default='Potansiyel'
    )
    expected_close_date = fields.Date(allow_none=True)
    probability = fields.Int(validate=validate.Range(min=0, max=100), load_default=0)
    notes = fields.Str(allow_none=True)


class DealUpdateSchema(Schema):
    """Deal güncelleme şeması."""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    contact_id = fields.Int(allow_none=True)
    company_id = fields.Int(allow_none=True)
    value = fields.Decimal(allow_none=True, places=2)
    stage = fields.Str(
        validate=validate.OneOf(['Potansiyel', 'İlk Görüşme', 'Teklif', 'Müzakere', 'Kazanıldı', 'Kaybedildi'])
    )
    expected_close_date = fields.Date(allow_none=True)
    actual_close_date = fields.Date(allow_none=True)
    probability = fields.Int(validate=validate.Range(min=0, max=100))
    notes = fields.Str(allow_none=True)


class TaskSchema(SQLAlchemyAutoSchema):
    """Task şeması."""
    class Meta:
        model = Task
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    assigned_user_name = fields.Method("get_assigned_user_name")
    is_overdue = fields.Method("get_is_overdue")
    
    def get_assigned_user_name(self, obj):
        if obj.assigned_user:
            return f"{obj.assigned_user.ad or ''} {obj.assigned_user.soyad or ''}".strip()
        return None
    
    def get_is_overdue(self, obj):
        if obj.due_date and obj.status != 'Tamamlandı':
            from datetime import date
            return obj.due_date < date.today()
        return False


class TaskCreateSchema(Schema):
    """Task oluşturma şeması."""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True)
    assigned_to_user_id = fields.Int(allow_none=True)
    contact_id = fields.Int(allow_none=True)
    deal_id = fields.Int(allow_none=True)
    due_date = fields.Date(allow_none=True)
    priority = fields.Str(
        validate=validate.OneOf(['Düşük', 'Normal', 'Yüksek', 'Acil']),
        load_default='Normal'
    )
    status = fields.Str(
        validate=validate.OneOf(['Beklemede', 'Devam Ediyor', 'Tamamlandı', 'İptal Edildi']),
        load_default='Beklemede'
    )
    category = fields.Str(allow_none=True, validate=validate.Length(max=100))
    reminder_date = fields.DateTime(allow_none=True)


class TaskUpdateSchema(Schema):
    """Task güncelleme şeması."""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True)
    assigned_to_user_id = fields.Int(allow_none=True)
    contact_id = fields.Int(allow_none=True)
    deal_id = fields.Int(allow_none=True)
    due_date = fields.Date(allow_none=True)
    completion_date = fields.DateTime(allow_none=True)
    priority = fields.Str(validate=validate.OneOf(['Düşük', 'Normal', 'Yüksek', 'Acil']))
    status = fields.Str(validate=validate.OneOf(['Beklemede', 'Devam Ediyor', 'Tamamlandı', 'İptal Edildi']))
    category = fields.Str(allow_none=True, validate=validate.Length(max=100))
    reminder_date = fields.DateTime(allow_none=True)


class InteractionSchema(SQLAlchemyAutoSchema):
    """Interaction şeması."""
    class Meta:
        model = Interaction
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    contact_name = fields.Method("get_contact_name")
    
    def get_contact_name(self, obj):
        if obj.contact:
            return f"{obj.contact.ad or ''} {obj.contact.soyad or ''}".strip()
        return None


class InteractionCreateSchema(Schema):
    """Interaction oluşturma şeması."""
    contact_id = fields.Int(required=True)
    deal_id = fields.Int(allow_none=True)
    interaction_type = fields.Str(
        required=True,
        validate=validate.OneOf(['Telefon', 'Email', 'Toplantı', 'Not'])
    )
    subject = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    notes = fields.Str(allow_none=True)
    interaction_date = fields.DateTime(allow_none=True)


class CRMStatsSchema(Schema):
    """CRM istatistikleri şeması."""
    total_contacts = fields.Int()
    total_companies = fields.Int()
    total_deals = fields.Int()
    total_tasks = fields.Int()
    active_deals_value = fields.Decimal(places=2)
    won_deals_value = fields.Decimal(places=2)
    overdue_tasks = fields.Int()
    recent_interactions = fields.Int()

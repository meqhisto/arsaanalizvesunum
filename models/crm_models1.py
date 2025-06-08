from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text
from models.db import db

class Contact(db.Model):
    __tablename__ = "crm_contacts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("crm_companies.id"), nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    role = db.Column(db.String(100))
    status = db.Column(db.String(50), default="Lead")
    source = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Yeni alanlar
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    birthday = db.Column(db.Date)
    linkedin = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    tags = db.Column(db.String(255))  # Virgülle ayrılmış etiketler
    lead_score = db.Column(db.Integer, default=0)  # 0-100 arası puanlama
    last_contact_date = db.Column(db.DateTime)
    
    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_contacts", lazy="dynamic"))
    interactions = db.relationship("Interaction", backref="contact", lazy="dynamic", cascade="all, delete-orphan")
    deals = db.relationship("Deal", backref="contact", lazy="dynamic", cascade="all, delete-orphan")
    tasks = db.relationship("Task", foreign_keys="[Task.contact_id]", backref="contact_tasks", lazy="dynamic", cascade="all, delete-orphan")
    activities = db.relationship("Activity", backref="contact", lazy="dynamic", cascade="all, delete-orphan")
    
    __table_args__ = (db.UniqueConstraint('user_id', 'email', name='uq_user_contact_email'),)
    
    def __repr__(self):
        return f"<Contact {self.first_name} {self.last_name}>"
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Contact nesnesini dictionary'ye dönüştürür"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'status': self.status,
            'source': self.source,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'postal_code': self.postal_code,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'linkedin': self.linkedin,
            'twitter': self.twitter,
            'tags': self.tags,
            'lead_score': self.lead_score,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None
        }


class Company(db.Model):
    __tablename__ = "crm_companies"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100))
    website = db.Column(db.String(200))
    address = db.Column(db.Text)
    phone = db.Column(db.String(30))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Yeni alanlar
    logo = db.Column(db.String(255))  # Logo dosya yolu
    email = db.Column(db.String(120))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    employee_count = db.Column(db.Integer)
    annual_revenue = db.Column(db.Numeric(15, 2))
    linkedin = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    facebook = db.Column(db.String(255))
    tags = db.Column(db.String(255))  # Virgülle ayrılmış etiketler
    
    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_companies", lazy="dynamic"))
    contacts = db.relationship("Contact", backref="company", lazy="dynamic")
    deals = db.relationship("Deal", backref="company", lazy="dynamic", cascade="all, delete-orphan")
    activities = db.relationship("Activity", backref="company", lazy="dynamic", cascade="all, delete-orphan")
    
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='uq_user_company_name'),)
    
    def __repr__(self):
        return f"<Company {self.name}>"
    
    def to_dict(self):
        """Company nesnesini dictionary'ye dönüştürür"""
        return {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'website': self.website,
            'address': self.address,
            'phone': self.phone,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'logo': self.logo,
            'email': self.email,
            'city': self.city,
            'country': self.country,
            'postal_code': self.postal_code,
            'employee_count': self.employee_count,
            'annual_revenue': float(self.annual_revenue) if self.annual_revenue else None,
            'linkedin': self.linkedin,
            'twitter': self.twitter,
            'facebook': self.facebook,
            'tags': self.tags,
            'contact_count': self.contacts.count()
        }


class Interaction(db.Model):
    __tablename__ = "crm_interactions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=False)
    deal_id = db.Column(db.Integer, db.ForeignKey("crm_deals.id"), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    interaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Yeni alanlar
    outcome = db.Column(db.Text)
    next_steps = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer)
    location = db.Column(db.String(255))
    attachments = db.Column(db.Text)  # JSON formatında dosya yolları
    
    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_interactions", lazy="dynamic"))
    
    def __repr__(self):
        return f"<Interaction {self.id} - {self.type}>"
    
    def to_dict(self):
        """Interaction nesnesini dictionary'ye dönüştürür"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'contact_name': f"{self.contact.first_name} {self.contact.last_name}" if self.contact else None,
            'deal_id': self.deal_id,
            'deal_title': self.deal.title if self.deal else None,
            'type': self.type,
            'interaction_date': self.interaction_date.isoformat() if self.interaction_date else None,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'outcome': self.outcome,
            'next_steps': self.next_steps,
            'duration_minutes': self.duration_minutes,
            'location': self.location,
            'attachments': self.attachments
        }


class Deal(db.Model):
    __tablename__ = "crm_deals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("crm_companies.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Numeric(15, 2), default=0.00)
    currency = db.Column(db.String(10), default="TRY")
    stage = db.Column(db.String(50), default="Potansiyel")
    expected_close_date = db.Column(db.Date)
    actual_close_date = db.Column(db.Date, nullable=True)
    probability = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Yeni alanlar
    source = db.Column(db.String(100))
    loss_reason = db.Column(db.String(255))
    win_reason = db.Column(db.String(255))
    products = db.Column(db.Text)  # JSON formatında ürün bilgileri
    tags = db.Column(db.String(255))  # Virgülle ayrılmış etiketler
    priority = db.Column(db.String(20), default="Normal")  # Düşük, Normal, Yüksek
    attachments = db.Column(db.Text)  # JSON formatında dosya yolları
    
    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_deals", lazy="dynamic"))
    interactions = db.relationship("Interaction", backref="deal", lazy="dynamic", cascade="all, delete-orphan")
    tasks = db.relationship("Task", foreign_keys="[Task.deal_id]", backref="deal_tasks", lazy="dynamic", cascade="all, delete-orphan")
    activities = db.relationship("Activity", backref="deal", lazy="dynamic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Deal {self.title} - {self.value} {self.currency}>"
    
    def to_dict(self):
        """Deal nesnesini dictionary'ye dönüştürür"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'contact_name': f"{self.contact.first_name} {self.contact.last_name}" if self.contact else None,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else None,
            'title': self.title,
            'value': float(self.value) if self.value else 0.0,
            'currency': self.currency,
            'stage': self.stage,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'actual_close_date': self.actual_close_date.isoformat() if self.actual_close_date else None,
            'probability': self.probability,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'source': self.source,
            'loss_reason': self.loss_reason,
            'win_reason': self.win_reason,
            'products': self.products,
            'tags': self.tags,
            'priority': self.priority,
            'attachments': self.attachments
        }


class Task(db.Model):
    __tablename__ = "crm_tasks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey("crm_deals.id"), nullable=True)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default="Beklemede")
    priority = db.Column(db.String(50), default="Normal")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Yeni alanlar
    completion_date = db.Column(db.DateTime)
    reminder_date = db.Column(db.DateTime)
    recurrence = db.Column(db.String(50))  # Günlük, Haftalık, Aylık, vb.
    recurrence_end_date = db.Column(db.Date)
    category = db.Column(db.String(100))
    attachments = db.Column(db.Text)  # JSON formatında dosya yolları
    
    # İlişkiler
    owner_user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("owned_crm_tasks", lazy="dynamic"))
    assigned_user = db.relationship("User", foreign_keys=[assigned_to_user_id], backref=db.backref("assigned_crm_tasks", lazy="dynamic"))
    activities = db.relationship("Activity", backref="task", lazy="dynamic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task {self.title} - {self.status}>"
    
    def to_dict(self):
        """Task nesnesini dictionary'ye dönüştürür"""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'contact_name': f"{self.contact_tasks.first_name} {self.contact_tasks.last_name}" if self.contact_id else None,
            'deal_id': self.deal_id,
            'deal_title': self.deal_tasks.title if self.deal_id else None,
            'assigned_to_user_id': self.assigned_to_user_id,
            'assigned_user_name': f"{self.assigned_user.ad} {self.assigned_user.soyad}" if self.assigned_user else None,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'recurrence': self.recurrence,
            'recurrence_end_date': self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
            'category': self.category,
            'attachments': self.attachments
        }


class Activity(db.Model):
    """CRM aktivitelerini takip etmek için yeni model"""
    __tablename__ = "crm_activities"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("crm_companies.id"), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey("crm_deals.id"), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey("crm_tasks.id"), nullable=True)
    
    activity_type = db.Column(db.String(50), nullable=False)  # Oluşturma, Güncelleme, Silme, vb.
    entity_type = db.Column(db.String(50), nullable=False)  # Contact, Company, Deal, Task, vb.
    entity_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_activities", lazy="dynamic"))
    
    def __repr__(self):
        return f"<Activity {self.activity_type} - {self.entity_type} {self.entity_id}>"
    
    def to_dict(self):
        """Activity nesnesini dictionary'ye dönüştürür"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': f"{self.user.ad} {self.user.soyad}" if self.user else None,
            'contact_id': self.contact_id,
            'company_id': self.company_id,
            'deal_id': self.deal_id,
            'task_id': self.task_id,
            'activity_type': self.activity_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# CRM Ayarları için yeni model
class CrmSettings(db.Model):
    """Kullanıcı bazlı CRM ayarları"""
    __tablename__ = "crm_settings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    
    # Genel ayarlar
    default_currency = db.Column(db.String(10), default="TRY")
    date_format = db.Column(db.String(20), default="DD.MM.YYYY")
    time_format = db.Column(db.String(20), default="HH:mm")
    
    # Kişi/Şirket ayarları
    contact_statuses = db.Column(db.Text, default='["Lead", "Prospect", "Customer", "Inactive"]')  # JSON formatında
    deal_stages = db.Column(db.Text, default='["Potansiyel", "İlk Görüşme", "Teklif", "Müzakere", "Kazanıldı", "Kaybedildi"]')  # JSON formatında
    task_statuses = db.Column(db.Text, default='["Beklemede", "Devam Ediyor", "Tamamlandı", "İptal Edildi"]')  # JSON formatında
    task_priorities = db.Column(db.Text, default='["Düşük", "Normal", "Yüksek", "Acil"]')  # JSON formatında
    
    # E-posta bildirimleri
    email_notifications = db.Column(db.Boolean, default=True)
    notification_types = db.Column(db.Text, default='["task_due", "deal_update", "new_contact"]')  # JSON formatında
    
    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_settings", uselist=False))
    
    def __repr__(self):
        return f"<CrmSettings for user {self.user_id}>"

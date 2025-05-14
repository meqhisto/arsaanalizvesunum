# models/crm_models.py
from datetime import datetime
from sqlalchemy import UniqueConstraint # UniqueConstraint için
from . import db
from .user_models import User # User ilişkisi için

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
    # CRM v2 için eklenen alanlar
    segment = db.Column(db.String(50), default='Potansiyel') # Potansiyel, Aktif, Pasif, VIP, Kaybedilen
    value_score = db.Column(db.Integer, default=0) # 0-100 arası bir değer puanı
    tags = db.Column(db.JSON) # Etiketler için JSON alanı (["etiket1", "etiket2"])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("crm_contacts_owned", lazy="dynamic")) # backref adı güncellendi
    # company ilişkisi Company modelinde backref ile tanımlanacak
    interactions = db.relationship("Interaction", backref="contact", lazy="dynamic", cascade="all, delete-orphan")
    deals = db.relationship("Deal", backref="contact", lazy="dynamic", cascade="all, delete-orphan")
    # Task ilişkisi Task modelinde backref ile tanımlanacak

    __table_args__ = (UniqueConstraint('user_id', 'email', name='uq_user_contact_email'),)

    def __repr__(self):
        return f"<Contact {self.first_name} {self.last_name}>"

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

    user = db.relationship("User", backref=db.backref("crm_companies_owned", lazy="dynamic")) # backref adı
    contacts = db.relationship("Contact", backref="company", lazy="dynamic") # Contact'a company_id üzerinden bağlanır
    deals = db.relationship("Deal", backref="company", lazy="dynamic", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('user_id', 'name', name='uq_user_company_name'),)

    def __repr__(self):
        return f"<Company {self.name}>"

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

    user = db.relationship("User", backref=db.backref("crm_interactions_created", lazy="dynamic")) # backref adı
    # contact ilişkisi Contact modelinde backref ile tanımlı
    # deal ilişkisi Deal modelinde backref ile tanımlanacak

    def __repr__(self):
        return f"<Interaction {self.type} on {self.interaction_date.strftime('%Y-%m-%d')}>"

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

    user = db.relationship("User", backref=db.backref("crm_deals_owned", lazy="dynamic")) # backref
    # contact ve company ilişkileri ilgili modellerde backref ile tanımlı
    interactions = db.relationship("Interaction", backref="deal", lazy="dynamic", cascade="all, delete-orphan")
    # tasks ilişkisi Task modelinde tanımlanacak

    def __repr__(self):
        return f"<Deal {self.title}>"

class Task(db.Model):
    __tablename__ = "crm_tasks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False) # Oluşturan
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey("crm_deals.id"), nullable=True)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True) # Atanan

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default="Beklemede")
    priority = db.Column(db.String(50), default="Normal")

    # CRM V2 Eklemeler
    reminder_enabled = db.Column(db.Boolean, default=False)
    reminder_time = db.Column(db.DateTime, nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_type = db.Column(db.String(20), nullable=True) # Günlük, Haftalık, Aylık
    recurrence_interval = db.Column(db.Integer, default=1, nullable=True) # örn: Her 2 haftada bir
    recurrence_end_date = db.Column(db.Date, nullable=True) # Tekrarlama bitiş tarihi
    completed_at = db.Column(db.DateTime, nullable=True) # Görevin tamamlandığı tarih
    # Ekip yönetimi için alanlar
    team_id = db.Column(db.Integer, db.ForeignKey('crm_teams.id'), nullable=True) # Eğer CRM_Teams modeli varsa
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Görevi atayan (broker için)
    previous_assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Önceki atanan
    reassigned_at = db.Column(db.DateTime, nullable=True) # Yeniden atama tarihi
    reassigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Yeniden atayan kişi
    reassignment_reason = db.Column(db.Text, nullable=True) # Yeniden atama sebebi
    task_type = db.Column(db.String(50), default='personal') # personal, team, supervised

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner_user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("owned_crm_tasks", lazy="dynamic"))
    assigned_user = db.relationship("User", foreign_keys=[assigned_to_user_id], backref=db.backref("assigned_crm_tasks", lazy="dynamic"))
    assigned_by = db.relationship("User", foreign_keys=[assigned_by_user_id], backref=db.backref("delegated_crm_tasks", lazy="dynamic"))
    previous_assignee_user = db.relationship("User", foreign_keys=[previous_assignee_id], backref=db.backref("previously_assigned_crm_tasks", lazy="dynamic"))
    reassigned_by_user = db.relationship("User", foreign_keys=[reassigned_by_id], backref=db.backref("reassigned_crm_tasks_by", lazy="dynamic"))


    contact = db.relationship("Contact", foreign_keys=[contact_id], backref=db.backref("contact_tasks", lazy="dynamic"))
    deal = db.relationship("Deal", foreign_keys=[deal_id], backref=db.backref("deal_tasks", lazy="dynamic"))

    def __repr__(self):
        return f"<Task {self.title}>"

# CrmTeam modeli (Ekip Yönetimi için)
class CrmTeam(db.Model):
    __tablename__ = 'crm_teams'
    id = db.Column(db.Integer, primary_key=True)
    broker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Takım lideri (Broker)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    broker = db.relationship('User', foreign_keys=[broker_id], backref='led_teams')
    members = db.relationship('User', secondary='crm_team_members', backref=db.backref('teams_part_of', lazy='dynamic'))
    tasks = db.relationship('Task', backref='team', lazy='dynamic') # Takıma atanan görevler

# CrmTeamMembers ara tablosu
crm_team_members = db.Table('crm_team_members',
    db.Column('team_id', db.Integer, db.ForeignKey('crm_teams.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)
# models/office_models.py
from datetime import datetime
from . import db

class Office(db.Model):
    __tablename__ = "offices"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    logo_path = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Ofis sahibi (Broker)
    # owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('owned_office', uselist=False)) # Bir ofisin tek sahibi

    def __repr__(self):
        return f"<Office {self.name}>"
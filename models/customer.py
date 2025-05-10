from models.db import db
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customers'
    __table_args__ = {'extend_existing': True}  # Add this to handle metadata conflicts
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    title = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationship with User
    user = db.relationship('User', backref=db.backref('customers', lazy=True))

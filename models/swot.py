from app import db
from datetime import datetime

class SwotTemplate(db.Model):
    __tablename__ = 'swot_templates'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # 'arsa', 'ticari', 'konut' vb.
    type = db.Column(db.String(20), nullable=False)  # 'strength', 'weakness', 'opportunity', 'threat'
    text = db.Column(db.String(500), nullable=False)
    impact_score = db.Column(db.Integer)  # 1-5 arası etki puanı
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class SwotAnalysis(db.Model):
    __tablename__ = 'swot_analyses'
    id = db.Column(db.Integer, primary_key=True)
    arsa_analiz_id = db.Column(db.Integer, db.ForeignKey('arsa_analizleri.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    impact_score = db.Column(db.Integer)
    template_id = db.Column(db.Integer, db.ForeignKey('swot_templates.id'), nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    arsa_analiz = db.relationship('ArsaAnaliz', backref=db.backref('swot_items', lazy=True))
    template = db.relationship('SwotTemplate', backref=db.backref('uses', lazy=True))

# from models.db import db
# from datetime import datetime

# class PortfolioTag(db.Model):
#     __tablename__ = 'portfolio_tags'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), nullable=False)
#     color = db.Column(db.String(7), default='#007bff')  # Hex color code
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

# class PortfolioGroup(db.Model):
#     __tablename__ = 'portfolio_groups'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     description = db.Column(db.Text)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# class Portfolio(db.Model):
#     __tablename__ = 'portfolios'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     description = db.Column(db.Text)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     group_id = db.Column(db.Integer, db.ForeignKey('portfolio_groups.id'))
#     status = db.Column(db.String(20), default='active')
#     target_value = db.Column(db.Numeric(15, 2))
#     risk_tolerance = db.Column(db.Integer)  # 1-10 arası risk toleransı
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

#     # Relationships
#     group = db.relationship('PortfolioGroup', backref='portfolios')
#     tags = db.relationship('PortfolioTag', secondary='portfolio_tag_associations', backref='portfolios')
#     performance_history = db.relationship('PortfolioPerformance', backref='portfolio', lazy='dynamic')

# # Association table for many-to-many relationship between Portfolio and PortfolioTag
# portfolio_tag_associations = db.Table('portfolio_tag_associations',
#     db.Column('portfolio_id', db.Integer, db.ForeignKey('portfolios.id'), primary_key=True),
#     db.Column('tag_id', db.Integer, db.ForeignKey('portfolio_tags.id'), primary_key=True)
# )

# class PortfolioPerformance(db.Model):
#     __tablename__ = 'portfolio_performance'
#     id = db.Column(db.Integer, primary_key=True)
#     portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
#     total_value = db.Column(db.Numeric(15, 2), nullable=False)
#     value_change = db.Column(db.Numeric(15, 2))
#     change_percentage = db.Column(db.Numeric(5, 2))
#     risk_score = db.Column(db.Integer)  # 1-10 arası risk skoru
#     measurement_date = db.Column(db.DateTime, default=datetime.utcnow)

# class Customer(db.Model):
#     __tablename__ = 'customers'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     name = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(120))
#     phone = db.Column(db.String(20))
#     company = db.Column(db.String(100))
#     title = db.Column(db.String(100))
#     address = db.Column(db.Text)
#     customer_type = db.Column(db.String(20))  # bireysel/kurumsal
#     notes = db.Column(db.Text)
#     status = db.Column(db.String(20), default='active')
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# class Appointment(db.Model):
#     __tablename__ = 'appointments'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
#     title = db.Column(db.String(200), nullable=False)
#     description = db.Column(db.Text)
#     start_time = db.Column(db.DateTime, nullable=False)
#     end_time = db.Column(db.DateTime, nullable=False)
#     location = db.Column(db.String(200))
#     status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
#     reminder = db.Column(db.Boolean, default=True)
#     reminder_time = db.Column(db.Integer, default=30)  # Dakika cinsinden hatırlatma süresi
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

# class CustomerInteraction(db.Model):
#     __tablename__ = 'customer_interactions'
#     id = db.Column(db.Integer, primary_key=True)
#     customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
#     interaction_type = db.Column(db.String(50))  # call, email, meeting, etc.
#     description = db.Column(db.Text)
#     date = db.Column(db.DateTime, default=datetime.utcnow)
#     outcome = db.Column(db.String(50))
#     next_action = db.Column(db.String(200))
#     next_action_date = db.Column(db.DateTime)
#     created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

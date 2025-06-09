"""
Unit tests for database models
"""

import pytest
from datetime import datetime
from models.user_models import User, Office
from models.crm_models import Contact, Task, Deal
from models.arsa_models import ArsaAnaliz
from models import db
from werkzeug.security import check_password_hash, generate_password_hash


class TestOfficeModel:
    """Test Office model functionality."""
    
    def test_office_creation(self, app):
        """Test office creation."""
        with app.app_context():
            office = Office(
                name="Test Office",
                address="123 Test St",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.commit()

            assert office.id is not None
            assert office.name == "Test Office"
            assert office.address == "123 Test St"
            assert office.phone == "555-0123"
            assert office.is_active is True
            assert office.created_at is not None
    
    def test_office_string_representation(self, app, test_office):
        """Test office string representation."""
        with app.app_context():
            office = Office.query.get(test_office)
            assert str(office) == office.name


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app, test_office):
        """Test user creation."""
        with app.app_context():
            user = User(
                ad="John",
                soyad="Doe",
                email="john@example.com",
                password_hash=generate_password_hash("password123"),
                role="danisman",
                office_id=test_office  # test_office is now an ID
            )
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.ad == "John"
            assert user.soyad == "Doe"
            assert user.email == "john@example.com"
            assert user.role == "danisman"
            assert user.office_id == test_office
            assert user.created_at is not None
    
    def test_user_password_hashing(self, app, test_office):
        """Test password hashing functionality."""
        with app.app_context():
            password = "securepassword123"
            user = User(
                ad="Test",
                soyad="User",
                email="test@example.com",
                password_hash=generate_password_hash(password),
                role="danisman",
                office_id=test_office.id
            )
            
            # Password should be hashed
            assert user.password_hash != password
            # Should be able to verify password
            assert check_password_hash(user.password_hash, password)
            assert not check_password_hash(user.password_hash, "wrongpassword")
    
    def test_user_full_name_property(self, app, test_user):
        """Test user full name property."""
        with app.app_context():
            assert test_user.full_name == f"{test_user.ad} {test_user.soyad}"
    
    def test_user_office_relationship(self, app, test_user, test_office):
        """Test user-office relationship."""
        with app.app_context():
            assert test_user.office == test_office
            assert test_user in test_office.users


class TestContactModel:
    """Test Contact model functionality."""
    
    def test_contact_creation(self, app, test_user):
        """Test contact creation."""
        with app.app_context():
            contact = Contact(
                ad="Jane",
                soyad="Smith",
                email="jane@example.com",
                telefon="555-0456",
                user_id=test_user.id,
                status="lead"
            )
            db.session.add(contact)
            db.session.commit()
            
            assert contact.id is not None
            assert contact.ad == "Jane"
            assert contact.soyad == "Smith"
            assert contact.email == "jane@example.com"
            assert contact.telefon == "555-0456"
            assert contact.user_id == test_user.id
            assert contact.status == "lead"
            assert contact.created_at is not None
    
    def test_contact_full_name_property(self, app, test_contact):
        """Test contact full name property."""
        with app.app_context():
            assert test_contact.full_name == f"{test_contact.ad} {test_contact.soyad}"
    
    def test_contact_user_relationship(self, app, test_contact, test_user):
        """Test contact-user relationship."""
        with app.app_context():
            assert test_contact.user == test_user
            assert test_contact in test_user.contacts


class TestArsaAnalyzModel:
    """Test ArsaAnaliz model functionality."""
    
    def test_analysis_creation(self, app, test_user):
        """Test analysis creation."""
        with app.app_context():
            analysis = ArsaAnaliz(
                baslik="Test Analysis",
                il="İstanbul",
                ilce="Beşiktaş",
                mahalle="Levent",
                user_id=test_user.id,
                durum="devam_ediyor"
            )
            db.session.add(analysis)
            db.session.commit()
            
            assert analysis.id is not None
            assert analysis.baslik == "Test Analysis"
            assert analysis.il == "İstanbul"
            assert analysis.ilce == "Beşiktaş"
            assert analysis.mahalle == "Levent"
            assert analysis.user_id == test_user.id
            assert analysis.durum == "devam_ediyor"
            assert analysis.created_at is not None
    
    def test_analysis_user_relationship(self, app, test_analysis, test_user):
        """Test analysis-user relationship."""
        with app.app_context():
            assert test_analysis.user == test_user
            assert test_analysis in test_user.analyses


class TestTaskModel:
    """Test Task model functionality."""
    
    def test_task_creation(self, app, test_user, test_contact):
        """Test task creation."""
        with app.app_context():
            task = Task(
                title="Follow up call",
                description="Call the client about the proposal",
                user_id=test_user.id,
                contact_id=test_contact.id,
                status="pending",
                priority="high",
                due_date=datetime.now()
            )
            db.session.add(task)
            db.session.commit()
            
            assert task.id is not None
            assert task.title == "Follow up call"
            assert task.description == "Call the client about the proposal"
            assert task.user_id == test_user.id
            assert task.contact_id == test_contact.id
            assert task.status == "pending"
            assert task.priority == "high"
            assert task.due_date is not None
            assert task.created_at is not None
    
    def test_task_relationships(self, app, test_user, test_contact):
        """Test task relationships."""
        with app.app_context():
            task = Task(
                title="Test Task",
                user_id=test_user.id,
                contact_id=test_contact.id,
                status="pending"
            )
            db.session.add(task)
            db.session.commit()
            
            assert task.user == test_user
            assert task.contact == test_contact
            assert task in test_user.tasks
            assert task in test_contact.tasks


class TestDealModel:
    """Test Deal model functionality."""
    
    def test_deal_creation(self, app, test_user, test_contact):
        """Test deal creation."""
        with app.app_context():
            deal = Deal(
                title="Property Sale",
                description="Selling a 3-bedroom apartment",
                user_id=test_user.id,
                contact_id=test_contact.id,
                value=500000.00,
                status="negotiation",
                stage="proposal"
            )
            db.session.add(deal)
            db.session.commit()
            
            assert deal.id is not None
            assert deal.title == "Property Sale"
            assert deal.description == "Selling a 3-bedroom apartment"
            assert deal.user_id == test_user.id
            assert deal.contact_id == test_contact.id
            assert deal.value == 500000.00
            assert deal.status == "negotiation"
            assert deal.stage == "proposal"
            assert deal.created_at is not None
    
    def test_deal_relationships(self, app, test_user, test_contact):
        """Test deal relationships."""
        with app.app_context():
            deal = Deal(
                title="Test Deal",
                user_id=test_user.id,
                contact_id=test_contact.id,
                value=100000.00,
                status="active"
            )
            db.session.add(deal)
            db.session.commit()
            
            assert deal.user == test_user
            assert deal.contact == test_contact
            assert deal in test_user.deals
            assert deal in test_contact.deals


class TestModelValidation:
    """Test model validation and constraints."""
    
    def test_user_email_uniqueness(self, app, test_office):
        """Test that user emails must be unique."""
        with app.app_context():
            # Create first user
            user1 = User(
                ad="User",
                soyad="One",
                email="same@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=test_office.id
            )
            db.session.add(user1)
            db.session.commit()
            
            # Try to create second user with same email
            user2 = User(
                ad="User",
                soyad="Two",
                email="same@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=test_office.id
            )
            db.session.add(user2)
            
            # Should raise an integrity error
            with pytest.raises(Exception):
                db.session.commit()
    
    def test_required_fields(self, app, test_office):
        """Test that required fields are enforced."""
        with app.app_context():
            # User without email should fail
            user = User(
                ad="Test",
                soyad="User",
                # email missing
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=test_office.id
            )
            db.session.add(user)
            
            with pytest.raises(Exception):
                db.session.commit()

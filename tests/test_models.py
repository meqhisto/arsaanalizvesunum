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
            # Refresh the object to avoid DetachedInstanceError
            db.session.add(test_office)
            assert str(test_office) == f"<Office {test_office.name}>"


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app):
        """Test user creation."""
        with app.app_context():
            # Create office first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="John",
                soyad="Doe",
                email="john@example.com",
                password_hash=generate_password_hash("password123"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.ad == "John"
            assert user.soyad == "Doe"
            assert user.email == "john@example.com"
            assert user.role == "danisman"
            assert user.office_id == office.id
            assert user.registered_on is not None  # User model uses registered_on, not created_at
    
    def test_user_password_hashing(self, app):
        """Test password hashing functionality."""
        with app.app_context():
            # Create office first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            password = "securepassword123"
            user = User(
                ad="Test",
                soyad="User",
                email="test_hash@example.com",
                password_hash=generate_password_hash(password),
                role="danisman",
                office_id=office.id
            )

            # Password should be hashed
            assert user.password_hash != password
            # Should be able to verify password
            assert check_password_hash(user.password_hash, password)
            assert not check_password_hash(user.password_hash, "wrongpassword")
    
    def test_user_full_name_property(self, app):
        """Test user full name property."""
        with app.app_context():
            # Create office first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="John",
                soyad="Doe",
                email="fullname@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.commit()

            assert user.full_name == "John Doe"
    
    def test_user_office_relationship(self, app):
        """Test user-office relationship."""
        with app.app_context():
            # Create office first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="John",
                soyad="Doe",
                email="relationship@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.commit()

            # Test relationships
            assert user.office == office
            assert user in office.users


class TestContactModel:
    """Test Contact model functionality."""
    
    def test_contact_creation(self, app):
        """Test contact creation."""
        with app.app_context():
            # Create office and user first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="testuser@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            contact = Contact(
                ad="Jane",
                soyad="Smith",
                email="jane@example.com",
                telefon="555-0456",
                user_id=user.id,
                status="lead"
            )
            db.session.add(contact)
            db.session.commit()

            assert contact.id is not None
            assert contact.ad == "Jane"
            assert contact.soyad == "Smith"
            assert contact.email == "jane@example.com"
            assert contact.telefon == "555-0456"
            assert contact.user_id == user.id
            assert contact.status == "lead"
            assert contact.created_at is not None
    
    def test_contact_full_name_property(self, app):
        """Test contact full name property."""
        with app.app_context():
            # Create office and user first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="testuser2@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            contact = Contact(
                ad="John",
                soyad="Doe",
                email="john.doe@example.com",
                user_id=user.id,
                status="lead"
            )
            db.session.add(contact)
            db.session.commit()

            assert contact.full_name == "John Doe"
    
    def test_contact_user_relationship(self, app):
        """Test contact-user relationship."""
        with app.app_context():
            # Create office and user first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="testuser3@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            contact = Contact(
                ad="Jane",
                soyad="Smith",
                email="jane.smith@example.com",
                user_id=user.id,
                status="lead"
            )
            db.session.add(contact)
            db.session.commit()

            # Test relationships
            assert contact.user == user
            assert contact in user.crm_contacts_owned


class TestArsaAnalyzModel:
    """Test ArsaAnaliz model functionality."""
    
    def test_analysis_creation(self, app):
        """Test analysis creation."""
        with app.app_context():
            # Create office and user first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="analysisuser@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            analysis = ArsaAnaliz(
                il="İstanbul",
                ilce="Beşiktaş",
                mahalle="Levent",
                metrekare=1000.50,
                fiyat=500000.00,
                user_id=user.id,
                notlar="Test analysis notes"
            )
            db.session.add(analysis)
            db.session.commit()

            assert analysis.id is not None
            assert analysis.il == "İstanbul"
            assert analysis.ilce == "Beşiktaş"
            assert analysis.mahalle == "Levent"
            assert analysis.metrekare == 1000.50
            assert analysis.fiyat == 500000.00
            assert analysis.user_id == user.id
            assert analysis.notlar == "Test analysis notes"
            assert analysis.created_at is not None
    
    def test_analysis_user_relationship(self, app):
        """Test analysis-user relationship."""
        with app.app_context():
            # Create office and user first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="analysisuser2@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            analysis = ArsaAnaliz(
                il="Ankara",
                ilce="Çankaya",
                mahalle="Kızılay",
                metrekare=750.25,
                fiyat=350000.00,
                user_id=user.id,
                notlar="Test analysis relationship notes"
            )
            db.session.add(analysis)
            db.session.commit()

            # Test relationships (using correct relationship names)
            assert analysis.user == user
            assert analysis in user.analizler_olusturdugu  # User model uses analizler_olusturdugu, not analyses


class TestTaskModel:
    """Test Task model functionality."""
    
    def test_task_creation(self, app):
        """Test task creation."""
        with app.app_context():
            # Create office, user and contact first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="taskuser@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            contact = Contact(
                ad="Task",
                soyad="Contact",
                email="taskcontact@example.com",
                user_id=user.id,
                status="lead"
            )
            db.session.add(contact)
            db.session.flush()

            task = Task(
                title="Follow up call",
                description="Call the client about the proposal",
                user_id=user.id,
                contact_id=contact.id,
                status="pending",
                priority="high",
                due_date=datetime.now()
            )
            db.session.add(task)
            db.session.commit()

            assert task.id is not None
            assert task.title == "Follow up call"
            assert task.description == "Call the client about the proposal"
            assert task.user_id == user.id
            assert task.contact_id == contact.id
            assert task.status == "pending"
            assert task.priority == "high"
            assert task.due_date is not None
            assert task.created_at is not None
    
    def test_task_relationships(self, app):
        """Test task relationships."""
        with app.app_context():
            # Create office, user and contact first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="taskuser2@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            contact = Contact(
                ad="Task",
                soyad="Contact",
                email="taskcontact2@example.com",
                user_id=user.id,
                status="lead"
            )
            db.session.add(contact)
            db.session.flush()

            task = Task(
                title="Test Task",
                user_id=user.id,
                contact_id=contact.id,
                status="pending"
            )
            db.session.add(task)
            db.session.commit()

            # Test relationships (using correct relationship names)
            assert task.owner_user == user  # Task model uses owner_user, not user
            assert task.contact == contact
            assert task in user.owned_crm_tasks  # User model uses owned_crm_tasks, not tasks
            assert task in contact.tasks


class TestDealModel:
    """Test Deal model functionality."""
    
    def test_deal_creation(self, app):
        """Test deal creation."""
        with app.app_context():
            # Create office, user and contact first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="dealuser@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            contact = Contact(
                ad="Deal",
                soyad="Contact",
                email="dealcontact@example.com",
                user_id=user.id,
                status="lead"
            )
            db.session.add(contact)
            db.session.flush()

            deal = Deal(
                title="Property Sale",
                notes="Selling a 3-bedroom apartment",  # Deal model has notes, not description
                user_id=user.id,
                contact_id=contact.id,
                value=500000.00,
                stage="proposal"  # Deal model uses stage, not status
            )
            db.session.add(deal)
            db.session.commit()

            assert deal.id is not None
            assert deal.title == "Property Sale"
            assert deal.notes == "Selling a 3-bedroom apartment"
            assert deal.user_id == user.id
            assert deal.contact_id == contact.id
            assert deal.value == 500000.00
            assert deal.stage == "proposal"
            assert deal.created_at is not None
    
    def test_deal_relationships(self, app):
        """Test deal relationships."""
        with app.app_context():
            # Create office, user and contact first
            office = Office(
                name="Test Office",
                address="Test Address",
                phone="555-0123"
            )
            db.session.add(office)
            db.session.flush()

            user = User(
                ad="Test",
                soyad="User",
                email="dealuser2@example.com",
                password_hash=generate_password_hash("password"),
                role="danisman",
                office_id=office.id
            )
            db.session.add(user)
            db.session.flush()

            contact = Contact(
                ad="Deal",
                soyad="Contact",
                email="dealcontact2@example.com",
                user_id=user.id,
                status="lead"
            )
            db.session.add(contact)
            db.session.flush()

            deal = Deal(
                title="Test Deal",
                user_id=user.id,
                contact_id=contact.id,
                value=100000.00,
                stage="active"  # Deal model uses stage, not status
            )
            db.session.add(deal)
            db.session.commit()

            # Test relationships (using correct relationship names)
            assert deal.user == user
            assert deal.contact == contact
            assert deal in user.crm_deals_owned  # User model uses crm_deals_owned, not deals
            assert deal in contact.deals


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

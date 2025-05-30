import unittest
from unittest.mock import patch, MagicMock, mock_open, PropertyMock
import os
from io import BytesIO
from flask import session, url_for, get_flashed_messages
from flask_login import login_user, logout_user, current_user, UserMixin
import sys

# Add project root to sys.path to allow importing project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app # Assuming app.py has create_app
from models import db as _db # Renamed to avoid conflict with potential fixtures
from models.user_models import User
from models.office_models import Office
from models.arsa_models import ArsaAnaliz, BolgeDagilimi, DashboardStats
from models.crm_models import Contact, Deal, Interaction, Task
# The blueprint to test is imported after app creation and context push in setUpClass usually
# from blueprints.main_bp import main_bp
from decimal import Decimal
import pytz

# Global dictionary to store mock users for the user_loader
# This needs to be accessible by the user_loader callback
_mock_users_for_loader = {}

# Mock User class for testing basic UserMixin properties
class MockFlaskLoginUser(UserMixin):
    def __init__(self, id, is_active_flag=True, role='danisman'):
        self.id = int(id)
        self.is_active_flag = is_active_flag
        self.role = role # For role_required decorator

    @property
    def is_active(self):
        return self.is_active_flag

    def get_id(self):
        return str(self.id)

class MainBlueprintTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing') # Create app once for the class
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for forms
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['LOGIN_DISABLED'] = False # Ensure Flask-Login is active
        cls.app.config['SECRET_KEY'] = 'test_secret_key_for_main_bp' # For session
        cls.app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

        # Configure UPLOAD_FOLDER for tests
        cls.test_upload_folder = os.path.join(os.path.dirname(__file__), 'test_uploads_main_bp')
        os.makedirs(cls.test_upload_folder, exist_ok=True)
        # Ensure UPLOAD_FOLDER is set on the app instance after creation
        cls.app.config["UPLOAD_FOLDER"] = cls.test_upload_folder
        profiles_dir = os.path.join(cls.test_upload_folder, "profiles")
        os.makedirs(profiles_dir, exist_ok=True)


        # Flask-Login setup is part of create_app, but user_loader needs to be specific for tests
        # We'll re-bind it here if create_app's one is too generic.
        # The user_loader in create_app uses User.query.get, which is fine if we populate the DB.
        # For more control, we can override it or use a mock DB.
        # For these tests, we will populate the in-memory DB with User instances.

        @cls.app.login_manager.user_loader
        def load_test_user(user_id):
            # This will load users from the in-memory SQLite DB for tests
            return _db.session.get(User, int(user_id))


        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        # _db.init_app(cls.app) # init_db_models in create_app already does this
        _db.create_all() # Create all tables based on models known to _db

    @classmethod
    def tearDownClass(cls):
        _db.session.remove()
        _db.drop_all()
        cls.app_context.pop()

        if os.path.exists(cls.test_upload_folder):
            for root, dirs, files in os.walk(cls.test_upload_folder, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except OSError:
                        pass # Ignore if file is already removed or locked
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError:
                        pass
            try:
                os.rmdir(cls.test_upload_folder)
            except OSError:
                pass


    def setUp(self):
        self.client = self.app.test_client()
        _db.session.begin_nested() # Use nested transactions for test isolation

        # Create a default user for login if needed for multiple tests
        self.default_user = User(id=1, email='default@example.com', ad='Default', soyad='User', role='danisman')
        self.default_user.set_password('password123')
        _db.session.add(self.default_user)
        _db.session.commit()


    def tearDown(self):
        _db.session.rollback() # Rollback the nested transaction
        # Clean all tables after each test to ensure independence
        # This is more robust than relying on rollback alone for all cases.
        meta = _db.metadata
        for table in reversed(meta.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()

        with self.app.test_request_context():
            if current_user.is_authenticated:
                logout_user()


    def _login(self, user_email, password):
        user = User.query.filter_by(email=user_email).first()
        if not user: # If user not in DB, create a mock one for login purposes
            # This path is less ideal, prefer adding users to DB in setUp
            mock_user_for_login = MockFlaskLoginUser(id=999, role='danisman')
            with self.app.test_request_context():
                login_user(mock_user_for_login)
            return mock_user_for_login

        # For users from DB
        with self.app.test_request_context():
            login_user(user)
        return user

    def _logout_user(self):
        with self.app.test_request_context():
            logout_user()

    def test_home_unauthenticated(self):
        response = self.client.get(url_for('main.home'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(url_for('auth.login') in response.location)

    def test_home_authenticated(self):
        self._login('default@example.com', 'password123')
        response = self.client.get(url_for('main.home'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(url_for('main.index') in response.location)
        self._logout_user()

    def test_index_unauthenticated(self):
        response = self.client.get(url_for('main.index'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(url_for('auth.login') in response.location)

    @patch('blueprints.main_bp.ArsaAnaliz.query')
    @patch('blueprints.main_bp.DashboardStats.query')
    # Add other necessary patches for db queries in index
    def test_index_authenticated(self, mock_dash_stats_query, mock_arsa_query):
        self._login('default@example.com', 'password123')

        mock_arsa_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        # Simulate no stats existing, so one is created
        mock_dash_stats_query.filter_by.return_value.first.return_value = None

        # Mock for arsa_bolge_dagilimi (db.session.query)
        mock_session_query_arsa_bolge = MagicMock()
        mock_session_query_arsa_bolge.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []
        
        # Mock for toplam_arsa_degeri (db.session.query)
        mock_session_query_sum_fiyat = MagicMock()
        mock_session_query_sum_fiyat.filter_by.return_value.scalar.return_value = Decimal('0.00')

        # Mock for toplam_acik_firsat_degeri_try (db.session.query)
        mock_session_query_sum_deal_value = MagicMock()
        mock_session_query_sum_deal_value.filter.return_value.scalar.return_value = Decimal('0.00')


        with patch('blueprints.main_bp.db.session.query') as mock_db_session_query, \
             patch('blueprints.main_bp.BolgeDagilimi.query') as mock_bolge_query, \
             patch('blueprints.main_bp.Task.query') as mock_task_query, \
             patch('blueprints.main_bp.Contact.query') as mock_contact_query, \
             patch('blueprints.main_bp.Deal.query') as mock_deal_query, \
             patch('blueprints.main_bp.Interaction.query') as mock_interaction_query:

            def query_side_effect(*args, **kwargs):
                if args and args[0] == ArsaAnaliz.il: # arsa_bolge_dagilimi
                    return mock_session_query_arsa_bolge
                if args and hasattr(args[0], 'name') and args[0].name == 'sum': # For sum queries
                    if 'fiyat' in str(args[0]): # toplam_arsa_degeri
                        return mock_session_query_sum_fiyat
                    if 'value' in str(args[0]): # toplam_acik_firsat_degeri_try
                        return mock_session_query_sum_deal_value
                return MagicMock() # Default mock for other db.session.query calls
            
            mock_db_session_query.side_effect = query_side_effect
            mock_bolge_query.filter_by.return_value.all.return_value = []
            mock_task_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_contact_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_deal_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_deal_query.filter.return_value.count.return_value = 0
            mock_interaction_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []


            response = self.client.get(url_for('main.index'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Dashboard', response.data)
        self._logout_user()

    def test_profile_get_authenticated(self):
        self._login('default@example.com', 'password123')
        with patch('blueprints.main_bp.pytz.all_timezones', ['Europe/London', 'America/New_York']):
            response = self.client.get(url_for('main.profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Profil Bilgileri', response.data)
        self.assertIn(b'Europe/London', response.data)
        self._logout_user()

    @patch('blueprints.main_bp.os.makedirs') # Mock os.makedirs
    @patch('werkzeug.utils.secure_filename', return_value='test_photo.jpg') # Mock secure_filename
    def test_profile_post_update_with_photo(self, mock_secure_filename, mock_os_makedirs):
        user_to_update = User.query.get(self.default_user.id)
        self._login(user_to_update.email, 'password123')

        data = {
            'ad': 'Updated', 'soyad': 'Name', 'telefon': '0987654321',
            'firma': 'New Corp', 'unvan': 'Developer', 'adres': 'New Address',
            'timezone': 'America/New_York',
        }
        # Simulate file upload
        file_data = (BytesIO(b"fakeimagecontent"), 'test_photo.jpg')
        data['profil_foto'] = file_data

        with patch('werkzeug.datastructures.FileStorage.save') as mock_file_save:
            with patch('blueprints.main_bp.pytz.all_timezones', ['Europe/London', 'America/New_York']):
                response = self.client.post(url_for('main.profile'), data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(url_for('main.profile') in response.location)
        
        mock_os_makedirs.assert_called_once()
        mock_file_save.assert_called_once()
        
        _db.session.refresh(user_to_update) # Refresh from DB
        self.assertEqual(user_to_update.ad, 'Updated')
        self.assertEqual(user_to_update.soyad, 'Name')
        self.assertEqual(user_to_update.timezone, 'America/New_York')
        expected_photo_path = f"profiles/{user_to_update.id}/test_photo.jpg"
        self.assertEqual(user_to_update.profil_foto, expected_photo_path)
        
        # Check if the directory for the user was created within the test_upload_folder
        expected_user_upload_dir = os.path.join(self.app.config["UPLOAD_FOLDER"], "profiles", str(user_to_update.id))
        self.assertTrue(os.path.isdir(expected_user_upload_dir))
        # The mock_file_save prevents actual file writing, so we don't check for the file itself here.

        self._logout_user()

    def test_change_password_success(self):
        user_to_change_pass = User.query.get(self.default_user.id)
        self._login(user_to_change_pass.email, 'password123')

        data = {
            'current_password': 'password123',
            'new_password': 'newsecurepassword',
            'confirm_password': 'newsecurepassword'
        }
        response = self.client.post(url_for('main.change_password'), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(url_for('main.profile') in response.location)
        
        messages = get_flashed_messages(with_categories=True)
        self.assertTrue(any(msg[0] == 'success' and 'Şifreniz başarıyla güncellendi' in msg[1] for msg in messages))
        
        _db.session.refresh(user_to_change_pass)
        self.assertTrue(user_to_change_pass.check_password('newsecurepassword'))
        self._logout_user()

    def test_analysis_form_get_with_session_data(self):
        self._login('default@example.com', 'password123')
        with self.client as c:
            with c.session_transaction() as sess:
                sess['analysis_form_data'] = {'il': 'Ankara'}
                sess['analysis_form_errors'] = ['Bir hata oluştu']
            
            response = c.get(url_for('main.analysis_form'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Ankara', response.data)
            self.assertIn(b'Bir hata olu', response.data) # Check for part of the error message

            # Check if session variables are popped
            with c.session_transaction() as sess_after:
                self.assertIsNone(sess_after.get('analysis_form_data'))
                self.assertIsNone(sess_after.get('analysis_form_errors'))
        self._logout_user()

    def test_favicon_exists(self):
        static_folder = self.app.static_folder # This is 'static' relative to app root
        # In test context, current_app.root_path might be tricky.
        # Let's assume create_app sets static_folder correctly.
        favicon_path = os.path.join(static_folder, 'favicon.ico')
        os.makedirs(static_folder, exist_ok=True) # Ensure static folder exists
        with open(favicon_path, 'w') as f:
            f.write("dummy_favicon_content")

        response = self.client.get(url_for('main.favicon'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/vnd.microsoft.icon')
        
        os.remove(favicon_path)

    # --- Tests for my_office ---
    def test_my_office_not_broker(self):
        # default_user has 'danisman' role
        self._login('default@example.com', 'password123')
        response = self.client.get(url_for('main.my_office'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(url_for('main.index') in response.location)
        messages = get_flashed_messages(with_categories=True)
        self.assertTrue(any(msg[0] == 'danger' and 'gerekli yetkiye sahip değilsiniz' in msg[1] for msg in messages))
        self._logout_user()

    def test_my_office_broker_no_office_no_firma_get(self):
        broker = User(id=2, email='broker_nooffice@example.com', role='broker', firma=None, office_id=None)
        broker.set_password('password123')
        _db.session.add(broker)
        _db.session.commit()
        self._login(broker.email, 'password123')

        response = self.client.get(url_for('main.my_office'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(url_for('main.index') in response.location)
        messages = get_flashed_messages(with_categories=True)
        self.assertTrue(any(msg[0] == 'warning' and 'Bir ofise atanmamışsınız' in msg[1] for msg in messages))
        self._logout_user()

    def test_my_office_broker_no_office_with_firma_creates_new_office(self):
        broker = User(id=3, email='broker_newoffice@example.com', role='broker', firma='My Firm Office', office_id=None)
        broker.set_password('password123')
        _db.session.add(broker)
        _db.session.commit()
        self._login(broker.email, 'password123')

        response = self.client.get(url_for('main.my_office'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Firm Office', response.data)
        
        created_office = Office.query.filter_by(name='My Firm Office').first()
        self.assertIsNotNone(created_office)
        _db.session.refresh(broker)
        self.assertEqual(broker.office_id, created_office.id)
        messages = get_flashed_messages(with_categories=True)
        self.assertTrue(any(msg[0] == 'info' and 'adında yeni bir ofis sizin için oluşturuldu' in msg[1] for msg in messages))
        self._logout_user()

    def test_my_office_broker_add_member_post_valid(self):
        office = Office(name="Broker's Grand Office")
        _db.session.add(office)
        _db.session.flush() # To get office.id

        broker = User(id=4, email='broker_leader@example.com', role='broker', firma=office.name, office_id=office.id)
        broker.set_password('password123')
        _db.session.add(broker)
        _db.session.commit()
        self._login(broker.email, 'password123')

        data = {
            'email': 'newteammember@example.com',
            'password': 'memberpassword',
            'ad': 'Team',
            'soyad': 'Member',
            'role': 'danisman'
        }
        response = self.client.post(url_for('main.my_office'), data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # After redirect
        
        new_member = User.query.filter_by(email='newteammember@example.com').first()
        self.assertIsNotNone(new_member)
        self.assertEqual(new_member.ad, 'Team')
        self.assertEqual(new_member.office_id, office.id)
        self.assertEqual(new_member.manager_id, broker.id)
        self.assertEqual(new_member.firma, office.name)

        messages = get_flashed_messages(with_categories=True)
        self.assertTrue(any(msg[0] == 'success' and "Ekip üyesi 'Team Member' eklendi" in msg[1] for msg in messages))
        self._logout_user()

if __name__ == '__main__':
    unittest.main()

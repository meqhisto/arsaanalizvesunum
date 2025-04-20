from migrations.add_user_profile_fields import upgrade, downgrade
from app import app, db

if __name__ == '__main__':
    try:
        print("Starting database migration...")
        # Initialize Flask app context
        with app.app_context():
            # Create all tables if they don't exist
            db.create_all()
            # Run migration
            upgrade()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        print("Rolling back changes...")
        try:
            with app.app_context():
                downgrade()
        except Exception as e:
            print(f"Rollback failed: {str(e)}")

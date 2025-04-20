from app import app, db
from sqlalchemy import text

def upgrade():
    with app.app_context():
        try:
            # Add columns using raw SQL with proper SQLAlchemy execution
            sql_commands = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS ad VARCHAR(50)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS soyad VARCHAR(50)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS telefon VARCHAR(20)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS firma VARCHAR(100)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS unvan VARCHAR(100)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS adres TEXT",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS profil_foto VARCHAR(200)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS son_giris DATETIME"
            ]
            
            connection = db.engine.connect()
            for command in sql_commands:
                try:
                    connection.execute(text(command))
                    print(f"Executed: {command}")
                except Exception as e:
                    print(f"Error executing {command}: {str(e)}")
            
            connection.commit()
            print("Migration completed successfully")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            raise e
        finally:
            connection.close()

def downgrade():
    with app.app_context():
        try:
            # Drop columns using raw SQL
            sql_commands = [
                "ALTER TABLE users DROP COLUMN IF EXISTS ad",
                "ALTER TABLE users DROP COLUMN IF EXISTS soyad",
                "ALTER TABLE users DROP COLUMN IF EXISTS telefon",
                "ALTER TABLE users DROP COLUMN IF EXISTS firma",
                "ALTER TABLE users DROP COLUMN IF EXISTS unvan",
                "ALTER TABLE users DROP COLUMN IF EXISTS adres",
                "ALTER TABLE users DROP COLUMN IF EXISTS profil_foto",
                "ALTER TABLE users DROP COLUMN IF EXISTS is_active",
                "ALTER TABLE users DROP COLUMN IF EXISTS son_giris"
            ]
            
            connection = db.engine.connect()
            for command in sql_commands:
                try:
                    connection.execute(text(command))
                    print(f"Executed: {command}")
                except Exception as e:
                    print(f"Error executing {command}: {str(e)}")
            
            connection.commit()
            print("Downgrade completed successfully")
            
        except Exception as e:
            print(f"Downgrade failed: {str(e)}")
            raise e
        finally:
            connection.close()

if __name__ == '__main__':
    upgrade()

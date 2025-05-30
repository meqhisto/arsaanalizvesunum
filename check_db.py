from app import create_app
from models import db

# Önemli: db'yi models'den import ediyoruz, böylece aynı SQLAlchemy örneğini kullanıyoruz
app = create_app()
with app.app_context():
    print("Veritabanı Tabloları:")
    try:
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        for table in tables:
            print(f"- {table}")
            columns = inspector.get_columns(table)
            print(f"  Sütunlar:")
            for column in columns:
                print(f"    - {column['name']} ({column['type']})")
    except Exception as e:
        print(f"Veritabanı kontrolü sırasında hata oluştu: {str(e)}")

from app import app, db

# Önemli: db'yi app.py'den doğrudan import ediyoruz, böylece aynı SQLAlchemy örneğini kullanıyoruz
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

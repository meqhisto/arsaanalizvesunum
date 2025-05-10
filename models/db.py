from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key support for SQLite if used"""
    if hasattr(dbapi_connection, 'execute'):
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT 1")  # Test the connection
        cursor.close()

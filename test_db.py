from app import app, db
from models.customer import Customer
from datetime import datetime
import traceback

def test_db_connection():
    print("Starting database test...")
    with app.app_context():
        try:
            print("Creating test customer...")
            # Create a test customer
            test_customer = Customer(
                user_id=1,  # Assuming user ID 1 exists
                name='Test Customer',
                email='test@example.com',
                phone='+1234567890',
                company='Test Company',
                title='Test Title',
                address='Test Address'
            )
            
            # Add to database
            print("Adding to database...")
            db.session.add(test_customer)
            db.session.commit()
            print("Successfully added test customer!")
            
            # Query back to verify
            print("Querying database...")
            customer = Customer.query.filter_by(email='test@example.com').first()
            print(f"Retrieved customer: {customer.name}")
            
            # Cleanup
            print("Cleaning up...")
            db.session.delete(customer)
            db.session.commit()
            print("Test customer removed")
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            db.session.rollback()
            raise

if __name__ == '__main__':
    try:
        test_db_connection()
    except Exception as e:
        print(f"Test failed: {str(e)}")

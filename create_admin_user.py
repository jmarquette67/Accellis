"""
Create admin user for the Accellis platform
"""
import sys
from app import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create admin user with specified credentials"""
    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email='admin@accellis.com').first()
        
        if existing_admin:
            print("Admin user already exists. Updating password...")
            existing_admin.password_hash = generate_password_hash('Accellis25')
            db.session.commit()
            print("Admin password updated successfully.")
            return
        
        # Create new admin user
        admin_user = User(
            id='admin_accellis',
            email='admin@accellis.com',
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN,
            profile_image_url=None
        )
        
        # Set password hash
        admin_user.password_hash = generate_password_hash('Accellis25')
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
            print(f"Email: admin@accellis.com")
            print(f"Password: Accellis25")
            print(f"Role: {UserRole.ADMIN.value}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin_user()
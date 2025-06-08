"""
Create a default admin user for initial system access
"""
from app import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_default_admin():
    """Create default admin user with email: admin@accellis.com, password: admin123"""
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@accellis.com').first()
        if existing_admin:
            print("Default admin user already exists")
            return
        
        # Create admin user
        admin_user = User()
        admin_user.id = 'admin-default'
        admin_user.email = 'admin@accellis.com'
        admin_user.first_name = 'System'
        admin_user.last_name = 'Administrator'
        admin_user.role = UserRole.ADMIN
        admin_user.password_hash = generate_password_hash('admin123')
        admin_user.password_set_date = datetime.utcnow()
        admin_user.is_active = True
        admin_user.created_at = datetime.utcnow()
        admin_user.updated_at = datetime.utcnow()
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("Default admin user created successfully!")
        print("Email: admin@accellis.com")
        print("Password: admin123")
        print("Please change this password after first login.")

if __name__ == "__main__":
    create_default_admin()
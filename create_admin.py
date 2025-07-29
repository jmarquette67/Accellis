"""
Create admin user for metrics management
"""
from app import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an admin user for the platform"""
    
    with app.app_context():
        # Check if admin already exists
        admin_user = User.query.filter_by(email="admin@accellis.com").first()
        
        if admin_user:
            # Update password if it doesn't exist
            if not admin_user.password_hash:
                admin_user.password_hash = generate_password_hash("admin123")
                db.session.commit()
                print(f"Updated password for existing admin user: {admin_user.email}")
            else:
                print(f"Admin user already exists with password: {admin_user.email}")
            return admin_user
        
        # Create a new admin user
        admin = User(
            id="admin_user_001",
            email="admin@accellis.com", 
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            password_hash=generate_password_hash("admin123"),
            is_active=True
        )
        
        db.session.add(admin)
        
        try:
            db.session.commit()
            print(f"Created admin user: {admin.email}")
            print(f"User ID: {admin.id}")
            print(f"Role: {admin.role}")
            return admin
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
            return None

if __name__ == "__main__":
    create_admin_user()
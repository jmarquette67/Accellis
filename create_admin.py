"""
Create admin user for metrics management
"""
from app import app, db
from models import User, UserRole

def create_admin_user():
    """Create an admin user for the platform"""
    
    with app.app_context():
        # Check if admin already exists
        admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
        
        if admin_user:
            print(f"Admin user already exists: {admin_user.email or admin_user.id}")
            return admin_user
        
        # Create a new admin user
        admin = User(
            id="admin_user_001",
            email="admin@accellis.com", 
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN
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
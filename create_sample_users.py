"""
Create 5 sample account managers/users for the platform
"""
import sys
from datetime import datetime
from app import app, db
from models import User, UserRole

def create_sample_users():
    """Create 5 sample users as account managers"""
    
    with app.app_context():
        # Sample users data
        sample_users = [
            {
                'id': 'user001',
                'email': 'sarah.johnson@accellis.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'role': UserRole.MANAGER,
                'profile_image_url': 'https://images.unsplash.com/photo-1494790108755-2616b612b47c?w=150'
            },
            {
                'id': 'user002', 
                'email': 'mike.chen@accellis.com',
                'first_name': 'Mike',
                'last_name': 'Chen',
                'role': UserRole.TAM,
                'profile_image_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150'
            },
            {
                'id': 'user003',
                'email': 'lisa.rodriguez@accellis.com', 
                'first_name': 'Lisa',
                'last_name': 'Rodriguez',
                'role': UserRole.VCIO,
                'profile_image_url': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150'
            },
            {
                'id': 'user004',
                'email': 'david.kumar@accellis.com',
                'first_name': 'David', 
                'last_name': 'Kumar',
                'role': UserRole.TAM,
                'profile_image_url': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150'
            },
            {
                'id': 'user005',
                'email': 'emma.thompson@accellis.com',
                'first_name': 'Emma',
                'last_name': 'Thompson', 
                'role': UserRole.MANAGER,
                'profile_image_url': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150'
            }
        ]
        
        # Create or update users
        created_count = 0
        for user_data in sample_users:
            existing_user = User.query.filter_by(id=user_data['id']).first()
            
            if not existing_user:
                new_user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    profile_image_url=user_data['profile_image_url']
                )
                db.session.add(new_user)
                created_count += 1
                print(f"Created user: {user_data['first_name']} {user_data['last_name']} ({user_data['role'].value})")
            else:
                # Update existing user
                existing_user.email = user_data['email']
                existing_user.first_name = user_data['first_name']
                existing_user.last_name = user_data['last_name']
                existing_user.role = user_data['role']
                existing_user.profile_image_url = user_data['profile_image_url']
                print(f"Updated user: {user_data['first_name']} {user_data['last_name']} ({user_data['role'].value})")
        
        db.session.commit()
        print(f"\n✓ Sample users created/updated successfully!")
        print(f"✓ {created_count} new users created")
        
        return True

if __name__ == "__main__":
    create_sample_users()
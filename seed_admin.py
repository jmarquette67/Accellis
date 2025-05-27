#!/usr/bin/env python3
"""
Seed script to create admin user
"""
import os
import sys
from app import app, db
from models import User, UserRole

def seed_admin():
    """Create admin user with Replit handle"""
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if admin already exists
        admin_id = "your-replit-handle"  # Replace with actual Replit handle
        existing_admin = User.query.filter_by(id=admin_id).first()
        
        if existing_admin:
            print(f"Admin user {admin_id} already exists with role: {existing_admin.role.value}")
            if existing_admin.role != UserRole.ADMIN:
                existing_admin.role = UserRole.ADMIN
                db.session.commit()
                print(f"Updated {admin_id} role to ADMIN")
        else:
            # Create new admin user
            admin_user = User(
                id=admin_id,
                email=None,  # Will be filled when they first log in
                first_name=None,
                last_name=None,
                profile_image_url=None,
                role=UserRole.ADMIN
            )
            
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created admin user: {admin_id} with ADMIN role")

if __name__ == "__main__":
    seed_admin()
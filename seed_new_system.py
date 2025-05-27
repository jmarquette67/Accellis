#!/usr/bin/env python3
"""
Seed script for the new client scoring system
"""
from datetime import datetime, date
from sqlmodel import Session
from app_new import engine
from models_new import User, Client, Metric, Score, UserClient, RoleType

def seed_system():
    """Seed the new client scoring system with sample data"""
    with Session(engine) as session:
        
        # Create sample metrics
        metrics = [
            Metric(
                name="Communication Quality",
                description="How well the client communicates with our team",
                weight=20,
                high_threshold=80,
                low_threshold=60
            ),
            Metric(
                name="Payment Timeliness", 
                description="How promptly the client pays invoices",
                weight=25,
                high_threshold=90,
                low_threshold=70
            ),
            Metric(
                name="Project Scope Adherence",
                description="How well the client sticks to agreed project scope",
                weight=15,
                high_threshold=85,
                low_threshold=65
            ),
            Metric(
                name="Strategic Value",
                description="Long-term strategic value of the client relationship",
                weight=20,
                high_threshold=75,
                low_threshold=50
            ),
            Metric(
                name="Technical Readiness",
                description="Client's technical infrastructure and readiness",
                weight=20,
                high_threshold=80,
                low_threshold=60
            )
        ]
        
        for metric in metrics:
            session.add(metric)
        session.commit()
        
        # Create sample clients
        clients = [
            Client(
                name="TechStart Inc",
                industry="Technology",
                mrr=15000,
                renewal_date=date(2025, 8, 15)
            ),
            Client(
                name="Healthcare Solutions LLC",
                industry="Healthcare",
                mrr=28000,
                renewal_date=date(2025, 6, 30)
            ),
            Client(
                name="Finance Plus Corp",
                industry="Financial Services",
                mrr=42000,
                renewal_date=date(2025, 12, 1)
            ),
            Client(
                name="Retail Innovations",
                industry="Retail",
                mrr=18500,
                renewal_date=date(2025, 9, 20)
            ),
            Client(
                name="Manufacturing Pro",
                industry="Manufacturing",
                mrr=35000,
                renewal_date=date(2025, 7, 10)
            )
        ]
        
        for client in clients:
            session.add(client)
        session.commit()
        
        # Create sample users (in addition to the admin)
        users = [
            User(username="john_vcio", role=RoleType.VCIO),
            User(username="sarah_tam", role=RoleType.TAM),
            User(username="mike_manager", role=RoleType.MANAGER),
        ]
        
        for user in users:
            session.add(user)
        session.commit()
        
        print("Successfully seeded the new client scoring system!")
        print(f"Created {len(metrics)} metrics")
        print(f"Created {len(clients)} clients") 
        print(f"Created {len(users)} users")

if __name__ == "__main__":
    seed_system()
"""
Create authentic metrics table from Q1 2025 spreadsheet
Based on exact specifications from the client engagement data
"""
import sys
import pandas as pd
from datetime import datetime
from sqlmodel import Session
from database import get_engine
from app import app, db
from models import Metric

def create_authentic_metrics():
    """Create metrics table with authentic Q1 2025 data and correct specifications"""
    
    # Authentic metrics from Q1 2025 spreadsheet with correct priority system
    # Higher weight numbers = higher priority
    authentic_metrics = [
        {
            'name': '1. Help Desk Usage',
            'description': 'Track client interactions with help desk (volume and types of tickets)',
            'scoring_criteria': 'Ideal usage: +1 point, Moderate Usage: .25-.5 tickets per end user per month: +0 points, Low Usage: less than .25 tickets per end user per month: +0 points',
            'weight': 5,  # Highest priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '2. First Touch Resolution/Escalation', 
            'description': 'First Touch Resolution percentage tracking',
            'scoring_criteria': 'Greater than 75%: +1 point, Less than 75%: 0 points',
            'weight': 4,  # High priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '3. Strategic Review Attendance',
            'description': 'Attendance and engagement in technology business reviews or strategic meetings in the last 90 days',
            'scoring_criteria': 'Attended: +1 point, Did not Attend: 0 points',
            'weight': 4,  # High priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '4. Cross Selling',
            'description': 'Engaged with multiple lines of service beyond MITS',
            'scoring_criteria': '+1 point for each additional service line beyond MITS (Managed Security, Managed Pen Test, Managed Back Ups)',
            'weight': 3,  # Medium priority
            'max_score': 10,
            'high_threshold': 3,
            'low_threshold': 1
        },
        {
            'name': '5. Project Engagement',
            'description': 'Project sales activity in the last 12 months',
            'scoring_criteria': 'Project has been sold in the last 12 months: +1 point',
            'weight': 5,  # Highest priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '6. Procurement',
            'description': 'Product or renewal purchase activity',
            'scoring_criteria': 'Product or renewal was purchased in last 30 days: +1 point',
            'weight': 2,  # Lower priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '7. Support Engagement Satisfaction',
            'description': 'Average satisfaction score from support or survey feedback over last 60 Days',
            'scoring_criteria': 'High Satisfaction: CSATs greater than 95%: +1 point',
            'weight': 4,  # High priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '8. Regular Feedback',
            'description': 'Participation in regular surveys like NPS',
            'scoring_criteria': 'Scored above a 6: +1 point',
            'weight': 5,  # Highest priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '9. Invoices/AR',
            'description': 'Good Payer and Satisfied with Invoicing Practices',
            'scoring_criteria': 'Good payer with satisfactory invoicing practices: +1 point',
            'weight': 1,  # Supporting priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '10. Client LifeCycle Phase',
            'description': 'Client lifecycle stage assessment',
            'scoring_criteria': 'Onboard/Chaos (first 90days): +1 point',
            'weight': 2,  # Lower priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '11. Tech Stack',
            'description': 'Client technology stack assessment and compatibility',
            'scoring_criteria': 'Compatible or well-managed tech stack: +1 point',
            'weight': 1,  # Supporting priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '12. Credit Requests',
            'description': 'Billing Satisfaction - frequency and nature of credit requests',
            'scoring_criteria': 'Low frequency of credit requests indicating billing satisfaction: +1 point',
            'weight': 1,  # Supporting priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        },
        {
            'name': '13. Gut Instinct',
            'description': 'Overall relationship assessment and client engagement level',
            'scoring_criteria': 'Relationship is good & client is engaged: +1 point',
            'weight': 4,  # High priority
            'max_score': 1,
            'high_threshold': 1,
            'low_threshold': 0
        }
    ]
    
    with app.app_context():
        # Clear existing metrics
        existing_metrics = Metric.query.all()
        for metric in existing_metrics:
            db.session.delete(metric)
        
        # Create authentic metrics
        created_count = 0
        for metric_data in authentic_metrics:
            metric = Metric(
                name=metric_data['name'],
                description=metric_data['description'],
                scoring_criteria=metric_data['scoring_criteria'],
                weight=metric_data['weight'],
                max_score=metric_data['max_score'],
                high_threshold=metric_data['high_threshold'],
                low_threshold=metric_data['low_threshold']
            )
            db.session.add(metric)
            created_count += 1
            print(f"Created: {metric_data['name']} (Weight: {metric_data['weight']}, Max Score: {metric_data['max_score']})")
        
        try:
            db.session.commit()
            print(f"\nSuccessfully created {created_count} authentic metrics from Q1 2025 data")
            
            # Show final metrics sorted by weight (low to high as requested)
            print("\nFinal Metrics (sorted by weight low to high):")
            metrics = Metric.query.order_by(Metric.weight, Metric.name).all()
            for metric in metrics:
                max_score = 10 if "Cross Selling" in metric.name else 1
                print(f"Weight {metric.weight}: {metric.name} (Max: {max_score})")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error creating metrics: {e}")

if __name__ == "__main__":
    create_authentic_metrics()
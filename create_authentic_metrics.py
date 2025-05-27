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
    
    # Authentic metrics from Q1 2025 spreadsheet with exact weighting and descriptions
    authentic_metrics = [
        {
            'name': '1. Help Desk Usage',
            'description': 'Track client interactions with help desk (volume and types of tickets). Ideal usage: +1, Moderate Usage: .25-.5 tickets per end user per month: +0, Low Usage: less than .25 tickets per end user per month: +0',
            'weight': 1,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '2. First Touch Resolution/Escalation', 
            'description': 'First Touch Resolution is greater than 75%. Greater than 75%: +1, Less than 75%: 0',
            'weight': 2,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '3. Strategic Review Attendance',
            'description': 'Attendance and engagement in technology business reviews or strategic meetings in the last 90 days. Attended: +1, Did not Attend: 0',
            'weight': 2,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '4. Cross Selling',
            'description': 'Engaged with multiple lines of service. +1 for each additional service line beyond MITS (Managed Security, Managed Pen Test, Managed Back Ups)',
            'weight': 3,
            'max_score': 10,
            'scoring_note': 'Can have up to 10 points'
        },
        {
            'name': '5. Project Engagement',
            'description': 'Project has been sold in the last 12 months. +1',
            'weight': 1,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '6. Procurement',
            'description': 'Product or renewal was purchased in last 30 days: +1',
            'weight': 4,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '7. Support Engagement Satisfaction',
            'description': 'Average satisfaction score from support or survey feedback over last 60 Days. High Satisfaction: CSATs greater than 95% +1',
            'weight': 2,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '8. Regular Feedback',
            'description': 'Participation in regular surveys like NPS and scored above a 6. +1',
            'weight': 1,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '9. Invoices/AR',
            'description': 'Good Payer and Satisfied with Invoicing Practices',
            'weight': 5,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '10. Client LifeCycle Phase',
            'description': 'Onboard/Chaos (first 90days) + 1',
            'weight': 4,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '11. Tech Stack',
            'description': 'Client technology stack assessment and compatibility',
            'weight': 5,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '12. Credit Requests',
            'description': 'Billing Satisfaction - frequency and nature of credit requests',
            'weight': 5,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
        },
        {
            'name': '13. Gut Instinct',
            'description': 'Relationship is good & client is engaged: +1',
            'weight': 2,
            'max_score': 1,
            'scoring_note': 'Binary: 0 (not happening) or 1 (happening)'
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
                weight=metric_data['weight'],
                high_threshold=metric_data['max_score'],  # Use max_score as high threshold
                low_threshold=0  # Always 0 for binary/low end
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
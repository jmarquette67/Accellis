"""
Update Help Desk sample data with realistic ticket per user numbers
Updates all existing Help Desk scores to use decimal values between 0-5
Keeps average between 0.5-1.5 as requested
"""

import random
from app import app, db
from sqlalchemy import text

def update_help_desk_sample_data():
    """Update all Help Desk scores with realistic ticket per user numbers"""
    with app.app_context():
        print("Updating Help Desk sample data with realistic ticket numbers...")
        
        # Get Help Desk metric ID
        help_desk_metric = db.session.execute(text(
            "SELECT id FROM metric WHERE name LIKE '%Help Desk%' LIMIT 1"
        )).fetchone()
        
        if not help_desk_metric:
            print("Help Desk metric not found!")
            return
        
        metric_id = help_desk_metric[0]
        
        # Get all existing Help Desk scores
        existing_scores = db.session.execute(text(
            "SELECT id, client_id FROM score WHERE metric_id = :metric_id"
        ), {"metric_id": metric_id}).fetchall()
        
        if not existing_scores:
            print("No existing Help Desk scores found!")
            return
        
        print(f"Found {len(existing_scores)} existing Help Desk scores to update...")
        
        # Generate realistic ticket per user numbers
        # Target average between 0.5-1.5, with range 0-5
        updated_count = 0
        total_value = 0
        
        for score_record in existing_scores:
            score_id = score_record[0]
            client_id = score_record[1]
            
            # Generate realistic ticket numbers with weighted distribution
            # More likely to be in the 0.25-1.5 range, but some outliers
            rand_val = random.random()
            
            if rand_val < 0.15:  # 15% too low (< 0.25)
                tickets_per_user = round(random.uniform(0.0, 0.24), 1)
            elif rand_val < 0.75:  # 60% ideal range (0.25-1.0)
                tickets_per_user = round(random.uniform(0.25, 1.0), 1)
            elif rand_val < 0.90:  # 15% slightly high (1.0-2.0)
                tickets_per_user = round(random.uniform(1.1, 2.0), 1)
            else:  # 10% very high (2.0-5.0)
                tickets_per_user = round(random.uniform(2.1, 5.0), 1)
            
            # Update the score with the new value
            db.session.execute(text(
                "UPDATE score SET value = :new_value WHERE id = :score_id"
            ), {"new_value": tickets_per_user, "score_id": score_id})
            
            total_value += tickets_per_user
            updated_count += 1
        
        # Commit all changes
        db.session.commit()
        
        # Calculate and display statistics
        average_tickets = total_value / updated_count if updated_count > 0 else 0
        
        print(f"\n✓ Updated {updated_count} Help Desk scores")
        print(f"✓ Average tickets per user per month: {average_tickets:.2f}")
        print(f"✓ Values range from 0.0 to 5.0")
        print(f"✓ Distribution: ~15% too low, ~60% ideal, ~25% too high")
        
        # Show some sample values
        sample_scores = db.session.execute(text(
            "SELECT s.value, c.name FROM score s JOIN client c ON s.client_id = c.id WHERE s.metric_id = :metric_id LIMIT 10"
        ), {"metric_id": metric_id}).fetchall()
        
        print(f"\nSample updated values:")
        for score_val, client_name in sample_scores:
            print(f"  {client_name}: {score_val} tickets/user/month")

if __name__ == "__main__":
    update_help_desk_sample_data()
"""
Complete rebuild of sample data with clean, realistic scoresheet values
Removes all existing score data and creates fresh, properly scaled data
"""
import sys
sys.path.append('.')

from datetime import datetime, timedelta
import random
from app import app, db
from models import Client, Score, Metric

def rebuild_clean_data():
    """Remove all existing scores and create clean sample data"""
    with app.app_context():
        print("Rebuilding clean sample data...")
        
        # Remove ALL existing scores to start fresh
        Score.query.delete()
        db.session.commit()
        print("Cleared all existing score data")
        
        # Get active clients and metrics
        clients = Client.query.filter_by(is_active=True).limit(15).all()
        metrics = Metric.query.all()
        
        if not clients or not metrics:
            print("No clients or metrics found")
            return
            
        print(f"Creating clean data for {len(clients)} clients with {len(metrics)} metrics...")
        
        # Create realistic scoresheets for the last 90 days
        scores_created = 0
        
        for client in clients:
            # Create 1-3 scoresheets per client over 90 days
            num_scoresheets = random.randint(1, 3)
            
            for sheet_num in range(num_scoresheets):
                # Spread scoresheets across the last 90 days
                days_ago = random.randint(1, 90)
                scoresheet_date = datetime.now() - timedelta(days=days_ago)
                
                for metric in metrics:
                    # Generate realistic score values based on metric configuration
                    if metric.input_type == 'select':
                        # Binary metrics: 75% chance of 1, 25% chance of 0
                        score_value = random.choices([0, 1], weights=[25, 75])[0]
                    elif metric.name == "Cross Selling":
                        # Cross selling: 0-5 additional services
                        score_value = random.randint(0, 5)
                    elif metric.name == "Client LifeCycle Phase":
                        # Lifecycle phases: 0-4 (most in steady state)
                        score_value = random.choices([0, 1, 2, 3, 4], weights=[10, 20, 40, 20, 10])[0]
                    elif metric.name == "Help Desk Usage":
                        # Help Desk usage: 0.0-2.0 tickets per user (stored as integer * 10)
                        usage_value = round(random.uniform(0.2, 1.2), 1)
                        score_value = int(usage_value * 10)  # Store as integer
                    else:
                        # Other metrics: 1-5 scale
                        score_value = random.randint(1, 5)
                    
                    # Create score entry
                    score = Score(
                        client_id=client.id,
                        metric_id=metric.id,
                        value=score_value,
                        taken_at=scoresheet_date,
                        status='final',
                        notes=f"Clean sample data - {scoresheet_date.strftime('%B %Y')}"
                    )
                    db.session.add(score)
                    scores_created += 1
                
        db.session.commit()
        print(f"Successfully created {scores_created} clean score entries")
        print("Dashboard data rebuilt with proper scoring ranges")

if __name__ == "__main__":
    rebuild_clean_data()
"""
Restore proper dashboard data with realistic score ranges
"""
import sys
sys.path.append('.')

from datetime import datetime, timedelta
import random
from app import app, db
from models import Client, Score, Metric

def restore_dashboard_data():
    """Create realistic scoresheet data for dashboard display"""
    with app.app_context():
        # Get active clients and metrics
        clients = Client.query.filter_by(is_active=True).limit(10).all()
        metrics = Metric.query.all()
        
        if not clients or not metrics:
            print("No clients or metrics found")
            return
            
        print(f"Creating realistic scoresheet data for {len(clients)} clients...")
        
        # Create realistic scores for the last 7 days
        for i, client in enumerate(clients):
            # Create a recent scoresheet (within last 7 days)
            scoresheet_date = datetime.now() - timedelta(days=random.randint(0, 7))
            
            for metric in metrics:
                # Generate realistic score values based on metric type
                if metric.input_type == 'select':
                    # Binary metrics: 70% chance of 1, 30% chance of 0
                    score_value = random.choices([0, 1], weights=[30, 70])[0]
                elif metric.name == "Cross Selling":
                    # Cross selling: 0-5 services
                    score_value = random.randint(0, 5)
                elif metric.name == "Client LifeCycle Phase":
                    # Lifecycle phases: 0-4
                    score_value = random.randint(0, 4)
                elif metric.name == "Help Desk Usage":
                    # Help Desk usage: decimal values 0.0-2.0
                    score_value = round(random.uniform(0.2, 1.5), 1) * 10  # Store as integer
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
                    notes=f"Recent scoresheet data for {scoresheet_date.strftime('%Y-%m-%d')}"
                )
                db.session.add(score)
                
        db.session.commit()
        print("Dashboard data restored successfully!")

if __name__ == "__main__":
    restore_dashboard_data()
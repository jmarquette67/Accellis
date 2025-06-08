"""
Create varied trending data to populate both trending up and down sections
"""
import sys
sys.path.append('.')

from datetime import datetime, timedelta
import random
from app import app, db
from models import Client, Score, Metric

def create_trending_data():
    """Create scores with varied trends for better dashboard visualization"""
    with app.app_context():
        # Get active clients and metrics
        clients = Client.query.filter_by(is_active=True).limit(10).all()
        metrics = Metric.query.all()
        
        if not clients or not metrics:
            print("No clients or metrics found")
            return
            
        print(f"Creating trending data for {len(clients)} clients...")
        
        # Create scores for the last 90 days with varied trends
        for i, client in enumerate(clients):
            # Create different trend patterns
            if i % 3 == 0:  # Declining trend
                base_score = 4.0
                trend_direction = -0.02  # Declining
            elif i % 3 == 1:  # Improving trend
                base_score = 3.0
                trend_direction = 0.03  # Improving
            else:  # Stable with slight decline
                base_score = 3.5
                trend_direction = -0.01  # Slight decline
                
            for days_ago in range(90, 0, -1):
                score_date = datetime.now() - timedelta(days=days_ago)
                
                # Calculate score with trend
                daily_variation = random.uniform(-0.3, 0.3)
                trend_factor = trend_direction * (90 - days_ago)
                current_score = base_score + trend_factor + daily_variation
                current_score = max(1.0, min(5.0, current_score))  # Keep in valid range
                
                for metric in metrics:
                    # Create score entry (value must be integer 0-100)
                    score_value = max(0, min(100, int(current_score * 20)))  # Scale 1-5 to 0-100
                    score = Score(
                        client_id=client.id,
                        metric_id=metric.id,
                        value=score_value,
                        taken_at=score_date,
                        status='final',
                        notes=f"Trending data - Day {90-days_ago}"
                    )
                    db.session.add(score)
                    
        db.session.commit()
        print("Trending data created successfully!")

if __name__ == "__main__":
    create_trending_data()
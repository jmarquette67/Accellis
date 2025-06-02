"""
Create 2 years of historical scoresheet data for better trend analysis
"""
import random
from datetime import datetime, timedelta
from app import app, db
from models import Score, Metric

def create_historical_data():
    """Create 2 years of monthly historical data for client 28"""
    
    with app.app_context():
        # Get all metrics
        metrics = Metric.query.all()
        
        # Create monthly data for the past 21 months (excluding the 3 recent months we have)
        base_date = datetime.now() - timedelta(days=90)  # Start 3 months ago
        
        created_count = 0
        
        for month_offset in range(1, 22):  # 21 months of historical data
            scoresheet_date = base_date - timedelta(days=30 * month_offset)
            
            # Vary completion rate: older data is less complete
            if month_offset <= 6:  # Last 6 months: 80-95%
                completion_rate = random.uniform(0.80, 0.95)
            elif month_offset <= 12:  # 6-12 months ago: 70-85%
                completion_rate = random.uniform(0.70, 0.85)
            else:  # 12+ months ago: 60-80%
                completion_rate = random.uniform(0.60, 0.80)
            
            # Select random subset of metrics for this month
            selected_metrics = random.sample(metrics, int(len(metrics) * completion_rate))
            
            for metric in selected_metrics:
                # Generate realistic score values
                if "Cross Selling" in metric.name:
                    score_value = random.randint(1, 5)
                elif "Help Desk" in metric.name:
                    score_value = random.choice([0, 1])
                else:
                    # Historical trend: gradually improving over time
                    base_rate = 0.60 + (month_offset * 0.01)  # Better scores in recent months
                    score_value = 1 if random.random() < base_rate else 0
                
                score = Score(
                    client_id=28,
                    metric_id=metric.id,
                    value=score_value,
                    taken_at=scoresheet_date,
                    locked=True,
                    notes=f"Historical data {scoresheet_date.strftime('%B %Y')}"
                )
                
                db.session.add(score)
                created_count += 1
            
            # Commit every few months to avoid large transactions
            if month_offset % 6 == 0:
                db.session.commit()
                print(f"Created scores for {scoresheet_date.strftime('%B %Y')}")
        
        db.session.commit()
        print(f"Created {created_count} historical scores spanning 2 years")

if __name__ == "__main__":
    create_historical_data()
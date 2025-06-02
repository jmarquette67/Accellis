"""
Complete comprehensive sample data specifically for client 28
"""
import random
from datetime import datetime, timedelta
from app import app, db
from models import Client, Metric, Score

def complete_client_28_data():
    """Create complete scoresheet data for client 28"""
    
    with app.app_context():
        client = Client.query.get(28)
        if not client:
            print("Client 28 not found")
            return
            
        metrics = Metric.query.all()
        if not metrics:
            print("No metrics found")
            return
        
        # Clear existing scores for client 28
        Score.query.filter_by(client_id=28).delete()
        db.session.commit()
        print(f"Cleared existing scores for {client.name}")
        
        # Create recent complete scoresheet (most recent)
        recent_date = datetime.now() - timedelta(days=7)
        
        print(f"Creating complete scoresheet for {recent_date.strftime('%B %d, %Y')}...")
        
        for metric in metrics:
            # Generate score based on metric type per requirements
            if "Cross Selling" in metric.name:
                # Cross Selling: values 1-5
                score_value = random.randint(1, 5)
            elif "Help Desk" in metric.name:
                # Keep Help Desk scores unchanged - existing pattern
                score_value = random.choice([0, 1])
            else:
                # Other metrics: 70-80% chance of value=1 (happening)
                score_value = 1 if random.random() < 0.75 else 0
            
            score = Score(
                client_id=28,
                metric_id=metric.id,
                value=score_value,
                taken_at=recent_date,
                locked=True,
                notes=f"Complete scoresheet for {recent_date.strftime('%B %Y')}"
            )
            
            db.session.add(score)
            print(f"  {metric.name}: {score_value} (weight: {metric.weight}, weighted: {score_value * metric.weight})")
        
        # Create a few more historical scoresheets
        for i in range(1, 4):
            historical_date = recent_date - timedelta(days=30*i + random.randint(1, 10))
            
            # Randomly include 80-90% of metrics for historical data
            metrics_subset = random.sample(metrics, int(len(metrics) * random.uniform(0.8, 0.9)))
            
            for metric in metrics_subset:
                if "Cross Selling" in metric.name:
                    score_value = random.randint(1, 5)
                elif "Help Desk" in metric.name:
                    score_value = random.choice([0, 1])
                else:
                    score_value = 1 if random.random() < 0.75 else 0
                
                score = Score(
                    client_id=28,
                    metric_id=metric.id,
                    value=score_value,
                    taken_at=historical_date,
                    locked=True,
                    notes=f"Historical scoresheet for {historical_date.strftime('%B %Y')}"
                )
                
                db.session.add(score)
        
        db.session.commit()
        
        # Verify the data
        total_scores = Score.query.filter_by(client_id=28).count()
        recent_scores = Score.query.filter(
            Score.client_id == 28,
            Score.taken_at >= recent_date.date()
        ).count()
        
        print(f"\n✓ Created {total_scores} total scores for {client.name}")
        print(f"✓ Most recent scoresheet has {recent_scores} complete scores")
        print(f"✓ Recent scoresheet date: {recent_date.strftime('%B %d, %Y')}")

if __name__ == "__main__":
    complete_client_28_data()
"""
Create comprehensive scores for clients that currently have no scoring data
Ensures all clients show proper weighted totals instead of "No scores"
"""
import random
from datetime import datetime, timedelta
from app import app, db
from models import Client, Score, Metric

def create_missing_client_scores():
    """Create scores for all clients that currently have no scoring data"""
    
    with app.app_context():
        # Get clients without scores
        clients_without_scores = []
        all_clients = Client.query.all()
        
        for client in all_clients:
            score_count = Score.query.filter_by(client_id=client.id).count()
            if score_count == 0:
                clients_without_scores.append(client)
        
        print(f"Found {len(clients_without_scores)} clients without scores")
        
        # Get all metrics
        metrics = Metric.query.all()
        if not metrics:
            print("No metrics found. Run create_authentic_metrics.py first.")
            return
        
        print(f"Found {len(metrics)} metrics to score")
        
        # Create realistic scoring patterns for each client
        for client in clients_without_scores:
            print(f"Creating scores for {client.name}...")
            
            # Create 12 months of historical data
            for month_offset in range(12):
                scoresheet_date = datetime.now() - timedelta(days=30 * month_offset)
                
                # Create scores for each metric with realistic patterns
                for metric in metrics:
                    # Generate realistic scores based on metric characteristics
                    if metric.name == "Cross Selling":
                        # Cross Selling: 1-5 range with weighted distribution
                        value = random.choices([1, 2, 3, 4, 5], weights=[30, 25, 25, 15, 5])[0]
                    elif metric.name == "Help Desk Usage":
                        # Help Desk: 70% chance of 0 (not happening), 30% chance of 1 (happening)
                        value = random.choices([0, 1], weights=[70, 30])[0]
                    elif metric.name in ["Credit Requests", "Invoices/AR", "Tech Stack"]:
                        # Low weight metrics: 80% chance of 1 (happening), 20% chance of 0
                        value = random.choices([0, 1], weights=[20, 80])[0]
                    else:
                        # Other metrics: 75% chance of 1 (happening), 25% chance of 0
                        value = random.choices([0, 1], weights=[25, 75])[0]
                    
                    # Create the score record
                    score = Score(
                        client_id=client.id,
                        metric_id=metric.id,
                        value=value,
                        taken_at=scoresheet_date,
                        locked=True,
                        notes=f"Sample data for {metric.name}"
                    )
                    
                    db.session.add(score)
            
            print(f"Created {len(metrics) * 12} scores for {client.name}")
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully created scores for {len(clients_without_scores)} clients")
        
        # Verify the results
        print("\nVerification:")
        for client in clients_without_scores:
            score_count = Score.query.filter_by(client_id=client.id).count()
            print(f"{client.name}: {score_count} scores")

if __name__ == "__main__":
    create_missing_client_scores()
"""
Create comprehensive 2 years of monthly scoresheet data for all clients
This will provide sufficient historical data for trending analysis
"""
import sys
import os
from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def create_2_year_historical_data():
    """Create 24 months of scoresheet data for all active clients"""
    session = next(get_session())
    
    try:
        # Get all active clients
        clients = session.query(Client).filter(Client.is_active == True).all()
        print(f"Found {len(clients)} active clients")
        
        # Get all metrics with their weights
        metrics = session.query(Metric).all()
        print(f"Found {len(metrics)} metrics")
        
        # Create data for last 24 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years
        
        current_date = start_date
        months_created = 0
        total_scores_created = 0
        
        while current_date <= end_date:
            # Create scoresheets for the 1st of each month
            scoresheet_date = current_date.replace(day=1)
            
            for client in clients:
                # Check if client already has scores for this month
                existing_scores = session.query(Score).filter(
                    Score.client_id == client.id,
                    Score.taken_at >= scoresheet_date,
                    Score.taken_at < scoresheet_date + timedelta(days=32)
                ).first()
                
                if existing_scores:
                    continue  # Skip if data already exists
                
                # Create realistic score variations based on client performance trends
                base_performance = random.uniform(0.6, 0.95)  # 60-95% base performance
                
                # Add some seasonal variation
                seasonal_factor = 1.0 + 0.1 * random.uniform(-1, 1)
                
                # Add gradual improvement or decline over time
                months_from_start = (scoresheet_date - start_date).days / 30
                trend_factor = 1.0 + (months_from_start * random.uniform(-0.01, 0.02))
                
                performance_multiplier = base_performance * seasonal_factor * trend_factor
                performance_multiplier = max(0.3, min(1.0, performance_multiplier))
                
                scores_for_month = []
                
                for metric in metrics:
                    # Generate realistic score based on metric type and client performance
                    if metric.input_type == 'dropdown':
                        # For dropdown metrics, pick from available options
                        options = [opt.value for opt in metric.options]
                        if options:
                            if random.random() < performance_multiplier:
                                # Pick higher value options more often for better performing clients
                                score_value = max(options) if random.random() < 0.7 else random.choice(options)
                            else:
                                score_value = random.choice(options)
                        else:
                            score_value = random.randint(1, 5)
                    else:
                        # For number inputs, scale based on metric weight and performance
                        if metric.name == 'Cross Selling':
                            score_value = int(performance_multiplier * 5)  # 0-5 services
                        elif metric.weight >= 5:  # High importance metrics
                            score_value = int(performance_multiplier * 10)
                        else:
                            score_value = int(performance_multiplier * 8)
                    
                    # Add some randomness
                    if metric.input_type != 'dropdown':
                        variation = random.uniform(0.8, 1.2)
                        score_value = max(0, int(score_value * variation))
                    
                    score = Score(
                        client_id=client.id,
                        metric_id=metric.id,
                        value=score_value,
                        taken_at=scoresheet_date + timedelta(hours=random.randint(8, 17)),
                        status='final',
                        notes=f"Historical data for {scoresheet_date.strftime('%B %Y')}"
                    )
                    scores_for_month.append(score)
                
                # Bulk insert scores for this client/month
                session.add_all(scores_for_month)
                total_scores_created += len(scores_for_month)
            
            months_created += 1
            print(f"Created scoresheet data for {scoresheet_date.strftime('%B %Y')} - {months_created} months completed")
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Commit all changes
        session.commit()
        print(f"\n✅ Successfully created {total_scores_created} scores across {months_created} months")
        print(f"📊 Historical data now spans from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating historical data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_2_year_historical_data()
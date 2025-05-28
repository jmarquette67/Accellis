"""
Generate 2 years of monthly sample engagement data
Creates realistic variations to help identify potential client issues and trends
"""
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app import app, db
from models import Client, Metric, Score

def generate_monthly_sample_data():
    """Generate 2 years of monthly sample data with realistic variations"""
    
    with app.app_context():
        # Get all clients and metrics
        clients = Client.query.all()
        metrics = Metric.query.all()
        
        if not clients or not metrics:
            print("Error: No clients or metrics found. Please run import first.")
            return
        
        # Define engagement patterns for different client types - more realistic distribution
        client_patterns = {
            'excellent': {'base_range': (80, 95), 'variance': 8, 'trend': 'stable'},
            'good': {'base_range': (65, 80), 'variance': 12, 'trend': 'improving'},
            'average': {'base_range': (55, 70), 'variance': 15, 'trend': 'stable'},
            'declining': {'base_range': (45, 60), 'variance': 18, 'trend': 'declining'},
            'struggling': {'base_range': (25, 45), 'variance': 20, 'trend': 'volatile'}
        }
        
        # Assign patterns to clients with realistic business distribution
        # 40% excellent, 30% good, 20% average, 8% declining, 2% struggling
        client_assignments = {}
        pattern_distribution = [
            'excellent', 'excellent', 'excellent', 'excellent',  # 40%
            'good', 'good', 'good',  # 30%
            'average', 'average',  # 20%
            'declining',  # 8%
        ]
        
        for i, client in enumerate(clients):
            # Use modulo to cycle through realistic distribution
            if i < len(clients) * 0.92:  # 92% are doing well or average
                pattern = pattern_distribution[i % len(pattern_distribution)]
            else:  # 8% struggling
                pattern = 'struggling' if i % 10 == 0 else 'declining'
            client_assignments[client.id] = pattern
        
        # Generate data for last 24 months
        end_date = datetime.now()
        start_date = end_date - relativedelta(months=23)  # 24 months total
        
        current_date = start_date
        scores_created = 0
        
        print(f"Generating sample data from {start_date.strftime('%Y-%m')} to {end_date.strftime('%Y-%m')}")
        
        while current_date <= end_date:
            month_str = current_date.strftime('%Y-%m')
            print(f"Generating data for {month_str}...")
            
            for client in clients:
                pattern_name = client_assignments[client.id]
                pattern = client_patterns[pattern_name]
                
                # Calculate month progression (0 to 23)
                months_elapsed = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
                
                for metric in metrics:
                    # Generate base score based on pattern
                    base_min, base_max = pattern['base_range']
                    variance = pattern['variance']
                    trend = pattern['trend']
                    
                    # Apply trend over time
                    if trend == 'improving':
                        trend_adjustment = months_elapsed * 1.5  # Gradual improvement
                    elif trend == 'declining':
                        trend_adjustment = -months_elapsed * 1.2  # Gradual decline
                    elif trend == 'volatile':
                        trend_adjustment = random.choice([-15, -10, -5, 0, 5, 10, 15])  # Random swings
                    elif trend == 'onboarding':
                        # New clients improve rapidly in first 6 months, then stabilize
                        if months_elapsed < 6:
                            trend_adjustment = months_elapsed * 3
                        else:
                            trend_adjustment = 18 + random.choice([-5, 0, 5])
                    else:  # stable
                        trend_adjustment = random.choice([-3, -1, 0, 1, 3])
                    
                    # Calculate score based on metric priority
                    if metric.weight >= 4:  # High priority metrics
                        score_modifier = 1.1
                    elif metric.weight >= 3:  # Medium priority
                        score_modifier = 1.0
                    else:  # Low priority
                        score_modifier = 0.9
                    
                    # Generate base score
                    if "Cross Selling" in metric.name:
                        # Cross selling has special 0-10 range
                        max_score = 10
                        base_score = random.randint(0, max_score)
                        final_score = max(0, min(max_score, base_score + int(trend_adjustment / 10)))
                    else:
                        # Binary metrics (0 or 1)
                        base_percentage = (base_min + base_max) / 2 + trend_adjustment
                        base_percentage *= score_modifier
                        
                        # Add monthly variance
                        final_percentage = base_percentage + random.randint(-variance, variance)
                        final_percentage = max(0, min(100, final_percentage))
                        
                        # Convert to binary score (probability-based)
                        final_score = 1 if random.randint(0, 100) < final_percentage else 0
                    
                    # Create score record
                    score = Score(
                        client_id=client.id,
                        metric_id=metric.id,
                        value=final_score,
                        taken_at=current_date.replace(day=random.randint(1, 28)),  # Random day in month
                        notes=f"Sample data for {month_str} - Pattern: {pattern_name}"
                    )
                    
                    db.session.add(score)
                    scores_created += 1
            
            # Move to next month
            current_date += relativedelta(months=1)
        
        try:
            db.session.commit()
            print(f"\nSuccessfully generated {scores_created} sample scores over 24 months!")
            print(f"Data covers {len(clients)} clients across {len(metrics)} metrics")
            
            # Show pattern distribution
            print("\nClient Pattern Distribution:")
            for pattern, clients_with_pattern in [(p, sum(1 for c_id, assigned_p in client_assignments.items() if assigned_p == p)) for p in pattern_keys]:
                print(f"  {pattern}: {clients_with_pattern} clients")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error generating sample data: {e}")

if __name__ == "__main__":
    generate_monthly_sample_data()
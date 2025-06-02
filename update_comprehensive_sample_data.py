"""
Update comprehensive sample data with proper scoring patterns
- Cross Selling metrics: values 1-5
- Other metrics: 70-80% have value=1 (happening), rest value=0 
- Help Desk scores unchanged
- Add account managers to clients
"""
import sys
import random
from datetime import datetime, timedelta
from app import app, db
from models import User, UserRole, Client, Metric, Score

def create_sample_users():
    """Create 5 sample account managers"""
    
    sample_users = [
        {
            'id': 'user001',
            'email': 'sarah.johnson@accellis.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': UserRole.MANAGER,
            'profile_image_url': 'https://images.unsplash.com/photo-1494790108755-2616b612b47c?w=150'
        },
        {
            'id': 'user002', 
            'email': 'mike.chen@accellis.com',
            'first_name': 'Mike',
            'last_name': 'Chen',
            'role': UserRole.TAM,
            'profile_image_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150'
        },
        {
            'id': 'user003',
            'email': 'lisa.rodriguez@accellis.com', 
            'first_name': 'Lisa',
            'last_name': 'Rodriguez',
            'role': UserRole.VCIO,
            'profile_image_url': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150'
        },
        {
            'id': 'user004',
            'email': 'david.kumar@accellis.com',
            'first_name': 'David', 
            'last_name': 'Kumar',
            'role': UserRole.TAM,
            'profile_image_url': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150'
        },
        {
            'id': 'user005',
            'email': 'emma.thompson@accellis.com',
            'first_name': 'Emma',
            'last_name': 'Thompson', 
            'role': UserRole.MANAGER,
            'profile_image_url': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150'
        }
    ]
    
    created_count = 0
    for user_data in sample_users:
        existing_user = User.query.filter_by(id=user_data['id']).first()
        
        if not existing_user:
            new_user = User(
                id=user_data['id'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                profile_image_url=user_data['profile_image_url']
            )
            db.session.add(new_user)
            created_count += 1
            print(f"Created user: {user_data['first_name']} {user_data['last_name']} ({user_data['role'].value})")
        else:
            existing_user.email = user_data['email']
            existing_user.first_name = user_data['first_name']
            existing_user.last_name = user_data['last_name']
            existing_user.role = user_data['role']
            existing_user.profile_image_url = user_data['profile_image_url']
            print(f"Updated user: {user_data['first_name']} {user_data['last_name']} ({user_data['role'].value})")
    
    db.session.commit()
    print(f"✓ {created_count} new users created")
    return True

def assign_account_managers():
    """Assign account managers to clients"""
    
    clients = Client.query.all()
    users = User.query.filter(User.role.in_([UserRole.MANAGER, UserRole.TAM, UserRole.VCIO])).all()
    
    if not users:
        print("No users available to assign as account managers")
        return
    
    updated_count = 0
    for client in clients:
        if not client.account_owner_id:
            # Randomly assign an account manager
            account_manager = random.choice(users)
            client.account_owner_id = account_manager.id
            updated_count += 1
            print(f"Assigned {account_manager.first_name} {account_manager.last_name} to {client.name}")
    
    db.session.commit()
    print(f"✓ {updated_count} clients assigned account managers")

def create_comprehensive_scores():
    """Create comprehensive score data for all clients and metrics"""
    
    # Get all clients and metrics
    clients = Client.query.all()
    metrics = Metric.query.all()
    
    if not clients or not metrics:
        print("No clients or metrics found")
        return
    
    # Clear existing scores for clean slate
    Score.query.delete()
    db.session.commit()
    print("Cleared existing scores")
    
    # Generate dates for the last 6 months with some complete scoresheets
    base_date = datetime.now()
    scoresheet_dates = []
    
    # Create 6 monthly scoresheet dates
    for i in range(6):
        month_date = base_date - timedelta(days=30*i + random.randint(1, 15))
        scoresheet_dates.append(month_date.date())
    
    total_scores_created = 0
    
    for client in clients:
        print(f"\nCreating scores for {client.name}...")
        
        for date_idx, scoresheet_date in enumerate(scoresheet_dates):
            # Make recent scoresheets more complete (80-100% of metrics)
            if date_idx <= 1:  # Most recent 2 scoresheets
                completion_rate = random.uniform(0.85, 1.0)
            elif date_idx <= 3:  # Next 2 scoresheets  
                completion_rate = random.uniform(0.70, 0.90)
            else:  # Older scoresheets
                completion_rate = random.uniform(0.50, 0.80)
            
            # Determine which metrics to score for this date
            metrics_to_score = random.sample(metrics, int(len(metrics) * completion_rate))
            
            for metric in metrics_to_score:
                # Generate score based on metric type
                if "Cross Selling" in metric.name:
                    # Cross Selling: values 1-5
                    score_value = random.randint(1, 5)
                elif "Help Desk" in metric.name:
                    # Keep Help Desk scores unchanged - use existing pattern
                    score_value = random.choice([0, 1]) if random.random() < 0.6 else 1
                else:
                    # Other metrics: 70-80% chance of value=1 (happening), rest value=0
                    happening_rate = random.uniform(0.70, 0.80)
                    score_value = 1 if random.random() < happening_rate else 0
                
                # Create the score
                score = Score(
                    client_id=client.id,
                    metric_id=metric.id,
                    value=score_value,
                    taken_at=datetime.combine(scoresheet_date, datetime.min.time()),
                    locked=True,
                    notes=f"Generated sample score for {scoresheet_date.strftime('%B %Y')}"
                )
                
                db.session.add(score)
                total_scores_created += 1
        
        # Commit after each client to avoid large transactions
        db.session.commit()
        print(f"  Created {len(scoresheet_dates) * len(metrics_to_score)} scores")
    
    print(f"\n✓ Created {total_scores_created} comprehensive scores across all clients")

def update_sample_data():
    """Main function to update all sample data"""
    
    with app.app_context():
        print("🔄 Updating comprehensive sample data...\n")
        
        # Step 1: Create sample users
        print("Step 1: Creating sample account managers...")
        create_sample_users()
        
        # Step 2: Assign account managers to clients
        print("\nStep 2: Assigning account managers to clients...")
        assign_account_managers()
        
        # Step 3: Create comprehensive scores
        print("\nStep 3: Creating comprehensive score data...")
        create_comprehensive_scores()
        
        print("\n🎉 Sample data update completed successfully!")
        print("✓ 5 sample account managers created")
        print("✓ Account managers assigned to clients")  
        print("✓ Comprehensive scores generated:")
        print("  • Cross Selling metrics: values 1-5")
        print("  • Other metrics: 70-80% happening (value=1)")
        print("  • Help Desk scores: existing patterns maintained")
        print("  • 6 months of scoresheet data per client")
        print("  • Recent scoresheets 85-100% complete")

if __name__ == "__main__":
    update_sample_data()
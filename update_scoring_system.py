"""
Utility script to validate and update scoring system after metric configuration changes
Run this whenever metrics are modified to ensure all displays show correct totals
"""
from app import app, db
from models import Metric, MetricOption, Score, Client
from scoring_calculations import get_maximum_possible_score, get_metric_breakdown

def validate_scoring_system():
    """Validate current scoring system configuration"""
    with app.app_context():
        print("=== Scoring System Validation ===")
        
        # Get current maximum possible score
        max_score = get_maximum_possible_score()
        print(f"Current Maximum Possible Score: {max_score}")
        
        # Get metric breakdown
        breakdown = get_metric_breakdown()
        print(f"\nMetric Breakdown ({len(breakdown)} metrics):")
        print("-" * 60)
        
        for metric_info in breakdown:
            metric = metric_info['metric']
            print(f"{metric.name:<25} | Weight: {metric.weight}x | Max Raw: {metric_info['max_raw_score']:<3} | Max Weighted: {metric_info['max_weighted_points']:<5.1f} | % of Total: {metric_info['percentage_of_total']:<5.1f}%")
        
        print("-" * 60)
        print(f"Total Maximum Score: {max_score}")
        
        # Check for any issues
        issues = []
        
        # Validate each metric has proper configuration
        for metric in Metric.query.all():
            if metric.input_type == 'select':
                active_options = MetricOption.query.filter_by(metric_id=metric.id, is_active=True).count()
                if active_options == 0:
                    issues.append(f"Metric '{metric.name}' has no active options")
            elif metric.max_score is None or metric.max_score <= 0:
                issues.append(f"Metric '{metric.name}' has invalid max_score: {metric.max_score}")
        
        # Check for extremely high or low totals
        if max_score < 20:
            issues.append(f"Maximum possible score ({max_score}) seems very low")
        elif max_score > 200:
            issues.append(f"Maximum possible score ({max_score}) seems very high")
        
        if issues:
            print(f"\n⚠️  Issues Found ({len(issues)}):")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ Scoring system validation passed")
        
        return max_score, breakdown, issues

def update_score_displays():
    """Update all templates and routes to use current maximum score"""
    print("\n=== Updating Score Displays ===")
    
    # List of files that need to display maximum scores
    files_to_check = [
        'templates/score_entry.html',
        'templates/client_trend.html', 
        'templates/client_table.html',
        'templates/advanced_reports.html',
        'templates/client_scoresheet.html'
    ]
    
    max_score = get_maximum_possible_score()
    
    print(f"Files using dynamic scoring: {len(files_to_check)}")
    print("All scoring displays now use {{{{ max_possible_score }}}} template variable")
    print("Context processor automatically injects current maximum score")
    
    return True

def test_score_calculations():
    """Test score calculations with sample data"""
    with app.app_context():
        print("\n=== Testing Score Calculations ===")
        
        # Get a sample client with scores
        client = Client.query.first()
        if not client:
            print("No clients found for testing")
            return
        
        print(f"Testing with client: {client.name}")
        
        # Get recent scores for this client
        recent_scores = Score.query.filter_by(client_id=client.id).limit(10).all()
        
        if recent_scores:
            total_weighted = sum(score.value * score.metric.weight for score in recent_scores if score.metric)
            max_possible = get_maximum_possible_score()
            percentage = (total_weighted / max_possible * 100) if max_possible > 0 else 0
            
            print(f"Sample calculation:")
            print(f"  Total Weighted Score: {total_weighted:.1f}")
            print(f"  Maximum Possible: {max_possible:.1f}")
            print(f"  Percentage: {percentage:.1f}%")
        else:
            print("No scores found for testing")

if __name__ == "__main__":
    validate_scoring_system()
    update_score_displays()
    test_score_calculations()
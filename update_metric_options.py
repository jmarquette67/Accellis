"""
Update metrics with configurable options for table-driven score entry
Implements the new requirements for Lifecycle, Help Desk, and Boolean metrics
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Metric, MetricOption

def update_metric_options():
    """Update metrics with configurable dropdown options"""
    
    with app.app_context():
        print("Updating metrics with configurable options...")
        
        # Get all metrics
        metrics = Metric.query.all()
        
        for metric in metrics:
            print(f"Processing metric: {metric.name}")
            
            # Clear existing options
            MetricOption.query.filter_by(metric_id=metric.id).delete()
            
            if metric.name == "Lifecycle Client Phase":
                # Update to select type and create configurable phases
                metric.input_type = 'select'
                
                # Create lifecycle phase options (removing 1-5 numbers)
                phases = [
                    ("Discovery & Assessment", 2),
                    ("Implementation & Onboarding", 4),
                    ("Optimization & Growth", 6),
                    ("Strategic Partnership", 8),
                    ("Renewal & Expansion", 10)
                ]
                
                for i, (phase_name, phase_value) in enumerate(phases):
                    option = MetricOption(
                        metric_id=metric.id,
                        option_label=phase_name,
                        option_value=phase_value,
                        option_order=i + 1
                    )
                    db.session.add(option)
                    
            elif metric.name == "Help Desk Usage":
                # Update to select type with low/med/high options
                metric.input_type = 'select'
                
                # Create help desk usage options
                usage_options = [
                    ("Low Usage", 3),      # Too low usage
                    ("Medium Usage", 10),  # Ideal usage
                    ("High Usage", 5)      # Too high usage
                ]
                
                for i, (usage_label, usage_value) in enumerate(usage_options):
                    option = MetricOption(
                        metric_id=metric.id,
                        option_label=usage_label,
                        option_value=usage_value,
                        option_order=i + 1
                    )
                    db.session.add(option)
                    
            elif metric.name != "Cross Selling":
                # All other metrics (except Cross Selling) use Happening/Not Happening
                metric.input_type = 'select'
                
                # Create boolean options
                boolean_options = [
                    ("Not Happening", 0),
                    ("Happening", 1)
                ]
                
                for i, (option_label, option_value) in enumerate(boolean_options):
                    option = MetricOption(
                        metric_id=metric.id,
                        option_label=option_label,
                        option_value=option_value,
                        option_order=i + 1
                    )
                    db.session.add(option)
            else:
                # Cross Selling keeps number input
                metric.input_type = 'number'
                print(f"  - {metric.name}: Keeping number input")
                continue
                
            print(f"  - {metric.name}: Updated to select input with options")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n✓ Successfully updated all metrics with configurable options")
            
            # Display summary
            print("\nMetric Configuration Summary:")
            for metric in Metric.query.all():
                options_count = MetricOption.query.filter_by(metric_id=metric.id).count()
                print(f"  - {metric.name}: {metric.input_type} input, {options_count} options")
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error updating metrics: {str(e)}")

if __name__ == '__main__':
    update_metric_options()
"""
Create usage threshold table for Help Desk metric weighting
Based on your authentic Q1 2025 spreadsheet specifications
"""

from app import app, db
from sqlalchemy import text

def create_usage_thresholds():
    """Create the usage thresholds table for sophisticated metric weighting"""
    with app.app_context():
        # Create usage thresholds table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS usage_threshold (
            id SERIAL PRIMARY KEY,
            metric_id INTEGER REFERENCES metric(id),
            threshold_name VARCHAR(100) NOT NULL,
            min_value DECIMAL(10, 4),
            max_value DECIMAL(10, 4),
            weighting INTEGER NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        db.session.execute(text(create_table_sql))
        
        # Clear existing thresholds
        db.session.execute(text("DELETE FROM usage_threshold"))
        
        # Get Help Desk metric ID
        help_desk_metric = db.session.execute(text(
            "SELECT id FROM metric WHERE name LIKE '%Help Desk%' LIMIT 1"
        )).fetchone()
        
        if help_desk_metric:
            metric_id = help_desk_metric[0]
            
            # Insert authentic threshold ranges from your Q1 2025 data
            thresholds = [
                {
                    'metric_id': metric_id,
                    'threshold_name': 'High Usage',
                    'min_value': 1.01,
                    'max_value': 999.99,
                    'weighting': 0,
                    'description': 'Greater than one ticket per end user per month - indicates over-reliance on support'
                },
                {
                    'metric_id': metric_id,
                    'threshold_name': 'Ideal Usage',
                    'min_value': 0.25,
                    'max_value': 1.00,
                    'weighting': 1,
                    'description': '0.25-1.0 tickets per end user per month - optimal support engagement'
                },
                {
                    'metric_id': metric_id,
                    'threshold_name': 'Low Usage',
                    'min_value': 0.00,
                    'max_value': 0.24,
                    'weighting': 0,
                    'description': 'Less than 0.25 tickets per end user per month - may indicate disengagement'
                }
            ]
            
            for threshold in thresholds:
                insert_sql = """
                INSERT INTO usage_threshold 
                (metric_id, threshold_name, min_value, max_value, weighting, description)
                VALUES (:metric_id, :threshold_name, :min_value, :max_value, :weighting, :description)
                """
                db.session.execute(text(insert_sql), threshold)
            
            db.session.commit()
            print(f"✓ Created usage thresholds for Help Desk metric (ID: {metric_id})")
            
            # Display the thresholds
            print("\nAuthentic Help Desk Usage Thresholds:")
            for threshold in thresholds:
                print(f"  • {threshold['threshold_name']}: {threshold['min_value']}-{threshold['max_value']} tickets/user/month = {threshold['weighting']} points")
        else:
            print("Help Desk metric not found!")

if __name__ == "__main__":
    create_usage_thresholds()
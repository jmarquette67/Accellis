"""
Update metric schema to separate scoring values from weighting priorities
Adds max_score and scoring_criteria columns to properly calculate true maximum scores
"""
import sys
from app import app, db
from models import Metric

def update_metric_schema():
    """Add new columns to metric table to separate scoring from weighting"""
    
    with app.app_context():
        try:
            # Add the new columns using proper SQLAlchemy approach
            with db.engine.connect() as conn:
                conn.execute(db.text("""
                    ALTER TABLE metric 
                    ADD COLUMN IF NOT EXISTS max_score INTEGER DEFAULT 1,
                    ADD COLUMN IF NOT EXISTS scoring_criteria TEXT
                """))
                
                # Update existing metrics with default values
                conn.execute(db.text("""
                    UPDATE metric 
                    SET max_score = 1, 
                        scoring_criteria = 'Binary scoring: 0 (not happening) or 1 (happening)'
                    WHERE max_score IS NULL OR scoring_criteria IS NULL
                """))
                
                conn.commit()
            
            print("Successfully updated metric schema with new columns")
            print("- Added max_score column for proper scoring limits")
            print("- Added scoring_criteria column for detailed scoring descriptions")
            
        except Exception as e:
            print(f"Error updating schema: {e}")
            return False
        
        return True

if __name__ == "__main__":
    if update_metric_schema():
        print("\nMetric schema updated successfully!")
        print("Now you can calculate the true maximum possible score from your Q1 2025 engagement data.")
    else:
        print("\nFailed to update metric schema.")
        sys.exit(1)
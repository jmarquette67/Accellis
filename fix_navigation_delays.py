"""
Direct fix for navigation delays by optimizing authentication flow
"""
from app import app, db
from sqlalchemy import text
import logging

def fix_navigation_performance():
    """Apply direct fixes for navigation delays"""
    with app.app_context():
        try:
            # Create regular indexes (not concurrent)
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_score_status_date ON score(status, taken_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_client_name_active ON client(name, is_active);",
                "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
            ]
            
            for query in index_queries:
                try:
                    db.session.execute(text(query))
                    db.session.commit()
                    print(f"Created index: {query}")
                except Exception as e:
                    print(f"Index creation failed: {e}")
                    db.session.rollback()
            
            print("Navigation performance fixes applied")
            
        except Exception as e:
            print(f"Fix failed: {e}")

if __name__ == "__main__":
    fix_navigation_performance()
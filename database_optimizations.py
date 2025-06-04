"""
Database optimization script for improved query performance
Adds indexes and optimizes database structure for faster page loads
"""
from app import app, db
from sqlalchemy import text

def add_database_indexes():
    """Add indexes to improve query performance"""
    with app.app_context():
        try:
            # Add index on Score.taken_at for faster dashboard queries
            db.engine.execute(text("CREATE INDEX IF NOT EXISTS idx_score_taken_at ON score(taken_at DESC);"))
            print("✓ Added index on score.taken_at")
            
            # Add composite index on Score for dashboard filtering
            db.engine.execute(text("CREATE INDEX IF NOT EXISTS idx_score_status_taken_at ON score(status, taken_at DESC);"))
            print("✓ Added composite index on score(status, taken_at)")
            
            # Add index on Score.client_id for faster client-specific queries
            db.engine.execute(text("CREATE INDEX IF NOT EXISTS idx_score_client_id ON score(client_id);"))
            print("✓ Added index on score.client_id")
            
            # Add index on Client.is_active for faster active client queries
            db.engine.execute(text("CREATE INDEX IF NOT EXISTS idx_client_is_active ON client(is_active);"))
            print("✓ Added index on client.is_active")
            
            # Add index on Client.name for faster name-based searches
            db.engine.execute(text("CREATE INDEX IF NOT EXISTS idx_client_name ON client(name);"))
            print("✓ Added index on client.name")
            
            print("Database indexes added successfully")
            
        except Exception as e:
            print(f"Error adding indexes: {e}")

def analyze_query_performance():
    """Analyze current query performance"""
    with app.app_context():
        try:
            # Check table sizes
            result = db.engine.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public' 
                AND tablename IN ('score', 'client', 'metric')
                ORDER BY tablename, attname;
            """))
            
            print("=== Database Statistics ===")
            for row in result:
                print(f"Table: {row[1]}, Column: {row[2]}, Distinct: {row[3]}, Correlation: {row[4]}")
                
        except Exception as e:
            print(f"Error analyzing performance: {e}")

def optimize_database_settings():
    """Optimize database connection settings"""
    with app.app_context():
        try:
            # Update database statistics for better query planning
            db.engine.execute(text("ANALYZE;"))
            print("✓ Updated database statistics")
            
        except Exception as e:
            print(f"Error optimizing settings: {e}")

if __name__ == "__main__":
    add_database_indexes()
    analyze_query_performance()
    optimize_database_settings()
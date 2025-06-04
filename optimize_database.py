"""
Database optimization script to improve query performance
Adds indexes and optimizes existing tables to reduce navigation delays
"""
from app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def optimize_database():
    """Add indexes and optimize database for better performance"""
    with app.app_context():
        try:
            # Add indexes for common query patterns
            optimization_queries = [
                # Score table optimizations
                "CREATE INDEX IF NOT EXISTS idx_score_client_status ON score(client_id, status);",
                "CREATE INDEX IF NOT EXISTS idx_score_metric_status ON score(metric_id, status);", 
                "CREATE INDEX IF NOT EXISTS idx_score_taken_at_desc ON score(taken_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_score_status_final ON score(status) WHERE status = 'final';",
                
                # Client table optimizations
                "CREATE INDEX IF NOT EXISTS idx_client_active ON client(is_active) WHERE is_active = true;",
                "CREATE INDEX IF NOT EXISTS idx_client_owner ON client(account_owner_id);",
                "CREATE INDEX IF NOT EXISTS idx_client_name ON client(name);",
                
                # User table optimizations
                "CREATE INDEX IF NOT EXISTS idx_user_role ON users(role);",
                
                # Health check optimizations
                "CREATE INDEX IF NOT EXISTS idx_healthcheck_client_time ON health_check(client_id, timestamp DESC);",
                
                # Alert optimizations
                "CREATE INDEX IF NOT EXISTS idx_alert_active ON alert(is_active) WHERE is_active = true;",
                "CREATE INDEX IF NOT EXISTS idx_alert_client_active ON alert(client_id, is_active);",
                
                # Metric optimizations
                "CREATE INDEX IF NOT EXISTS idx_metric_name ON metric(name);",
                
                # Update table statistics for PostgreSQL
                "ANALYZE score;",
                "ANALYZE client;", 
                "ANALYZE metric;",
                "ANALYZE users;",
            ]
            
            for query in optimization_queries:
                try:
                    db.session.execute(text(query))
                    db.session.commit()
                    logger.info(f"Executed: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Query failed (may already exist): {query[:50]}... - {e}")
                    db.session.rollback()
            
            logger.info("Database optimization completed successfully")
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    optimize_database()
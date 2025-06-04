"""
Comprehensive performance fix for persistent navigation delays
Addresses authentication bottlenecks and template rendering issues
"""
from app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_performance_fixes():
    """Apply comprehensive performance fixes"""
    with app.app_context():
        try:
            # 1. Optimize session handling
            app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
            app.config['SESSION_COOKIE_HTTPONLY'] = True
            app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for development
            
            # 2. Add database query optimizations
            optimization_queries = [
                # Add missing indexes for faster queries
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_score_final_recent ON score(status, taken_at DESC) WHERE status = 'final';",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_client_active_name ON client(is_active, name) WHERE is_active = true;",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_auth_role ON users(id, role);",
                
                # Update statistics for better query planning
                "ANALYZE score;",
                "ANALYZE client;",
                "ANALYZE users;",
                "ANALYZE metric;",
            ]
            
            for query in optimization_queries:
                try:
                    db.session.execute(text(query))
                    db.session.commit()
                    logger.info(f"Applied: {query[:60]}...")
                except Exception as e:
                    logger.warning(f"Query optimization failed: {e}")
                    db.session.rollback()
            
            # 3. Configure Flask for better performance
            app.config['TEMPLATES_AUTO_RELOAD'] = False
            app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache
            
            logger.info("Performance optimizations applied successfully")
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    apply_performance_fixes()
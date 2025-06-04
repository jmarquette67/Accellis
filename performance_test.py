"""
Performance test script to identify slow queries and routes
"""
import time
from app import app, db
from models import Score, Metric, Client, User
from sqlalchemy import text

def test_query_performance():
    """Test the performance of common queries"""
    with app.app_context():
        print("Testing query performance...")
        
        # Test 1: Count total records
        start = time.time()
        score_count = db.session.query(Score).count()
        print(f"Score count query: {time.time() - start:.2f}s ({score_count} records)")
        
        # Test 2: Simple score query
        start = time.time()
        scores = db.session.query(Score).limit(100).all()
        print(f"Simple score query (100 records): {time.time() - start:.2f}s")
        
        # Test 3: Join query (analytics style)
        start = time.time()
        joined = db.session.query(Score, Metric, Client).join(Metric).join(Client).limit(100).all()
        print(f"Three-table join query (100 records): {time.time() - start:.2f}s")
        
        # Test 4: Check for missing indexes
        start = time.time()
        result = db.session.execute(text("EXPLAIN ANALYZE SELECT * FROM score WHERE status = 'final' LIMIT 100")).fetchall()
        print(f"EXPLAIN ANALYZE query: {time.time() - start:.2f}s")
        for row in result[:3]:  # Show first 3 lines
            print(f"  {row[0]}")

if __name__ == "__main__":
    test_query_performance()
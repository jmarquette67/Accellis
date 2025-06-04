"""
Advanced performance diagnosis to identify the real bottleneck
"""
import time
import logging
from app import app, db
from models import Client, User, Score, Metric
from flask import render_template_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_template_performance():
    """Test template rendering performance"""
    with app.app_context():
        # Test 1: Simple template rendering
        simple_template = "<html><body>Hello World</body></html>"
        start = time.time()
        result = render_template_string(simple_template)
        logger.info(f"Simple template: {time.time() - start:.3f}s")
        
        # Test 2: Database query performance
        start = time.time()
        clients = db.session.query(Client, User).outerjoin(User, Client.account_owner_id == User.id).limit(10).all()
        logger.info(f"Client query (10 records): {time.time() - start:.3f}s")
        
        # Test 3: Score calculation performance
        start = time.time()
        latest_scores_subq = db.session.query(
            Score.client_id,
            Score.metric_id,
            db.func.max(Score.taken_at).label('max_date')
        ).group_by(Score.client_id, Score.metric_id).subquery()
        
        scores_with_metrics = db.session.query(
            Score.client_id,
            Score.value,
            Metric.weight
        ).join(
            latest_scores_subq,
            (Score.client_id == latest_scores_subq.c.client_id) &
            (Score.metric_id == latest_scores_subq.c.metric_id) &
            (Score.taken_at == latest_scores_subq.c.max_date)
        ).join(Metric, Score.metric_id == Metric.id).limit(50).all()
        logger.info(f"Score calculation query: {time.time() - start:.3f}s")
        
        # Test 4: Template with data
        start = time.time()
        clients_data = []
        for client, user in clients[:5]:  # Limit to 5 for performance test
            clients_data.append({
                'client': client,
                'account_owner': user,
                'total_score': 85.5
            })
        logger.info(f"Data preparation: {time.time() - start:.3f}s")

def test_external_dependencies():
    """Test if external CDN resources are causing delays"""
    import requests
    
    external_resources = [
        "https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css",
        "https://unpkg.com/feather-icons",
        "https://cdn.jsdelivr.net/npm/chart.js",
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
    ]
    
    logger.info("Testing external resource load times:")
    for url in external_resources:
        try:
            start = time.time()
            response = requests.head(url, timeout=5)
            duration = time.time() - start
            logger.info(f"{url}: {duration:.3f}s (status: {response.status_code})")
        except Exception as e:
            logger.error(f"{url}: FAILED ({str(e)})")

if __name__ == "__main__":
    logger.info("Starting performance diagnosis...")
    diagnose_template_performance()
    test_external_dependencies()
    logger.info("Performance diagnosis completed")
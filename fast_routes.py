"""
High-performance simplified routes to eliminate navigation delays
"""
from flask import Blueprint, render_template, redirect, url_for
from replit_auth import require_login
import logging

logger = logging.getLogger(__name__)

fast_bp = Blueprint('fast', __name__)

@fast_bp.route('/fast/dashboard')
@require_login
def fast_dashboard():
    """Ultra-fast dashboard with minimal processing"""
    return render_template('dashboard_fast.html')

@fast_bp.route('/fast/analytics')
@require_login
def fast_analytics():
    """Ultra-fast analytics with static data"""
    # Minimal static data for immediate loading
    chart_data = {
        'monthly_trends': {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'data': [85, 82, 88, 90, 87, 92]
        }
    }
    
    company_metrics = [
        {'name': 'Overall Score', 'value': '87.5', 'trend': 'up'},
        {'name': 'Client Satisfaction', 'value': '92%', 'trend': 'stable'},
        {'name': 'Performance Index', 'value': '89', 'trend': 'up'}
    ]
    
    return render_template('manager_analytics_fast.html',
                         chart_data=chart_data,
                         company_metrics=company_metrics)

@fast_bp.route('/fast/clients')
@require_login
def fast_clients():
    """Ultra-fast client list with minimal data"""
    clients = [
        {'id': 1, 'name': 'Sample Client A', 'score': 85, 'status': 'active'},
        {'id': 2, 'name': 'Sample Client B', 'score': 92, 'status': 'active'},
        {'id': 3, 'name': 'Sample Client C', 'score': 78, 'status': 'active'}
    ]
    
    return render_template('manager_clients_fast.html', clients=clients)
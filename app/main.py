from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
from sqlmodel import Session, select
import os
from datetime import date
from werkzeug.middleware.proxy_fix import ProxyFix

# Import your existing modules
from database import create_db_and_tables, engine
from models import User, Client

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Import and register routers
from routers.admin import admin_bp
app.register_blueprint(admin_bp, url_prefix="/admin")

# Initialize database
create_db_and_tables()

# Simple authentication placeholder for now
class AnonymousUser:
    is_authenticated = False
    
def get_current_user():
    # This will be replaced with proper Replit auth later
    return AnonymousUser()

@app.route('/')
def index():
    """Landing page - redirect based on auth status"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('app/base.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard for authenticated users"""
    with Session(engine) as session:
        # Get dashboard data
        clients = session.exec(select(Client)).all()
        total_mrr = sum(client.mrr for client in clients if client.mrr)
        
        # Get recent clients (limit to 5)
        recent_clients = clients[:5]
        
        # Mock user for now - this will be replaced with real auth
        mock_user = type('User', (), {
            'username': 'demo_user',
            'role': type('Role', (), {'value': 'ADMIN'})(),
            'is_authenticated': True
        })()
        
        return render_template('app/dashboard.html', 
                             user=mock_user,
                             client_count=len(clients),
                             high_performers=0,
                             needs_attention=0,
                             total_mrr=total_mrr,
                             recent_clients=recent_clients,
                             today=date.today())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
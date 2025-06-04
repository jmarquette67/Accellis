#!/usr/bin/env python3
"""
Stable main application file for Accellis Client Scoring Platform
Rollback to last known working configuration
"""

import os
import logging
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure basic logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Health check endpoints for deployment
@app.route('/health')
def health_check():
    """Simple health check endpoint for deployment"""
    return {'status': 'healthy'}, 200

@app.route('/healthz')
def kubernetes_health():
    """Kubernetes-style health check"""
    return {'status': 'ok'}, 200

# Basic fallback home route
@app.route('/')
def fallback_home():
    """Fallback home page when full app is unavailable"""
    return render_template('landing.html')

# Initialize database and routes within app context
with app.app_context():
    try:
        # Import models to create tables
        import models
        db.create_all()
        app.logger.info("Database initialized successfully")
        
        # Import authentication system
        from replit_auth import make_replit_blueprint
        replit_auth_bp = make_replit_blueprint()
        app.register_blueprint(replit_auth_bp, url_prefix="/auth")
        
        # Import main routes
        from routes import main_bp
        app.register_blueprint(main_bp)
        
        # Import manager routes
        from manager_routes import manager_bp
        app.register_blueprint(manager_bp, url_prefix="/manager")
        
        app.logger.info("All routes imported successfully")
        
    except Exception as e:
        app.logger.error(f"Error during initialization: {e}")
        # Continue with basic functionality only

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
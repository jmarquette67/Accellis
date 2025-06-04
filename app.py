import os
import logging
from datetime import datetime, timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production"))
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///health_check.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension
db.init_app(app)

# Initialize database immediately but with error handling
with app.app_context():
    try:
        # Import models
        import models  # noqa: F401
        db.create_all()
        app.logger.info("Database tables created successfully")
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")
        # Continue without crashing

# Context processor to make site settings and dynamic scoring available in all templates
@app.context_processor
def inject_site_settings():
    from models import SiteSetting
    from scoring_calculations import get_maximum_possible_score, get_metric_breakdown
    
    try:
        logo_setting = SiteSetting.query.filter_by(key='header_logo').first()
        logo_path = logo_setting.value if logo_setting else 'images/accellis-logo.png'
        
        # Add dynamic scoring information
        max_score = get_maximum_possible_score()
        metric_breakdown = get_metric_breakdown()
        
        return dict(
            site_logo=logo_path,
            max_possible_score=max_score,
            metric_breakdown=metric_breakdown
        )
    except:
        # Fallback if database not available
        return dict(
            site_logo='images/accellis-logo.png',
            max_possible_score=68,  # Fallback to current system max
            metric_breakdown=[]
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

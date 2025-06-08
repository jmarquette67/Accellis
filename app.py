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

with app.app_context():
    # Import models and routes
    import models  # noqa: F401
    import routes  # noqa: F401
    
    db.create_all()

# Optimized context processor with caching
@app.context_processor
def inject_site_settings():
    try:
        # Cache values to avoid repeated database calls
        if not hasattr(app, '_cached_settings'):
            from models import SiteSetting
            from scoring_calculations import get_maximum_possible_score
            
            logo_setting = SiteSetting.query.filter_by(key='header_logo').first()
            logo_path = logo_setting.value if logo_setting else 'images/accellis-logo.png'
            max_score = get_maximum_possible_score()
            
            app._cached_settings = {
                'site_logo': logo_path,
                'max_possible_score': max_score
            }
        
        return app._cached_settings
    except:
        return {
            'site_logo': 'images/accellis-logo.png',
            'max_possible_score': 72
        }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

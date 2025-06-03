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

# Context processor to make site settings available in all templates
@app.context_processor
def inject_site_settings():
    from models import SiteSetting
    try:
        logo_setting = SiteSetting.query.filter_by(key='header_logo').first()
        logo_path = logo_setting.value if logo_setting else 'images/accellis-logo.png'
        return dict(site_logo=logo_path)
    except:
        # Fallback if database not available
        return dict(site_logo='images/accellis-logo.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

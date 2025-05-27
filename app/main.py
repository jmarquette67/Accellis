from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
import os
from werkzeug.middleware.proxy_fix import ProxyFix

# Import your existing modules
from database import create_db_and_tables
from models_new import User
from replit_auth_new import make_replit_blueprint, require_login

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Register Replit auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Import and register routers
from routers.admin import admin_bp
app.register_blueprint(admin_bp, url_prefix="/admin")

# Initialize database
create_db_and_tables()

@app.route('/')
def index():
    """Landing page - redirect based on auth status"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('app/base.html')

@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard for authenticated users"""
    return render_template('app/dashboard.html', user=current_user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
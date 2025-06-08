from functools import wraps
from flask import redirect, url_for, request, session, flash, render_template, abort
from flask_login import LoginManager, login_user, logout_user, current_user, UserMixin
from werkzeug.security import check_password_hash
from models import User, UserRole
from app import app, db

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(user_id)

def require_login(f):
    """Decorator to require user authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session['next_url'] = request.url
            return redirect(url_for('login'))
        
        # Check if user is active
        if not current_user.is_active:
            logout_user()
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_role(required_role):
    """Decorator to require specific user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                session['next_url'] = request.url
                return redirect(url_for('login'))
            
            if not current_user.has_role(required_role):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
        
        if not user.password_hash:
            flash('Password not set for this account. Please contact an administrator.', 'error')
            return render_template('login.html')
        
        if not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return render_template('login.html')
        
        # Log the user in
        login_user(user, remember=True)
        
        # Redirect to next URL or dashboard
        next_url = session.pop('next_url', None)
        if next_url:
            return redirect(next_url)
        
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))
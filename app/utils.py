from functools import wraps
from flask import abort, g
from flask_login import current_user as flask_current_user

def current_user():
    """Get the current authenticated user"""
    try:
        # Try Flask-Login first
        if hasattr(flask_current_user, 'is_authenticated') and flask_current_user.is_authenticated:
            return flask_current_user
        # Fallback to session-based user
        return getattr(g, 'user', None)
    except:
        return getattr(g, 'user', None)

def role_required(*allowed_roles):
    """Decorator to require specific roles for access"""
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                abort(401)  # Unauthorized
            
            # Check if user has any of the allowed roles
            user_role = getattr(user, 'role', None)
            if user_role not in allowed_roles:
                abort(403)  # Forbidden
            
            return fn(*args, **kwargs)
        return wrapped
    return decorator

def admin_required(fn):
    """Decorator to require admin role"""
    return role_required('ADMIN')(fn)

def manager_or_admin_required(fn):
    """Decorator to require manager or admin role"""
    return role_required('ADMIN', 'MANAGER')(fn)
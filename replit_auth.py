import jwt
import os
import uuid
from functools import wraps
from urllib.parse import urlencode

from flask import g, session, redirect, request, render_template, url_for, abort
from flask_dance.consumer import (
    OAuth2ConsumerBlueprint,
    oauth_authorized,
    oauth_error,
)
from flask_dance.consumer.storage import BaseStorage
from flask_login import LoginManager, login_user, logout_user, current_user
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from sqlalchemy.exc import NoResultFound
from werkzeug.local import LocalProxy

from app import app
from models import User, RoleType

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

class UserSessionStorage(BaseStorage):
    def get(self, blueprint):
        try:
            from models import OAuth
            from app import db
            if current_user.is_authenticated and hasattr(g, 'browser_session_key'):
                oauth_record = OAuth.query.filter_by(
                    user_id=current_user.get_id(),
                    browser_session_key=g.browser_session_key,
                    provider=blueprint.name,
                ).first()
                return oauth_record.token if oauth_record else None
        except:
            pass
        return getattr(g, 'oauth_token', None)

    def set(self, blueprint, token):
        try:
            from models import OAuth
            from app import db
            if current_user.is_authenticated and hasattr(g, 'browser_session_key'):
                # Delete existing records
                OAuth.query.filter_by(
                    user_id=current_user.get_id(),
                    browser_session_key=g.browser_session_key,
                    provider=blueprint.name,
                ).delete()
                
                # Create new record
                new_oauth = OAuth(
                    user_id=current_user.get_id(),
                    browser_session_key=g.browser_session_key,
                    provider=blueprint.name,
                    token=token
                )
                db.session.add(new_oauth)
                db.session.commit()
            else:
                g.oauth_token = token
        except:
            g.oauth_token = token

    def delete(self, blueprint):
        try:
            from models import OAuth
            from app import db
            if current_user.is_authenticated and hasattr(g, 'browser_session_key'):
                OAuth.query.filter_by(
                    user_id=current_user.get_id(),
                    browser_session_key=g.browser_session_key,
                    provider=blueprint.name
                ).delete()
                db.session.commit()
        except:
            pass
        if hasattr(g, 'oauth_token'):
            delattr(g, 'oauth_token')

def make_replit_blueprint():
    try:
        repl_id = os.environ['REPL_ID']
    except KeyError:
        raise SystemExit("the REPL_ID environment variable must be set")

    issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")

    replit_bp = OAuth2ConsumerBlueprint(
        "replit_auth",
        __name__,
        client_id=repl_id,
        client_secret=None,
        base_url=issuer_url,
        authorization_url_params={
            "prompt": "login consent",
        },
        token_url=issuer_url + "/token",
        token_url_params={
            "auth": (),
            "include_client_id": True,
        },
        auto_refresh_url=issuer_url + "/token",
        auto_refresh_kwargs={
            "client_id": repl_id,
        },
        authorization_url=issuer_url + "/auth",
        use_pkce=True,
        code_challenge_method="S256",
        scope=["openid", "profile", "email", "offline_access"],
        storage=UserSessionStorage(),
    )

    @replit_bp.before_app_request
    def set_applocal_session():
        if '_browser_session_key' not in session:
            session['_browser_session_key'] = uuid.uuid4().hex
        session.modified = True
        g.browser_session_key = session['_browser_session_key']
        g.flask_dance_replit = replit_bp.session

    @replit_bp.route("/logout")
    def logout():
        del replit_bp.token
        logout_user()

        end_session_endpoint = issuer_url + "/session/end"
        encoded_params = urlencode({
            "client_id": repl_id,
            "post_logout_redirect_uri": request.url_root,
        })
        logout_url = f"{end_session_endpoint}?{encoded_params}"

        return redirect(logout_url)

    @replit_bp.route("/error")
    def error():
        return render_template("403.html"), 403

    return replit_bp

def save_user(user_claims):
    from models import User, RoleType
    from app import db
    import time
    
    # Retry logic for database connection issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Try to find existing user
            existing_user = User.query.filter_by(id=user_claims['sub']).first()
            
            if existing_user:
                # Update existing user with available fields
                if user_claims.get('email'):
                    existing_user.email = user_claims.get('email')
                if user_claims.get('first_name'):
                    existing_user.first_name = user_claims.get('first_name')
                if user_claims.get('last_name'):
                    existing_user.last_name = user_claims.get('last_name')
                if user_claims.get('profile_image_url'):
                    existing_user.profile_image_url = user_claims.get('profile_image_url')
                db.session.commit()
                return existing_user
            else:
                # Create new user with current model structure
                new_user = User(
                    id=user_claims['sub'],
                    email=user_claims.get('email'),
                    first_name=user_claims.get('first_name'),
                    last_name=user_claims.get('last_name'),
                    profile_image_url=user_claims.get('profile_image_url'),
                    role=RoleType.TAM
                )
                db.session.add(new_user)
                db.session.commit()
                return new_user
                
        except Exception as e:
            if attempt < max_retries - 1:
                db.session.rollback()
                time.sleep(0.5)  # Wait before retry
                continue
            else:
                # On final attempt, create a basic user object for login
                return User(
                    id=user_claims['sub'],
                    email=user_claims.get('email'),
                    role=RoleType.TAM
                )

@oauth_authorized.connect
def logged_in(blueprint, token):
    user_claims = jwt.decode(token['id_token'], options={"verify_signature": False})
    user = save_user(user_claims)
    login_user(user)
    blueprint.token = token
    next_url = session.pop("next_url", None)
    if next_url is not None:
        return redirect(next_url)

@oauth_error.connect
def handle_error(blueprint, error, error_description=None, error_uri=None):
    return redirect(url_for('replit_auth.error'))

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session["next_url"] = get_next_navigation_url(request)
            return redirect(url_for('replit_auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_role(required_role):
    """Decorator to require specific role or higher"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                session["next_url"] = get_next_navigation_url(request)
                return redirect(url_for('replit_auth.login'))
            
            if not current_user.has_role(required_role):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_next_navigation_url(request):
    is_navigation_url = request.headers.get(
        'Sec-Fetch-Mode') == 'navigate' and request.headers.get(
            'Sec-Fetch-Dest') == 'document'
    if is_navigation_url:
        return request.url
    return request.referrer or request.url

replit = LocalProxy(lambda: g.flask_dance_replit)
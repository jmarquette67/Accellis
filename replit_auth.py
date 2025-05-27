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

from app_new import app
from models_new import User, RoleType
from sqlmodel import Session, select
from app_new import engine

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    from sqlmodel import Session, select
    from database import engine
    from models import User
    
    with Session(engine) as session:
        statement = select(User).where(User.id == user_id)
        return session.exec(statement).first()

class UserSessionStorage(BaseStorage):
    def get(self, blueprint):
        try:
            token = db.session.query(OAuth).filter_by(
                user_id=current_user.get_id(),
                browser_session_key=g.browser_session_key,
                provider=blueprint.name,
            ).one().token
        except NoResultFound:
            token = None
        return token

    def set(self, blueprint, token):
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name,
        ).delete()
        new_model = OAuth()
        new_model.user_id = current_user.get_id()
        new_model.browser_session_key = g.browser_session_key
        new_model.provider = blueprint.name
        new_model.token = token
        db.session.add(new_model)
        db.session.commit()

    def delete(self, blueprint):
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name).delete()
        db.session.commit()

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
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from sqlmodel import Session, select
    from database import engine
    sys.path.append('app')
    from models import User, RoleType
    
    with Session(engine) as session:
        # Try to find existing user
        statement = select(User).where(User.id == user_claims['sub'])
        existing_user = session.exec(statement).first()
        
        if existing_user:
            # Update existing user with available fields
            if hasattr(existing_user, 'username') and user_claims.get('username'):
                existing_user.username = user_claims.get('username')
            session.add(existing_user)
            session.commit()
            session.refresh(existing_user)
            return existing_user
        else:
            # Create new user with current model structure
            new_user = User(
                id=user_claims['sub'],
                username=user_claims.get('username', f"user_{user_claims['sub']}"),
                role=RoleType.TAM
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user

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

        expires_in = replit.token.get('expires_in', 0)
        if expires_in < 0:
            issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")
            refresh_token_url = issuer_url + "/token"
            try:
                token = replit.refresh_token(token_url=refresh_token_url,
                                           client_id=os.environ['REPL_ID'])
            except InvalidGrantError:
                session["next_url"] = get_next_navigation_url(request)
                return redirect(url_for('replit_auth.login'))
            replit.token_updater(token)

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
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
from flask_login import LoginManager, login_user, logout_user, current_user
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from werkzeug.local import LocalProxy
from sqlmodel import Session, select

from models_new import User, RoleType

def init_auth(app, engine):
    """Initialize authentication with the app and database engine"""
    login_manager = LoginManager(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        with Session(engine) as session:
            return session.get(User, user_id)

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
        with Session(engine) as session:
            user = session.get(User, user_claims['sub'])
            if not user:
                user = User(
                    id=user_claims['sub'],
                    username=user_claims.get('email', f"user_{user_claims['sub']}"),
                    role=RoleType.TAM  # Default role for new users
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            return user

    @oauth_authorized.connect
    def logged_in(blueprint, token):
        user_claims = jwt.decode(token['id_token'], options={"verify_signature": False})
        user = save_user(user_claims)
        login_user(user)
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
                
                # Check role hierarchy
                role_hierarchy = {
                    RoleType.TAM: 1,
                    RoleType.VCIO: 2,
                    RoleType.MANAGER: 3,
                    RoleType.ADMIN: 4
                }
                if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
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

    return make_replit_blueprint(), require_login, require_role
from app import app  # noqa: F401

# Import authentication system first
import auth  # noqa: F401

# Import all routes and blueprints
import routes  # noqa: F401
from manager_routes import manager_bp
from connectwise_routes import connectwise_bp

# Register blueprints
app.register_blueprint(manager_bp)
app.register_blueprint(connectwise_bp)

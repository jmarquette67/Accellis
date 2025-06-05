from app import app  # noqa: F401

# Import all routes and blueprints
import routes  # noqa: F401
from manager_routes import manager_bp

# Register manager blueprint
app.register_blueprint(manager_bp)

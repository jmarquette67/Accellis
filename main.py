from app import app  # noqa: F401

# Import and register manager blueprint
from manager_routes import manager_bp
app.register_blueprint(manager_bp)

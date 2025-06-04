from app import app  # noqa: F401

# Add health check endpoint before other imports
@app.route('/health')
def health_check():
    """Simple health check endpoint for deployment"""
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}, 200

@app.route('/healthz')
def kubernetes_health():
    """Kubernetes-style health check"""
    return 'OK', 200

# Import datetime for health check
from datetime import datetime

# Import all routes and blueprints with error handling
try:
    import routes  # noqa: F401
    from manager_routes import manager_bp
    
    # Register manager blueprint
    app.register_blueprint(manager_bp)
except Exception as e:
    app.logger.error(f"Error importing routes: {e}")
    # Add basic fallback route
    @app.route('/')
    def fallback_home():
        return {'error': 'Application starting', 'status': 'initializing'}, 503

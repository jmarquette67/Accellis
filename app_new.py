from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlmodel import SQLModel, create_engine, Session
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Database configuration for SQLModel
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)

# Import models to ensure they're registered
from models_new import User, Client, UserClient, Metric, Score, Snapshot, AuditLog

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session

# Create tables (this will be handled by Alembic migrations in production)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
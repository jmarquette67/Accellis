from sqlmodel import create_engine, Session
from typing import Generator
import os

def create_db_and_tables():
    """Create database tables"""
    from models import Client, HealthCheck, Alert
    engine = get_engine()
    # This would be handled by Alembic in production
    # For now, we'll use Flask-SQLAlchemy's create_all()
    pass

def get_engine():
    """Get SQLModel database engine"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    return create_engine(database_url, echo=False)

def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    engine = get_engine()
    with Session(engine) as session:
        yield session
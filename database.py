from sqlmodel import create_engine, Session
from typing import Generator
import os

def get_engine():
    """Get SQLModel database engine"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    return create_engine(database_url, echo=False)

# Export engine for direct use
engine = get_engine()

def create_db_and_tables():
    """Create database tables"""
    from models_new import User, Client, Metric, Score, Snapshot, AuditLog
    # This would be handled by Alembic in production
    # For now, we'll use SQLModel's create_all()
    pass

def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    engine = get_engine()
    with Session(engine) as session:
        yield session
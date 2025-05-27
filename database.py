import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./health_check.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    with Session(engine) as session:
        yield session
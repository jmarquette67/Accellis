from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class RoleType(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    VCIO = "VCIO"
    TAM = "TAM"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    role: RoleType
    
    # Relationships
    clients: List["UserClient"] = Relationship(back_populates="user")

class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    industry: Optional[str] = None
    mrr: Optional[int] = None
    renewal_date: Optional[date] = None
    
    # Relationships
    users: List["UserClient"] = Relationship(back_populates="client")
    scores: List["Score"] = Relationship(back_populates="client")

class UserClient(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    client_id: int = Field(foreign_key="client.id", primary_key=True)
    user: User = Relationship(back_populates="clients")
    client: Client = Relationship(back_populates="users")

class Metric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: Optional[str] = None
    weight: int  # 1-100
    high_threshold: int  # ≥ marks "high"
    low_threshold: int   # ≤ marks "low"
    scores: List["Score"] = Relationship(back_populates="metric")

class Score(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    metric_id: int = Field(foreign_key="metric.id")
    value: int  # 0-100, rounded on save
    taken_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    locked: bool = True
    client: Client = Relationship(back_populates="scores")
    metric: Metric = Relationship(back_populates="scores")

class Snapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    month: date = Field(index=True)
    client_id: int = Field(foreign_key="client.id")
    overall_score: int

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    action: str
    target_table: str
    target_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
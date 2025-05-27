from datetime import datetime, timedelta
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel

class ClientBase(SQLModel):
    name: str = Field(max_length=100)
    hostname: str = Field(max_length=100, unique=True)
    ip_address: str = Field(max_length=45)
    description: Optional[str] = None
    is_active: bool = Field(default=True)

class Client(ClientBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checkin: Optional[datetime] = None
    
    # Relationships
    health_checks: List["HealthCheck"] = Relationship(back_populates="client")
    alerts: List["Alert"] = Relationship(back_populates="client")
    
    @property
    def status(self) -> str:
        """Determine client status based on last check-in and latest health metrics"""
        if not self.last_checkin:
            return 'unknown'
        
        # If no check-in in last 5 minutes, consider offline
        if datetime.utcnow() - self.last_checkin > timedelta(minutes=5):
            return 'offline'
        
        # Get latest health check
        if not self.health_checks:
            return 'unknown'
        
        latest_check = max(self.health_checks, key=lambda x: x.timestamp)
        
        # Check if any critical metrics are unhealthy
        if (latest_check.cpu_usage > 90 or 
            latest_check.memory_usage > 95 or 
            latest_check.disk_usage > 95):
            return 'critical'
        
        # Check if any metrics are warning level
        if (latest_check.cpu_usage > 75 or 
            latest_check.memory_usage > 85 or 
            latest_check.disk_usage > 85):
            return 'warning'
        
        return 'healthy'
    
    @property
    def status_color(self) -> str:
        """Get Bootstrap color class for status"""
        status_colors = {
            'healthy': 'success',
            'warning': 'warning', 
            'critical': 'danger',
            'offline': 'secondary',
            'unknown': 'secondary'
        }
        return status_colors.get(self.status, 'secondary')

class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    created_at: datetime
    last_checkin: Optional[datetime]
    status: str
    status_color: str

class HealthCheckBase(SQLModel):
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    disk_usage: float = Field(ge=0, le=100)
    uptime: int = Field(ge=0)
    load_average: Optional[float] = None
    network_rx: Optional[int] = None
    network_tx: Optional[int] = None
    notes: Optional[str] = None

class HealthCheck(HealthCheckBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="healthy", max_length=20)
    
    # Relationships
    client: Optional[Client] = Relationship(back_populates="health_checks")

class HealthCheckCreate(HealthCheckBase):
    pass

class HealthCheckRead(HealthCheckBase):
    id: int
    client_id: int
    timestamp: datetime
    status: str

class AlertBase(SQLModel):
    alert_type: str = Field(max_length=50)  # 'cpu', 'memory', 'disk', 'offline'
    severity: str = Field(max_length=20)    # 'warning', 'critical'
    message: str
    is_active: bool = Field(default=True)

class Alert(AlertBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    # Relationships
    client: Optional[Client] = Relationship(back_populates="alerts")

class AlertCreate(AlertBase):
    client_id: int

class AlertRead(AlertBase):
    id: int
    client_id: int
    created_at: datetime
    resolved_at: Optional[datetime]
    client_name: Optional[str] = None

# Request/Response models
class ClientCheckInRequest(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: int
    load_average: Optional[float] = None
    network_rx: Optional[int] = None
    network_tx: Optional[int] = None
    notes: Optional[str] = None

class ClientCheckInResponse(BaseModel):
    status: str
    message: str
    client_status: str

class DashboardStats(BaseModel):
    total: int
    healthy: int
    warning: int
    critical: int
    offline: int
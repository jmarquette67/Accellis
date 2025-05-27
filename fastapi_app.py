import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Field, Relationship, Session, select, desc, create_engine
from pydantic import BaseModel

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./health_check.db")
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Models
class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    hostname: str = Field(max_length=100, unique=True)
    ip_address: str = Field(max_length=45)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checkin: Optional[datetime] = None
    
    @property
    def status(self) -> str:
        if not self.last_checkin:
            return 'unknown'
        if datetime.utcnow() - self.last_checkin > timedelta(minutes=5):
            return 'offline'
        return 'healthy'
    
    @property
    def status_color(self) -> str:
        status_colors = {
            'healthy': 'success',
            'warning': 'warning', 
            'critical': 'danger',
            'offline': 'secondary',
            'unknown': 'secondary'
        }
        return status_colors.get(self.status, 'secondary')

class HealthCheck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    disk_usage: float = Field(ge=0, le=100)
    uptime: int = Field(ge=0)
    load_average: Optional[float] = None
    network_rx: Optional[int] = None
    network_tx: Optional[int] = None
    notes: Optional[str] = None
    status: str = Field(default="healthy", max_length=20)

class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    alert_type: str = Field(max_length=50)
    severity: str = Field(max_length=20)
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    is_active: bool = Field(default=True)

# Request models
class ClientCheckInRequest(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: int
    load_average: Optional[float] = None
    network_rx: Optional[int] = None
    network_tx: Optional[int] = None
    notes: Optional[str] = None

class DashboardStats(BaseModel):
    total: int
    healthy: int
    warning: int
    critical: int
    offline: int

# FastAPI app
app = FastAPI(title="Accellis Health Check System", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    statement = select(Client).where(Client.is_active == True)
    clients = session.exec(statement).all()
    
    total_clients = len(clients)
    healthy_clients = len([c for c in clients if c.status == 'healthy'])
    warning_clients = len([c for c in clients if c.status == 'warning'])
    critical_clients = len([c for c in clients if c.status == 'critical'])
    offline_clients = len([c for c in clients if c.status == 'offline'])
    
    alert_statement = select(Alert).where(Alert.is_active == True).order_by(desc(Alert.created_at)).limit(10)
    recent_alerts = session.exec(alert_statement).all()
    
    stats = DashboardStats(
        total=total_clients,
        healthy=healthy_clients,
        warning=warning_clients,
        critical=critical_clients,
        offline=offline_clients
    )
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "clients": clients,
        "stats": stats,
        "recent_alerts": recent_alerts
    })

@app.get("/register", response_class=HTMLResponse)
def register_client_form(request: Request):
    return templates.TemplateResponse("register_client.html", {"request": request})

@app.post("/register")
def register_client(
    request: Request,
    name: str = Form(...),
    hostname: str = Form(...),
    ip_address: str = Form(...),
    description: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    statement = select(Client).where(Client.hostname == hostname)
    existing_client = session.exec(statement).first()
    
    if existing_client:
        return templates.TemplateResponse("register_client.html", {
            "request": request,
            "error": "A client with this hostname already exists.",
            "name": name,
            "hostname": hostname,
            "ip_address": ip_address,
            "description": description
        })
    
    client = Client(
        name=name,
        hostname=hostname,
        ip_address=ip_address,
        description=description
    )
    
    session.add(client)
    session.commit()
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/client/{client_id}", response_class=HTMLResponse)
def client_details(request: Request, client_id: int, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    since = datetime.utcnow() - timedelta(hours=24)
    health_statement = select(HealthCheck).where(
        HealthCheck.client_id == client_id,
        HealthCheck.timestamp >= since
    ).order_by(desc(HealthCheck.timestamp)).limit(100)
    recent_checks = session.exec(health_statement).all()
    
    alert_statement = select(Alert).where(Alert.client_id == client_id).order_by(desc(Alert.created_at)).limit(20)
    client_alerts = session.exec(alert_statement).all()
    
    return templates.TemplateResponse("client_details.html", {
        "request": request,
        "client": client,
        "recent_checks": recent_checks,
        "alerts": client_alerts
    })

@app.post("/api/client/{hostname}/checkin")
def api_client_checkin(
    hostname: str,
    data: ClientCheckInRequest,
    session: Session = Depends(get_session)
):
    statement = select(Client).where(Client.hostname == hostname)
    client = session.exec(statement).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    health_check = HealthCheck(
        client_id=client.id if client.id else 0,
        cpu_usage=data.cpu_usage,
        memory_usage=data.memory_usage,
        disk_usage=data.disk_usage,
        uptime=data.uptime,
        load_average=data.load_average,
        network_rx=data.network_rx,
        network_tx=data.network_tx,
        notes=data.notes
    )
    
    client.last_checkin = datetime.utcnow()
    
    session.add(health_check)
    session.add(client)
    session.commit()
    
    return {
        "status": "success",
        "message": "Health check recorded",
        "client_status": client.status
    }

@app.get("/api/clients")
def api_get_clients(session: Session = Depends(get_session)):
    statement = select(Client).where(Client.is_active == True)
    clients = session.exec(statement).all()
    
    return [
        {
            "id": client.id,
            "name": client.name,
            "hostname": client.hostname,
            "ip_address": client.ip_address,
            "last_checkin": client.last_checkin.isoformat() if client.last_checkin else None,
            "status": client.status,
            "status_color": client.status_color
        }
        for client in clients
    ]

@app.get("/api/alerts")
def api_get_alerts(session: Session = Depends(get_session)):
    statement = select(Alert).where(Alert.is_active == True).order_by(desc(Alert.created_at))
    alerts = session.exec(statement).all()
    
    result = []
    for alert in alerts:
        client = session.get(Client, alert.client_id)
        result.append({
            "id": alert.id,
            "client_id": alert.client_id,
            "client_name": client.name if client else "Unknown",
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "created_at": alert.created_at.isoformat(),
            "is_active": alert.is_active
        })
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
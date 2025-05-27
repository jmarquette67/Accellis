import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, desc, SQLModel, Field, Relationship
from pydantic import BaseModel

from database import get_session, create_db_and_tables

# Create FastAPI app
app = FastAPI(title="Accellis Health Check System", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Create tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Helper functions
def check_and_create_alerts(session: Session, client: Client, health_check: HealthCheck):
    """Check health metrics and create alerts if needed"""
    alerts_to_create = []
    
    # CPU usage alerts
    if health_check.cpu_usage > 90:
        alerts_to_create.append({
            'type': 'cpu',
            'severity': 'critical',
            'message': f'CPU usage critical: {health_check.cpu_usage:.1f}%'
        })
    elif health_check.cpu_usage > 75:
        alerts_to_create.append({
            'type': 'cpu',
            'severity': 'warning',
            'message': f'CPU usage high: {health_check.cpu_usage:.1f}%'
        })
    
    # Memory usage alerts
    if health_check.memory_usage > 95:
        alerts_to_create.append({
            'type': 'memory',
            'severity': 'critical',
            'message': f'Memory usage critical: {health_check.memory_usage:.1f}%'
        })
    elif health_check.memory_usage > 85:
        alerts_to_create.append({
            'type': 'memory',
            'severity': 'warning',
            'message': f'Memory usage high: {health_check.memory_usage:.1f}%'
        })
    
    # Disk usage alerts
    if health_check.disk_usage > 95:
        alerts_to_create.append({
            'type': 'disk',
            'severity': 'critical',
            'message': f'Disk usage critical: {health_check.disk_usage:.1f}%'
        })
    elif health_check.disk_usage > 85:
        alerts_to_create.append({
            'type': 'disk',
            'severity': 'warning',
            'message': f'Disk usage high: {health_check.disk_usage:.1f}%'
        })
    
    # Create alerts
    for alert_data in alerts_to_create:
        # Check if similar alert already exists and is active
        statement = select(Alert).where(
            Alert.client_id == client.id,
            Alert.alert_type == alert_data['type'],
            Alert.severity == alert_data['severity'],
            Alert.is_active == True
        )
        existing_alert = session.exec(statement).first()
        
        if not existing_alert:
            alert = Alert(
                client_id=client.id,
                alert_type=alert_data['type'],
                severity=alert_data['severity'],
                message=alert_data['message']
            )
            session.add(alert)
    
    session.commit()

# Routes
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    """Main dashboard view"""
    # Get all active clients
    statement = select(Client).where(Client.is_active == True)
    clients = session.exec(statement).all()
    
    # Calculate stats
    total_clients = len(clients)
    healthy_clients = len([c for c in clients if c.status == 'healthy'])
    warning_clients = len([c for c in clients if c.status == 'warning'])
    critical_clients = len([c for c in clients if c.status == 'critical'])
    offline_clients = len([c for c in clients if c.status == 'offline'])
    
    # Get recent alerts
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
    """Show client registration form"""
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
    """Register a new client"""
    # Check if hostname already exists
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
    session.refresh(client)
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/client/{client_id}", response_class=HTMLResponse)
def client_details(request: Request, client_id: int, session: Session = Depends(get_session)):
    """View detailed information about a specific client"""
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get recent health checks (last 24 hours)
    since = datetime.utcnow() - timedelta(hours=24)
    health_statement = select(HealthCheck).where(
        HealthCheck.client_id == client_id,
        HealthCheck.timestamp >= since
    ).order_by(desc(HealthCheck.timestamp)).limit(100)
    recent_checks = session.exec(health_statement).all()
    
    # Get client alerts
    alert_statement = select(Alert).where(Alert.client_id == client_id).order_by(desc(Alert.created_at)).limit(20)
    client_alerts = session.exec(alert_statement).all()
    
    return templates.TemplateResponse("client_details.html", {
        "request": request,
        "client": client,
        "recent_checks": recent_checks,
        "alerts": client_alerts
    })

# API Endpoints
@app.get("/api/clients", response_model=List[ClientRead])
def api_get_clients(session: Session = Depends(get_session)):
    """Get all clients with their current status"""
    statement = select(Client).where(Client.is_active == True)
    clients = session.exec(statement).all()
    
    client_reads = []
    for client in clients:
        client_reads.append(ClientRead(
            id=client.id or 0,
            name=client.name,
            hostname=client.hostname,
            ip_address=client.ip_address,
            description=client.description,
            is_active=client.is_active,
            created_at=client.created_at,
            last_checkin=client.last_checkin,
            status=client.status,
            status_color=client.status_color
        ))
    
    return client_reads

@app.post("/api/client/{hostname}/checkin", response_model=ClientCheckInResponse)
def api_client_checkin(
    hostname: str,
    data: ClientCheckInRequest,
    session: Session = Depends(get_session)
):
    """API endpoint for clients to check in with health data"""
    statement = select(Client).where(Client.hostname == hostname)
    client = session.exec(statement).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Create health check record
    health_check = HealthCheck(
        client_id=client.id or 0,
        cpu_usage=data.cpu_usage,
        memory_usage=data.memory_usage,
        disk_usage=data.disk_usage,
        uptime=data.uptime,
        load_average=data.load_average,
        network_rx=data.network_rx,
        network_tx=data.network_tx,
        notes=data.notes
    )
    
    # Update client last check-in
    client.last_checkin = datetime.utcnow()
    
    session.add(health_check)
    session.add(client)
    session.commit()
    session.refresh(client)
    session.refresh(health_check)
    
    # Check for alerts
    check_and_create_alerts(session, client, health_check)
    
    return ClientCheckInResponse(
        status="success",
        message="Health check recorded",
        client_status=client.status
    )

@app.get("/api/client/{client_id}/metrics", response_model=List[HealthCheckRead])
def api_client_metrics(client_id: int, session: Session = Depends(get_session)):
    """Get metrics for a specific client"""
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get metrics for the last 24 hours
    since = datetime.utcnow() - timedelta(hours=24)
    statement = select(HealthCheck).where(
        HealthCheck.client_id == client_id,
        HealthCheck.timestamp >= since
    ).order_by(HealthCheck.timestamp)
    metrics = session.exec(statement).all()
    
    return [HealthCheckRead(
        id=metric.id,
        client_id=metric.client_id,
        timestamp=metric.timestamp,
        cpu_usage=metric.cpu_usage,
        memory_usage=metric.memory_usage,
        disk_usage=metric.disk_usage,
        uptime=metric.uptime,
        load_average=metric.load_average,
        network_rx=metric.network_rx,
        network_tx=metric.network_tx,
        notes=metric.notes,
        status=metric.status
    ) for metric in metrics]

@app.get("/api/alerts", response_model=List[AlertRead])
def api_get_alerts(session: Session = Depends(get_session)):
    """Get active alerts"""
    statement = select(Alert).where(Alert.is_active == True).order_by(desc(Alert.created_at))
    alerts = session.exec(statement).all()
    
    alert_reads = []
    for alert in alerts:
        alert_reads.append(AlertRead(
            id=alert.id,
            client_id=alert.client_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            message=alert.message,
            is_active=alert.is_active,
            created_at=alert.created_at,
            resolved_at=alert.resolved_at,
            client_name=alert.client.name if alert.client else "Unknown"
        ))
    
    return alert_reads

@app.post("/api/alert/{alert_id}/resolve")
def api_resolve_alert(alert_id: int, session: Session = Depends(get_session)):
    """Resolve an alert"""
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_active = False
    alert.resolved_at = datetime.utcnow()
    
    session.add(alert)
    session.commit()
    
    return {"status": "success", "message": "Alert resolved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
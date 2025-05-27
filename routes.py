from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, flash
from sqlalchemy import desc, func
from app import app, db
from models import Client, HealthCheck, Alert
from forms import ClientRegistrationForm, HealthCheckForm

@app.route('/')
def dashboard():
    """Main dashboard view"""
    # Get all active clients with their latest status
    clients = Client.query.filter_by(is_active=True).all()
    
    # Get system overview stats
    total_clients = len(clients)
    healthy_clients = len([c for c in clients if c.status == 'healthy'])
    warning_clients = len([c for c in clients if c.status == 'warning'])
    critical_clients = len([c for c in clients if c.status == 'critical'])
    offline_clients = len([c for c in clients if c.status == 'offline'])
    
    # Get recent alerts
    recent_alerts = Alert.query.filter_by(is_active=True).order_by(desc(Alert.created_at)).limit(10).all()
    
    stats = {
        'total': total_clients,
        'healthy': healthy_clients,
        'warning': warning_clients,
        'critical': critical_clients,
        'offline': offline_clients
    }
    
    return render_template('dashboard.html', 
                         clients=clients, 
                         stats=stats, 
                         recent_alerts=recent_alerts)

@app.route('/register', methods=['GET', 'POST'])
def register_client():
    """Register a new client"""
    form = ClientRegistrationForm()
    
    if form.validate_on_submit():
        # Check if hostname already exists
        existing_client = Client.query.filter_by(hostname=form.hostname.data).first()
        if existing_client:
            flash('A client with this hostname already exists.', 'error')
            return render_template('register_client.html', form=form)
        
        client = Client(
            name=form.name.data,
            hostname=form.hostname.data,
            ip_address=form.ip_address.data,
            description=form.description.data
        )
        
        try:
            db.session.add(client)
            db.session.commit()
            flash(f'Client "{client.name}" registered successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error registering client. Please try again.', 'error')
            app.logger.error(f'Error registering client: {e}')
    
    return render_template('register_client.html', form=form)

@app.route('/client/<int:client_id>')
def client_details(client_id):
    """View detailed information about a specific client"""
    client = Client.query.get_or_404(client_id)
    
    # Get recent health checks (last 24 hours)
    since = datetime.utcnow() - timedelta(hours=24)
    recent_checks = HealthCheck.query.filter(
        HealthCheck.client_id == client_id,
        HealthCheck.timestamp >= since
    ).order_by(desc(HealthCheck.timestamp)).limit(100).all()
    
    # Get client alerts
    client_alerts = Alert.query.filter_by(client_id=client_id).order_by(desc(Alert.created_at)).limit(20).all()
    
    return render_template('client_details.html', 
                         client=client, 
                         recent_checks=recent_checks,
                         alerts=client_alerts)

# API Endpoints

@app.route('/api/clients', methods=['GET'])
def api_get_clients():
    """Get all clients with their current status"""
    clients = Client.query.filter_by(is_active=True).all()
    return jsonify([client.to_dict() for client in clients])

@app.route('/api/client/<string:hostname>/checkin', methods=['POST'])
def api_client_checkin(hostname):
    """API endpoint for clients to check in with health data"""
    client = Client.query.filter_by(hostname=hostname).first()
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['cpu_usage', 'memory_usage', 'disk_usage', 'uptime']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Create health check record
        health_check = HealthCheck(
            client_id=client.id,
            cpu_usage=float(data['cpu_usage']),
            memory_usage=float(data['memory_usage']),
            disk_usage=float(data['disk_usage']),
            uptime=int(data['uptime']),
            load_average=float(data.get('load_average', 0)),
            network_rx=int(data.get('network_rx', 0)),
            network_tx=int(data.get('network_tx', 0)),
            notes=data.get('notes', '')
        )
        
        # Update client last check-in
        client.last_checkin = datetime.utcnow()
        
        db.session.add(health_check)
        db.session.commit()
        
        # Check for alerts
        check_and_create_alerts(client, health_check)
        
        return jsonify({
            'status': 'success',
            'message': 'Health check recorded',
            'client_status': client.status
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error processing check-in for {hostname}: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/client/<int:client_id>/metrics')
def api_client_metrics(client_id):
    """Get metrics for a specific client"""
    client = Client.query.get_or_404(client_id)
    
    # Get metrics for the last 24 hours
    since = datetime.utcnow() - timedelta(hours=24)
    metrics = HealthCheck.query.filter(
        HealthCheck.client_id == client_id,
        HealthCheck.timestamp >= since
    ).order_by(HealthCheck.timestamp).all()
    
    return jsonify([metric.to_dict() for metric in metrics])

@app.route('/api/alerts')
def api_get_alerts():
    """Get active alerts"""
    alerts = Alert.query.filter_by(is_active=True).order_by(desc(Alert.created_at)).all()
    return jsonify([alert.to_dict() for alert in alerts])

@app.route('/api/alert/<int:alert_id>/resolve', methods=['POST'])
def api_resolve_alert(alert_id):
    """Resolve an alert"""
    alert = Alert.query.get_or_404(alert_id)
    alert.is_active = False
    alert.resolved_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Alert resolved'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to resolve alert'}), 500

def check_and_create_alerts(client, health_check):
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
        existing_alert = Alert.query.filter_by(
            client_id=client.id,
            alert_type=alert_data['type'],
            severity=alert_data['severity'],
            is_active=True
        ).first()
        
        if not existing_alert:
            alert = Alert(
                client_id=client.id,
                alert_type=alert_data['type'],
                severity=alert_data['severity'],
                message=alert_data['message']
            )
            db.session.add(alert)
    
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error(f'Error creating alerts: {e}')
        db.session.rollback()

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html', error_message='Internal server error'), 500

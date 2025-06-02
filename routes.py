from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, flash
from sqlalchemy import desc, func
from flask_login import current_user
from app import app, db
from models import Client, HealthCheck, Alert, User, UserRole
from forms import ClientRegistrationForm, HealthCheckForm
from replit_auth import require_login, require_role, make_replit_blueprint

# Register Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Register Scores blueprint - we'll add this when ready
# from app.routers.scores import bp as scores_bp
# app.register_blueprint(scores_bp)

# Make session permanent
@app.before_request
def make_session_permanent():
    from flask import session
    session.permanent = True

@app.route('/')
def dashboard():
    """Main dashboard view"""
    # Check if user is authenticated (with fallback for missing login manager)
    try:
        user_authenticated = current_user.is_authenticated
        if user_authenticated:
            user = current_user
            # Use the full dashboard template now that authentication is working
            return render_template('dashboard.html', user=user)
    except Exception as e:
        user_authenticated = False
        app.logger.error(f"Authentication check failed: {e}")
    
    if not user_authenticated:
        return render_template('landing.html')
    
    # Fallback for unauthenticated users
    return render_template('landing.html')
    
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
@require_role(UserRole.MANAGER)
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

# Score management routes
@app.route('/score_entry', methods=['GET', 'POST'])
def score_entry():
    """Comprehensive score entry form for all metrics"""
    # Simple authentication check
    if not current_user.is_authenticated:
        return redirect(url_for('replit_auth.login'))
    
    from models import Metric, Score
    
    if request.method == 'POST':
        # Handle form submission for all metrics
        client_id = request.form.get('client_id')
        score_month = request.form.get('score_month')
        notes = request.form.get('notes', '')
        
        if client_id and score_month:
            try:
                from datetime import datetime, timedelta
                scores_created = 0
                metrics = Metric.query.all()
                
                # Parse the selected month and create scoresheet timestamp
                score_date = datetime.strptime(score_month, '%Y-%m')
                scoresheet_datetime = datetime.now().replace(
                    year=score_date.year,
                    month=score_date.month,
                    day=15,
                    microsecond=0
                )
                
                # First pass: collect all metric scores for this scoresheet
                scoresheet_data = []
                for metric in metrics:
                    metric_field = f'metric_{metric.id}'
                    score_value = request.form.get(metric_field)
                    
                    if score_value and score_value.strip():
                        # Calculate final score based on metric type
                        final_score = 0
                        if "Help Desk" in metric.name:
                            # Use Help Desk scoring logic with thresholds
                            tickets_per_user = float(score_value)
                            low_threshold = metric.low_threshold
                            high_threshold = metric.high_threshold
                            
                            if tickets_per_user >= low_threshold and tickets_per_user <= high_threshold:
                                final_score = 1  # Ideal usage
                            else:
                                final_score = 0  # High or low usage
                            
                            score_notes = f"Tickets/user/month: {score_value} | {notes}" if notes else f"Tickets/user/month: {score_value}"
                        else:
                            # Regular scoring for other metrics
                            final_score = int(float(score_value))
                            score_notes = f"{notes} (Scored for {score_month})" if notes else f"Scored for {score_month}"
                        
                        scoresheet_data.append({
                            'metric_id': metric.id,
                            'value': final_score,
                            'notes': score_notes
                        })
                
                # If we have any scores, delete existing scores for this month and create complete locked scoresheet
                if scoresheet_data:
                    # Delete existing scores for this client/month combination
                    existing_scores = Score.query.filter(
                        Score.client_id == int(client_id),
                        Score.taken_at >= score_date.replace(day=1),
                        Score.taken_at < (score_date.replace(day=28) + timedelta(days=4))
                    ).all()
                    
                    for existing_score in existing_scores:
                        db.session.delete(existing_score)
                    
                    # Create all scores for this scoresheet with same timestamp and lock them
                    for score_data in scoresheet_data:
                        score = Score(
                            client_id=int(client_id),
                            metric_id=score_data['metric_id'],
                            value=score_data['value'],
                            taken_at=scoresheet_datetime,
                            notes=score_data['notes'],
                            locked=True  # Lock all scores in the complete scoresheet
                        )
                        db.session.add(score)
                        scores_created += 1
                
                db.session.commit()
                flash(f'Successfully saved {scores_created} metric scores!', 'success')
                return redirect(url_for('score_entry'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error saving scores. Please try again.', 'error')
                print(f"Error saving scores: {e}")
    
    from datetime import datetime
    
    clients = Client.query.order_by(Client.name).all()
    metrics = Metric.query.order_by(Metric.id).all()
    current_month = datetime.now().strftime('%Y-%m')
    
    return render_template("comprehensive_score_entry.html", 
                         clients=clients, 
                         metrics=metrics, 
                         current_month=current_month,
                         user=current_user)

@app.route('/scores/')
def score_history():
    """View score history"""
    # Simple authentication check
    if not current_user.is_authenticated:
        return redirect(url_for('replit_auth.login'))
        
    from models import Score
    recent_scores = Score.query.order_by(Score.taken_at.desc()).limit(20).all()
    return render_template("score_history.html", scores=recent_scores, user=current_user)

@app.route('/clients')
def client_list():
    """Display list of clients"""
    # Simple authentication check
    if not current_user.is_authenticated:
        return redirect(url_for('replit_auth.login'))
        
    clients = Client.query.order_by(Client.name).all()
    return render_template('simple_client_list.html', clients=clients, user=current_user)

@app.route('/simple-clients')
def simple_client_list():
    """Simple client list for testing"""
    if not current_user.is_authenticated:
        return redirect(url_for('replit_auth.login'))
    
    clients = Client.query.order_by(Client.name).all()
    client_html = "<h2>Your Clients</h2><ul>"
    for client in clients:
        client_html += f"<li>{client.name} - {client.description}</li>"
    client_html += "</ul>"
    return f"<html><body>{client_html}<p>Total clients: {len(clients)}</p></body></html>"

# Admin routes
@app.route('/admin')
def admin_dashboard():
    """Main admin console dashboard"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    from models import Metric, Score
    
    # Get system statistics
    stats = {
        'total_users': User.query.count(),
        'total_clients': Client.query.count(),
        'total_metrics': Metric.query.count(),
        'total_scores': Score.query.count()
    }
    
    # Get recent activity (placeholder for now)
    recent_activity = [
        {
            'timestamp': datetime.utcnow(),
            'action': 'System Initialized',
            'type_color': 'success',
            'user_email': current_user.email,
            'details': 'Admin console accessed'
        }
    ]
    
    return render_template("admin_dashboard.html", stats=stats, recent_activity=recent_activity, user=current_user)

@app.route('/admin/metrics')
def admin_metrics():
    """Admin metrics management interface"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    from models import Metric
    metrics = Metric.query.order_by(Metric.id).all()
    return render_template("admin_metrics.html", metrics=metrics, user=current_user)

@app.route('/admin/metrics/<int:metric_id>/update', methods=['POST'])
def admin_update_metric(metric_id):
    """Update a metric via admin interface"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    from models import Metric
    metric = Metric.query.get_or_404(metric_id)
    
    try:
        metric.name = request.form.get('name')
        metric.weight = int(request.form.get('weight'))
        metric.max_score = int(request.form.get('max_score'))
        metric.scoring_criteria = request.form.get('scoring_criteria')
        metric.description = request.form.get('description')
        
        # Update thresholds for Help Desk Usage metric
        if "Help Desk" in metric.name:
            metric.too_low_threshold = float(request.form.get('too_low_threshold', 0.25))
            metric.too_low_score = int(request.form.get('too_low_score', 0))
            metric.ideal_min_threshold = float(request.form.get('ideal_min_threshold', 0.25))
            metric.ideal_max_threshold = float(request.form.get('ideal_max_threshold', 1.0))
            metric.ideal_score = int(request.form.get('ideal_score', 1))
            metric.too_high_threshold = float(request.form.get('too_high_threshold', 1.0))
            metric.too_high_score = int(request.form.get('too_high_score', 0))
        
        db.session.commit()
        flash(f'Successfully updated metric: {metric.name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating metric. Please try again.', 'error')
    
    return redirect(url_for('admin_metrics'))

@app.route('/admin/users')
def admin_users():
    """Admin user management interface"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.email).all()
    return render_template("admin_users.html", users=users, user=current_user)

@app.route('/admin/users/<user_id>/update', methods=['POST'])
def admin_update_user(user_id):
    """Update user role via admin interface"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    user_to_update = User.query.get_or_404(user_id)
    
    try:
        new_role = request.form.get('role')
        user_to_update.role = UserRole(new_role)
        db.session.commit()
        flash(f'Successfully updated {user_to_update.email} to {new_role} role', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating user role. Please try again.', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/clients')
def admin_clients():
    """Admin client management interface"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    clients = Client.query.order_by(Client.name).all()
    return render_template("admin_clients.html", clients=clients, user=current_user)

@app.route('/admin/data')
def admin_data():
    """Admin data management interface"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template("admin_data.html", user=current_user)

@app.route('/admin/backup')
def admin_backup():
    """System backup functionality"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    flash('Backup functionality will be implemented based on your requirements', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/import')
def admin_import():
    """Data import functionality"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template("admin_import.html", user=current_user)

@app.route('/admin/reports')
def admin_reports():
    """Admin reports interface"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    flash('Admin reports functionality will be implemented based on your requirements', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings')
def admin_settings():
    """Admin system settings"""
    if not current_user.is_authenticated or not current_user.has_role(UserRole.ADMIN):
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    flash('System settings functionality will be implemented based on your requirements', 'info')
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html', error_message='Internal server error'), 500

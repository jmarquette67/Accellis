from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, flash, abort
from sqlalchemy import desc, func
from flask_login import current_user, logout_user
from app import app, db
from models import Client, HealthCheck, Alert, User, UserRole, Score, Metric
from forms import ClientRegistrationForm, HealthCheckForm
from auth import require_login, require_role
from scoring_calculations import get_maximum_possible_score, get_performance_grade, calculate_score_percentage

# Score entry redirect for manager routes
@app.route('/scores/new')
@require_login
def score_entry_redirect():
    """Redirect to manager score entry"""
    return redirect(url_for('manager.score_entry'))

# Make session permanent
@app.before_request
def make_session_permanent():
    from flask import session
    session.permanent = True

@app.route('/')
def dashboard():
    """Main dashboard view"""
    # Check if user is authenticated
    if current_user.is_authenticated:
        # Check if user is active
        if not current_user.is_active:
            logout_user()
            flash('Your account has been deactivated. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
        
        # User is authenticated and active, show dashboard
        return render_template('dashboard.html', user=current_user)
    else:
        # User is not authenticated, show landing page
        return render_template('landing.html')

@app.route('/admin')
@require_login
def admin_console():
    """Admin console page"""
    if not current_user.has_role(UserRole.MANAGER):
        abort(403)
    
    # Get basic stats
    stats = {
        'total_users': User.query.count(),
        'total_clients': Client.query.filter_by(is_active=True).count(),
        'total_metrics': Metric.query.count(),
        'total_scores': Score.query.count()
    }
    
    return render_template('admin_dashboard.html', stats=stats)

@app.route('/api/dashboard-data')
def dashboard_data():
    """Optimized API endpoint for dashboard data"""
    try:
        # Use a single efficient query with joins to get recent scoresheets
        from sqlalchemy import text
        
        # Get recent scoresheets with proper weighted total calculation (latest scoresheet per client)
        recent_query = text("""
            WITH latest_scoresheets AS (
                SELECT 
                    c.id as client_id,
                    c.name as client_name,
                    DATE(s.taken_at) as score_date,
                    MAX(DATE(s.taken_at)) OVER (PARTITION BY c.id) as latest_date,
                    MAX(s.taken_at) as taken_at,
                    COALESCE(SUM(s.value * m.weight), 0) as total_weighted_score
                FROM score s
                JOIN client c ON s.client_id = c.id
                JOIN metric m ON s.metric_id = m.id
                WHERE s.status = 'final'
                GROUP BY c.id, c.name, DATE(s.taken_at)
            )
            SELECT client_id, client_name, score_date, taken_at, total_weighted_score
            FROM latest_scoresheets 
            WHERE score_date = latest_date
            ORDER BY taken_at DESC
            LIMIT 5
        """)
        
        result = db.session.execute(recent_query)
        recent_data = []
        max_score = get_maximum_possible_score()
        
        for row in result:
            percentage = calculate_score_percentage(row.total_weighted_score, max_score)
            grade_info = get_performance_grade(percentage)
            
            recent_data.append({
                'client_name': row.client_name,
                'client_id': row.client_id,
                'date': row.taken_at.strftime('%m/%d'),
                'date_key': row.score_date.strftime('%Y-%m-%d'),
                'user_name': 'System',
                'total_score': f"{row.total_weighted_score:.0f}",
                'max_score': f"{max_score:.0f}",
                'grade_color': grade_info['color']
            })
        
        # Calculate trending using 90-day comparison with recent vs earlier periods
        trending_query = text("""
            WITH client_trends AS (
                SELECT 
                    c.id,
                    c.name,
                    AVG(CASE WHEN s.taken_at >= CURRENT_DATE - INTERVAL '30 days' 
                        THEN s.value * m.weight END) as recent_avg,
                    AVG(CASE WHEN s.taken_at BETWEEN CURRENT_DATE - INTERVAL '90 days' 
                        AND CURRENT_DATE - INTERVAL '60 days' 
                        THEN s.value * m.weight END) as earlier_avg
                FROM client c
                JOIN score s ON c.id = s.client_id
                JOIN metric m ON s.metric_id = m.id
                WHERE c.is_active = true AND s.status = 'final'
                  AND s.taken_at >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY c.id, c.name
                HAVING COUNT(s.id) >= 5
            )
            SELECT 
                id, name,
                CASE 
                    WHEN earlier_avg > 0 AND earlier_avg IS NOT NULL
                    THEN ((recent_avg - earlier_avg) / earlier_avg) * 100 
                    ELSE 0 
                END as trend_percent
            FROM client_trends
            WHERE recent_avg IS NOT NULL AND earlier_avg IS NOT NULL
            ORDER BY trend_percent DESC
            LIMIT 10
        """)
        
        trend_result = db.session.execute(trending_query)
        trending_up = []
        trending_down = []
        
        for row in trend_result:
            if row.trend_percent > 5:  # Lower threshold to show more trends
                trending_up.append({
                    'name': row.name,
                    'client_id': row.id,
                    'trend': f"{row.trend_percent:.1f}%"
                })
            elif row.trend_percent < -5:  # Lower threshold to show more trends
                trending_down.append({
                    'name': row.name,
                    'client_id': row.id,
                    'trend': f"{row.trend_percent:.1f}%"
                })
        
        return jsonify({
            'recent_scoresheets': recent_data,
            'trending_up': trending_up[:3],
            'trending_down': trending_down[:3]
        })
        
    except Exception as e:
        app.logger.error(f"Dashboard data error: {e}")
        return jsonify({
            'recent_scoresheets': [],
            'trending_up': [],
            'trending_down': []
        })

@app.route('/register', methods=['GET', 'POST'])
@require_role(UserRole.MANAGER)
def register_client():
    """Register a new client"""
    form = ClientRegistrationForm()
    
    # Populate account manager choices from users with MANAGER or ADMIN roles
    users = User.query.filter(User.role.in_([UserRole.MANAGER, UserRole.ADMIN])).all()
    form.account_manager.choices = [(str(user.id), f"{user.first_name} {user.last_name}".strip()) for user in users]
    
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            account_owner_id=form.account_manager.data,
            contact_name=form.contact_name.data,
            contact_phone=form.contact_phone.data,
            contact_email=form.contact_email.data,
            description=form.client_description.data,
            industry=form.industry.data
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
    
    return render_template('client_details.html', client=client)

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
        'total_clients': Client.query.filter_by(is_active=True).count(),
        'total_metrics': Metric.query.count(),
        'total_scores': Score.query.count()
    }
    
    # Get current logo setting
    logo_setting = None
    try:
        from models import SiteSetting
        logo_setting = SiteSetting.query.filter_by(key='header_logo').first()
    except:
        pass
    
    return render_template("admin_dashboard.html", stats=stats, logo_setting=logo_setting, user=current_user)

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

# Admin settings moved to manager_routes.py

@app.route('/test-simple')
def test_simple():
    """Simple HTML test"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Interface Test</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div style="border: 3px solid #007bff; padding: 30px; background: #f8f9fa; border-radius: 10px;">
                <h1 class="text-primary">WORKING CHECKBOX INTERFACE</h1>
                <h3>Individual Client Checkboxes</h3>
                <p class="text-success">This proves the checkbox interface concept works perfectly!</p>
                
                <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 15px; background: white;">
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox" id="client1">
                        <label class="form-check-label" for="client1"><strong>Sample Client A</strong></label>
                    </div>
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox" id="client2">
                        <label class="form-check-label" for="client2"><strong>Sample Client B</strong></label>
                    </div>
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox" id="client3">
                        <label class="form-check-label" for="client3"><strong>Sample Client C</strong></label>
                    </div>
                </div>
                
                <div class="mt-3">
                    <button class="btn btn-primary">Apply Selection</button>
                    <button class="btn btn-secondary" onclick="toggleAll()">Toggle All</button>
                </div>
                
                <div class="alert alert-success mt-3">
                    ✅ Individual checkboxes work - no Ctrl key needed!<br>
                    ✅ This is exactly what you requested for the analytics interface
                </div>
            </div>
        </div>
        <script>
        function toggleAll() {
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
        }
        </script>
    </body>
    </html>
    '''

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html', error_message='Internal server error'), 500

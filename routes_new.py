from datetime import datetime, timedelta, date
from flask import render_template, request, jsonify, redirect, url_for, flash
from sqlmodel import Session, select
from flask_login import current_user
from app_new import app, engine
from models_new import User, Client, UserClient, Metric, Score, Snapshot, AuditLog, RoleType
from replit_auth_new import init_auth

# Register Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    from flask import session
    session.permanent = True

def get_session():
    return Session(engine)

@app.route('/')
def dashboard():
    """Main dashboard view"""
    if not current_user.is_authenticated:
        return render_template('landing.html')
    
    with get_session() as session:
        # Get clients accessible to current user
        if current_user.role in [RoleType.ADMIN, RoleType.MANAGER]:
            # Admins and managers can see all clients
            clients = session.exec(select(Client)).all()
        else:
            # VCIO and TAM can only see their assigned clients
            user_clients = session.exec(
                select(UserClient).where(UserClient.user_id == int(current_user.id))
            ).all()
            client_ids = [uc.client_id for uc in user_clients]
            clients = session.exec(select(Client).where(Client.id.in_(client_ids))).all() if client_ids else []
        
        # Calculate statistics
        total_clients = len(clients)
        
        # Get recent scores for status calculation
        recent_scores = {}
        for client in clients:
            latest_scores = session.exec(
                select(Score)
                .where(Score.client_id == client.id)
                .order_by(Score.taken_at.desc())
                .limit(5)
            ).all()
            if latest_scores:
                avg_score = sum(score.value for score in latest_scores) / len(latest_scores)
                recent_scores[client.id] = avg_score
        
        # Categorize clients by score
        excellent = sum(1 for score in recent_scores.values() if score >= 90)
        good = sum(1 for score in recent_scores.values() if 70 <= score < 90)
        needs_attention = sum(1 for score in recent_scores.values() if 50 <= score < 70)
        critical = sum(1 for score in recent_scores.values() if score < 50)
        no_data = total_clients - len(recent_scores)
        
        stats = {
            'total': total_clients,
            'excellent': excellent,
            'good': good,
            'needs_attention': needs_attention,
            'critical': critical,
            'no_data': no_data
        }
        
        # Get recent audit logs for activity feed
        recent_logs = session.exec(
            select(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(10)
        ).all()
        
        return render_template('dashboard_new.html', 
                             clients=clients, 
                             stats=stats, 
                             recent_scores=recent_scores,
                             recent_logs=recent_logs)

@app.route('/clients')
@require_login
def clients_list():
    """List all clients with their scores"""
    with get_session() as session:
        if current_user.role in [RoleType.ADMIN, RoleType.MANAGER]:
            clients = session.exec(select(Client)).all()
        else:
            user_clients = session.exec(
                select(UserClient).where(UserClient.user_id == int(current_user.id))
            ).all()
            client_ids = [uc.client_id for uc in user_clients]
            clients = session.exec(select(Client).where(Client.id.in_(client_ids))).all() if client_ids else []
        
        return render_template('clients_list.html', clients=clients)

@app.route('/client/<int:client_id>')
@require_login
def client_detail(client_id):
    """View detailed information about a specific client"""
    with get_session() as session:
        client = session.get(Client, client_id)
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('clients_list'))
        
        # Check access permissions
        if current_user.role not in [RoleType.ADMIN, RoleType.MANAGER]:
            user_client = session.exec(
                select(UserClient).where(
                    UserClient.user_id == int(current_user.id),
                    UserClient.client_id == client_id
                )
            ).first()
            if not user_client:
                flash('Access denied', 'error')
                return redirect(url_for('clients_list'))
        
        # Get recent scores
        recent_scores = session.exec(
            select(Score)
            .where(Score.client_id == client_id)
            .order_by(Score.taken_at.desc())
            .limit(20)
        ).all()
        
        # Get metrics for scoring
        metrics = session.exec(select(Metric)).all()
        
        return render_template('client_detail.html', 
                             client=client, 
                             recent_scores=recent_scores,
                             metrics=metrics)

@app.route('/metrics')
@require_role(RoleType.MANAGER)
def metrics_list():
    """List all metrics"""
    with get_session() as session:
        metrics = session.exec(select(Metric)).all()
        return render_template('metrics_list.html', metrics=metrics)

@app.route('/add_client', methods=['GET', 'POST'])
@require_role(RoleType.MANAGER)
def add_client():
    """Add a new client"""
    if request.method == 'POST':
        with get_session() as session:
            client = Client(
                name=request.form['name'],
                industry=request.form.get('industry'),
                mrr=int(request.form['mrr']) if request.form.get('mrr') else None,
                renewal_date=datetime.strptime(request.form['renewal_date'], '%Y-%m-%d').date() if request.form.get('renewal_date') else None
            )
            session.add(client)
            session.commit()
            session.refresh(client)
            
            # Log the action
            log = AuditLog(
                user_id=int(current_user.id),
                action='CREATE',
                target_table='client',
                target_id=client.id
            )
            session.add(log)
            session.commit()
            
            flash('Client added successfully!', 'success')
            return redirect(url_for('clients_list'))
    
    return render_template('add_client.html')

@app.route('/add_score/<int:client_id>', methods=['GET', 'POST'])
@require_login
def add_score(client_id):
    """Add a score for a client"""
    with get_session() as session:
        client = session.get(Client, client_id)
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('clients_list'))
        
        if request.method == 'POST':
            metric_id = int(request.form['metric_id'])
            value = max(0, min(100, int(request.form['value'])))  # Ensure 0-100 range
            
            score = Score(
                client_id=client_id,
                metric_id=metric_id,
                value=value,
                locked=True
            )
            session.add(score)
            session.commit()
            
            # Log the action
            log = AuditLog(
                user_id=int(current_user.id),
                action='CREATE',
                target_table='score',
                target_id=score.id
            )
            session.add(log)
            session.commit()
            
            flash('Score added successfully!', 'success')
            return redirect(url_for('client_detail', client_id=client_id))
        
        metrics = session.exec(select(Metric)).all()
        return render_template('add_score.html', client=client, metrics=metrics)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
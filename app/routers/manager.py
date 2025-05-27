from flask import Blueprint, render_template, request, redirect, url_for, abort, flash, jsonify
from sqlmodel import Session, select
from app.database import engine
from app.models import Client, Metric, Score, AuditLog, RoleType, User, UserClient
from app.utils import current_user, role_required, manager_or_admin_required
from app.forms import ClientForm, MetricForm, UserClientAssignForm
from datetime import datetime, timedelta

bp = Blueprint("manager", __name__, url_prefix="/manager")

@bp.route("/clients")
@manager_or_admin_required
def client_list():
    """Display list of all clients for management"""
    with Session(engine) as session:
        clients = session.exec(select(Client)).all()
        return render_template('app/manager_client_list.html', clients=clients)

@bp.route("/clients/new", methods=["GET", "POST"])
@manager_or_admin_required
def create_client():
    """Create a new client"""
    form = ClientForm(request.form)
    
    if request.method == "POST" and form.validate():
        user = current_user()
        
        with Session(engine) as session:
            client = Client(
                name=form.name.data,
                industry=form.industry.data,
                mrr=form.mrr.data,
                renewal_date=datetime.strptime(form.renewal_date.data, '%Y-%m-%d').date() if form.renewal_date.data else None
            )
            session.add(client)
            session.commit()
            
            # Log the action
            audit_log = AuditLog(
                user_id=user.id,
                action="CREATE",
                target_table="client",
                target_id=client.id
            )
            session.add(audit_log)
            session.commit()
            
            flash(f'Client "{client.name}" created successfully!', 'success')
            return redirect(url_for('manager.client_list'))
    
    return render_template('app/client_form.html', form=form, title="Create Client")

@bp.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
@manager_or_admin_required
def edit_client(client_id):
    """Edit an existing client"""
    with Session(engine) as session:
        client = session.get(Client, client_id)
        if not client:
            abort(404)
        
        form = ClientForm(request.form, obj=client)
        
        if request.method == "POST" and form.validate():
            user = current_user()
            
            client.name = form.name.data
            client.industry = form.industry.data
            client.mrr = form.mrr.data
            client.renewal_date = datetime.strptime(form.renewal_date.data, '%Y-%m-%d').date() if form.renewal_date.data else None
            
            session.add(client)
            
            # Log the action
            audit_log = AuditLog(
                user_id=user.id,
                action="UPDATE",
                target_table="client",
                target_id=client_id
            )
            session.add(audit_log)
            session.commit()
            
            flash(f'Client "{client.name}" updated successfully!', 'success')
            return redirect(url_for('manager.client_list'))
    
    return render_template('app/client_form.html', form=form, client=client, title="Edit Client")

@bp.route("/clients/<int:client_id>/trends")
@manager_or_admin_required
def client_trends(client_id):
    """View client scoring trends over time"""
    with Session(engine) as session:
        client = session.get(Client, client_id)
        if not client:
            abort(404)
        
        # Get all scores for this client ordered by date
        scores = session.exec(
            select(Score)
            .where(Score.client_id == client_id)
            .order_by(Score.taken_at.desc())
        ).all()
        
        # Group scores by metric for trend analysis
        metrics_data = {}
        for score in scores:
            metric_name = score.metric.name
            if metric_name not in metrics_data:
                metrics_data[metric_name] = []
            metrics_data[metric_name].append({
                'date': score.taken_at.strftime('%Y-%m-%d'),
                'value': score.value,
                'locked': score.locked
            })
        
        return render_template('app/client_trend.html', 
                             client=client, 
                             metrics_data=metrics_data,
                             scores=scores)

@bp.route("/metrics")
@manager_or_admin_required
def metric_list():
    """Display list of all metrics for management"""
    with Session(engine) as session:
        metrics = session.exec(select(Metric).order_by(Metric.id)).all()
        return render_template('app/metric_list.html', metrics=metrics)

@bp.route("/metrics/new", methods=["GET", "POST"])
@manager_or_admin_required
def create_metric():
    """Create a new metric"""
    form = MetricForm(request.form)
    
    if request.method == "POST" and form.validate():
        user = current_user()
        
        with Session(engine) as session:
            metric = Metric(
                name=form.name.data,
                description=form.description.data,
                weight=form.weight.data,
                high_threshold=form.high_threshold.data,
                low_threshold=form.low_threshold.data
            )
            session.add(metric)
            session.commit()
            
            # Log the action
            audit_log = AuditLog(
                user_id=user.id,
                action="CREATE",
                target_table="metric",
                target_id=metric.id
            )
            session.add(audit_log)
            session.commit()
            
            flash(f'Metric "{metric.name}" created successfully!', 'success')
            return redirect(url_for('manager.metric_list'))
    
    return render_template('app/metric_form.html', form=form, title="Create Metric")

@bp.route("/user-assignments")
@manager_or_admin_required
def user_assignments():
    """Manage user-client assignments"""
    with Session(engine) as session:
        assignments = session.exec(select(UserClient)).all()
        users = session.exec(select(User)).all()
        clients = session.exec(select(Client)).all()
        
        return render_template('app/user_assignments.html', 
                             assignments=assignments,
                             users=users,
                             clients=clients)

@bp.route("/user-assignments/assign", methods=["POST"])
@manager_or_admin_required
def assign_user_to_client():
    """Assign a user to a client"""
    form = UserClientAssignForm(request.form)
    
    if form.validate():
        user = current_user()
        
        with Session(engine) as session:
            # Check if assignment already exists
            existing = session.exec(
                select(UserClient)
                .where(UserClient.user_id == form.user_id.data)
                .where(UserClient.client_id == form.client_id.data)
            ).first()
            
            if existing:
                flash('User is already assigned to this client.', 'warning')
            else:
                assignment = UserClient(
                    user_id=form.user_id.data,
                    client_id=form.client_id.data
                )
                session.add(assignment)
                session.commit()
                
                # Log the action
                audit_log = AuditLog(
                    user_id=user.id,
                    action="ASSIGN",
                    target_table="user_client",
                    target_id=form.client_id.data
                )
                session.add(audit_log)
                session.commit()
                
                flash('User assigned to client successfully!', 'success')
    
    return redirect(url_for('manager.user_assignments'))

@bp.route("/audit-logs")
@manager_or_admin_required
def audit_logs():
    """View audit logs"""
    with Session(engine) as session:
        logs = session.exec(
            select(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(100)
        ).all()
        
        return render_template('app/audit_logs.html', logs=logs)
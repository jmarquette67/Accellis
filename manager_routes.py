from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from app import db
from models import Client, HealthCheck, Alert, User, UserRole, Metric, Score
from replit_auth import require_login
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy import func

manager_bp = Blueprint("manager", __name__, url_prefix="/manager")

def latest_scores_subq(session):
    """Returns subquery with latest score per metric per client."""
    subq = (
        session.query(
            Score.client_id,
            Score.metric_id,
            func.max(Score.taken_at).label("max_ts")
        )
        .group_by(Score.client_id, Score.metric_id)
        .subquery()
    )
    return subq

def require_manager():
    """Decorator to ensure user has manager or admin role"""
    user = current_user
    if not user.is_authenticated or user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
        abort(403)
    return user

@manager_bp.route("/")
@require_login
def dashboard():
    """Manager dashboard overview"""
    require_manager()
    
    # Get summary statistics
    total_clients = Client.query.count()
    active_alerts = Alert.query.filter_by(is_active=True).count()
    recent_checkins = HealthCheck.query.filter(
        HealthCheck.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    # Get recent activity
    recent_clients = Client.query.order_by(Client.last_checkin.desc()).limit(5).all()
    recent_alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).limit(5).all()
    
    return render_template('manager_dashboard.html', 
                         total_clients=total_clients,
                         active_alerts=active_alerts,
                         recent_checkins=recent_checkins,
                         recent_clients=recent_clients,
                         recent_alerts=recent_alerts)

@manager_bp.route("/clients")
@require_login
def client_list():
    """Display all clients for management"""
    require_manager()
    
    clients = Client.query.order_by(Client.name).all()
    return render_template('manager_clients.html', clients=clients)

@manager_bp.route("/clients/analytics")
@require_login
def client_table():
    """Advanced client analytics with weighted scoring"""
    require_manager()
    
    subq = latest_scores_subq(db.session)
    # join subq back to full Score rows
    latest = (
        db.session.query(Score)
        .join(subq, (Score.client_id == subq.c.client_id) &
                   (Score.metric_id == subq.c.metric_id) &
                   (Score.taken_at == subq.c.max_ts))
        .all()
    )

    # compute weighted average per client
    totals = {}
    for sc in latest:
        w = sc.metric.weight
        totals.setdefault(sc.client_id, {"sum": 0, "weight": 0, "client": sc.client})
        totals[sc.client_id]["sum"] += sc.value * w
        totals[sc.client_id]["weight"] += w

    rows = [
        {
            "client": v["client"],
            "overall": round(v["sum"] / v["weight"]) if v["weight"] > 0 else 0
        }
        for v in totals.values()
    ]

    return render_template("manager_analytics.html", rows=rows)

@manager_bp.route("/client/<int:client_id>/trend")
@require_login
def client_trend(client_id):
    """Display performance trend analysis for a specific client"""
    require_manager()
    
    client = Client.query.get_or_404(client_id)
    
    # Get last 12 scores for trend analysis
    points = (
        Score.query
        .filter(Score.client_id == client_id)
        .order_by(Score.taken_at.desc())
        .limit(12)
        .all()
    )
    
    # Format data for chart (oldest to newest)
    data = [{"x": sc.taken_at.strftime("%Y-%m-%d"), "y": sc.value} for sc in points]
    data = data[::-1]  # Reverse to show oldest → newest
    
    return render_template("client_trend.html", client=client, data=data)

@manager_bp.route("/clients/<int:client_id>/details")
@require_login
def client_details(client_id):
    """View detailed client information and trends"""
    require_manager()
    
    client = Client.query.get_or_404(client_id)
    
    # Get recent health checks for trends
    health_checks = HealthCheck.query.filter_by(client_id=client_id)\
                                   .order_by(HealthCheck.timestamp.desc())\
                                   .limit(20).all()
    
    # Get active alerts for this client
    alerts = Alert.query.filter_by(client_id=client_id, is_active=True)\
                       .order_by(Alert.created_at.desc()).all()
    
    return render_template('manager_client_details.html', 
                         client=client,
                         health_checks=health_checks,
                         alerts=alerts)

@manager_bp.route("/alerts")
@require_login
def alert_management():
    """Manage system alerts"""
    require_manager()
    
    # Get all active alerts
    active_alerts = Alert.query.filter_by(is_active=True)\
                              .order_by(Alert.created_at.desc()).all()
    
    # Get recently resolved alerts
    resolved_alerts = Alert.query.filter_by(is_active=False)\
                                .order_by(Alert.resolved_at.desc())\
                                .limit(10).all()
    
    return render_template('manager_alerts.html',
                         active_alerts=active_alerts,
                         resolved_alerts=resolved_alerts)

@manager_bp.route("/alerts/<int:alert_id>/resolve", methods=["POST"])
@require_login
def resolve_alert(alert_id):
    """Resolve an active alert"""
    require_manager()
    
    alert = Alert.query.get_or_404(alert_id)
    alert.is_active = False
    alert.resolved_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'Alert resolved successfully!', 'success')
    
    return redirect(url_for('manager.alert_management'))

@manager_bp.route("/users")
@require_login
def user_management():
    """Manage users and their roles"""
    user = require_manager()
    
    # Only admins can manage users
    if user.role != UserRole.ADMIN:
        abort(403)
    
    users = User.query.order_by(User.email).all()
    return render_template('manager_users.html', users=users)
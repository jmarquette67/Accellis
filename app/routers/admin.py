from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from sqlmodel import Session, select
from database import get_session, engine
from models import User, Client, Metric, Score, UserClient, AuditLog, RoleType
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def require_login(f):
    """Simple login requirement decorator"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def require_role(required_role):
    """Role-based access control decorator"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('index'))
            
            # Check if user has required role or higher
            role_hierarchy = {
                RoleType.TAM: 1,
                RoleType.VCIO: 2,
                RoleType.MANAGER: 3,
                RoleType.ADMIN: 4
            }
            
            if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 5):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@admin_bp.route('/metrics')
@require_login
def metric_list():
    """List all metrics"""
    with Session(engine) as session:
        metrics = session.exec(select(Metric)).all()
    return render_template('app/metric_list.html', metrics=metrics)

@admin_bp.route('/metrics/new', methods=['GET', 'POST'])
@require_role(RoleType.MANAGER)
def metric_new():
    """Create new metric"""
    if request.method == 'POST':
        with Session(engine) as session:
            metric = Metric(
                name=request.form['name'],
                description=request.form.get('description'),
                weight=int(request.form['weight']),
                high_threshold=int(request.form['high_threshold']),
                low_threshold=int(request.form['low_threshold'])
            )
            session.add(metric)
            session.commit()
            
            # Log action
            log = AuditLog(
                user_id=current_user.id,
                action='CREATE',
                target_table='metric',
                target_id=metric.id
            )
            session.add(log)
            session.commit()
            
            flash('Metric created successfully!', 'success')
            return redirect(url_for('admin.metric_list'))
    
    return render_template('app/metric_form.html')

@admin_bp.route('/clients')
@require_login
def client_list():
    """List all clients"""
    with Session(engine) as session:
        if current_user.role in [RoleType.ADMIN, RoleType.MANAGER]:
            # Admin and Manager can see all clients
            clients = session.exec(select(Client)).all()
        else:
            # TAM and VCIO see only assigned clients
            user_clients = session.exec(
                select(UserClient).where(UserClient.user_id == current_user.id)
            ).all()
            client_ids = [uc.client_id for uc in user_clients]
            if client_ids:
                clients = session.exec(
                    select(Client).where(Client.id.in_(client_ids))
                ).all()
            else:
                clients = []
    
    return render_template('app/client_list.html', clients=clients)

@admin_bp.route('/clients/new', methods=['GET', 'POST'])
@require_role(RoleType.MANAGER)
def client_new():
    """Create new client"""
    if request.method == 'POST':
        with Session(engine) as session:
            client = Client(
                name=request.form['name'],
                industry=request.form.get('industry'),
                mrr=int(request.form['mrr']) if request.form.get('mrr') else None,
                renewal_date=datetime.strptime(request.form['renewal_date'], '%Y-%m-%d').date() if request.form.get('renewal_date') else None
            )
            session.add(client)
            session.commit()
            
            # Log action
            log = AuditLog(
                user_id=current_user.id,
                action='CREATE',
                target_table='client',
                target_id=client.id
            )
            session.add(log)
            session.commit()
            
            flash('Client created successfully!', 'success')
            return redirect(url_for('admin.client_list'))
    
    return render_template('app/client_form.html')

@admin_bp.route('/user-clients', methods=['GET', 'POST'])
@require_role(RoleType.MANAGER)
def user_client_assign():
    """Assign users to clients"""
    with Session(engine) as session:
        if request.method == 'POST':
            user_id = int(request.form['user_id'])
            client_id = int(request.form['client_id'])
            
            # Check if assignment already exists
            existing = session.exec(
                select(UserClient).where(
                    UserClient.user_id == user_id,
                    UserClient.client_id == client_id
                )
            ).first()
            
            if not existing:
                user_client = UserClient(user_id=user_id, client_id=client_id)
                session.add(user_client)
                session.commit()
                
                # Log action
                log = AuditLog(
                    user_id=current_user.id,
                    action='ASSIGN',
                    target_table='user_client',
                    target_id=client_id
                )
                session.add(log)
                session.commit()
                
                flash('User assigned to client successfully!', 'success')
            else:
                flash('User is already assigned to this client.', 'warning')
        
        users = session.exec(select(User)).all()
        clients = session.exec(select(Client)).all()
        assignments = session.exec(select(UserClient)).all()
    
    return render_template('app/userclient_form.html', users=users, clients=clients, assignments=assignments)
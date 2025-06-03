from datetime import datetime, timedelta
from app import db
from sqlalchemy import func
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
import enum

# Role enum for user permissions
class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    VCIO = "VCIO"
    TAM = "TAM"

# Alias for compatibility with authentication system
RoleType = UserRole

# User model for Replit Auth
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.TAM)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def has_role(self, required_role):
        """Check if user has required role or higher"""
        role_hierarchy = {
            UserRole.TAM: 1,
            UserRole.VCIO: 2,
            UserRole.MANAGER: 3,
            UserRole.ADMIN: 4
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

# OAuth model for Replit Auth
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Contact information
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    
    # Business information
    description = db.Column(db.Text)
    industry = db.Column(db.String(50))
    
    # Management
    account_owner_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_checkin = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    health_checks = db.relationship('HealthCheck', backref='client', lazy=True, cascade='all, delete-orphan')
    account_owner = db.relationship('User', backref='managed_clients')
    
    @property
    def status(self):
        """Determine client status based on last check-in and latest health metrics"""
        if not self.last_checkin:
            return 'unknown'
        
        # If no check-in in last 5 minutes, consider offline
        if datetime.utcnow() - self.last_checkin > timedelta(minutes=5):
            return 'offline'
        
        # Get latest health check
        latest_check = HealthCheck.query.filter_by(client_id=self.id).order_by(HealthCheck.timestamp.desc()).first()
        if not latest_check:
            return 'unknown'
        
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
    def status_color(self):
        """Get Bootstrap color class for status"""
        status_colors = {
            'healthy': 'success',
            'warning': 'warning', 
            'critical': 'danger',
            'offline': 'secondary',
            'unknown': 'secondary'
        }
        return status_colors.get(self.status, 'secondary')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'description': self.description,
            'last_checkin': self.last_checkin.isoformat() if self.last_checkin else None,
            'status': self.status,
            'status_color': self.status_color,
            'is_active': self.is_active
        }

class HealthCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # System metrics
    cpu_usage = db.Column(db.Float, nullable=False)  # Percentage
    memory_usage = db.Column(db.Float, nullable=False)  # Percentage
    disk_usage = db.Column(db.Float, nullable=False)  # Percentage
    uptime = db.Column(db.Integer, nullable=False)  # Seconds
    
    # Network and additional info
    load_average = db.Column(db.Float)
    network_rx = db.Column(db.BigInteger)  # Bytes received
    network_tx = db.Column(db.BigInteger)  # Bytes transmitted
    
    # Status and notes
    status = db.Column(db.String(20), default='healthy')
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'uptime': self.uptime,
            'load_average': self.load_average,
            'network_rx': self.network_rx,
            'network_tx': self.network_tx,
            'status': self.status,
            'notes': self.notes
        }

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'cpu', 'memory', 'disk', 'offline'
    severity = db.Column(db.String(20), nullable=False)  # 'warning', 'critical'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    client = db.relationship('Client', backref='alerts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else 'Unknown',
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_active': self.is_active
        }

class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    weight = db.Column(db.Integer, nullable=False)  # Priority weight (1-5)
    max_score = db.Column(db.Integer, nullable=False)  # Maximum possible points for this metric
    scoring_criteria = db.Column(db.Text)  # Detailed scoring description
    high_threshold = db.Column(db.Integer, nullable=False)  # >= marks "high"
    low_threshold = db.Column(db.Integer, nullable=False)   # <= marks "low"
    
    # Three-range scoring fields for Help Desk Usage
    too_low_threshold = db.Column(db.Numeric(5,2))
    too_low_score = db.Column(db.Integer)
    ideal_min_threshold = db.Column(db.Numeric(5,2))
    ideal_max_threshold = db.Column(db.Numeric(5,2))
    ideal_score = db.Column(db.Integer)
    too_high_threshold = db.Column(db.Numeric(5,2))
    too_high_score = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scores = db.relationship('Score', backref='metric', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'weight': self.weight,
            'max_score': self.max_score,
            'scoring_criteria': self.scoring_criteria,
            'high_threshold': self.high_threshold,
            'low_threshold': self.low_threshold,
            'created_at': self.created_at.isoformat()
        }

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    metric_id = db.Column(db.Integer, db.ForeignKey('metric.id'), nullable=False)
    value = db.Column(db.Integer, nullable=False)  # 0-100, rounded on save
    taken_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    locked = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    # Relationships
    client = db.relationship('Client', backref='scores')
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else 'Unknown',
            'metric_id': self.metric_id,
            'metric_name': self.metric.name if self.metric else 'Unknown',
            'value': self.value,
            'taken_at': self.taken_at.isoformat(),
            'locked': self.locked,
            'notes': self.notes
        }

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    
    # Relationship
    updated_by_user = db.relationship('User', backref='site_settings_updated')
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }

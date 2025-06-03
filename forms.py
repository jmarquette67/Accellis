from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional, ValidationError
from models import Client

class ClientRegistrationForm(FlaskForm):
    name = StringField('Client Name', validators=[
        DataRequired(message='Client name is required'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    account_manager = SelectField('Account Manager', coerce=str, validators=[
        DataRequired(message='Account manager is required')
    ])
    
    # Primary client contact information
    contact_name = StringField('Primary Contact Name', validators=[
        DataRequired(message='Primary contact name is required'),
        Length(min=2, max=100, message='Contact name must be between 2 and 100 characters')
    ])
    
    contact_phone = StringField('Primary Contact Phone', validators=[
        DataRequired(message='Primary contact phone is required'),
        Length(min=10, max=20, message='Phone number must be between 10 and 20 characters')
    ])
    
    contact_email = StringField('Primary Contact Email', validators=[
        DataRequired(message='Primary contact email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    # Client business information
    client_description = TextAreaField('Client Description', validators=[
        Optional(),
        Length(max=500, message='Description must be less than 500 characters')
    ])
    
    industry = SelectField('Industry', validators=[
        DataRequired(message='Industry is required')
    ], choices=[
        ('legal', 'Legal'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('healthcare', 'Healthcare'),
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('education', 'Education'),
        ('nonprofit', 'Non-Profit'),
        ('other', 'Other')
    ])

class HealthCheckForm(FlaskForm):
    cpu_usage = FloatField('CPU Usage (%)', validators=[
        DataRequired(message='CPU usage is required'),
        NumberRange(min=0, max=100, message='CPU usage must be between 0 and 100%')
    ])
    
    memory_usage = FloatField('Memory Usage (%)', validators=[
        DataRequired(message='Memory usage is required'),
        NumberRange(min=0, max=100, message='Memory usage must be between 0 and 100%')
    ])
    
    disk_usage = FloatField('Disk Usage (%)', validators=[
        DataRequired(message='Disk usage is required'),
        NumberRange(min=0, max=100, message='Disk usage must be between 0 and 100%')
    ])
    
    uptime = IntegerField('Uptime (seconds)', validators=[
        DataRequired(message='Uptime is required'),
        NumberRange(min=0, message='Uptime must be a positive number')
    ])
    
    load_average = FloatField('Load Average', validators=[
        Optional(),
        NumberRange(min=0, message='Load average must be positive')
    ])
    
    network_rx = IntegerField('Network RX (bytes)', validators=[
        Optional(),
        NumberRange(min=0, message='Network RX must be positive')
    ])
    
    network_tx = IntegerField('Network TX (bytes)', validators=[
        Optional(),
        NumberRange(min=0, message='Network TX must be positive')
    ])
    
    notes = TextAreaField('Notes', validators=[
        Optional(),
        Length(max=500, message='Notes must be less than 500 characters')
    ])

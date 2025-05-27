from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, IPAddress, NumberRange, Optional
from models import Client

class ClientRegistrationForm(FlaskForm):
    name = StringField('Client Name', validators=[
        DataRequired(message='Client name is required'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    hostname = StringField('Hostname', validators=[
        DataRequired(message='Hostname is required'),
        Length(min=2, max=100, message='Hostname must be between 2 and 100 characters')
    ])
    
    ip_address = StringField('IP Address', validators=[
        DataRequired(message='IP address is required'),
        IPAddress(message='Please enter a valid IP address')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must be less than 500 characters')
    ])
    
    def validate_hostname(self, field):
        client = Client.query.filter_by(hostname=field.data).first()
        if client:
            raise ValidationError('Hostname already registered. Please choose a different hostname.')

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

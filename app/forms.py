from wtforms import Form, IntegerField, validators, SelectField, TextAreaField, StringField, SubmitField
from wtforms.validators import InputRequired, NumberRange, Length, Optional

def build_score_form(metrics):
    """Dynamically create a form with one IntegerField per metric."""
    class _ScoreForm(Form):
        pass
    
    for m in metrics:
        setattr(_ScoreForm, f"metric_{m.id}",
                IntegerField(m.name,
                  [validators.InputRequired(),
                   validators.NumberRange(min=0, max=100)],
                  description=f"{m.description} (Weight: {m.weight}%)"))
    
    # Add submit button
    setattr(_ScoreForm, 'submit', SubmitField('Save Scores'))
    
    return _ScoreForm

class ClientForm(Form):
    """Form for creating/editing clients"""
    name = StringField('Client Name', [
        InputRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    industry = StringField('Industry', [
        Optional(),
        Length(max=100, message='Industry must be less than 100 characters')
    ])
    
    mrr = IntegerField('Monthly Recurring Revenue ($)', [
        Optional(),
        NumberRange(min=0, message='MRR must be positive')
    ])
    
    renewal_date = StringField('Renewal Date (YYYY-MM-DD)', [
        Optional()
    ])
    
    submit = SubmitField('Save Client')

class MetricForm(Form):
    """Form for creating/editing metrics"""
    name = StringField('Metric Name', [
        InputRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    description = TextAreaField('Description', [
        Optional(),
        Length(max=500, message='Description must be less than 500 characters')
    ])
    
    weight = IntegerField('Weight (1-100)', [
        InputRequired(),
        NumberRange(min=1, max=100, message='Weight must be between 1 and 100')
    ])
    
    high_threshold = IntegerField('High Threshold (≥)', [
        InputRequired(),
        NumberRange(min=0, max=100, message='Threshold must be between 0 and 100')
    ])
    
    low_threshold = IntegerField('Low Threshold (≤)', [
        InputRequired(),
        NumberRange(min=0, max=100, message='Threshold must be between 0 and 100')
    ])
    
    submit = SubmitField('Save Metric')

class UserClientAssignForm(Form):
    """Form for assigning users to clients"""
    user_id = SelectField('User', [InputRequired()], coerce=str)
    client_id = SelectField('Client', [InputRequired()], coerce=int)
    submit = SubmitField('Assign User to Client')

class ScoreEditForm(Form):
    """Form for editing individual scores"""
    value = IntegerField('Score Value', [
        InputRequired(),
        NumberRange(min=0, max=100, message='Score must be between 0 and 100')
    ])
    
    submit = SubmitField('Update Score')
"""
Dynamic scoring calculations based on current metric configuration
Automatically adjusts maximum points and percentages based on active metrics
"""
from models import Metric, MetricOption

def get_maximum_possible_score():
    """Calculate maximum possible score based on current metric configuration"""
    total_max = 0
    metrics = Metric.query.all()
    
    for metric in metrics:
        if metric.input_type == 'select':
            # For dropdown metrics, get the highest option value
            max_option = MetricOption.query.filter_by(
                metric_id=metric.id, 
                is_active=True
            ).order_by(MetricOption.option_value.desc()).first()
            
            if max_option:
                metric_max = max_option.option_value * metric.weight
            else:
                metric_max = 0
        else:
            # For number input metrics, use max_score field
            metric_max = (metric.max_score or 0) * metric.weight
        
        total_max += metric_max
    
    return total_max

def calculate_score_percentage(score_total, max_possible=None):
    """Calculate percentage based on dynamic maximum"""
    if max_possible is None:
        max_possible = get_maximum_possible_score()
    
    if max_possible == 0:
        return 0
    
    return (score_total / max_possible) * 100

def get_performance_grade(percentage):
    """Get performance grade based on percentage"""
    if percentage >= 85:
        return {'grade': 'A', 'color': 'success', 'description': 'Excellent'}
    elif percentage >= 75:
        return {'grade': 'B', 'color': 'info', 'description': 'Good'}
    elif percentage >= 65:
        return {'grade': 'C', 'color': 'warning', 'description': 'Satisfactory'}
    elif percentage >= 50:
        return {'grade': 'D', 'color': 'danger', 'description': 'Needs Improvement'}
    else:
        return {'grade': 'F', 'color': 'dark', 'description': 'Critical'}

def get_metric_breakdown():
    """Get detailed breakdown of each metric's contribution to total score"""
    metrics = Metric.query.all()
    breakdown = []
    
    for metric in metrics:
        if metric.input_type == 'select':
            max_option = MetricOption.query.filter_by(
                metric_id=metric.id, 
                is_active=True
            ).order_by(MetricOption.option_value.desc()).first()
            
            max_value = max_option.option_value if max_option else 0
        else:
            max_value = metric.max_score or 0
        
        max_weighted = max_value * metric.weight
        
        breakdown.append({
            'metric': metric,
            'max_raw_score': max_value,
            'weight': metric.weight,
            'max_weighted_points': max_weighted,
            'percentage_of_total': (max_weighted / get_maximum_possible_score()) * 100 if get_maximum_possible_score() > 0 else 0
        })
    
    return breakdown

def format_score_display(score_total, show_percentage=True, show_grade=True):
    """Format score for consistent display across the platform"""
    max_possible = get_maximum_possible_score()
    percentage = calculate_score_percentage(score_total, max_possible)
    
    display = f"{score_total:.1f}/{max_possible:.0f}"
    
    if show_percentage:
        display += f" ({percentage:.1f}%)"
    
    if show_grade:
        grade_info = get_performance_grade(percentage)
        display += f" - Grade {grade_info['grade']}"
    
    return {
        'display_text': display,
        'score_total': score_total,
        'max_possible': max_possible,
        'percentage': percentage,
        'grade_info': get_performance_grade(percentage) if show_grade else None
    }
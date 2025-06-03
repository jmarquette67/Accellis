"""
Normalized scoring system to address Cross Selling metric dominance
Creates fair performance comparisons by normalizing metric contributions
"""

def calculate_normalized_scoresheet_total(scores_data):
    """
    Calculate normalized scoresheet total that treats Cross Selling proportionally
    
    Args:
        scores_data: List of tuples (score_value, metric_weight, metric_name)
    
    Returns:
        dict with normalized_total and breakdown
    """
    
    # Define normalization factors based on analysis
    # Cross Selling: weight 3, avg 7.43 contribution -> normalize to ~2.5 contribution
    # Other high metrics: weight 4-5, avg 2.9-3.8 contribution -> keep similar
    
    normalization_factors = {
        'Cross Selling': 0.33,  # Reduce impact by 67%
        'Regular Feedback': 1.0,  # Keep as baseline
        'Project Engagement': 1.0,
        'Strategic Review Attendance': 1.0,
        'Gut Instinct': 1.0,
        'Support Engagement Satisfaction': 1.0,
        'First Touch Resolution/Escalation': 1.0,
        'Help Desk Usage': 1.0,
        'Procurement': 1.0,
        'Client LifeCycle Phase': 1.0,
        'Invoices/AR': 1.0,
        'Tech Stack': 1.0,
        'Credit Requests': 1.0
    }
    
    normalized_total = 0
    breakdown = {}
    
    for score_value, metric_weight, metric_name in scores_data:
        # Apply normalization factor
        factor = normalization_factors.get(metric_name, 1.0)
        normalized_contribution = score_value * metric_weight * factor
        
        normalized_total += normalized_contribution
        breakdown[metric_name] = {
            'original_contribution': score_value * metric_weight,
            'normalized_contribution': normalized_contribution,
            'normalization_factor': factor
        }
    
    return {
        'normalized_total': normalized_total,
        'breakdown': breakdown
    }

def get_normalized_performance_ranges():
    """
    Return performance ranges based on normalized scoring
    With Cross Selling normalized, expect lower overall totals
    """
    return {
        'high_performance': 25,    # Top 15% after normalization
        'medium_performance': 18,  # Above median after normalization
        'low_performance': 0       # Below median
    }

def calculate_normalized_metrics_by_client(all_scores):
    """
    Calculate normalized scoresheet totals for all clients
    
    Args:
        all_scores: Query result with score, metric, client, user data
    
    Returns:
        dict: client_id -> list of normalized scoresheet totals
    """
    
    # Group scores by date and client to form scoresheets
    scoresheet_data = {}
    
    for score, metric, client, user in all_scores:
        date_key = score.taken_at.date()
        sheet_key = f"{date_key}_{client.id}"
        
        if sheet_key not in scoresheet_data:
            scoresheet_data[sheet_key] = {
                'date': date_key,
                'client_id': client.id,
                'client_name': client.name,
                'scores': []
            }
        
        scoresheet_data[sheet_key]['scores'].append(
            (score.value, metric.weight, metric.name)
        )
    
    # Calculate normalized totals for each scoresheet
    client_normalized_totals = {}
    
    for sheet_key, data in scoresheet_data.items():
        client_id = data['client_id']
        
        if client_id not in client_normalized_totals:
            client_normalized_totals[client_id] = {
                'totals': [],
                'client_name': data['client_name']
            }
        
        normalized_result = calculate_normalized_scoresheet_total(data['scores'])
        client_normalized_totals[client_id]['totals'].append(
            normalized_result['normalized_total']
        )
    
    return client_normalized_totals
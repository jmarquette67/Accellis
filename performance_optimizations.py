"""
Performance optimizations for Accellis Client Engagement Platform
Implements caching and database query optimizations
"""
from functools import lru_cache
from datetime import datetime, timedelta
import time

# Cache for expensive calculations
_cache = {}
_cache_timeout = 300  # 5 minutes

def get_cached_or_calculate(cache_key, calculation_func, timeout=300):
    """Generic caching function with timeout"""
    now = time.time()
    
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if now - timestamp < timeout:
            return data
    
    # Calculate new value
    result = calculation_func()
    _cache[cache_key] = (result, now)
    return result

@lru_cache(maxsize=32)
def get_maximum_possible_score_cached():
    """Cached version of maximum possible score calculation"""
    from scoring_calculations import get_maximum_possible_score
    return get_maximum_possible_score()

def get_dashboard_data_cached():
    """Cached dashboard data with optimized queries"""
    from app import db
    from models import Score, Client, Metric
    from scoring_calculations import calculate_score_percentage, get_performance_grade
    
    def calculate_dashboard():
        # Optimized query with joins to reduce database calls
        recent_scores = db.session.query(Score, Client, Metric).join(
            Client, Score.client_id == Client.id
        ).join(
            Metric, Score.metric_id == Metric.id
        ).filter(
            Score.status == 'final'
        ).order_by(Score.taken_at.desc()).limit(15).all()
        
        # Group by client and date efficiently
        scoresheet_data = {}
        for score, client, metric in recent_scores:
            key = (client.id, score.taken_at.date())
            if key not in scoresheet_data:
                scoresheet_data[key] = {
                    'client_name': client.name,
                    'client_id': client.id,
                    'date': score.taken_at.strftime('%m/%d'),
                    'date_key': score.taken_at.strftime('%Y-%m-%d'),
                    'user_name': 'System',
                    'scores': [],
                    'taken_at': score.taken_at
                }
            scoresheet_data[key]['scores'].append((score.value, metric.weight))
        
        # Calculate totals efficiently
        max_score = get_maximum_possible_score_cached()
        recent_data = []
        
        for sheet_data in sorted(scoresheet_data.values(), key=lambda x: x['taken_at'], reverse=True)[:5]:
            if sheet_data['scores']:
                total_weighted = sum(score * weight for score, weight in sheet_data['scores'])
                percentage = calculate_score_percentage(total_weighted, max_score)
                grade_info = get_performance_grade(percentage)
                
                recent_data.append({
                    'client_name': sheet_data['client_name'],
                    'client_id': sheet_data['client_id'],
                    'date': sheet_data['date'],
                    'date_key': sheet_data['date_key'],
                    'user_name': sheet_data['user_name'],
                    'total_score': f"{total_weighted:.1f}",
                    'max_score': f"{max_score:.0f}",
                    'grade_color': grade_info['color']
                })
        
        # Simplified trending calculation for performance
        trending_up = []
        trending_down = []
        
        # Only check top 10 active clients for trends
        active_clients = Client.query.filter_by(is_active=True).limit(10).all()
        for client in active_clients:
            recent_client_scores = Score.query.filter_by(
                client_id=client.id, 
                status='final'
            ).order_by(Score.taken_at.desc()).limit(6).all()
            
            if len(recent_client_scores) >= 4:
                # Get metrics in one query
                metric_ids = list(set(s.metric_id for s in recent_client_scores))
                metrics_dict = {m.id: m for m in Metric.query.filter(Metric.id.in_(metric_ids)).all()}
                
                # Calculate trend efficiently
                recent_scores = recent_client_scores[:3]
                older_scores = recent_client_scores[3:6]
                
                recent_avg = sum(s.value * metrics_dict[s.metric_id].weight for s in recent_scores if s.metric_id in metrics_dict) / len(recent_scores)
                older_avg = sum(s.value * metrics_dict[s.metric_id].weight for s in older_scores if s.metric_id in metrics_dict) / len(older_scores)
                
                if older_avg > 0:
                    trend_percent = ((recent_avg - older_avg) / older_avg) * 100
                    
                    if trend_percent > 15:
                        trending_up.append({
                            'name': client.name,
                            'client_id': client.id,
                            'trend': trend_percent
                        })
                    elif trend_percent < -15:
                        trending_down.append({
                            'name': client.name,
                            'client_id': client.id,
                            'trend': trend_percent
                        })
        
        # Sort and limit
        trending_up = sorted(trending_up, key=lambda x: x['trend'], reverse=True)[:3]
        trending_down = sorted(trending_down, key=lambda x: x['trend'])[:3]
        
        return {
            'recent_scoresheets': recent_data,
            'trending_up': trending_up,
            'trending_down': trending_down
        }
    
    return get_cached_or_calculate('dashboard_data', calculate_dashboard, timeout=180)

def clear_dashboard_cache():
    """Clear dashboard cache when new scores are added"""
    if 'dashboard_data' in _cache:
        del _cache['dashboard_data']

def get_optimized_client_list():
    """Optimized client list query"""
    def calculate_clients():
        from models import Client
        return Client.query.filter_by(is_active=True).order_by(Client.name).all()
    
    return get_cached_or_calculate('client_list', calculate_clients, timeout=600)
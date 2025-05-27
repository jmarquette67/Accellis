#!/usr/bin/env python3
"""
Quick data viewer for your authentic Q1 2025 client engagement data
Shows the sample data that was generated from your real spreadsheet
"""

from app import app, db
from models import Client, Metric, Score
from datetime import datetime

def view_sample_data():
    """Display overview of your authentic sample data"""
    with app.app_context():
        print("=" * 60)
        print("ACCELLIS CLIENT ENGAGEMENT DATA OVERVIEW")
        print("=" * 60)
        
        # Show client count
        clients = Client.query.all()
        print(f"\n📊 CLIENTS: {len(clients)} total")
        for client in clients[:10]:  # Show first 10
            print(f"   • {client.name}")
        if len(clients) > 10:
            print(f"   ... and {len(clients) - 10} more clients")
        
        # Show metrics from your Q1 2025 data
        metrics = Metric.query.order_by(Metric.weight.desc()).all()
        print(f"\n📈 ENGAGEMENT METRICS: {len(metrics)} authentic metrics from Q1 2025")
        for metric in metrics:
            print(f"   • {metric.name} (Weight: {metric.weight}/5)")
        
        # Show score statistics
        scores = Score.query.all()
        print(f"\n📋 SCORES: {len(scores)} authentic engagement scores")
        
        if scores:
            # Date range
            earliest = min(s.taken_at for s in scores)
            latest = max(s.taken_at for s in scores)
            print(f"   📅 Date Range: {earliest.strftime('%b %Y')} to {latest.strftime('%b %Y')}")
            
            # Score distribution
            avg_score = sum(s.value for s in scores) / len(scores)
            high_scores = len([s for s in scores if s.value >= 80])
            low_scores = len([s for s in scores if s.value <= 40])
            
            print(f"   🎯 Average Score: {avg_score:.1f}%")
            print(f"   🟢 High Performers (80%+): {high_scores} scores")
            print(f"   🔴 Need Attention (40% or below): {low_scores} scores")
            
            # Monthly breakdown
            monthly_counts = {}
            for score in scores:
                month_key = score.taken_at.strftime('%Y-%m')
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            
            print(f"\n📆 MONTHLY BREAKDOWN:")
            for month in sorted(monthly_counts.keys())[-6:]:  # Last 6 months
                count = monthly_counts[month]
                month_name = datetime.strptime(month, '%Y-%m').strftime('%b %Y')
                print(f"   • {month_name}: {count} scores")
        
        # Sample client performance
        print(f"\n🏆 SAMPLE CLIENT PERFORMANCE:")
        for client in clients[:5]:
            client_scores = Score.query.filter_by(client_id=client.id).all()
            if client_scores:
                avg = sum(s.value for s in client_scores) / len(client_scores)
                print(f"   • {client.name}: {avg:.1f}% avg ({len(client_scores)} scores)")
        
        print("\n" + "=" * 60)
        print("Your authentic Q1 2025 engagement data is ready!")
        print("Access it through the web interface Manager Tools > View Analytics")
        print("=" * 60)

if __name__ == "__main__":
    view_sample_data()
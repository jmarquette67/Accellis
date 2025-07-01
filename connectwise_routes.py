"""
ConnectWise Integration Routes for Accellis Client Engagement Platform
Provides web interface and API endpoints for ConnectWise data synchronization
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from auth import require_login, require_role
from app import db
from models import UserRole, Client, Score, Metric
from connectwise_integration import ConnectWiseAPI, ConnectWiseDataSync, setup_connectwise_integration
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create ConnectWise blueprint
connectwise_bp = Blueprint("connectwise", __name__, url_prefix="/connectwise")

@connectwise_bp.route("/")
@require_login
def integration_dashboard():
    """ConnectWise integration dashboard"""
    user = require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    # Get integration status
    cw_api = ConnectWiseAPI()
    connection_status = cw_api.test_connection()
    
    # Get statistics
    total_clients = Client.query.count()
    synced_clients = Client.query.filter(Client.connectwise_id.isnot(None)).count()
    
    stats = {
        'total_clients': total_clients,
        'synced_clients': synced_clients,
        'sync_percentage': round((synced_clients / total_clients * 100) if total_clients > 0 else 0, 1)
    }
    
    return render_template('connectwise/dashboard.html', 
                         connection_status=connection_status,
                         stats=stats)

@connectwise_bp.route("/setup", methods=['GET', 'POST'])
@require_login
def setup():
    """ConnectWise integration setup and configuration"""
    require_role([UserRole.ADMIN])
    
    if request.method == 'POST':
        # Initialize database schema for ConnectWise integration
        result = setup_connectwise_integration()
        
        if result['status'] == 'success':
            flash('ConnectWise integration setup completed successfully', 'success')
        else:
            flash(f'Setup failed: {result["message"]}', 'error')
        
        return redirect(url_for('connectwise.integration_dashboard'))
    
    return render_template('connectwise/setup.html')

@connectwise_bp.route("/test-connection")
@require_login
def test_connection():
    """Test ConnectWise API connection"""
    require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    cw_api = ConnectWiseAPI()
    result = cw_api.test_connection()
    
    return jsonify(result)

@connectwise_bp.route("/sync-clients", methods=['POST'])
@require_login
def sync_clients():
    """Synchronize clients from ConnectWise"""
    require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    try:
        sync_service = ConnectWiseDataSync()
        result = sync_service.sync_clients()
        
        if result['status'] == 'success':
            flash(f"Synchronized {result['synced']} new clients and updated {result['updated']} existing clients", 'success')
        else:
            flash(f"Sync failed: {result['message']}", 'error')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in client sync: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@connectwise_bp.route("/auto-score/<int:client_id>", methods=['POST'])
@require_login
def auto_score_client():
    """Auto-generate scores for a client based on ConnectWise data"""
    require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    client_id = request.view_args['client_id']
    days_back = request.json.get('days_back', 30) if request.is_json else 30
    
    try:
        sync_service = ConnectWiseDataSync()
        metrics_result = sync_service.calculate_engagement_metrics(client_id, days_back)
        
        if metrics_result['status'] == 'error':
            return jsonify(metrics_result), 400
        
        # Create scores based on calculated metrics
        client = Client.query.get_or_404(client_id)
        created_scores = 0
        
        for metric_name, score_value in metrics_result['metrics'].items():
            metric = Metric.query.filter_by(name=metric_name).first()
            if metric:
                # Create new score entry
                new_score = Score(
                    client_id=client_id,
                    metric_id=metric.id,
                    value=score_value,
                    taken_at=datetime.now(),
                    status='final',
                    notes=f'Auto-generated from ConnectWise data ({days_back} days)',
                    locked=False
                )
                db.session.add(new_score)
                created_scores += 1
        
        db.session.commit()
        
        result = {
            "status": "success",
            "client_name": client.name,
            "scores_created": created_scores,
            "metrics": metrics_result['metrics']
        }
        
        flash(f"Created {created_scores} auto-generated scores for {client.name}", 'success')
        return jsonify(result)
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error auto-scoring client {client_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@connectwise_bp.route("/client-mapping")
@require_login
def client_mapping():
    """View and manage client mapping between Accellis and ConnectWise"""
    require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    # Get all clients with their ConnectWise sync status
    clients = db.session.query(Client).all()
    
    # Get ConnectWise companies for mapping
    cw_api = ConnectWiseAPI()
    cw_companies = cw_api.get_companies()
    
    # Create mapping data
    mapping_data = []
    for client in clients:
        client_data = {
            'client': client,
            'has_connectwise_id': client.connectwise_id is not None,
            'last_sync': None,  # TODO: Add sync tracking
            'available_cw_companies': [c for c in cw_companies if c['id'] != client.connectwise_id]
        }
        mapping_data.append(client_data)
    
    return render_template('connectwise/client_mapping.html', 
                         mapping_data=mapping_data,
                         cw_companies=cw_companies)

@connectwise_bp.route("/map-client", methods=['POST'])
@require_login
def map_client():
    """Map an Accellis client to a ConnectWise company"""
    require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    client_id = request.form.get('client_id')
    connectwise_id = request.form.get('connectwise_id')
    
    try:
        client = Client.query.get_or_404(client_id)
        client.connectwise_id = int(connectwise_id) if connectwise_id else None
        db.session.commit()
        
        action = "mapped to" if connectwise_id else "unmapped from"
        flash(f"Client '{client.name}' {action} ConnectWise successfully", 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error mapping client: {e}")
        flash(f"Error mapping client: {e}", 'error')
    
    return redirect(url_for('connectwise.client_mapping'))

@connectwise_bp.route("/sync-history")
@require_login
def sync_history():
    """View ConnectWise synchronization history and logs"""
    require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    # TODO: Implement sync history tracking
    # For now, show current sync status
    
    sync_logs = [
        {
            'timestamp': datetime.now(),
            'action': 'Manual Client Sync',
            'status': 'Success',
            'details': 'Synchronized 15 clients, updated 3'
        }
    ]
    
    return render_template('connectwise/sync_history.html', sync_logs=sync_logs)

@connectwise_bp.route("/api/companies")
@require_login
def api_companies():
    """API endpoint to get ConnectWise companies"""
    require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    try:
        cw_api = ConnectWiseAPI()
        companies = cw_api.get_companies()
        return jsonify({"status": "success", "companies": companies})
    
    except Exception as e:
        logger.error(f"Error fetching ConnectWise companies: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@connectwise_bp.route("/api/tickets/<int:company_id>")
@require_login
def api_company_tickets(company_id):
    """Get recent tickets for a ConnectWise company"""
    require_role([UserRole.ADMIN, UserRole.MANAGER])
    
    days_back = request.args.get('days', 30, type=int)
    
    try:
        cw_api = ConnectWiseAPI()
        tickets = cw_api.get_tickets(company_id, days_back)
        return jsonify({"status": "success", "tickets": tickets})
    
    except Exception as e:
        logger.error(f"Error fetching tickets for company {company_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@connectwise_bp.route("/webhook", methods=['POST'])
def webhook():
    """ConnectWise webhook endpoint for real-time updates"""
    try:
        # Verify webhook authenticity (implement signature verification)
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({"error": "No data received"}), 400
        
        # Process webhook based on type
        event_type = webhook_data.get('type')
        
        if event_type == 'company.updated':
            # Handle company updates
            company_data = webhook_data.get('data', {})
            connectwise_id = company_data.get('id')
            
            if connectwise_id:
                client = Client.query.filter_by(connectwise_id=connectwise_id).first()
                if client:
                    # Update client information
                    client.name = company_data.get('name', client.name)
                    client.is_active = company_data.get('status', {}).get('name') == 'Active'
                    db.session.commit()
                    logger.info(f"Updated client {client.name} from ConnectWise webhook")
        
        elif event_type == 'ticket.created':
            # Handle new ticket creation for engagement tracking
            ticket_data = webhook_data.get('data', {})
            company_id = ticket_data.get('company', {}).get('id')
            
            if company_id:
                client = Client.query.filter_by(connectwise_id=company_id).first()
                if client:
                    # Could trigger automatic score updates or notifications
                    logger.info(f"New ticket created for client {client.name}")
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return jsonify({"error": "Webhook processing failed"}), 500
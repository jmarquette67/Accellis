"""
CrewHu CSAT Integration for Accellis Client Engagement Platform

This module handles integration with CrewHu for customer satisfaction scoring.
CrewHu provides the Support Engagement Satisfaction metric that complements
the ConnectWise PSA integration for comprehensive client engagement scoring.
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models import Client, db

logger = logging.getLogger(__name__)

class CrewHuAPI:
    """CrewHu API client for CSAT data integration"""
    
    def __init__(self):
        self.base_url = os.environ.get('CREWHU_BASE_URL', 'https://api.crewhu.com')
        self.api_key = os.environ.get('CREWHU_API_KEY')
        self.company_id = os.environ.get('CREWHU_COMPANY_ID')
        
        if not self.api_key:
            logger.warning("CrewHu API key not configured - CSAT integration disabled")
            
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def test_connection(self) -> Dict:
        """Test CrewHu API connection"""
        if not self.api_key:
            return {"status": "error", "message": "CrewHu API key not configured"}
        
        try:
            url = f"{self.base_url}/api/v1/health"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return {"status": "success", "message": "CrewHu connection successful"}
        except requests.exceptions.RequestException as e:
            logger.error(f"CrewHu connection test failed: {e}")
            return {"status": "error", "message": f"Connection failed: {str(e)}"}
    
    def get_client_csat_scores(self, client_name: str = None, days_back: int = 30) -> List[Dict]:
        """
        Get CSAT scores for clients from CrewHu
        
        Args:
            client_name: Specific client name to filter by
            days_back: Number of days to look back for CSAT data
            
        Returns:
            List of CSAT records with client mapping
        """
        if not self.api_key:
            logger.warning("CrewHu API key not configured")
            return []
        
        try:
            url = f"{self.base_url}/api/v1/csat/scores"
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            params = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'company_id': self.company_id
            }
            
            if client_name:
                params['client_name'] = client_name
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json().get('scores', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching CrewHu CSAT scores: {e}")
            return []
    
    def get_client_satisfaction_score(self, client_name: str, days_back: int = 30) -> Optional[float]:
        """
        Get average satisfaction score for a specific client
        
        Args:
            client_name: Name of the client to get CSAT for
            days_back: Number of days to look back
            
        Returns:
            Average CSAT score (1-5 scale) or None if no data
        """
        try:
            csat_data = self.get_client_csat_scores(client_name, days_back)
            
            if not csat_data:
                logger.info(f"No CSAT data found for client: {client_name}")
                return None
            
            # Calculate average from all CSAT responses
            scores = [record.get('score', 0) for record in csat_data if record.get('score')]
            
            if scores:
                avg_score = sum(scores) / len(scores)
                # Ensure score is in 1-5 range for Accellis scoring system
                return max(1, min(5, round(avg_score)))
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating satisfaction score for {client_name}: {e}")
            return None


class CrewHuDataSync:
    """Handles synchronization of CSAT data from CrewHu to Accellis"""
    
    def __init__(self):
        self.crewhu_api = CrewHuAPI()
    
    def sync_satisfaction_scores(self, days_back: int = 30) -> Dict:
        """
        Sync CSAT scores from CrewHu for all active clients
        
        Args:
            days_back: Number of days to look back for CSAT data
            
        Returns:
            Dictionary with sync results
        """
        try:
            if not self.crewhu_api.api_key:
                return {"status": "error", "message": "CrewHu API key not configured"}
            
            # Get all active clients
            active_clients = Client.query.filter_by(is_active=True).all()
            
            updated_count = 0
            skipped_count = 0
            
            for client in active_clients:
                # Get CSAT score from CrewHu
                csat_score = self.crewhu_api.get_client_satisfaction_score(client.name, days_back)
                
                if csat_score is not None:
                    # Store CSAT score - this would typically update a scoresheet
                    # For now, we'll log it and prepare for scoresheet integration
                    logger.info(f"Client {client.name}: CSAT score {csat_score}")
                    updated_count += 1
                else:
                    logger.debug(f"No CSAT data for client: {client.name}")
                    skipped_count += 1
            
            return {
                "status": "success",
                "updated": updated_count,
                "skipped": skipped_count,
                "total": len(active_clients)
            }
            
        except Exception as e:
            logger.error(f"Error syncing CrewHu CSAT scores: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_satisfaction_metric_for_client(self, client_id: int, days_back: int = 30) -> Optional[int]:
        """
        Get Support Engagement Satisfaction metric for a specific client
        
        Args:
            client_id: Accellis client ID
            days_back: Number of days to look back
            
        Returns:
            Satisfaction score (1-5) or None if no data
        """
        try:
            client = Client.query.get(client_id)
            if not client:
                return None
            
            return self.crewhu_api.get_client_satisfaction_score(client.name, days_back)
            
        except Exception as e:
            logger.error(f"Error getting satisfaction metric for client {client_id}: {e}")
            return None


# Integration utility functions
def setup_crewhu_integration():
    """Initialize CrewHu integration"""
    try:
        crewhu_api = CrewHuAPI()
        connection_test = crewhu_api.test_connection()
        
        if connection_test["status"] == "success":
            logger.info("CrewHu integration initialized successfully")
            return {"status": "success", "message": "CrewHu integration ready"}
        else:
            logger.warning(f"CrewHu integration setup failed: {connection_test['message']}")
            return connection_test
            
    except Exception as e:
        logger.error(f"Error setting up CrewHu integration: {e}")
        return {"status": "error", "message": str(e)}


def test_crewhu_connection():
    """Test CrewHu API connection"""
    crewhu_api = CrewHuAPI()
    return crewhu_api.test_connection()


def get_client_csat_score(client_id: int, days_back: int = 30) -> Optional[int]:
    """
    Get CSAT score for a client from CrewHu
    
    Args:
        client_id: Accellis client ID
        days_back: Days to look back for CSAT data
        
    Returns:
        CSAT score (1-5) or None
    """
    sync = CrewHuDataSync()
    return sync.get_satisfaction_metric_for_client(client_id, days_back)
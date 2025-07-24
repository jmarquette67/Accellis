"""
ConnectWise API Integration for Accellis Client Engagement Platform
Handles authentication, data sync, and API communication with ConnectWise PSA
"""

import requests
import base64
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app import db
from models import Client, User, Score, Metric
import logging

logger = logging.getLogger(__name__)

class ConnectWiseAPI:
    """ConnectWise REST API client for data synchronization"""
    
    def __init__(self):
        # ConnectWise API configuration - set via environment variables
        self.base_url = os.environ.get('CONNECTWISE_BASE_URL', '')  # e.g., https://api-na.myconnectwise.net
        self.company_id = os.environ.get('CONNECTWISE_COMPANY_ID', '')
        self.public_key = os.environ.get('CONNECTWISE_PUBLIC_KEY', '')
        self.private_key = os.environ.get('CONNECTWISE_PRIVATE_KEY', '')
        self.client_id = os.environ.get('CONNECTWISE_CLIENT_ID', '')
        
        # API version and endpoints
        self.api_version = 'v4_6_release'
        self.session = requests.Session()
        self._setup_authentication()
    
    def _setup_authentication(self):
        """Setup ConnectWise API authentication headers"""
        if not all([self.company_id, self.public_key, self.private_key, self.client_id]):
            logger.warning("ConnectWise credentials not fully configured")
            return
        
        # Create authentication string
        auth_string = f"{self.company_id}+{self.public_key}:{self.private_key}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # Set session headers
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}',
            'ClientId': self.client_id,
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.connectwise.com+json; version={}'.format(self.api_version)
        })
    
    def test_connection(self) -> Dict:
        """Test ConnectWise API connectivity"""
        try:
            url = f"{self.base_url}/{self.api_version}/system/info"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except Exception as e:
            logger.error(f"ConnectWise connection test failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_companies(self, page_size: int = 100) -> List[Dict]:
        """Retrieve companies (clients) from ConnectWise"""
        try:
            url = f"{self.base_url}/{self.api_version}/company/companies"
            params = {
                'pageSize': page_size,
                'conditions': 'status/id=1'  # Active companies only
            }
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ConnectWise companies: {e}")
            return []
    
    def get_company_contacts(self, company_id: int) -> List[Dict]:
        """Get contacts for a specific company"""
        try:
            url = f"{self.base_url}/{self.api_version}/company/companies/{company_id}/contacts"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching contacts for company {company_id}: {e}")
            return []
    
    def get_tickets(self, company_id: int = None, days_back: int = 30) -> List[Dict]:
        """Retrieve service tickets, optionally filtered by company"""
        try:
            url = f"{self.base_url}/{self.api_version}/service/tickets"
            
            # Build conditions for filtering
            conditions = []
            if company_id:
                conditions.append(f"company/id={company_id}")
            
            # Filter by date range
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
            conditions.append(f"dateEntered>=[\{start_date}]")
            
            params = {
                'pageSize': 1000,
                'conditions': ' and '.join(conditions) if conditions else None
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ConnectWise tickets: {e}")
            return []
    
    def get_time_entries(self, company_id: int = None, days_back: int = 30) -> List[Dict]:
        """Retrieve time entries for billing/project engagement analysis"""
        try:
            url = f"{self.base_url}/{self.api_version}/time/entries"
            
            conditions = []
            if company_id:
                conditions.append(f"company/id={company_id}")
            
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
            conditions.append(f"timeStart>=[\{start_date}]")
            
            params = {
                'pageSize': 1000,
                'conditions': ' and '.join(conditions) if conditions else None
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ConnectWise time entries: {e}")
            return []
    
    def get_agreements(self, company_id: int = None) -> List[Dict]:
        """Get managed service agreements for recurring revenue analysis"""
        try:
            url = f"{self.base_url}/{self.api_version}/finance/agreements"
            
            conditions = ["agreementStatus='Active'"]
            if company_id:
                conditions.append(f"company/id={company_id}")
            
            params = {
                'pageSize': 1000,
                'conditions': ' and '.join(conditions)
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ConnectWise agreements: {e}")
            return []


class ConnectWiseDataSync:
    """Handles synchronization between ConnectWise and Accellis data"""
    
    def __init__(self):
        self.cw_api = ConnectWiseAPI()
    
    def sync_clients(self) -> Dict:
        """Synchronize client data from ConnectWise to Accellis"""
        try:
            cw_companies = self.cw_api.get_companies()
            if not cw_companies:
                return {"status": "error", "message": "No companies retrieved from ConnectWise"}
            
            synced_count = 0
            updated_count = 0
            
            for cw_company in cw_companies:
                # Map ConnectWise company data to Accellis client
                client_data = {
                    'name': cw_company.get('name', ''),
                    'connectwise_id': cw_company.get('id'),
                    'industry': self._map_industry(cw_company.get('market', '')),
                    'contact_name': '',
                    'contact_email': '',
                    'contact_phone': '',
                    'is_active': cw_company.get('status', {}).get('name') == 'Active'
                }
                
                # Get primary contact information
                contacts = self.cw_api.get_company_contacts(cw_company['id'])
                if contacts:
                    primary_contact = contacts[0]  # Use first contact as primary
                    client_data.update({
                        'contact_name': f"{primary_contact.get('firstName', '')} {primary_contact.get('lastName', '')}".strip(),
                        'contact_email': primary_contact.get('email', ''),
                        'contact_phone': primary_contact.get('phone', '')
                    })
                
                # Check if client exists in Accellis
                existing_client = Client.query.filter_by(connectwise_id=cw_company['id']).first()
                
                if existing_client:
                    # Update existing client
                    for key, value in client_data.items():
                        if hasattr(existing_client, key) and value:
                            setattr(existing_client, key, value)
                    updated_count += 1
                else:
                    # Create new client
                    new_client = Client(**client_data)
                    db.session.add(new_client)
                    synced_count += 1
            
            db.session.commit()
            
            return {
                "status": "success",
                "synced": synced_count,
                "updated": updated_count,
                "total": len(cw_companies)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing clients from ConnectWise: {e}")
            return {"status": "error", "message": str(e)}
    
    def calculate_engagement_metrics(self, client_id: int, days_back: int = 30) -> Dict:
        """Calculate engagement metrics based on ConnectWise data"""
        try:
            client = Client.query.get(client_id)
            if not client or not client.connectwise_id:
                return {"status": "error", "message": "Client not found or missing ConnectWise ID"}
            
            # Get ConnectWise data for metrics calculation
            tickets = self.cw_api.get_tickets(client.connectwise_id, days_back)
            time_entries = self.cw_api.get_time_entries(client.connectwise_id, days_back)
            agreements = self.cw_api.get_agreements(client.connectwise_id)
            
            # Calculate metrics
            metrics = {}
            
            # Help Desk Usage (based on ticket volume)
            metrics['Help Desk Usage'] = min(5, len(tickets) // 2)  # 2+ tickets = 1 point, max 5
            
            # First Touch Resolution (tickets resolved quickly)
            quick_resolutions = sum(1 for t in tickets if self._is_quick_resolution(t))
            metrics['First Touch Resolution/Escalation'] = min(5, quick_resolutions)
            
            # Support Engagement Satisfaction - NOT included in ConnectWise integration
            # This metric requires CrewHu CSAT data integration
            # metrics['Support Engagement Satisfaction'] = None  # Handled by CrewHu
            
            # Project Engagement (based on billable time)
            total_hours = sum(entry.get('actualHours', 0) for entry in time_entries)
            if total_hours >= 40:
                metrics['Project Engagement'] = 5
            elif total_hours >= 20:
                metrics['Project Engagement'] = 4
            elif total_hours >= 10:
                metrics['Project Engagement'] = 3
            else:
                metrics['Project Engagement'] = 2
            
            # Procurement (based on agreement additions/changes)
            recent_agreements = [a for a in agreements if self._is_recent_agreement(a, days_back)]
            metrics['Procurement'] = min(5, len(recent_agreements))
            
            return {"status": "success", "metrics": metrics}
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    def _map_industry(self, cw_market: str) -> str:
        """Map ConnectWise market types to Accellis industry categories"""
        market_mapping = {
            'Legal': 'legal',
            'Healthcare': 'healthcare',
            'Manufacturing': 'manufacturing',
            'Retail': 'retail',
            'Financial': 'finance',
            'Education': 'education',
            'Non-Profit': 'nonprofit'
        }
        return market_mapping.get(cw_market, 'other')
    
    def _is_quick_resolution(self, ticket: Dict) -> bool:
        """Check if ticket was resolved quickly (within 4 hours)"""
        if not ticket.get('closedDate'):
            return False
        
        try:
            created = datetime.fromisoformat(ticket['dateEntered'].replace('Z', '+00:00'))
            closed = datetime.fromisoformat(ticket['closedDate'].replace('Z', '+00:00'))
            return (closed - created).total_seconds() <= 4 * 3600  # 4 hours
        except:
            return False
    
    def _calculate_avg_resolution_time(self, tickets: List[Dict]) -> float:
        """Calculate average resolution time in hours"""
        resolution_times = []
        
        for ticket in tickets:
            if ticket.get('closedDate'):
                try:
                    created = datetime.fromisoformat(ticket['dateEntered'].replace('Z', '+00:00'))
                    closed = datetime.fromisoformat(ticket['closedDate'].replace('Z', '+00:00'))
                    hours = (closed - created).total_seconds() / 3600
                    resolution_times.append(hours)
                except:
                    continue
        
        return sum(resolution_times) / len(resolution_times) if resolution_times else 999
    
    def _is_recent_agreement(self, agreement: Dict, days_back: int) -> bool:
        """Check if agreement was created/modified recently"""
        try:
            created_date = datetime.fromisoformat(agreement.get('dateEntered', '').replace('Z', '+00:00'))
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return created_date >= cutoff_date
        except:
            return False


# Integration utility functions
def setup_connectwise_integration():
    """Initialize ConnectWise integration with required database fields"""
    try:
        # Add ConnectWise ID field to Client model if it doesn't exist
        # This should be done through a proper migration in production
        from sqlalchemy import text
        
        # Check if connectwise_id column exists
        result = db.session.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'client' AND column_name = 'connectwise_id'
        """))
        
        if not result.fetchone():
            # Add ConnectWise ID column
            db.session.execute(text("ALTER TABLE client ADD COLUMN connectwise_id INTEGER UNIQUE"))
            db.session.commit()
            logger.info("Added ConnectWise ID column to client table")
        
        return {"status": "success", "message": "ConnectWise integration setup complete"}
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting up ConnectWise integration: {e}")
        return {"status": "error", "message": str(e)}
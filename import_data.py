#!/usr/bin/env python3
"""
Data import utility for Accellis Client Scoring Platform
Imports client engagement data from Excel files
"""

import pandas as pd
from app import app, db
from models import Client, Metric, Score
from datetime import datetime

def import_excel_data(file_path):
    """Import client data from Excel file"""
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        print(f"Successfully loaded Excel file with {len(df)} rows")
        
        # Extract metrics from the first column
        metrics_data = []
        for idx, row in df.iterrows():
            metric_name = str(row.iloc[0]).strip()
            if metric_name and metric_name != 'nan' and metric_name != 'Metric':
                # Look for description in nearby columns if available
                description = ""
                if len(df.columns) > 1:
                    desc_val = str(row.iloc[1]).strip()
                    if desc_val and desc_val != 'nan':
                        description = desc_val
                
                metrics_data.append({
                    'name': metric_name,
                    'description': description,
                    'row_index': idx
                })
        
        # Extract client names from the header row
        client_columns = []
        for col in df.columns:
            if col not in ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2'] and 'Unnamed:' not in str(col):
                if str(col).strip() and str(col) != 'nan':
                    client_name = str(col).strip().replace('Client Name: --->', '').strip()
                    if client_name and client_name != 'nan':
                        client_columns.append((col, client_name))
        
        print(f"Found {len(metrics_data)} metrics:")
        for metric in metrics_data:
            print(f"  - {metric['name']}: {metric['description']}")
        
        print(f"Found {len(client_columns)} client columns:")
        for original, clean in client_columns:
            print(f"  - {clean}")
        
        return df, client_columns, metrics_data
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None, None, None

def create_clients_from_excel(df, client_columns):
    """Create client records from Excel data"""
    created_clients = []
    
    for original_col, client_name in client_columns:
        # Check if client already exists
        existing_client = Client.query.filter_by(name=client_name).first()
        if not existing_client:
            # Create new client
            client = Client(
                name=client_name,
                hostname=client_name.lower().replace(' ', '-').replace("'", ''),
                ip_address='192.168.1.1',  # Default IP
                description=f'Client imported from Q1 2025 engagement data'
            )
            db.session.add(client)
            created_clients.append(client_name)
            print(f"Created client: {client_name}")
        else:
            print(f"Client already exists: {client_name}")
    
    try:
        db.session.commit()
        print(f"Successfully created {len(created_clients)} new clients")
        return created_clients
    except Exception as e:
        db.session.rollback()
        print(f"Error creating clients: {e}")
        return []

def create_metrics_from_excel(metrics_data):
    """Create metric records from Excel data with proper weighting"""
    created_metrics = []
    
    # Define default weights based on typical client engagement importance
    metric_weights = {
        '1. Help Desk Usage': 15,
        '2. Project Management': 20,
        '3. Strategic Planning': 25,
        '4. Communication Quality': 20,
        '5. Response Time': 20
    }
    
    for metric_info in metrics_data:
        metric_name = metric_info['name']
        
        # Check if metric already exists
        existing_metric = Metric.query.filter_by(name=metric_name).first()
        if not existing_metric:
            # Assign weight based on name or use default
            weight = metric_weights.get(metric_name, 20)  # Default 20%
            
            metric = Metric(
                name=metric_name,
                description=metric_info['description'] or f'Client engagement metric: {metric_name}',
                weight=weight,
                high_threshold=85,
                low_threshold=60
            )
            db.session.add(metric)
            created_metrics.append(metric_name)
            print(f"Created metric: {metric_name} (Weight: {weight}%)")
        else:
            print(f"Metric already exists: {metric_name}")
    
    try:
        db.session.commit()
        print(f"Successfully created {len(created_metrics)} new metrics")
        return created_metrics
    except Exception as e:
        db.session.rollback()
        print(f"Error creating metrics: {e}")
        return []

if __name__ == "__main__":
    with app.app_context():
        # Try to import the uploaded file
        file_path = "attached_assets/Client Engagement Q1 2025 (1).xlsx"
        result = import_excel_data(file_path)
        
        if result and len(result) == 3:
            df, client_columns, metrics_data = result
            print("\nFile imported successfully!")
            
            print("Creating metrics from spreadsheet...")
            created_metrics = create_metrics_from_excel(metrics_data)
            
            print("Creating client records...")
            created_clients = create_clients_from_excel(df, client_columns)
            
            print(f"\nImport complete!")
            print(f"Created {len(created_metrics)} metrics from your Q1 2025 data")
            print(f"Created {len(created_clients)} new clients from your Q1 2025 data")
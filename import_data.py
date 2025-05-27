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
        
        # Extract client names from the header row
        client_columns = []
        for col in df.columns:
            if col not in ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2'] and 'Unnamed:' not in str(col):
                if str(col).strip() and str(col) != 'nan':
                    client_name = str(col).strip().replace('Client Name: --->', '').strip()
                    if client_name and client_name != 'nan':
                        client_columns.append((col, client_name))
        
        print(f"Found {len(client_columns)} client columns:")
        for original, clean in client_columns:
            print(f"  - {clean}")
        
        return df, client_columns
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None, None

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

if __name__ == "__main__":
    with app.app_context():
        # Try to import the uploaded file
        file_path = "attached_assets/Client Engagement Q1 2025 (1).xlsx"
        df, client_columns = import_excel_data(file_path)
        
        if df is not None and client_columns:
            print("\nFile imported successfully!")
            print("Creating client records...")
            created_clients = create_clients_from_excel(df, client_columns)
            print(f"\nImport complete! Created {len(created_clients)} new clients from your Q1 2025 data.")
#!/usr/bin/env python3
"""AI Health Assistant - Main Entry Point.
Run this file to start the application: python run.py
On first run, it creates the database and seeds demo data.
"""
import os
import sys

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from backend.app import create_app
from backend.config import config
from backend import db as database
from database.seed import seed_database

def main():
    # Create Flask app
    app = create_app()
    
    # Initialize database on first run
    print('\n=== AI Health Assistant ===')
    print(f'  Database: {config.DB_TYPE}')
    print(f'  AI Mode:  {config.AI_MODE}')
    
    # Auto-switch to demo mode if no API key
    if config.AI_MODE == 'openai' and not config.OPENAI_API_KEY:
        print('  Warning: No OPENAI_API_KEY found, switching to demo mode')
        config.AI_MODE = 'demo'
    
    # Create tables and seed data
    conn = database.get_connection()
    try:
        if not database.check_tables_exist(conn):
            print('  Creating database tables...')
            database.init_db(conn)
        
        if database.count_users(conn) == 0:
            print('  Seeding demo data...')
            seed_database(conn)
        else:
            print(f'  Database has {database.count_users(conn)} users')
    finally:
        database.close_connection(conn)
    
    print(f'\n  Open http://localhost:5000 in your browser')
    print('  Press Ctrl+C to stop\n')
    
    # Run Flask
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()

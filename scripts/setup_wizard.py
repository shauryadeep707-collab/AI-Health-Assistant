#!/usr/bin/env python3
"""
Setup Wizard for AI Health Assistant.
Guides you through configuring the application step by step.
Run: python scripts/setup_wizard.py
"""

import os
import sys
import secrets
import shutil

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)


def print_banner():
    print('\n' + '=' * 50)
    print('  AI Health Assistant - Setup Wizard')
    print('=' * 50 + '\n')


def ensure_env_file():
    """Copy .env.example to .env if it doesn't exist."""
    env_path = os.path.join(PROJECT_ROOT, '.env')
    example_path = os.path.join(PROJECT_ROOT, '.env.example')

    if os.path.exists(env_path):
        print('[OK] .env file exists')
        return env_path

    if os.path.exists(example_path):
        shutil.copy(example_path, env_path)
        print('[OK] Created .env from .env.example')
    else:
        # Create a minimal .env
        with open(env_path, 'w') as f:
            f.write('SECRET_KEY=\nAI_MODE=demo\n')
        print('[OK] Created minimal .env file')

    return env_path


def update_env(env_path, key, value):
    """Update a single key in the .env file."""
    lines = []
    found = False

    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith(f'{key}=') or line.strip().startswith(f'{key} ='):
            new_lines.append(f'{key}={value}\n')
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f'{key}={value}\n')

    with open(env_path, 'w') as f:
        f.writelines(new_lines)


def setup_secret_key(env_path):
    """Generate a cryptographically secure secret key."""
    key = secrets.token_hex(32)
    update_env(env_path, 'SECRET_KEY', key)
    print('[OK] Generated secure SECRET_KEY')


def setup_ai_mode(env_path):
    """Ask the user which AI mode to use."""
    print('\nAI Mode Configuration:')
    print('  1. Demo mode (no API key needed - works offline)')
    print('  2. OpenAI API (requires an API key and billing)')

    choice = input('\nSelect mode [1]: ').strip() or '1'

    if choice == '2':
        update_env(env_path, 'AI_MODE', 'openai')
        api_key = input('Enter your OpenAI API key: ').strip()
        if api_key:
            update_env(env_path, 'OPENAI_API_KEY', api_key)
            print('[OK] OpenAI API key configured')
        else:
            print('[!] No key entered - demo mode will be used as fallback')

        model = input('OpenAI model [gpt-3.5-turbo]: ').strip() or 'gpt-3.5-turbo'
        update_env(env_path, 'OPENAI_MODEL', model)
    else:
        update_env(env_path, 'AI_MODE', 'demo')
        print('[OK] Demo mode selected (no API key needed)')


def setup_database(env_path):
    """Ask about database configuration."""
    print('\nDatabase Configuration:')
    print('  1. SQLite (local file, no setup needed)')
    print('  2. PostgreSQL (Supabase or other cloud DB)')

    choice = input('\nSelect database [1]: ').strip() or '1'

    if choice == '2':
        db_url = input('Enter PostgreSQL connection URL: ').strip()
        if db_url:
            update_env(env_path, 'DATABASE_URL', db_url)
            print('[OK] PostgreSQL configured')
        else:
            print('[!] No URL entered - using SQLite')
    else:
        print('[OK] Using SQLite (local database)')


def test_database():
    """Test the database connection."""
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

        from backend.config import config
        from backend import db as database

        conn = database.get_connection()
        database.close_connection(conn)
        print(f'[OK] Database connection works ({config.DB_TYPE})')
        return True
    except Exception as e:
        print(f'[ERROR] Database connection failed: {e}')
        return False


def create_tables():
    """Create database tables."""
    try:
        from backend import db as database
        conn = database.get_connection()
        database.init_db(conn)
        database.close_connection(conn)
        print('[OK] Database tables created')
        return True
    except Exception as e:
        print(f'[ERROR] Failed to create tables: {e}')
        return False


def seed_data():
    """Seed demo data."""
    try:
        from backend import db as database
        from database.seed import seed_database

        conn = database.get_connection()
        seed_database(conn)
        database.close_connection(conn)
        print('[OK] Demo data seeded')
        return True
    except Exception as e:
        print(f'[ERROR] Failed to seed data: {e}')
        return False


def run_health_check():
    """Run a basic health check."""
    try:
        from backend import db as database
        conn = database.get_connection()
        row = database.fetch_one(conn, 'SELECT 1 as ok')
        user_count = database.count_users(conn)
        database.close_connection(conn)
        print(f'[OK] Health check passed - {user_count} users in database')
        return True
    except Exception as e:
        print(f'[ERROR] Health check failed: {e}')
        return False


def main():
    print_banner()

    # Step 1: Create .env file
    print('Step 1: Environment file')
    env_path = ensure_env_file()

    # Step 2: Generate secret key
    print('\nStep 2: Secret key')
    setup_secret_key(env_path)

    # Step 3: AI mode
    print('\nStep 3: AI mode')
    setup_ai_mode(env_path)

    # Step 4: Database
    print('\nStep 4: Database')
    setup_database(env_path)

    # Reload env after changes
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'), override=True)

    # Step 5: Test connection
    print('\nStep 5: Testing database connection')
    if test_database():
        # Step 6: Create tables
        print('\nStep 6: Creating tables')
        if create_tables():
            # Step 7: Seed data
            print('\nStep 7: Seeding demo data')
            seed_data()

    # Step 8: Health check
    print('\nStep 8: Health check')
    run_health_check()

    # Summary
    print('\n' + '=' * 50)
    print('  Setup Complete!')
    print('=' * 50)
    print('\nTo start the application:')
    print('  python run.py')
    print('\nThen open http://localhost:5000 in your browser')
    print('\nDemo logins:')
    print('  Patient: patient@demo.com / Patient@123')
    print('  Doctor:  doctor@demo.com / Doctor@123')
    print('  Admin:   admin@demo.com / Admin@123')
    print()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Environment Checker for AI Health Assistant.
Verifies all configuration settings are properly set.
Run: python scripts/check_env.py

SECURITY: This script NEVER prints secret values - only OK/MISSING status.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


def check_setting(name, required=True, is_secret=False):
    """Check if an environment variable is set. Never print secret values."""
    value = os.getenv(name, '')
    if value:
        # Show OK with masked value for secrets, actual value for non-secrets
        if is_secret:
            print(f'  {name}: OK (configured)')
        else:
            display = value if len(value) < 40 else value[:20] + '...'
            print(f'  {name}: OK ({display})')
        return True
    else:
        status = 'MISSING (required)' if required else 'MISSING (optional)'
        print(f'  {name}: {status}')
        return not required  # False only if required and missing


def test_database():
    """Test the database connection."""
    try:
        from backend.config import config
        from backend import db as database

        conn = database.get_connection()
        if config.DB_TYPE == 'oracle':
            row = database.fetch_one(conn, 'SELECT 1 as ok FROM dual')
        else:
            row = database.fetch_one(conn, 'SELECT 1 as ok')

        user_count = database.count_users(conn)
        database.close_connection(conn)
        print(f'  Database: OK ({config.DB_TYPE}, {user_count} users)')
        return True
    except Exception as e:
        print(f'  Database: ERROR - {e}')
        return False


def test_openai():
    """Test the OpenAI API key (if set)."""
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        print('  OpenAI: SKIPPED (no key set, using demo mode)')
        return True

    try:
        import urllib.request
        import json

        req = urllib.request.Request(
            'https://api.openai.com/v1/models',
            headers={'Authorization': f'Bearer {api_key}'}
        )
        response = urllib.request.urlopen(req, timeout=10)
        if response.status == 200:
            print('  OpenAI: OK (API key valid)')
            return True
    except Exception as e:
        print(f'  OpenAI: ERROR - {e}')
    return False


def main():
    print('\n' + '=' * 50)
    print('  AI Health Assistant - Environment Check')
    print('=' * 50 + '\n')

    all_ok = True

    # Required settings
    print('Required Settings:')
    all_ok &= check_setting('SECRET_KEY', required=True, is_secret=True)

    # AI settings
    print('\nAI Settings:')
    check_setting('AI_MODE', required=False)
    check_setting('OPENAI_API_KEY', required=False, is_secret=True)
    check_setting('OPENAI_MODEL', required=False)

    # Database settings
    print('\nDatabase Settings:')
    check_setting('DATABASE_URL', required=False, is_secret=True)
    check_setting('ORACLE_DSN', required=False)

    # Optional settings
    print('\nOptional Settings:')
    check_setting('GOOGLE_MAPS_API_KEY', required=False, is_secret=True)
    check_setting('EMERGENCY_NUMBER', required=False)
    check_setting('AMBULANCE_NUMBER', required=False)

    # Connection tests
    print('\nConnection Tests:')
    all_ok &= test_database()
    test_openai()

    # Summary
    print('\n' + '-' * 50)
    if all_ok:
        print('  Overall: ALL CHECKS PASSED [OK]')
    else:
        print('  Overall: SOME CHECKS FAILED [!]')
        print('  Run scripts/setup_wizard.py to configure')
    print()


if __name__ == '__main__':
    main()

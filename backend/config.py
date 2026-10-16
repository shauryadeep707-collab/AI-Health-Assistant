"""
Configuration module for AI Health Assistant.
Loads settings from .env file and provides sensible defaults.
WHY a Config class: centralises all settings so routes/services never read os.environ directly.
"""

import os
from dotenv import load_dotenv

# Load .env from the project root (one level up from backend/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    """All application configuration in one place."""

    # --- Flask ---
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # --- AI ---
    AI_MODE = os.getenv('AI_MODE', 'demo')  # 'openai' or 'demo'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    AI_DAILY_LIMIT = int(os.getenv('AI_DAILY_LIMIT', '30'))

    # --- Database ---
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    SQLITE_PATH = os.path.join(BASE_DIR, 'health_assistant.db')

    # Oracle (optional, only if college requires it)
    ORACLE_USER = os.getenv('ORACLE_USER', '')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', '')
    ORACLE_DSN = os.getenv('ORACLE_DSN', '')
    ORACLE_WALLET_DIR = os.getenv('ORACLE_WALLET_DIR', '')

    # --- Maps ---
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

    # --- Emergency ---
    EMERGENCY_NUMBER = os.getenv('EMERGENCY_NUMBER', '112')
    AMBULANCE_NUMBER = os.getenv('AMBULANCE_NUMBER', '108')

    # --- Rate Limiting ---
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES = 5

    # --- Risk Engine Thresholds ---
    # WHY separate thresholds: makes the scoring transparent and tunable without code changes
    RISK_LOW_MAX = 2       # score 0-2 → Low
    RISK_MEDIUM_MAX = 5    # score 3-5 → Medium, >=6 → Urgent

    # Scoring weights (each adds to the total risk score)
    RISK_WEIGHTS = {
        'duration_3d': 1,       # symptoms > 3 days
        'duration_7d': 2,       # symptoms > 7 days
        'severity_moderate': 1,  # self-reported moderate
        'severity_severe': 2,   # self-reported severe
        'worsening': 2,         # getting worse
        'temp_101': 1,          # fever >= 101°F
        'temp_103': 3,          # fever >= 103°F
        'age_risk': 1,          # age < 5 or > 60
        'chronic': 1,           # has chronic conditions
    }

    @property
    def DB_TYPE(self):
        """Determine which database engine to use."""
        if self.DATABASE_URL:
            return 'postgres'
        if self.ORACLE_DSN:
            return 'oracle'
        return 'sqlite'


# Singleton config instance used throughout the app
config = Config()

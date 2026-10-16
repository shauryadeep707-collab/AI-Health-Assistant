"""
Health Check route for AI Health Assistant.
Runs SELECT 1 to verify database connectivity.
Useful for Render / Railway uptime monitoring and preventing free cloud DB pause.
"""

from flask import Blueprint, jsonify, g
from backend.config import config
from backend import db as database

health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    Executes SELECT 1 on SQLite / PostgreSQL, or SELECT 1 FROM dual on Oracle.
    """
    try:
        db_type = config.DB_TYPE
        if db_type == 'oracle':
            database.fetch_one(g.db, "SELECT 1 FROM dual")
        else:
            database.fetch_one(g.db, "SELECT 1 as healthy")
        
        return jsonify({
            'ok': True,
            'data': {
                'status': 'healthy',
                'db': db_type,
                'ai_mode': config.AI_MODE
            }
        }), 200
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e),
            'data': {
                'status': 'unhealthy',
                'db': config.DB_TYPE
            }
        }), 500

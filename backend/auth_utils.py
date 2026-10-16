"""
Authentication utilities for AI Health Assistant.
Provides decorators and helpers for role-based access control.
WHY decorators: keeps auth checks out of route logic, one line per route.
"""

from functools import wraps
from flask import session, jsonify, request, g
from backend import db as database
from backend.config import config
from datetime import datetime, timedelta


def get_current_user():
    """Fetch the currently logged-in user from the database.
    Returns a dict with user info, or None if not logged in.
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    return database.fetch_one(g.db, 'SELECT id, name, email, role, is_verified FROM users WHERE id = ?', (user_id,))


def role_required(*roles):
    """Decorator that checks login status and role.
    Usage: @role_required('patient') or @role_required('patient', 'doctor')
    WHY: every API route needs auth checking; a decorator avoids repetition.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return jsonify({'ok': False, 'error': 'Please log in'}), 401
            if user['role'] not in roles:
                return jsonify({'ok': False, 'error': 'Access denied'}), 403
            # Pass user as first argument to the route function
            return f(user, *args, **kwargs)
        return wrapped
    return decorator


def check_rate_limit(email, ip):
    """Check if login attempts are within the allowed limit.
    Returns True if the user can attempt login, False if locked out.
    WHY: prevents brute-force password guessing.
    """
    cutoff = (datetime.utcnow() - timedelta(minutes=config.LOCKOUT_MINUTES)).isoformat()
    row = database.fetch_one(
        g.db,
        'SELECT COUNT(*) as cnt FROM login_attempts WHERE email = ? AND attempted_at > ?',
        (email, cutoff)
    )
    return (row['cnt'] if row else 0) < config.MAX_LOGIN_ATTEMPTS


def record_failed_attempt(email, ip):
    """Record a failed login attempt for rate limiting."""
    database.execute(
        g.db,
        'INSERT INTO login_attempts (email, ip_address) VALUES (?, ?)',
        (email, ip)
    )


def clear_attempts(email):
    """Remove failed attempts after a successful login."""
    database.execute(g.db, 'DELETE FROM login_attempts WHERE email = ?', (email,))


def check_ai_limit(user_id):
    """Check if the user has remaining AI calls for today.
    Returns True if under the daily limit.
    WHY: prevents abuse and controls API costs.
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    row = database.fetch_one(
        g.db,
        'SELECT COUNT(*) as cnt FROM ai_usage WHERE user_id = ? AND used_at > ?',
        (user_id, today_start)
    )
    return (row['cnt'] if row else 0) < config.AI_DAILY_LIMIT


def record_ai_usage(user_id):
    """Record one AI API call for rate tracking."""
    database.execute(
        g.db,
        'INSERT INTO ai_usage (user_id) VALUES (?)',
        (user_id,)
    )

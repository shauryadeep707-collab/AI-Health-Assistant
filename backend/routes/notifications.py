"""
Notifications and Knowledge Base retrieval routes for AI Health Assistant.
"""

from flask import Blueprint, request, jsonify, g
from backend.auth_utils import role_required
from backend.services.notification_service import get_user_notifications, mark_notification_read
from backend.services.knowledge_base import get_guidance, get_medicines

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications', methods=['GET'])
@role_required('patient', 'doctor', 'admin')
def list_notifications(user):
    """Fetch notifications for the logged-in user."""
    unread_only = request.args.get('unread') == 'true'
    notifications = get_user_notifications(g.db, user['id'], unread_only=unread_only)
    return jsonify({'ok': True, 'data': notifications})

@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@role_required('patient', 'doctor', 'admin')
def mark_read(user, notification_id):
    """Mark a notification as read."""
    mark_notification_read(g.db, notification_id, user['id'])
    return jsonify({'ok': True, 'data': {'message': 'Notification marked as read'}})

@notifications_bp.route('/api/guidance/<category>', methods=['GET'])
def fetch_guidance(category):
    """Fetch home-care guidance for low-risk scenarios."""
    guidance = get_guidance(category)
    return jsonify({'ok': True, 'data': guidance})

@notifications_bp.route('/api/medicines/<category>', methods=['GET'])
def fetch_medicines(category):
    """Fetch controlled OTC medicine info for low-risk scenarios."""
    medicines = get_medicines(category)
    return jsonify({'ok': True, 'data': medicines})

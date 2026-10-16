"""
Notification Service for AI Health Assistant.
Creates and manages in-app notifications for users (patients and doctors).
FIFO queue conceptually: pending notifications are retrieved oldest-to-newest or unread-first.
"""

from backend import db as database

def create_notification(db_conn, user_id, text, link=None):
    """
    Insert a new notification for a user.
    """
    return database.insert(
        db_conn,
        "INSERT INTO notifications (user_id, text, link, is_read) VALUES (?, ?, ?, 0)",
        (user_id, text, link)
    )

def get_user_notifications(db_conn, user_id, unread_only=False):
    """
    Retrieve notifications for a user.
    """
    if unread_only:
        return database.fetch_all(
            db_conn,
            "SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC",
            (user_id,)
        )
    return database.fetch_all(
        db_conn,
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
        (user_id,)
    )

def mark_notification_read(db_conn, notification_id, user_id):
    """
    Mark a single notification as read if it belongs to user_id.
    """
    database.execute(
        db_conn,
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
        (notification_id, user_id)
    )

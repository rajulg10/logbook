import logging
import sqlite3
from datetime import datetime
import os
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.database import get_db_connection, close_connection, get_user_by_id

logger = logging.getLogger(__name__)

def send_report_notification(user_id, subject, message):
    """
    Send a notification to a user about a report event
    
    Args:
        user_id (int): The ID of the user to notify
        subject (str): The notification subject
        message (str): The notification message
    
    Returns:
        bool: True if notification was successfully stored, False otherwise
    """
    try:
        conn, cursor = get_db_connection()
        
        # Check if we need to create the notifications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Insert the notification
        cursor.execute(
            "INSERT INTO notifications (user_id, subject, message) VALUES (?, ?, ?)",
            (user_id, subject, message)
        )
        
        conn.commit()
        close_connection(conn)
        
        logger.info(f"Notification sent to user {user_id}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

def get_user_notifications(user_id, include_read=False):
    """
    Get notifications for a specific user
    
    Args:
        user_id (int): The ID of the user
        include_read (bool): Whether to include already read notifications
    
    Returns:
        list: A list of notification dictionaries
    """
    try:
        conn, cursor = get_db_connection()
        
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"
        )
        if not cursor.fetchone():
            close_connection(conn)
            return []
        
        if include_read:
            cursor.execute(
                "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC",
                (user_id,)
            )
            
        notifications = cursor.fetchall()
        close_connection(conn)
        
        return [dict(notification) for notification in notifications]
        
    except Exception as e:
        logger.error(f"Error retrieving notifications: {e}")
        return []

def mark_notification_as_read(notification_id):
    """
    Mark a notification as read
    
    Args:
        notification_id (int): The ID of the notification to mark
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn, cursor = get_db_connection()
        
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,)
        )
        
        conn.commit()
        close_connection(conn)
        
        return True
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return False 
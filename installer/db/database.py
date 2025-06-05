import sqlite3
import os
from pathlib import Path
from datetime import datetime

def get_db_path():
    """Get the path to the SQLite database file"""
    db_dir = Path(__file__).resolve().parent
    return os.path.join(db_dir, 'logbook.db')

def get_db_connection():
    """Create a database connection and return the connection and cursor"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Enable row factory for dict-like access
    cursor = conn.cursor()
    return conn, cursor

def close_connection(conn):
    """Close the database connection"""
    if conn:
        conn.close()

# User management functions
def add_user(username, password_hash, role, email, emp_code="", designation=""):
    """Add a new user to the database"""
    conn, cursor = get_db_connection()
    try:
        cursor.execute('''
        INSERT INTO users (username, password_hash, role, email, emp_code, designation)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, role, email, emp_code, designation))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        close_connection(conn)

def delete_user(user_id):
    """Delete a user from the database"""
    conn, cursor = get_db_connection()
    try:
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            return False
            
        # Delete the user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        close_connection(conn)

def get_user_by_username(username):
    """Get a user by username"""
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    close_connection(conn)
    return dict(user) if user else None

def get_user_by_id(user_id):
    """Get a user by ID"""
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    close_connection(conn)
    return dict(user) if user else None

def get_user_name(user_id):
    """Get a user's username by ID"""
    user = get_user_by_id(user_id)
    if user:
        return user.get('username', 'Unknown')
    return 'Unknown'

def get_all_users():
    """Get all users"""
    conn, cursor = get_db_connection()
    cursor.execute('SELECT id, username, role, email, emp_code, designation, created_at FROM users')
    users = cursor.fetchall()
    close_connection(conn)
    return [dict(user) for user in users]

def update_user(user_id, username=None, password_hash=None, role=None, email=None, emp_code=None, designation=None):
    """Update user details in the database."""
    conn, cursor = get_db_connection()
    try:
        fields = []
        values = []
        if username is not None:
            fields.append("username = ?")
            values.append(username)
        if password_hash is not None:
            fields.append("password_hash = ?")
            values.append(password_hash)
        if role is not None:
            fields.append("role = ?")
            values.append(role)
        if email is not None:
            fields.append("email = ?")
            values.append(email)
        if emp_code is not None:
            fields.append("emp_code = ?")
            values.append(emp_code)
        if designation is not None:
            fields.append("designation = ?")
            values.append(designation)
        if not fields:
            return False
        values.append(user_id)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, tuple(values))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating user: {e}")
        return False
    finally:
        close_connection(conn)

# Template management functions
def add_template(name, file_path, uploaded_by):
    """
    Add a template to the database
    """
    try:
        conn, cursor = get_db_connection()
        
        # Insert new template
        cursor.execute(
            "INSERT INTO templates (name, file_path, uploaded_by) VALUES (?, ?, ?)",
            (name, file_path, uploaded_by)
        )
        
        template_id = cursor.lastrowid
        conn.commit()
        close_connection(conn)
        
        return template_id
    except Exception as e:
        print(f"Error adding template: {e}")
        return None

def delete_template(template_id):
    """
    Delete a template from the database
    """
    try:
        conn, cursor = get_db_connection()
        
        # Get file path for deletion
        cursor.execute("SELECT file_path FROM templates WHERE id = ?", (template_id,))
        template = cursor.fetchone()
        
        if not template:
            close_connection(conn)
            return False
        
        # Delete the template
        cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
        
        conn.commit()
        close_connection(conn)
        
        # Delete file if exists
        try:
            if os.path.exists(template['file_path']):
                os.remove(template['file_path'])
        except Exception as e:
            print(f"Error deleting template file: {e}")
        
        return True
    except Exception as e:
        print(f"Error deleting template: {e}")
        return False

def get_active_template():
    """Get templates that can be used (all templates)"""
    # Now returns all templates as all templates are treated as active
    return get_all_templates()

def is_template_active(template_id):
    """Check if a template is active (all templates are now active)"""
    # Now all templates are treated as active
    conn, cursor = get_db_connection()
    cursor.execute('SELECT id FROM templates WHERE id = ?', (template_id,))
    result = cursor.fetchone()
    close_connection(conn)
    return result is not None

def get_all_templates():
    """
    Get all templates
    """
    try:
        conn, cursor = get_db_connection()
        
        cursor.execute("SELECT * FROM templates")
        templates = cursor.fetchall()
        
        close_connection(conn)
        return templates
    except Exception as e:
        print(f"Error getting templates: {e}")
        return []

# Report management functions
def create_report(user_id, title):
    """Create a new report in draft status"""
    conn, cursor = get_db_connection()
    cursor.execute('''
    INSERT INTO reports (user_id, title, status, last_modified_by)
    VALUES (?, ?, 'draft', ?)
    ''', (user_id, title, user_id))
    conn.commit()
    report_id = cursor.lastrowid
    close_connection(conn)
    return report_id

def update_report_status(report_id, status, modified_by):
    """Update a report's status"""
    try:
        print(f"DEBUG: Inside update_report_status - report_id={report_id}, status={status}, modified_by={modified_by}")
        conn, cursor = get_db_connection()
        cursor.execute('''
        UPDATE reports 
        SET status = ?, last_modified_at = ?, last_modified_by = ?
        WHERE report_id = ?
        ''', (status, datetime.now(), modified_by, report_id))
        
        # Check if any rows were affected
        rows_affected = cursor.rowcount
        print(f"DEBUG: Rows affected by update: {rows_affected}")
        
        conn.commit()
        close_connection(conn)
        
        # Return True if at least one row was updated
        return rows_affected > 0
    except Exception as e:
        print(f"ERROR: Error updating report status: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def add_report_data(report_id, field_name, field_value):
    """Add or update a field in a report"""
    conn, cursor = get_db_connection()
    
    # Check if field already exists
    cursor.execute('''
    SELECT id FROM report_data
    WHERE report_id = ? AND field_name = ?
    ''', (report_id, field_name))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing field
        cursor.execute('''
        UPDATE report_data
        SET field_value = ?
        WHERE report_id = ? AND field_name = ?
        ''', (field_value, report_id, field_name))
    else:
        # Insert new field
        cursor.execute('''
        INSERT INTO report_data (report_id, field_name, field_value)
        VALUES (?, ?, ?)
        ''', (report_id, field_name, field_value))
    
    conn.commit()
    close_connection(conn)

def get_report(report_id):
    """Get a report by ID with all its data"""
    conn, cursor = get_db_connection()
    
    # Get report metadata
    cursor.execute('''
    SELECT r.*, u.username as creator_name, m.username as modifier_name, r.excel_file_path
    FROM reports r
    JOIN users u ON r.user_id = u.id
    LEFT JOIN users m ON r.last_modified_by = m.id
    WHERE r.report_id = ?
    ''', (report_id,))
    report = cursor.fetchone()
    
    if not report:
        close_connection(conn)
        return None
    
    report_dict = dict(report)
    
    # Get report data fields
    cursor.execute('''
    SELECT field_name, field_value
    FROM report_data
    WHERE report_id = ?
    ''', (report_id,))
    fields = cursor.fetchall()
    report_dict['fields'] = {field['field_name']: field['field_value'] for field in fields}
    
    # Get approval logs
    cursor.execute('''
    SELECT a.*, u.username as actor_name
    FROM approval_logs a
    JOIN users u ON a.action_by = u.id
    WHERE a.report_id = ?
    ORDER BY a.timestamp ASC
    ''', (report_id,))
    logs = cursor.fetchall()
    report_dict['approval_logs'] = [dict(log) for log in logs]
    
    close_connection(conn)
    return report_dict

def get_reports_by_status(status, user_id=None):
    """Get reports by status, optionally filtered by user"""
    conn, cursor = get_db_connection()
    
    if user_id:
        cursor.execute('''
        SELECT r.*, u.username as creator_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE r.status = ? AND r.user_id = ?
        ORDER BY r.created_at DESC
        ''', (status, user_id))
    else:
        cursor.execute('''
        SELECT r.*, u.username as creator_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE r.status = ?
        ORDER BY r.created_at DESC
        ''', (status,))
    
    reports = cursor.fetchall()
    close_connection(conn)
    return [dict(report) for report in reports]

def get_user_reports(user_id):
    """Get all reports created by a user"""
    conn, cursor = get_db_connection()
    cursor.execute('''
    SELECT r.*, u.username as creator_name
    FROM reports r
    JOIN users u ON r.user_id = u.id
    WHERE r.user_id = ?
    ORDER BY r.created_at DESC
    ''', (user_id,))
    reports = cursor.fetchall()
    close_connection(conn)
    return [dict(report) for report in reports]

def get_all_reports():
    """Get all reports in the system"""
    conn, cursor = get_db_connection()
    cursor.execute('''
    SELECT r.*, u.username as creator_name
    FROM reports r
    JOIN users u ON r.user_id = u.id
    ORDER BY r.created_at DESC
    ''')
    reports = cursor.fetchall()
    close_connection(conn)
    return [dict(report) for report in reports]

def add_approval_log(report_id, action_by, action, comments=None):
    """Add an approval log entry"""
    conn, cursor = get_db_connection()
    cursor.execute('''
    INSERT INTO approval_logs (report_id, action_by, action, comments)
    VALUES (?, ?, ?, ?)
    ''', (report_id, action_by, action, comments))
    conn.commit()
    close_connection(conn)

def get_leader_approval(report_id):
    """Get the leader approval log entry for a report"""
    conn, cursor = get_db_connection()
    cursor.execute('''
    SELECT a.*, u.username as actor_name
    FROM approval_logs a
    JOIN users u ON a.action_by = u.id
    WHERE a.report_id = ? AND a.action = 'approve_leader'
    ORDER BY a.timestamp DESC
    LIMIT 1
    ''', (report_id,))
    approval = cursor.fetchone()
    close_connection(conn)
    return dict(approval) if approval else None

# Offline email queue and processing
# Ensure email_queue table exists
conn, cursor = get_db_connection()
cursor.execute("""
CREATE TABLE IF NOT EXISTS email_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    admin_id INTEGER NOT NULL,
    pdf_path TEXT NOT NULL,
    queued_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT
)
""")
conn.commit()
close_connection(conn)

def add_email_queue(report_id, admin_id, pdf_path):
    """Add an email to the offline queue"""
    conn, cursor = get_db_connection()
    queued_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO email_queue (report_id, admin_id, pdf_path, queued_at, status) VALUES (?, ?, ?, ?, 'pending')",
        (report_id, admin_id, pdf_path, queued_at)
    )
    conn.commit()
    close_connection(conn)

def get_pending_email_queue():
    """Get all pending queued emails"""
    conn, cursor = get_db_connection()
    cursor.execute("SELECT * FROM email_queue WHERE status = 'pending'")
    rows = cursor.fetchall()
    close_connection(conn)
    return [dict(row) for row in rows]

def update_email_queue_status(queue_id, status, error_message=None):
    """Update the status of a queued email"""
    conn, cursor = get_db_connection()
    if error_message:
        cursor.execute(
            "UPDATE email_queue SET status = ?, error_message = ? WHERE id = ?",
            (status, error_message, queue_id)
        )
    else:
        cursor.execute("UPDATE email_queue SET status = ? WHERE id = ?", (status, queue_id))
    conn.commit()
    close_connection(conn)
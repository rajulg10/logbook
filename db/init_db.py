import sqlite3
import os
import sys
import datetime
from pathlib import Path

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

def get_db_path():
    """Get the path to the SQLite database file"""
    # Use the local appdata directory to ensure write permissions
    app_data_dir = Path(os.getenv('LOCALAPPDATA')) / 'LogbookApp'
    app_data_dir.mkdir(exist_ok=True, parents=True)
    
    # Set appropriate permissions (full control for the current user)
    try:
        import win32api
        import win32con
        import win32security
        
        # Get the current user's SID
        username = os.getlogin()
        domain = os.getenv('USERDOMAIN')
        user_sid = win32security.LookupAccountName(domain, username)[0]
        
        # Set full control for the current user
        sd = win32security.GetFileSecurity(str(app_data_dir), win32security.DACL_SECURITY_INFORMATION)
        dacl = win32security.ACL()
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, win32con.GENERIC_ALL, user_sid)
        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        win32security.SetFileSecurity(str(app_data_dir), win32security.DACL_SECURITY_INFORMATION, sd)
    except ImportError:
        # If pywin32 is not available, just continue with default permissions
        pass
    
    return str(app_data_dir / 'logbook.db')

def init_db():
    """Initialize the database with necessary tables"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT NOT NULL,
        emp_code TEXT,
        designation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create reports table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'draft',
        version INTEGER DEFAULT 1,
        last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_modified_by INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (last_modified_by) REFERENCES users (id)
    )
    ''')
    
    # Create report_data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS report_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL,
        field_name TEXT NOT NULL,
        field_value TEXT,
        FOREIGN KEY (report_id) REFERENCES reports (report_id)
    )
    ''')
    
    # Create approval_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS approval_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL,
        action_by INTEGER NOT NULL,
        action TEXT NOT NULL,
        comments TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports (report_id),
        FOREIGN KEY (action_by) REFERENCES users (id)
    )
    ''')
    
    # Create templates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        uploaded_by INTEGER NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (uploaded_by) REFERENCES users (id)
    )
    ''')
    
    # Create email_queue table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        pdf_path TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports (report_id),
        FOREIGN KEY (admin_id) REFERENCES users (id)
    )
    ''')
    
    # Add excel_file_path column to reports table if it doesn't exist
    cursor.execute('''
    PRAGMA table_info(reports)
    ''')
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'excel_file_path' not in columns:
        cursor.execute('''
        ALTER TABLE reports ADD COLUMN excel_file_path TEXT
        ''')
    
    # Insert default admin user if it doesn't exist
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, role, email, emp_code, designation)
    VALUES ('admin', '$2b$12$IRy/60CFikmkIE/0t81My.VG/8S/661J1XbhmkfHbNgde.3O/HKFy', 'admin', 'admin@example.com', '', '')
    ''')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully")
    print("Default admin user created:")
    print("Username: admin")
    print("Password: admin123")

if __name__ == "__main__":
    init_db() 
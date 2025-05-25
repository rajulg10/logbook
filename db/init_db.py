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
    db_dir = Path(__file__).resolve().parent
    return os.path.join(db_dir, 'logbook.db')

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
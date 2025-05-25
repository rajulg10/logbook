import sqlite3
import os
import sys
from pathlib import Path

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.init_db import get_db_path

def update_database():
    """Update the database to ensure all users have emp_code and designation fields"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Check if the emp_code column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    # Add the new columns if they don't exist
    if 'emp_code' not in column_names:
        print("Adding emp_code column to users table...")
        cursor.execute('ALTER TABLE users ADD COLUMN emp_code TEXT')
    
    if 'designation' not in column_names:
        print("Adding designation column to users table...")
        cursor.execute('ALTER TABLE users ADD COLUMN designation TEXT')
    
    # Update existing users to have empty values for the new fields
    print("Updating existing users with empty values for new fields...")
    cursor.execute('''
    UPDATE users 
    SET emp_code = '', designation = ''
    WHERE emp_code IS NULL OR designation IS NULL
    ''')
    
    conn.commit()
    conn.close()
    
    print("Database update completed successfully!")

if __name__ == "__main__":
    update_database() 
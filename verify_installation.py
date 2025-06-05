#!/usr/bin/env python3
"""
Verify Logbook installation and functionality.

This script verifies that:
1. The application is properly installed
2. Database is accessible and initialized
3. Login functionality works
4. Core features are functional
"""

import os
import sys
import sqlite3
import tempfile
import shutil
from pathlib import Path
import json
import subprocess
import time

# ANSI color codes for console output
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color

def print_section(title):
    """Print a section header."""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{title.upper()}{NC}")
    print(f"{BLUE}{'='*60}{NC}")

def print_status(message, status):
    """Print a status message with colored status."""
    status_color = GREEN if status == "PASS" else RED
    print(f"{message.ljust(60)} [{status_color}{status}{NC}]")

class InstallationVerifier:
    """Verify Logbook installation and functionality."""
    
    def __init__(self):
        """Initialize the verifier."""
        self.install_dir = Path(os.getenv('PROGRAMFILES')) / 'Logbook'
        self.app_data_dir = Path(os.getenv('LOCALAPPDATA')) / 'LogbookApp'
        self.db_path = self.app_data_dir / 'logbook.db'
        self.test_username = "test_verification_user"
        self.test_password = "Test@123"
        self.test_email = "test_verification@example.com"
        self.test_report_title = "Verification Test Report"
        self.test_template_name = "Verification Test Template"
    
    def verify_installation(self):
        """Verify the Logbook installation."""
        print_section("Verifying Installation")
        
        # Check installation directory
        if not self.install_dir.exists():
            print_status("Installation directory exists", "FAIL")
            return False
        print_status("Installation directory exists", "PASS")
        
        # Check main executable
        exe_path = self.install_dir / 'dist' / 'Logbook.exe'
        if not exe_path.exists():
            print_status("Main executable exists", "FAIL")
            return False
        print_status("Main executable exists", "PASS")
        
        # Check database directory
        if not self.app_data_dir.exists():
            print_status("Application data directory exists", "FAIL")
            return False
        print_status("Application data directory exists", "PASS")
        
        return True
    
    def verify_database(self):
        """Verify database connectivity and schema."""
        print_section("Verifying Database")
        
        # Check if database exists
        if not self.db_path.exists():
            print_status("Database file exists", "FAIL")
            return False
        print_status("Database file exists", "PASS")
        
        # Check database schema
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Check required tables
            tables = ['users', 'reports', 'report_data', 'templates', 'email_queue']
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            all_tables_found = True
            for table in tables:
                if table not in existing_tables:
                    print_status(f"Table '{table}' exists", "FAIL")
                    all_tables_found = False
                else:
                    print_status(f"Table '{table}' exists", "PASS")
            
            if not all_tables_found:
                return False
                
            return True
            
        except Exception as e:
            print(f"{RED}Database verification failed: {e}{NC}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def test_application(self):
        """Test the application functionality."""
        print_section("Testing Application Functionality")
        
        # Add a test user
        if not self._add_test_user():
            return False
        
        # Test login
        if not self._test_login():
            return False
        
        # Test report creation
        if not self._test_report_creation():
            return False
        
        # Test template management
        if not self._test_template_management():
            return False
        
        return True
    
    def _add_test_user(self):
        """Add a test user to the database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Delete test user if exists
            cursor.execute("DELETE FROM users WHERE username = ?", (self.test_username,))
            
            # Add test user
            from passlib.hash import bcrypt
            hashed_password = bcrypt.hash(self.test_password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, email)
                VALUES (?, ?, ?, ?)
            """, (self.test_username, hashed_password, 'admin', self.test_email))
            
            conn.commit()
            print_status("Test user created", "PASS")
            return True
            
        except Exception as e:
            print_status(f"Failed to create test user: {e}", "FAIL")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _test_login(self):
        """Test login functionality."""
        try:
            # Import the auth module
            sys.path.append(str(self.install_dir / 'dist'))
            from db.database import get_user_by_username
            from utils.auth import Auth
            
            auth = Auth()
            
            # Test valid login
            user = auth.login(self.test_username, self.test_password)
            if not user or user['username'] != self.test_username:
                print_status("Login with valid credentials", "FAIL")
                return False
            print_status("Login with valid credentials", "PASS")
            
            # Test invalid password
            user = auth.login(self.test_username, "wrong_password")
            if user is not None:
                print_status("Login with invalid password", "FAIL")
                return False
            print_status("Login with invalid password", "PASS")
            
            return True
            
        except Exception as e:
            print_status(f"Login test failed: {e}", "FAIL")
            return False
    
    def _test_report_creation(self):
        """Test report creation and management."""
        try:
            # Import required modules
            sys.path.append(str(self.install_dir / 'dist'))
            from db.database import (
                create_report, add_report_data, get_report,
                update_report_status
            )
            
            # Get test user ID
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (self.test_username,))
            user = cursor.fetchone()
            
            if not user:
                print_status("Test user not found", "FAIL")
                return False
                
            user_id = user[0]
            
            # Create a test report
            report_id = create_report(
                user_id=user_id,
                title=self.test_report_title
            )
            
            if not report_id:
                print_status("Failed to create test report", "FAIL")
                return False
            
            # Add report data
            add_report_data(report_id, "test_field", "test_value")
            
            # Verify report
            report = get_report(report_id)
            if not report or report['title'] != self.test_report_title:
                print_status("Failed to retrieve test report", "FAIL")
                return False
            
            # Update report status
            update_report_status(report_id, 'submitted', user_id)
            report = get_report(report_id)
            if report['status'] != 'submitted':
                print_status("Failed to update report status", "FAIL")
                return False
            
            print_status("Report creation and management", "PASS")
            return True
            
        except Exception as e:
            print_status(f"Report test failed: {e}", "FAIL")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _test_template_management(self):
        """Test template management functionality."""
        try:
            # Import required modules
            sys.path.append(str(self.install_dir / 'dist'))
            from db.database import add_template, get_all_templates, delete_template
            
            # Create a test template file
            templates_dir = self.app_data_dir / 'templates'
            templates_dir.mkdir(exist_ok=True)
            
            template_path = templates_dir / 'test_template.docx'
            with open(template_path, 'w') as f:
                f.write("Test template content")
            
            # Add template
            template_id = add_template(
                name=self.test_template_name,
                file_path=str(template_path),
                uploaded_by=1  # Assuming admin user has ID 1
            )
            
            if not template_id:
                print_status("Failed to add template", "FAIL")
                return False
            
            # Verify template was added
            templates = get_all_templates()
            template_names = [t['name'] for t in templates]
            
            if self.test_template_name not in template_names:
                print_status("Template not found in database", "FAIL")
                return False
            
            # Clean up
            delete_template(template_id)
            
            print_status("Template management", "PASS")
            return True
            
        except Exception as e:
            print_status(f"Template test failed: {e}", "FAIL")
            return False

def main():
    """Main function to run all verification steps."""
    print(f"{YELLOW}=== Logbook Installation Verification ==={NC}\n")
    
    verifier = InstallationVerifier()
    
    # Run all verification steps
    steps = [
        ("Installation", verifier.verify_installation),
        ("Database", verifier.verify_database),
        ("Application", verifier.test_application)
    ]
    
    all_passed = True
    for name, step in steps:
        print_section(f"Verifying {name}")
        if not step():
            print(f"{RED}❌ {name} verification failed{NC}")
            all_passed = False
        else:
            print(f"{GREEN}✅ {name} verification passed{NC}")
    
    # Print final result
    print("\n" + "="*60)
    if all_passed:
        print(f"{GREEN}✅ ALL VERIFICATIONS PASSED SUCCESSFULLY!{NC}")
        print(f"{GREEN}The Logbook application is properly installed and functioning.{NC}")
        return 0
    else:
        print(f"{RED}❌ SOME VERIFICATIONS FAILED!{NC}")
        print(f"{YELLOW}Please check the error messages above and fix the issues.{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

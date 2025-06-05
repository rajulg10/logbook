#!/usr/bin/env python3
"""
Test script to verify Logbook application functionality.

This script tests:
1. Database connectivity and initialization
2. User authentication (login/register)
3. Report creation and management
4. Template management
5. Email queue functionality
"""

import os
import sys
import sqlite3
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import application modules
from db.database import (
    get_db_path, get_db_connection, close_connection,
    add_user, get_user_by_username, update_user, delete_user,
    create_report, update_report_status, add_report_data, get_report,
    add_template, delete_template, get_all_templates
)
from utils.auth import Auth

class TestDatabase(unittest.TestCase):
    """Test database functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create a temporary directory for the test database
        cls.test_dir = tempfile.mkdtemp()
        os.environ['LOCALAPPDATA'] = cls.test_dir
        
        # Initialize the database
        from db.init_db import init_db
        cls.db_path = get_db_path()
        init_db()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        # Remove the temporary directory
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def setUp(self):
        """Set up test data."""
        self.conn, self.cursor = get_db_connection()
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up test data
        self.cursor.execute("DELETE FROM users WHERE username LIKE 'test_%'")
        self.cursor.execute("DELETE FROM reports WHERE title LIKE 'Test Report%'")
        self.cursor.execute("DELETE FROM templates WHERE name LIKE 'Test Template%'")
        self.conn.commit()
        close_connection(self.conn)
    
    def test_database_connection(self):
        """Test database connection and schema."""
        # Check if tables exist
        tables = ['users', 'reports', 'report_data', 'approval_logs', 'templates', 'email_queue']
        for table in tables:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            self.assertIsNotNone(self.cursor.fetchone(), f"Table '{table}' does not exist")
        
        print("\nDatabase connection and schema verified")


class TestAuthentication(unittest.TestCase):
    """Test user authentication."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create a temporary directory for the test database
        cls.test_dir = tempfile.mkdtemp()
        os.environ['LOCALAPPDATA'] = cls.test_dir
        
        # Initialize the database
        from db.init_db import init_db
        cls.db_path = get_db_path()
        init_db()
        
        # Create test user
        cls.test_username = "test_user"
        cls.test_password = "Test@123"
        cls.test_email = "test@example.com"
        
        # Add test user
        cls.auth = Auth()
        cls.auth.register_user(
            username=cls.test_username,
            password=cls.test_password,
            role="user",
            email=cls.test_email
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def test_user_registration(self):
        """Test user registration."""
        # Test with new user
        result = self.auth.register_user(
            username="test_user2",
            password="Test@123",
            role="user",
            email="test2@example.com"
        )
        self.assertTrue(result, "User registration failed")
        
        # Test with existing username
        result = self.auth.register_user(
            username=self.test_username,
            password="Test@123",
            role="user",
            email="test3@example.com"
        )
        self.assertFalse(result, "Duplicate username should not be allowed")
        print("\n[PASS] User registration tests passed")
    
    def test_user_login(self):
        """Test user login."""
        # Test valid login
        user = self.auth.login(self.test_username, self.test_password)
        self.assertIsNotNone(user, "Valid login failed")
        self.assertEqual(user['username'], self.test_username)
        self.assertEqual(user['email'], self.test_email)
        self.assertEqual(user['role'], 'user')
        
        # Test invalid password
        user = self.auth.login(self.test_username, "wrong_password")
        self.assertIsNone(user, "Login with wrong password should fail")
        
        # Test non-existent user
        user = self.auth.login("nonexistent_user", "password")
        self.assertIsNone(user, "Non-existent user should not be able to login")
        print("\n[PASS] User login tests passed")


class TestReportManagement(unittest.TestCase):
    """Test report management functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create a temporary directory for the test database
        cls.test_dir = tempfile.mkdtemp()
        os.environ['LOCALAPPDATA'] = cls.test_dir
        
        # Initialize the database
        from db.init_db import init_db
        cls.db_path = get_db_path()
        init_db()
        
        # Create test user
        cls.test_username = "test_user"
        cls.test_password = "Test@123"
        cls.test_email = "test@example.com"
        
        # Add test user
        cls.auth = Auth()
        cls.user_id = add_user(
            username=cls.test_username,
            password_hash=cls.auth.hash_password(cls.test_password),
            role="user",
            email=cls.test_email
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def setUp(self):
        """Set up test data."""
        self.conn, self.cursor = get_db_connection()
    
    def tearDown(self):
        """Clean up after each test."""
        self.cursor.execute("DELETE FROM reports WHERE user_id = ?", (self.user_id,))
        self.conn.commit()
        close_connection(self.conn)
    
    def test_create_report(self):
        """Test report creation."""
        # Create a new report
        report_id = create_report(
            user_id=self.user_id,
            title="Test Report"
        )
        self.assertIsNotNone(report_id, "Failed to create report")
        
        # Add report data
        add_report_data(report_id, "test_field", "test_value")
        
        # Get the report and verify data
        report = get_report(report_id)
        self.assertIsNotNone(report, "Failed to retrieve report")
        self.assertEqual(report['title'], "Test Report")
        self.assertEqual(report['status'], 'draft')
        self.assertEqual(report['fields']['test_field'], 'test_value')
        print("\n[PASS] Report creation and retrieval tests passed")
    
    def test_update_report_status(self):
        """Test report status updates."""
        # Create a test report
        report_id = create_report(
            user_id=self.user_id,
            title="Test Report Status"
        )
        
        # Update status to submitted
        update_report_status(report_id, 'submitted', self.user_id)
        report = get_report(report_id)
        self.assertEqual(report['status'], 'submitted')
        
        # Update status to approved
        update_report_status(report_id, 'approved', self.user_id)
        report = get_report(report_id)
        self.assertEqual(report['status'], 'approved')
        print("\n[PASS] Report status update tests passed")


class TestTemplateManagement(unittest.TestCase):
    """Test template management functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create a temporary directory for the test database and files
        cls.test_dir = tempfile.mkdtemp()
        os.environ['LOCALAPPDATA'] = cls.test_dir
        
        # Create a test templates directory
        cls.templates_dir = Path(cls.test_dir) / "templates"
        cls.templates_dir.mkdir(exist_ok=True)
        
        # Initialize the database
        from db.init_db import init_db
        cls.db_path = get_db_path()
        init_db()
        
        # Create test user
        cls.test_username = "test_user"
        cls.test_user_id = 1
        
        # Create a test template file
        cls.test_template_path = cls.templates_dir / "test_template.docx"
        with open(cls.test_template_path, 'w') as f:
            f.write("Test template content")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def test_add_template(self):
        """Test adding a template."""
        template_id = add_template(
            name="Test Template",
            file_path=str(self.test_template_path),
            uploaded_by=self.test_user_id
        )
        
        self.assertIsNotNone(template_id, "Failed to add template")
        
        # Verify template was added
        templates = get_all_templates()
        self.assertGreater(len(templates), 0, "No templates found")
        
        template_names = [t['name'] for t in templates]
        self.assertIn("Test Template", template_names)
        print("\n[PASS] Template management tests passed")


def run_tests():
    """Run all tests and print summary."""
    print("\n" + "="*60)
    print("STARTING LOGBOOK FUNCTIONALITY TESTS")
    print("="*60 + "\n")
    
    # Run tests
    test_suites = [
        unittest.TestLoader().loadTestsFromTestCase(TestDatabase),
        unittest.TestLoader().loadTestsFromTestCase(TestAuthentication),
        unittest.TestLoader().loadTestsFromTestCase(TestReportManagement),
        unittest.TestLoader().loadTestsFromTestCase(TestTemplateManagement),
    ]
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    results = []
    
    for suite in test_suites:
        result = test_runner.run(suite)
        results.append(result.wasSuccessful())
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if all(results):
        print("[PASS] All tests passed successfully!")
    else:
        print("[FAIL] Some tests failed. Please check the test output above for details.")
    
    print("\nTest execution completed.")


if __name__ == "__main__":
    run_tests()

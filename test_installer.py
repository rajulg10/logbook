#!/usr/bin/env python3
"""
Test script for the Logbook installer.

This script tests the installer build process and verifies the created installer.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestInstaller(unittest.TestCase):
    """Test cases for the Logbook installer."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment before any tests are run."""
        # Get the project root directory
        cls.project_root = Path(__file__).parent.absolute()
        
        # Create a temporary directory for testing
        cls.test_dir = Path(tempfile.mkdtemp(prefix="logbook_test_"))
        print(f"Test directory: {cls.test_dir}")
        
        # Copy necessary files to test directory
        cls.setup_test_environment()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run."""
        # Remove the test directory
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
    
    @classmethod
    def setup_test_environment(cls):
        """Set up the test environment by copying necessary files."""
        # Copy the build_installer.py script
        shutil.copy(
            cls.project_root / "build_installer.py",
            cls.test_dir / "build_installer.py"
        )
        
        # Copy the NSIS script
        os.makedirs(cls.test_dir / "installer", exist_ok=True)
        shutil.copy(
            cls.project_root / "installer" / "logbook_installer_clean.nsi",
            cls.test_dir / "installer" / "logbook_installer_clean.nsi"
        )
        
        # Create a simple main.py for testing
        with open(cls.test_dir / "main.py", "w") as f:
            f.write("""
# Simple test application
print("Logbook Application")
input("Press Enter to exit...")
""")
        
        # Create a simple requirements.txt
        with open(cls.test_dir / "requirements.txt", "w") as f:
            f.write("""
# Test requirements
pywin32>=300; sys_platform == 'win32'
""")
    
    def test_build_installer(self):
        """Test building the installer."""
        # Change to test directory
        original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        try:
            # Run the build_installer script
            result = subprocess.run(
                [sys.executable, "build_installer.py"],
                capture_output=True,
                text=True
            )
            
            # Check if the build was successful
            self.assertEqual(result.returncode, 0, 
                          f"Build failed with error: {result.stderr}")
            
            # Check if the installer was created
            installer_path = self.test_dir / "Logbook_Setup.exe"
            self.assertTrue(installer_path.exists(), 
                         f"Installer not found at {installer_path}")
            
            print(f"\nInstaller created successfully at: {installer_path}")
            print(f"Size: {installer_path.stat().st_size / (1024*1024):.2f} MB")
            
        finally:
            # Change back to the original directory
            os.chdir(original_dir)


if __name__ == "__main__":
    unittest.main()

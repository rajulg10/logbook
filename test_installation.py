#!/usr/bin/env python3
"""
Test script to verify the Logbook installation and uninstallation.

This script tests the installed application and verifies proper uninstallation.
"""

import os
import sys
import time
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path


class TestInstallation(unittest.TestCase):
    """Test cases for Logbook installation and uninstallation."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment before any tests are run."""
        # Get the project root directory
        cls.project_root = Path(__file__).parent.absolute()
        
        # Path to the installer
        cls.installer_path = cls.project_root / "Logbook_Setup.exe"
        
        # Installation directory
        cls.install_dir = Path("C:\\Program Files\\Logbook")
        
        # Create a temporary directory for testing
        cls.test_dir = Path(tempfile.mkdtemp(prefix="logbook_test_"))
        print(f"Test directory: {cls.test_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run."""
        # Remove the test directory
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def test_01_installer_exists(self):
        """Verify that the installer exists."""
        self.assertTrue(
            self.installer_path.exists(),
            f"Installer not found at {self.installer_path}"
        )
        print(f"\nFound installer at: {self.installer_path}")
    
    def test_02_run_installer(self):
        """Run the installer and verify the installation."""
        # Skip if installer doesn't exist
        if not self.installer_path.exists():
            self.skipTest("Installer not found")
        
        # Run the installer silently
        cmd = [str(self.installer_path), 
               "/S",  # Silent mode
               f"/D={self.install_dir}"  # Installation directory
              ]
        
        print(f"\nRunning installer: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minutes timeout
            )
            print(f"Installer output: {result.stdout}")
            if result.stderr:
                print(f"Installer errors: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.fail(f"Installer failed with error: {e}")
        except subprocess.TimeoutExpired:
            self.fail("Installer timed out")
        
        # Verify installation
        self.assertTrue(self.install_dir.exists(), 
                       f"Installation directory not found: {self.install_dir}")
        
        # Verify main executable
        exe_path = self.install_dir / "dist" / "Logbook.exe"
        self.assertTrue(exe_path.exists(), 
                       f"Main executable not found: {exe_path}")
        
        print(f"\nInstallation verified at: {self.install_dir}")
    
    def test_03_run_application(self):
        """Run the installed application."""
        # Skip if not installed
        if not self.install_dir.exists():
            self.skipTest("Application not installed")
        
        # Path to the installed executable
        exe_path = self.install_dir / "dist" / "Logbook.exe"
        
        if not exe_path.exists():
            self.skipTest("Executable not found")
        
        print(f"\nRunning application: {exe_path}")
        
        try:
            # Start the application
            process = subprocess.Popen(
                [str(exe_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Let it run for a few seconds
            time.sleep(5)
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # Check if the process started successfully
            self.assertIsNotNone(process.poll(), 
                               "Application failed to start")
            
            print("Application ran successfully")
            
        except Exception as e:
            self.fail(f"Failed to run application: {e}")
    
    def test_04_uninstall(self):
        """Test uninstalling the application."""
        # Skip if not installed
        if not self.install_dir.exists():
            self.skipTest("Application not installed")
        
        # Path to the uninstaller
        uninstaller_path = self.install_dir / "uninstall.exe"
        
        if not uninstaller_path.exists():
            self.skipTest("Uninstaller not found")
        
        print(f"\nRunning uninstaller: {uninstaller_path}")
        
        try:
            # Run the uninstaller silently
            cmd = [str(uninstaller_path), 
                   "/S"  # Silent mode
                  ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minutes timeout
            )
            
            print(f"Uninstaller output: {result.stdout}")
            if result.stderr:
                print(f"Uninstaller errors: {result.stderr}")
            
            # Verify uninstallation
            self.assertFalse(
                self.install_dir.exists(),
                f"Installation directory still exists: {self.install_dir}"
            )
            
            # Check Start Menu shortcuts
            start_menu = Path(os.environ["PROGRAMDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Logbook"
            self.assertFalse(
                start_menu.exists(),
                f"Start Menu shortcuts still exist: {start_menu}"
            )
            
            # Check Desktop shortcut
            desktop = Path(os.environ["PUBLIC"]) / "Desktop" / "Logbook.lnk"
            self.assertFalse(
                desktop.exists(),
                f"Desktop shortcut still exists: {desktop}"
            )
            
            print("Uninstallation verified")
            
        except subprocess.CalledProcessError as e:
            self.fail(f"Uninstaller failed with error: {e}")
        except subprocess.TimeoutExpired:
            self.fail("Uninstaller timed out")


if __name__ == "__main__":
    unittest.main(failfast=True)

#!/usr/bin/env python3
"""
Build and test the Logbook installer.

This script automates the process of building the installer and running tests.
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

# ANSI color codes for console output
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"  # No Color

def print_header(text):
    """Print a formatted header."""
    print(f"\n{YELLOW}{'=' * 60}{NC}")
    print(f"{YELLOW}{text.upper()}{NC}")
    print(f"{YELLOW}{'=' * 60}{NC}")

def run_command(cmd, cwd=None, check=True):
    """Run a shell command with real-time output."""
    print(f"\n{GREEN}Running: {' '.join(cmd)}{NC}")
    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        # Wait for the process to complete
        return_code = process.wait()
        
        if check and return_code != 0:
            print(f"{RED}Command failed with exit code {return_code}{NC}")
            return False
            
        return True
        
    except Exception as e:
        print(f"{RED}Error running command: {e}{NC}")
        return False

def build_installer():
    """Build the Logbook installer."""
    print_header("Building Installer")
    
    # Clean up old build artifacts
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Build the executable
    if not run_command(["pyinstaller", "--onefile", "--windowed", "--name", "Logbook", "main.py"]):
        return False
    
    # Build the installer
    if not run_command([sys.executable, "build_installer.py"]):
        return False
    
    # Verify the installer was created
    if not os.path.exists("Logbook_Setup.exe"):
        print(f"{RED}Installer was not created successfully{NC}")
        return False
    
    print(f"\n{GREEN}Installer built successfully: {os.path.abspath('Logbook_Setup.exe')}{NC}")
    return True

def run_tests():
    """Run the test suite."""
    print_header("Running Tests")
    
    # Run the installer tests
    if not run_command([sys.executable, "test_installer.py"]):
        return False
    
    # Run the installation tests
    if not run_command([sys.executable, "test_installation.py"]):
        return False
    
    print(f"\n{GREEN}All tests passed successfully!{NC}")
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Build and test the Logbook installer.")
    parser.add_argument(
        "--build-only", 
        action="store_true", 
        help="Only build the installer, don't run tests"
    )
    parser.add_argument(
        "--test-only", 
        action="store_true", 
        help="Only run tests, don't build"
    )
    
    args = parser.parse_args()
    
    try:
        # Build the installer if not in test-only mode
        if not args.test_only:
            if not build_installer():
                return 1
        
        # Run tests if not in build-only mode
        if not args.build_only:
            if not run_tests():
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nBuild and test process interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n{RED}An error occurred: {e}{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

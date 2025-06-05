import os
import shutil
import subprocess
import sys
import platform
from pathlib import Path

def find_nsis():
    """Find the NSIS installation path."""
    # Check common installation paths
    nsis_paths = [
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'NSIS', 'makensis.exe'),
        os.path.join(os.environ.get('ProgramFiles', ''), 'NSIS', 'makensis.exe'),
        'C:\\Program Files (x86)\\NSIS\\makensis.exe',
        'C:\\Program Files\\NSIS\\makensis.exe'
    ]
    
    # Check if makensis is in PATH
    try:
        result = subprocess.run(['where', 'makensis'], capture_output=True, text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.splitlines()[0].strip()
    except Exception:
        pass
    
    # Check common paths
    for path in nsis_paths:
        if os.path.isfile(path):
            return path
    
    return None

def print_banner():
    print("=" * 50)
    print("Logbook Installer Build Script")
    print("=" * 50)

def run_command(command, cwd=None, check=True):
    """Run a shell command and return the output."""
    print(f"\n[EXEC] {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"[STDERR] {result.stderr}")
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}")
        if e.stdout:
            print(f"[STDOUT] {e.stdout}")
        if e.stderr:
            print(f"[STDERR] {e.stderr}")
        return False, e.stdout, e.stderr

def check_requirements():
    """Check if all required tools are installed."""
    print("\n[INFO] Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("[ERROR] Python 3.9 or higher is required.")
        return False
    print(f"[OK] Python {platform.python_version()}")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("[WARN] PyInstaller not found. Installing...")
        success, _, _ = run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
        if not success:
            print("[ERROR] Failed to install PyInstaller.")
            return False
    
    # Check NSIS
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe"
    ]
    nsis_found = False
    for path in nsis_paths:
        if os.path.exists(path):
            print(f"[OK] NSIS found at {path}")
            nsis_found = True
            break
    
    if not nsis_found:
        print("""
[ERROR] NSIS not found. Please install NSIS (Nullsoft Scriptable Install System) from:
       https://nsis.sourceforge.io/Download
       Then add it to your system PATH or update the path in this script.
       """)
        return False
    
    return True

def clean_build():
    """Clean up previous build artifacts."""
    print("\n[INFO] Cleaning up previous builds...")
    for path in ["build", "dist", "__pycache__", "Logbook.spec"]:
        if os.path.exists(path):
            print(f"Removing {path}")
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                print(f"Warning: Could not remove {path}: {e}")

def create_virtualenv():
    """Create a virtual environment if it doesn't exist."""
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print(f"\n[INFO] Creating virtual environment in {venv_dir}...")
        success, _, _ = run_command([sys.executable, "-m", "venv", venv_dir])
        if not success:
            return False, None
    
    # Get the correct Python executable for the virtual environment
    python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = os.path.join(venv_dir, "bin", "python")
    
    return True, python_exe

def install_dependencies(python_exe):
    """Install required Python packages."""
    print("\n[INFO] Installing dependencies...")
    
    # Upgrade pip
    run_command([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        success, _, _ = run_command([python_exe, "-m", "pip", "install", "-r", "requirements.txt"])
        if not success:
            print("[WARN] Failed to install some dependencies. Continuing anyway...")
    
    # Ensure PyInstaller is installed in the virtual environment
    run_command([python_exe, "-m", "pip", "install", "pyinstaller"])
    
    return True

def build_executable(python_exe):
    """Build the executable using PyInstaller."""
    print("\n[INFO] Building executable with PyInstaller...")
    
    pyinstaller_cmd = [
        python_exe, "-m", "PyInstaller",
        "--name=Logbook",
        "--onefile",
        "--windowed",
        "--add-data=db;db",
        "--add-data=email_module;email_module",
        "--add-data=templates;templates",
        "--add-data=.env;.",
        "--clean",
        "--noconfirm",
        "main.py"
    ]
    
    success, _, _ = run_command(pyinstaller_cmd)
    if not success:
        print("[ERROR] Failed to build executable.")
        return False
    
    return True

def prepare_installer_files(target_dir):
    """
    Prepare all necessary files for the installer.
    Copies all required files to the specified target directory.
    
    Args:
        target_dir (str): The target directory where files should be copied
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"[INFO] Preparing installer files in {target_dir}...")
    
    try:
        # Define source directory
        base_dir = os.path.abspath('.')
        
        print(f"[DEBUG] Base directory: {base_dir}")
        print(f"[DEBUG] Target directory: {target_dir}")
        
        # Create the target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # List of files and directories to copy with their relative paths
        items_to_copy = [
            ("dist", "dist"),
            ("db", "db"),
            ("email_module", "email_module"),
            ("templates", "templates"),
            (".env", ".env"),
            ("requirements.txt", "requirements.txt"),
            ("logbook.db", "logbook.db")
        ]
        
        # List of directories to create
        dirs_to_create = [
            "admin_all_reports",
            "approved_reports",
            "pdf",
            "user_reports"
        ]
        
        # Copy all required files and directories
        for src_rel, dest_rel in items_to_copy:
            src_path = os.path.join(base_dir, src_rel)
            dest_path = os.path.join(target_dir, dest_rel)
            
            # Skip if source doesn't exist (except for optional files)
            if not os.path.exists(src_path):
                if src_rel in [".env", "logbook.db"]:  # These files are optional
                    print(f"[WARN] Optional file not found: {src_path}")
                    continue
                else:
                    print(f"[ERROR] Required file/directory not found: {src_path}")
                    return False
            
            try:
                # Create parent directory if it doesn't exist
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Copy the file or directory
                if os.path.isdir(src_path):
                    print(f"[INFO] Copying directory: {src_rel} -> {dest_rel}")
                    # Remove destination if it exists
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path, ignore_errors=True)
                    shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                else:
                    print(f"[INFO] Copying file: {src_rel} -> {dest_rel}")
                    shutil.copy2(src_path, dest_path)
                    
            except Exception as e:
                print(f"[ERROR] Failed to copy {src_rel}: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
        
        # Create required empty directories
        for dir_name in dirs_to_create:
            dir_path = os.path.join(target_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            print(f"[INFO] Created directory: {dir_name}")
        
        print("[INFO] Successfully prepared all installer files")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error in prepare_installer_files: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def build_installer():
    """
    Build the NSIS installer.
    
    Returns:
        bool: True if the installer was built successfully, False otherwise
    """
    print("\n[INFO] Building NSIS installer...")
    
    # Find makensis.exe
    nsis_path = find_nsis()
    if not nsis_path:
        print("[ERROR] Could not find makensis.exe. Please ensure NSIS is installed.")
        print("       Download NSIS from: https://nsis.sourceforge.io/Download")
        return False
    
    print(f"[INFO] Found NSIS at: {nsis_path}")
    
    # Define directories
    base_dir = os.path.abspath(".")
    installer_dir = os.path.join(base_dir, "installer")
    temp_dir = os.path.join(base_dir, "_temp")
    log_file = os.path.join(base_dir, "installer_build.log")
    
    # Clean up old files if they exist
    for directory in [installer_dir, temp_dir]:
        if os.path.exists(directory):
            print(f"[INFO] Removing old directory: {directory}")
            shutil.rmtree(directory, ignore_errors=True)
    
    # Clean up old log file if it exists
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Create fresh directories
    os.makedirs(installer_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save current directory
    original_dir = os.getcwd()
    
    try:
        # Copy NSIS script to installer directory
        nsis_script_src = os.path.join(base_dir, "logbook_installer_clean.nsi")
        nsis_script_dst = os.path.join(installer_dir, "logbook_installer_clean.nsi")
        
        if not os.path.exists(nsis_script_src):
            print(f"[ERROR] NSIS script not found at {nsis_script_src}")
            return False
            
        shutil.copy2(nsis_script_src, nsis_script_dst)
        print(f"[INFO] Copied NSIS script to {nsis_script_dst}")
        
        # Prepare installer files in the temp directory
        print("[INFO] Preparing installer files...")
        if not prepare_installer_files(temp_dir):
            print("[ERROR] Failed to prepare installer files.")
            return False
        
        # Change to the base directory where the _temp folder is located
        os.chdir(base_dir)
        
        # Build the installer with detailed output
        cmd = [
            nsis_path,
            "/V4",         # Verbose level 4
            "/NOCD",       # No change directory
            "/P4",         # Set priority to low
            f"-O{log_file}", # Output log file
            nsis_script_dst
        ]
        
        print(f"[INFO] Running: {' '.join(cmd)}")
        print(f"[INFO] Build log will be saved to: {log_file}")
        
        # Run NSIS compiler with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=base_dir
        )
        
        # Print output in real-time
        print("\n[NSIS Output]")
        for line in process.stdout:
            print(line, end='')
        
        # Wait for the process to complete
        return_code = process.wait()
        
        # Check if the installer was created successfully
        installer_path = os.path.join(base_dir, "Logbook_Setup.exe")
        
        if return_code == 0 and os.path.exists(installer_path):
            size_mb = os.path.getsize(installer_path) / (1024 * 1024)
            print(f"\n[SUCCESS] Installer built successfully!")
            print(f"[INFO] Installer location: {installer_path}")
            print(f"[INFO] Installer size: {size_mb:.2f} MB")
            
            # Make sure the installer has the correct permissions
            os.chmod(installer_path, 0o755)  # rwxr-xr-x
            
            return True
        else:
            print("\n[ERROR] Failed to build installer.")
            
            # Show the last few lines of the log for debugging
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print("\n[Last 20 lines of installer log:")
                            print(''.join(lines[-20:]))
                        else:
                            print("Installer log file is empty.")
                else:
                    print(f"Installer log file not found at: {log_file}")
            except Exception as e:
                print(f"Could not read installer log: {e}")
                
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Failed to build installer: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(temp_dir):
                print(f"[INFO] Cleaning up temporary directory: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"[WARNING] Failed to clean up temporary directory: {e}")
        
        # Change back to the original directory
        os.chdir(original_dir)

def main():
    print_banner()
    
    # Check system requirements
    if not check_requirements():
        return 1
    
    # Clean up previous builds
    clean_build()
    
    # Create and activate virtual environment
    success, python_exe = create_virtualenv()
    if not success:
        print("[ERROR] Failed to create virtual environment.")
        return 1
    
    # Install dependencies
    if not install_dependencies(python_exe):
        print("[ERROR] Failed to install dependencies.")
        return 1
    
    # Build the executable
    if not build_executable(python_exe):
        return 1
    
    # Prepare installer files
    if not prepare_installer_files():
        return 1
    
    # Build the installer
    if not build_installer():
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[INFO] Build process interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

import os
import sys
import requests
import zipfile
import tempfile
import shutil
import winreg
import win32serviceutil
import win32service
import win32event
import servicemanager

class LogbookUpdater(win32serviceutil.ServiceFramework):
    _svc_name_ = "LogbookUpdateService"
    _svc_display_name_ = "Logbook Update Service"
    _svc_description_ = "Automatic update service for Logbook Application"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                             servicemanager.PYS_SERVICE_STARTED,
                             (self._svc_name_, ''))
        
        self.main()

    def main(self):
        while self.is_alive:
            try:
                # Get current version
                current_version = self.get_current_version()
                
                # Check for updates
                latest_version = self.check_for_updates()
                
                if latest_version and latest_version > current_version:
                    self.update_application(latest_version)
                    
                # Wait for 24 hours before checking again
                win32event.WaitForSingleObject(self.hWaitStop, 86400000)
                
            except Exception as e:
                servicemanager.LogErrorMsg(f"Error in update service: {str(e)}")
                win32event.WaitForSingleObject(self.hWaitStop, 3600000)  # Wait 1 hour before retrying

    def get_current_version(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Logbook")
            version, _ = winreg.QueryValueEx(key, "Version")
            winreg.CloseKey(key)
            return version
        except:
            return "0.0.0"

    def check_for_updates(self):
        try:
            response = requests.get("https://api.example.com/logbook/version")
            if response.status_code == 200:
                return response.json().get("version", None)
            return None
        except:
            return None

    def update_application(self, version):
        try:
            # Get the update package
            response = requests.get(f"https://api.example.com/logbook/download/{version}", stream=True)
            
            if response.status_code == 200:
                # Create temp directory
                temp_dir = tempfile.mkdtemp()
                
                # Save the update package
                update_path = os.path.join(temp_dir, "logbook_update.zip")
                with open(update_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract the update
                with zipfile.ZipFile(update_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Get installation directory
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Logbook")
                install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                winreg.CloseKey(key)
                
                # Backup current installation
                backup_dir = os.path.join(temp_dir, "backup")
                shutil.copytree(install_dir, backup_dir)
                
                # Update the application
                update_dir = os.path.join(temp_dir, "update")
                for item in os.listdir(update_dir):
                    src = os.path.join(update_dir, item)
                    dst = os.path.join(install_dir, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                
                # Clean up
                shutil.rmtree(temp_dir)
                
                # Update version in registry
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Logbook", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, version)
                winreg.CloseKey(key)
                
                servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                     servicemanager.PYS_SERVICE_INFO,
                                     ("Successfully updated to version", version))
                
        except Exception as e:
            servicemanager.LogErrorMsg(f"Error updating application: {str(e)}")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(LogbookUpdater)

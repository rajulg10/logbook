# Logbook Windows Installer

This repository contains the Windows installer files for the Logbook application.

## Features

- Custom installation options
- Automatic updates
- Proper uninstallation
- Professional installer interface

## Installation Steps

1. **Install Wix Toolset**:
   - Download from: https://wixtoolset.org/releases/
   - Install both Wix Toolset and Wix UI Extension

2. **Build the Installer**:
```powershell
# Navigate to the wix directory
cd path\to\logbook\wix

# Generate unique GUIDs
powershell -ExecutionPolicy Bypass -File generate_guids.ps1

# Build the installer
powershell -ExecutionPolicy Bypass -File build.ps1
```

3. **Install the Application**:
   - Double-click `installer\Logbook.msi`
   - Follow the installation wizard
   - Choose installation location
   - Select installation options:
     - Desktop shortcut
     - Start Menu shortcut
     - Sample data
     - Automatic updates

## Custom Installation Options

During installation, you can choose:
- Installation location
- Desktop shortcut
- Start Menu shortcut
- Sample data
- Automatic updates

## Uninstallation

You can uninstall the application in three ways:
1. Through Windows Control Panel
2. Using the Uninstall shortcut in Start Menu
3. Using the uninstall script:
```powershell
# Run the uninstall script
path\to\installer\uninstall.bat
```

## Automatic Updates

The installer includes an automatic update service that:
- Checks for updates every 24 hours
- Downloads and installs updates automatically
- Creates backups before updating
- Logs all update activities

## Requirements

- Windows 10 or later
- Wix Toolset v3.11 or later
- Python 3.7 or later (for updater service)

## Icons and Images

The installer uses custom icons and images:
- `banner.bmp` - Installer banner
- `dialog.bmp` - Installer dialog background
- `Logbook.ico` - Application icon

## Troubleshooting

If you encounter any issues:
1. Check the Windows Event Viewer for service logs
2. Run the installer with logging:
```powershell
msiexec /i Logbook.msi /L*v install.log
```
3. Review the generated log file for errors

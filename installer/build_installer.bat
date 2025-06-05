@echo off
setlocal

:: Check if NSIS is installed
echo Checking NSIS installation...
where makensis >nul 2>&1
if errorlevel 1 (
    echo NSIS is not installed. Downloading and installing...
    
    :: Download NSIS
    powershell -Command "Invoke-WebRequest -Uri 'https://sourceforge.net/projects/nsis/files/NSIS%203/3.08/nsis-3.08-setup.exe' -OutFile 'nsis-setup.exe'"
    
    :: Install NSIS
    start /wait nsis-setup.exe /S
    
    :: Clean up
    del nsis-setup.exe
)

:: Build the installer
echo Building installer...
makensis logbook.nsi

:: Check if build was successful
if errorlevel 1 (
    echo Failed to build installer
    exit /b 1
)

echo Installer created successfully!
echo Installer location: LogbookSetup.exe

endlocal

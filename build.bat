@echo off
echo Building Logbook Installer...
echo =============================

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.9+ and try again.
    pause
    exit /b 1
)

:: Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo Failed to install PyInstaller. Please install it manually: pip install pyinstaller
        pause
        exit /b 1
    )
)

:: Run the build script
echo.
echo Starting the build process...
python build_installer.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo Build completed successfully!
    echo The installer is ready in the current directory as 'LogbookSetup.exe'
) else (
    echo.
    echo Build failed. Check the error messages above for details.
)

pause

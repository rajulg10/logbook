@echo off
setlocal

:: Get the installation directory from registry
for /f "tokens=3" %%i in ('reg query "HKCU\Software\Logbook\Uninstall" /v "installed"') do set "INSTALLED=%%i"

if "%INSTALLED%"=="1" (
    echo Logbook is installed. Proceeding with uninstallation...
    
    :: Get the product code
    for /f "tokens=2* delims=" %%a in ('wmic product where "name='Logbook Application'" get IdentifyingNumber /format:value') do set "PRODUCTCODE=%%b"
    
    if not "%PRODUCTCODE%"=="" (
        echo Uninstalling Logbook Application...
        msiexec /x "%PRODUCTCODE%" /qn
        
        echo Cleaning up registry entries...
        reg delete "HKCU\Software\Logbook\Uninstall" /f
        
        echo Cleaning up temporary files...
        del /f /q "%TEMP%\logbook*.tmp" 2>nul
        
        echo Logbook has been successfully uninstalled.
    ) else (
        echo Error: Could not find Logbook installation.
    )
) else (
    echo Logbook is not installed.
)

endlocal

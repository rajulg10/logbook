$ErrorActionPreference = "Stop"

# Check if NSIS is already installed
$nsisPath = "C:\Program Files (x86)\NSIS"
if (Test-Path $nsisPath) {
    Write-Host "NSIS is already installed at $nsisPath" -ForegroundColor Green
    exit 0
}

# Download NSIS installer
Write-Host "Downloading NSIS installer..." -ForegroundColor Cyan
$installerUrl = "https://sourceforge.net/projects/nsis/files/NSIS%203/3.08/nsis-3.08-setup.exe/download"
$installerPath = "nsis-setup.exe"

try {
    # Download the installer
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
    
    # Run the installer silently
    Write-Host "Installing NSIS..." -ForegroundColor Cyan
    Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait
    
    # Verify installation
    if (Test-Path $nsisPath) {
        Write-Host "NSIS installed successfully!" -ForegroundColor Green
        Write-Host "NSIS path: $nsisPath" -ForegroundColor Green
    } else {
        Write-Host "NSIS installation failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
} finally {
    # Clean up
    if (Test-Path $installerPath) {
        Remove-Item $installerPath
    }
}

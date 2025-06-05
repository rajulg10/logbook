$ErrorActionPreference = "Stop"

# Get current directory
$currentDir = Get-Location

# Set NSIS path
$nsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"

# Check if makensis exists
if (-not (Test-Path $nsisPath)) {
    Write-Host "NSIS not found at $nsisPath. Please install NSIS first." -ForegroundColor Red
    exit 1
}

# Build the installer
Write-Host "Building installer..." -ForegroundColor Cyan
& $nsisPath "$currentDir\logbook_installer.nsi"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Installer created successfully!" -ForegroundColor Green
    Write-Host "Installer location: $currentDir\LogbookSetup.exe" -ForegroundColor Green
} else {
    Write-Host "Failed to build installer" -ForegroundColor Red
    exit 1
}

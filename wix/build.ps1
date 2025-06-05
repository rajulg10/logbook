# Set the Wix Toolset path
$wixPath = "C:\Program Files\WiX Toolset v3.11\bin"

# Set the output directory
$outputDir = "..\installer"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
}

# Compile the WiX source
& "$wixPath\candle.exe" -nologo -out "$outputDir\Logbook.wixobj" "product.wxs"

# Build the MSI
& "$wixPath\light.exe" -nologo -out "$outputDir\Logbook.msi" "$outputDir\Logbook.wixobj" -ext WixUIExtension

Write-Host "Installer created at: $outputDir\Logbook.msi"

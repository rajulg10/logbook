$guids = @{
    'UpgradeCode' = [guid]::NewGuid()
    'MainExecutable' = [guid]::NewGuid()
    'ConfigFile' = [guid]::NewGuid()
    'ReportsDir' = [guid]::NewGuid()
}

# Read the product.wxs file
$content = Get-Content "product.wxs"

# Replace GUID placeholders
foreach($key in $guids.Keys) {
    $content = $content -replace "YOUR-UNIQUE-GUID", $guids[$key]
}

# Write the updated content back
$content | Set-Content "product.wxs"

Write-Host "Generated GUIDs:" -ForegroundColor Green
$guids.GetEnumerator() | ForEach-Object { Write-Host "$_" }

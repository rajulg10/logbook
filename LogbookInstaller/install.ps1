$ErrorActionPreference = "Stop"

# Function to install required components
function Install-Components {
    Write-Host "Installing required components..." -ForegroundColor Cyan

    # Install Visual Studio Build Tools
    Write-Host "Installing Visual Studio Build Tools..." -ForegroundColor Yellow
    $vsUrl = "https://aka.ms/vs/17/release/vs_buildtools.exe"
    $vsInstaller = "vs_buildtools.exe"
    Invoke-WebRequest -Uri $vsUrl -OutFile $vsInstaller
    Start-Process -FilePath $vsInstaller -ArgumentList "--quiet --wait --add Microsoft.VisualStudio.Workload.ManagedDesktop --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.VC.CMake.Project" -Wait
    Remove-Item $vsInstaller

    # Install Wix Toolset
    Write-Host "Installing Wix Toolset..." -ForegroundColor Yellow
    $wixUrl = "https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311-binaries.msi"
    $wixInstaller = "wix311-binaries.msi"
    Invoke-WebRequest -Uri $wixUrl -OutFile $wixInstaller
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i $wixInstaller /quiet" -Wait
    Remove-Item $wixInstaller
}

# Function to create installer project
function Create-InstallerProject {
    Write-Host "Creating installer project..." -ForegroundColor Cyan

    # Create solution
    dotnet new sln -n LogbookInstaller

    # Create setup project
    dotnet new console -n LogbookInstaller
    Set-Location LogbookInstaller

    # Add required NuGet packages
    dotnet add package Microsoft.VisualStudio.Setup.Configuration.Interop
    dotnet add package Microsoft.Deployment.WindowsInstaller

    # Create installer class
    $installerClass = @"
using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Configuration.Install;
using Microsoft.Deployment.WindowsInstaller;

[RunInstaller(true)]
public partial class LogbookInstaller : Installer
{
    public LogbookInstaller()
    {
        InitializeComponent();
    }

    public override void Install(IDictionary stateSaver)
    {
        base.Install(stateSaver);
        
        // Register update service
        string installDir = Context.Parameters["INSTALLDIR"];
        if (!string.IsNullOrEmpty(installDir))
        {
            string updaterPath = System.IO.Path.Combine(installDir, "LogbookUpdater.exe");
            if (System.IO.File.Exists(updaterPath))
            {
                try
                {
                    System.Diagnostics.Process.Start(updaterPath, "--register-update").WaitForExit();
                }
                catch (Exception ex)
                {
                    throw new InstallException("Failed to register update service", ex);
                }
            }
        }
    }

    public override void Uninstall(IDictionary savedState)
    {
        base.Uninstall(savedState);
        
        // Unregister update service
        string installDir = Context.Parameters["INSTALLDIR"];
        if (!string.IsNullOrEmpty(installDir))
        {
            string updaterPath = System.IO.Path.Combine(installDir, "LogbookUpdater.exe");
            if (System.IO.File.Exists(updaterPath))
            {
                try
                {
                    System.Diagnostics.Process.Start(updaterPath, "--unregister-update").WaitForExit();
                }
                catch (Exception ex)
                {
                    throw new InstallException("Failed to unregister update service", ex);
                }
            }
        }
    }
}
"@

    $installerClass | Out-File -FilePath "LogbookInstaller.cs"

    # Add project to solution
    Set-Location ..
    dotnet sln add LogbookInstaller/LogbookInstaller.csproj
}

# Function to build installer
function Build-Installer {
    Write-Host "Building installer..." -ForegroundColor Cyan
    
    # Build the project
    dotnet build -c Release
    
    # Create installer output directory
    $outputDir = "Installer"
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir
    }
    
    # Copy required files
    Copy-Item -Path "dist\Logbook.exe" -Destination $outputDir
    Copy-Item -Path "updater\LogbookUpdater.exe" -Destination $outputDir
    Copy-Item -Path "wix\icons\*" -Destination $outputDir
    
    # Create installer
    $wixPath = "C:\Program Files (x86)\WiX Toolset v3.11\bin"
    
    # Create Wix source file
    $wxsContent = @"
<?xml version='1.0' encoding='windows-1252'?>
<Wix xmlns='http://schemas.microsoft.com/wix/2006/wi'>
    <Product Id='*' Name='Logbook Application' Language='1033' Version='1.0.0.0' Manufacturer='Your Company' UpgradeCode='YOUR-UNIQUE-GUID'>
        <Package InstallerVersion='200' Compressed='yes' InstallScope='perMachine' />

        <MajorUpgrade DowngradeErrorMessage='A newer version of [ProductName] is already installed.' />
        <MediaTemplate />

        <Feature Id='ProductFeature' Title='Logbook Application' Level='1'>
            <ComponentGroupRef Id='ProductComponents' />
        </Feature>

        <UIRef Id='WixUI_InstallDir' />
        <WixVariable Id='WixUILicenseRtf' Value='license.rtf' />
        <WixVariable Id='WixUIBannerBmp' Value='banner.bmp' />
        <WixVariable Id='WixUIDialogBmp' Value='dialog.bmp' />
        <Icon Id='Logbook.ico' SourceFile='Logbook.ico' />
        <Property Id='ARPPRODUCTICON' Value='Logbook.ico' />
    </Product>

    <Fragment>
        <Directory Id='TARGETDIR' Name='SourceDir'>
            <Directory Id='ProgramFilesFolder'>
                <Directory Id='INSTALLDIR' Name='Logbook'>
                    <!-- Application files will be added here -->
                </Directory>
            </Directory>
            <Directory Id='ProgramMenuFolder'>
                <Directory Id='ApplicationProgramsFolder' Name='Logbook' />
            </Directory>
        </Directory>
    </Fragment>

    <Fragment>
        <ComponentGroup Id='ProductComponents' Directory='INSTALLDIR'>
            <Component Id='MainExecutable' Guid='YOUR-UNIQUE-GUID'>
                <File Id='MainExe' Name='Logbook.exe' Source='Logbook.exe' KeyPath='yes' />
                <Shortcut Id='startmenuLogbook' Directory='ApplicationProgramsFolder' Name='Logbook' 
                         WorkingDirectory='INSTALLDIR' Icon='Logbook.ico' IconIndex='0' Advertise='yes' />
                <Shortcut Id='desktopLogbook' Directory='DesktopFolder' Name='Logbook' 
                         WorkingDirectory='INSTALLDIR' Icon='Logbook.ico' IconIndex='0' Advertise='yes' />
            </Component>

            <!-- Add other required files -->
            <Component Id='ConfigFile' Guid='YOUR-UNIQUE-GUID'>
                <File Id='ConfigFile' Name='.env' Source='.env' />
            </Component>

            <!-- Add required directories -->
            <Component Id='ReportsDir' Guid='YOUR-UNIQUE-GUID'>
                <CreateFolder />
                <Directory Id='AdminReportsDir' Name='admin_all_reports'>
                    <CreateFolder />
                </Directory>
                <Directory Id='ApprovedReportsDir' Name='approved_reports'>
                    <CreateFolder />
                </Directory>
                <Directory Id='UserReportsDir' Name='user_reports'>
                    <CreateFolder />
                </Directory>
                <Directory Id='DbDir' Name='db'>
                    <CreateFolder />
                </Directory>
                <Directory Id='PdfDir' Name='pdf'>
                    <CreateFolder />
                </Directory>
            </Component>
        </ComponentGroup>
    </Fragment>
</Wix>
"@

    $wxsContent | Out-File -FilePath "$outputDir\product.wxs"
    
    # Compile and build installer
    & "$wixPath\candle.exe" -nologo -out "$outputDir\Logbook.wixobj" "$outputDir\product.wxs"
    & "$wixPath\light.exe" -nologo -out "$outputDir\Logbook.msi" "$outputDir\Logbook.wixobj" -ext WixUIExtension
}

# Main execution
try {
    Install-Components
    Create-InstallerProject
    Build-Installer
    Write-Host "Installer created successfully!" -ForegroundColor Green
    Write-Host "Installer location: Installer\Logbook.msi" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

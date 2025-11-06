#Requires -Version 5.1

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Restarting with elevated privileges..." -ForegroundColor Yellow
    
    # Restart script with elevated privileges
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`""
    Start-Process PowerShell -Verb RunAs -ArgumentList $arguments
    exit
}

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "abletonCracker.py"
$ConfigFile = Join-Path $ScriptDir "config.json"
$StartupDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutName = "abletonCracker RePatcher.lnk"
$ShortcutPath = Join-Path $StartupDir $ShortcutName

# Check if required files exist
if (-not (Test-Path $PythonScript)) {
    Write-Host "Error: abletonCracker.py not found in the same directory as this script." -ForegroundColor Red
    Write-Host "Please make sure repatch_setup.ps1 is in the same folder as abletonCracker.py" -ForegroundColor Yellow
    pause
    exit 1
}

if (-not (Test-Path $ConfigFile)) {
    Write-Host "Error: config.json not found in the same directory as this script." -ForegroundColor Red
    Write-Host "Please make sure config.json exists." -ForegroundColor Yellow
    pause
    exit 1
}

# Read config.json and build command line arguments
try {
    $config = Get-Content $ConfigFile | ConvertFrom-Json
    $cmdArgs = @()
    
    if ($config.file_path) {
        if ($config.file_path -eq "auto") {
            Write-Host "WARNING: file_path is set to 'auto' in config.json." -ForegroundColor Yellow
            Write-Host "Because the patcher runs silently, this will always default to the newest version of Ableton Live installed." -ForegroundColor Yellow
            Write-Host "To change this behavior, set a specific path to your ableton exe in the 'file_path' field of config.json." -ForegroundColor Yellow
        }
        $cmdArgs += "--file_path `"$($config.file_path)`""
    }
    if ($config.old_signkey) { $cmdArgs += "--old_signkey `"$($config.old_signkey)`"" }
    if ($config.new_signkey) { $cmdArgs += "--new_signkey `"$($config.new_signkey)`"" }
    if ($config.hwid) { $cmdArgs += "--hwid `"$($config.hwid)`"" }
    if ($config.edition) { $cmdArgs += "--edition `"$($config.edition)`"" }
    if ($config.version) { $cmdArgs += "--version `"$($config.version)`"" }
    if ($config.authorize_file_output) { $cmdArgs += "--authorize_file_output `"$($config.authorize_file_output)`"" }
    
    # Add silent and no output file flags for repatching
    $cmdArgs += "--silent"
    $cmdArgs += "--no-output-file"
    
    $fullCmdArgs = $cmdArgs -join " "
}
catch {
    Write-Host "Error reading config.json: $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}

# Display information
Write-Host "    abletonCracker Repatcher Setup" -ForegroundColor Cyan
Write-Host ""
Write-Host "`nThis will create a startup shortcut that automatically reapplies the patch"
Write-Host "when you log in, in case Ableton updates itself.`n"
Write-Host "Startup folder: $StartupDir" -ForegroundColor Yellow
Write-Host ""

# Check if shortcut already exists and handle options
if (Test-Path $ShortcutPath) {
    Write-Host "WARNING: A repatcher shortcut already exists!" -ForegroundColor Red
    Write-Host "`nOptions:" -ForegroundColor White
    Write-Host "  [O] Override - Replace existing shortcut with new one" -ForegroundColor Yellow
    Write-Host "  [R] Remove - Delete existing shortcut and exit" -ForegroundColor Yellow
    Write-Host "  [C] Cancel - Exit without changes" -ForegroundColor Yellow
    
    do {
        $choice = Read-Host "`nChoose an option (O/R/C)"
        $choice = $choice.Trim().ToUpper()
    } while ($choice -notin @('O', 'R', 'C'))
    
    switch ($choice) {
        'O' {
            Write-Host "Removing existing shortcut..." -ForegroundColor Yellow
            Remove-Item $ShortcutPath -Force
            # Continue to create new shortcut
        }
        'R' {
            Write-Host "Removing shortcut..." -ForegroundColor Yellow
            Remove-Item $ShortcutPath -Force
            Write-Host "Shortcut removed successfully." -ForegroundColor Green
            pause
            exit 0
        }
        'C' {
            Write-Host "Operation cancelled." -ForegroundColor Yellow
            pause
            exit 0
        }
    }
}

# Create the shortcut
try {
    Write-Host "`nCreating startup shortcut..." -ForegroundColor Green
    
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "python"
    $Shortcut.Arguments = "`"$PythonScript`" $fullCmdArgs"
    $Shortcut.WorkingDirectory = $ScriptDir
    $Shortcut.WindowStyle = 1  # Minimized window
    $Shortcut.Description = "Automatically repatch Ableton Live on startup"
    $Shortcut.Save()
    
    Write-Host "`n<<< SUCCESS >>>" -ForegroundColor Green
    Write-Host "`nRepatcher shortcut has been created successfully!" -ForegroundColor Green
    Write-Host "`nThe repatcher will run automatically when you log in with these settings:" 
    Write-Host "- Silent mode (no console window)" -ForegroundColor Yellow
    Write-Host "- No authorization file generation (only patching)" -ForegroundColor Yellow
    Write-Host "- Uses all settings from your config.json" -ForegroundColor Yellow
    Write-Host "`nShortcut location: $ShortcutPath" -ForegroundColor Cyan
    Write-Host "`nThe shortcut will be visible in Task Manager (Startup tab)"
    Write-Host "`nTo remove this later:" -ForegroundColor White
    Write-Host "1. Open Task Manager (Ctrl+Shift+Esc)" -ForegroundColor Gray
    Write-Host "2. Go to the Startup tab" -ForegroundColor Gray
    Write-Host "3. Find 'python.exe'" -ForegroundColor Gray
    Write-Host "4. Right-click and select Disable" -ForegroundColor Gray
    Write-Host "`nOr simply restart this script to remove the entry:" -ForegroundColor White
}
catch {
    Write-Host "`n<<< ERROR >>>" -ForegroundColor Red
    Write-Host "`nFailed to create startup shortcut: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nThis might be due to:" -ForegroundColor Yellow
    Write-Host "- Lack of write permissions to startup folder" -ForegroundColor Gray
    Write-Host "- Antivirus blocking the operation" -ForegroundColor Gray
    Write-Host "- System policy restrictions" -ForegroundColor Gray
}

Write-Host "`n"
pause

@echo off
setlocal

:: Temporary PowerShell script path
set "TEMP_PS=%TEMP%\install_dependencies_temp.ps1"

(
echo $ErrorActionPreference = "Stop"
echo # ASCII Logo in Red
echo Write-Host "      ___.   .__          __                _________                       __                 " -ForegroundColor Red
echo Write-Host "_____ \_ |__ |  |   _____/  |_  ____   ____ \_   ___ \____________    ____ |  | __ ___________ " -ForegroundColor Red
echo Write-Host "\__  \ | __ \|  | _/ __ \   __\/  _ \ /    \/    \  \/\_  __ \__  \ _/ ___\|  |/ // __ \_  __ \" -ForegroundColor Red
echo Write-Host " / __ \| \_\ \  |_\  ___/|  | (  <_> )   |  \     \____|  | \// __ \\  \___|    <\  ___/|  | \/" -ForegroundColor Red
echo Write-Host "(____  /___  /____/\___  >__|  \____/|___|  /\______  /|__|  (____  /\___  >__|_ \\___  >__|   " -ForegroundColor Red
echo Write-Host "     \/    \/          \/                 \/        \/            \/     \/     \/    \/    " -ForegroundColor Red
echo Write-Host "________   ____ ___.____________  ____  __.  _________________________ _____________________" -ForegroundColor Red
echo Write-Host "\_____  \ |    |   \   \_   ___ \|    |/ _| /   _____/\__    ___/  _  \\______   \__    ___/" -ForegroundColor Red
echo Write-Host " /  / \  \|    |   /   /    \  \/|      <   \_____  \   |    | /  /_\  \|       _/ |    |   " -ForegroundColor Red
echo Write-Host "/   \_/.  \    |  /|   \     \___|    |  \  /        \  |    |/    |    \    |   \ |    |   " -ForegroundColor Red
echo Write-Host "\_____\ \_/______/ |___|\______  /____|__ \/_______  /  |____|\____|__  /____|_  / |____|   " -ForegroundColor Red
echo Write-Host "       \__>                    \/        \/        \/                 \/       \/           " -ForegroundColor Red
echo Write-Host ""
echo Write-Host "=========================================================" -ForegroundColor White
echo Write-Host "  Checking configuration..." -ForegroundColor White
echo Write-Host "=========================================================" -ForegroundColor White
echo.

:: Read config.json with manual parsing (compatible with older PowerShell)
echo $skipPythonCheck = $false
echo $skipPythonDependencies = $false
echo if ^(Test-Path "config.json"^) {
echo     try {
echo         $configContent = Get-Content "config.json" -Raw
echo         # Manual JSON parsing for compatibility
echo         if ^($configContent -match '"skipPythonCheck"\s*:\s*true'^) {
echo             $skipPythonCheck = $true
echo         }
echo         if ^($configContent -match '"skipPythonDependencies"\s*:\s*true'^) {
echo             $skipPythonDependencies = $true
echo         }
echo     } catch {
echo         Write-Host "Warning: Error reading config.json, using default settings" -ForegroundColor Yellow
echo     }
echo }
echo.

:: Check if Python exists (unless skipped)
echo if ^(-not $skipPythonCheck^) {
echo     Write-Host ""
echo     Write-Host "=========================================================" -ForegroundColor White
echo     Write-Host "  Checking for Python installation..." -ForegroundColor White
echo     Write-Host "=========================================================" -ForegroundColor White
echo     $pythonPath = ^(Get-Command python -ErrorAction SilentlyContinue^).Source
echo     if ^(-not $pythonPath^) {
echo         Write-Host "Python not found. Installing via winget..." -ForegroundColor White
echo         if ^(-not ^(Get-Command winget -ErrorAction SilentlyContinue^)^) {
echo             Write-Host "ERROR: winget not available. Install Windows Package Manager first." -ForegroundColor Red
echo             exit 1
echo         }
echo         winget install --id Python.Python.3 -e --source winget
echo         $pythonPath = ^(Get-Command python -ErrorAction SilentlyContinue^).Source
echo         if ^(-not $pythonPath^) {
echo             Write-Host "ERROR: Python installation failed." -ForegroundColor Red
echo             exit 1
echo         }
echo         Write-Host 'Python installed successfully.' -ForegroundColor Green
echo     } else {
echo         Write-Host 'Python is already installed at: ' + $pythonPath -ForegroundColor Green
echo     }
echo } else {
echo     Write-Host "Skipping Python check as per config.json" -ForegroundColor Yellow
echo     $pythonPath = ^(Get-Command python -ErrorAction SilentlyContinue^).Source
echo }

echo if ^(-not $skipPythonDependencies^) {
echo     if ^($pythonPath^) {
echo         Write-Host ""
echo         Write-Host "Installing required Python packages: cryptography, colorama..." -ForegroundColor White
echo         Write-Host ""
echo         Write-Host "Upgrading pip..." -ForegroundColor Gray
echo         ^& $pythonPath -m pip install --upgrade pip
echo         Write-Host "Installing required Python packages: cryptography, colorama..." -ForegroundColor Gray
echo         ^& $pythonPath -m pip install cryptography colorama
echo         if ^($LASTEXITCODE -eq 0^) {
echo             Write-Host ""
echo             Write-Host "=========================================================" -ForegroundColor Green
echo             Write-Host " Python and required packages installed successfully!" -ForegroundColor Green
echo             Write-Host "=========================================================" -ForegroundColor Green
echo             Write-Host ""
echo         } else {
echo             Write-Host "ERROR: Failed to install one or more packages." -ForegroundColor Red
echo         }
echo     } else {
echo         Write-Host "ERROR: Python not found and cannot install dependencies." -ForegroundColor Red
echo     }
echo } else {
echo     Write-Host "Skipping Python dependencies installation as per config.json" -ForegroundColor Yellow
echo }

:: Ask to run patcher
echo Write-Host "=========================================================" -ForegroundColor White
echo Write-Host "  Dependencies installed!" -ForegroundColor DarkGreen
echo Write-Host "=========================================================" -ForegroundColor White
echo Write-Host ""
echo $runPatcher = Read-Host "Do you want to run the edit the config.json? (Needed for first run) (y/n)"
echo if ($runPatcher -eq "y" -or $runPatcher -eq "Y"^) {
echo    Write-Host "Opening config.json in Notepad..." -ForegroundColor Green
echo    Start-Process notepad.exe -ArgumentList "config.json"
echo }
echo $runPatcher = Read-Host "Do you want to run the patcher now? (y/n)"
echo if ^($runPatcher -eq "y" -or $runPatcher -eq "Y"^) {
echo     if ^($pythonPath^) {
echo         Write-Host "Running patcher..." -ForegroundColor Green
echo         ^& $pythonPath abletonCracker.py
echo     } else {
echo         Write-Host "ERROR: Python not found. Cannot run patcher." -ForegroundColor Red
echo     }
echo }
echo else {
echo     Write-Host "You can run the patcher later by executing: python abletonCracker.py" -ForegroundColor Yellow
echo     Write-Host "You can also always undo the patch by running: python abletonCracker.py --undo" -ForegroundColor Yellow
echo }
) > "%TEMP_PS%"

:: Run the PowerShell script with execution policy bypass
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%"

:: Delete temporary script
del "%TEMP_PS%" >nul 2>&1

pause
exit /b 0
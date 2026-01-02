@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"

set "TEMP_PS=%TEMP%\install_dependencies_temp.ps1"

(
echo $ErrorActionPreference = "Stop"
echo Set-Location "%SCRIPT_DIR%"
echo.

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
echo ""

echo $skipPythonCheck = $false
echo $skipPythonDependencies = $false
echo if ^(Test-Path "config.json"^) {
echo     try {
echo         $configContent = Get-Content "config.json" -Raw
echo         if ^($configContent -match '"skipPythonCheck"\s*:\s*true'^) { $skipPythonCheck = $true }
echo         if ^($configContent -match '"skipPythonDependencies"\s*:\s*true'^) { $skipPythonDependencies = $true }
echo     } catch {
echo         Write-Host "Warning: Error reading config.json, using defaults" -ForegroundColor Yellow
echo     }
echo }

echo if ^(-not $skipPythonCheck^) {
echo     Write-Host ""
echo     Write-Host "=========================================================" -ForegroundColor White
echo     Write-Host "  Checking for Python installation..." -ForegroundColor White
echo     Write-Host "=========================================================" -ForegroundColor White
echo     $pythonPath = ^(Get-Command python -ErrorAction SilentlyContinue^).Source
echo     if ^(-not $pythonPath^) {
echo         Write-Host "Python not found. Installing via winget..." -ForegroundColor White
echo         if ^(-not ^(Get-Command winget -ErrorAction SilentlyContinue^)^) {
echo             Write-Host "ERROR: winget not available." -ForegroundColor Red
echo             exit 1
echo         }
echo         winget install --id Python.Python.3 -e --source winget
echo         $pythonPath = ^(Get-Command python -ErrorAction SilentlyContinue^).Source
echo         if ^(-not $pythonPath^) {
echo             Write-Host "ERROR: Python installation failed." -ForegroundColor Red
echo             exit 1
echo         }
echo     } else {
echo         Write-Host "Python found: $pythonPath" -ForegroundColor Green
echo     }
echo } else {
echo     Write-Host "Skipping Python check (config.json)" -ForegroundColor Yellow
echo     $pythonPath = ^(Get-Command python -ErrorAction SilentlyContinue^).Source
echo }

echo if ^(-not $skipPythonDependencies^) {
echo     if ^($pythonPath^) {
echo         Write-Host ""
echo         Write-Host "Installing Python dependencies..." -ForegroundColor White
echo         ^& $pythonPath -m pip install --upgrade pip
echo         ^& $pythonPath -m pip install cryptography colorama
echo     } else {
echo         Write-Host "ERROR: Python not found." -ForegroundColor Red
echo     }
echo } else {
echo     Write-Host "Skipping Python dependencies (config.json)" -ForegroundColor Yellow
echo }

echo Write-Host ""
echo Write-Host "=========================================================" -ForegroundColor White
echo Write-Host "  Dependencies installed!" -ForegroundColor DarkGreen
echo Write-Host "=========================================================" -ForegroundColor White
echo ""

echo $editConfig = Read-Host "Edit config.json now? (y/n)"
echo if ^($editConfig -match '^[Yy]'^) {
echo     notepad "$PWD\config.json"
echo }

echo $runPatcher = Read-Host "Run patcher now? (y/n)"
echo if ^($runPatcher -match '^[Yy]'^) {
echo     if ^($pythonPath^) {
echo         Write-Host "Running patcher..." -ForegroundColor Green
echo         ^& $pythonPath "$PWD\abletonCracker.py"
echo     } else {
echo         Write-Host "ERROR: Python not found." -ForegroundColor Red
echo     }
echo } else {
echo     Write-Host "Run later with: python abletonCracker.py" -ForegroundColor Yellow
echo }

) > "%TEMP_PS%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%"

del "%TEMP_PS%" >nul 2>&1

pause
exit /b 0

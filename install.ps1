# AutoBiz Engine — Windows Installer (PowerShell)
# Run: iwr -useb https://autobiz.ai/install.ps1 | iex

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "AutoBiz Installer"

Write-Host ""
Write-Host "  AutoBiz Engine — installer" -ForegroundColor Cyan
Write-Host ""

# ─── Check Docker ────────────────────────────────
try {
  $dockerVersion = docker --version 2>$null
  $composeVersion = "docker compose version" | cmd /c 2>$null
  if (-not $dockerVersion) { throw "Docker not found" }
  Write-Host "  ✓ Docker detected" -ForegroundColor Green
} catch {
  Write-Host "  ✗ Docker Desktop is required" -ForegroundColor Red
  Write-Host "    Install: https://docs.docker.com/get-docker/"
  exit 1
}

# ─── Check Python ────────────────────────────────
$python = $null
try { $python = (Get-Command python3 -ErrorAction Stop).Source } catch {}
if (-not $python) {
  try { $python = (Get-Command python -ErrorAction Stop).Source } catch {}
}
if (-not $python) {
  Write-Host "  ✗ Python 3.9+ is required" -ForegroundColor Red
  Write-Host "    Install: https://www.python.org/downloads/"
  exit 1
}
$pyVer = & $python --version 2>&1
Write-Host "  ✓ $pyVer" -ForegroundColor Green

# ─── Install location ────────────────────────────
$installDir = "$env:USERPROFILE\.autobiz"
$appDir = "$installDir\app"
$venvDir = "$installDir\venv"
$binDir = "$installDir\bin"

New-Item -ItemType Directory -Force -Path $appDir | Out-Null
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

# ─── Download project ────────────────────────────
Write-Host "  ℹ Downloading AutoBiz..." -ForegroundColor DarkGray
$repo = "https://github.com/autobiz/autobiz-engine.git"
if (Test-Path "$appDir\.git") {
  Push-Location $appDir; git pull --ff-only 2>$null; Pop-Location
} else {
  git clone --depth 1 $repo $appDir 2>$null
  if (-not $?) {
    Write-Host "  ⚠ Git clone failed, copying local files" -ForegroundColor Yellow
    Copy-Item -Recurse -Force "$PSScriptRoot\*" $appDir
  }
}
Write-Host "  ✓ Project downloaded" -ForegroundColor Green

# ─── Setup virtualenv ────────────────────────────
if (-not (Test-Path "$venvDir\Scripts\python.exe")) {
  Write-Host "  ℹ Creating virtualenv..." -ForegroundColor DarkGray
  & $python -m venv $venvDir
}
Write-Host "  ℹ Installing dependencies..." -ForegroundColor DarkGray
& "$venvDir\Scripts\pip" install -q -r "$appDir\backend\requirements.txt" 2>$null
& "$venvDir\Scripts\pip" install -q -r "$appDir\tui\requirements.txt" 2>$null
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# ─── Generate .env ───────────────────────────────
if (-not (Test-Path "$appDir\.env")) {
  Copy-Item "$appDir\.env.example" "$appDir\.env"
  Write-Host "  ✓ .env created" -ForegroundColor Green
}

# ─── Auto-generate SECRET_KEY ────────────────────
$envContent = Get-Content "$appDir\.env" -Raw
if (-not ($envContent -match "SECRET_KEY=")) {
  $key = & $python -c "import secrets; print(secrets.token_hex(32))"
  Add-Content "$appDir\.env" "SECRET_KEY=$key"
  Write-Host "  ✓ SECRET_KEY auto-generated" -ForegroundColor Green
}

# ─── Create wrapper script ───────────────────────
$wrapperPath = "$binDir\autobiz.cmd"
@"
@echo off
set ROOT=%USERPROFILE%\.autobiz\app
set VENV=%USERPROFILE%\.autobiz\venv
cd /d "%ROOT%"

docker compose up -d db redis >nul 2>&1

set PYTHONPATH=%ROOT%\backend
start /B "" "%VENV%\Scripts\uvicorn" backend.app.main:app --host 0.0.0.0 --port 8000 --log-level warning >nul 2>&1

for /l %%i in (1,1,30) do (
  curl -sf http://localhost:8000/health >nul 2>&1 && goto :RUN
  timeout /t 1 /nobreak >nul
)

:RUN
"%VENV%\Scripts\python" "%ROOT%\tui\main.py"
"@ | Out-File -FilePath $wrapperPath -Encoding ascii

Write-Host "  ✓ Wrapper created at $wrapperPath" -ForegroundColor Green

# ─── Add to PATH ─────────────────────────────────
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$binDir*") {
  $newPath = "$userPath;$binDir"
  [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
  $env:Path = "$env:Path;$binDir"
  Write-Host "  ✓ Added to PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Run:  autobiz" -ForegroundColor Cyan
Write-Host "  Or:   $wrapperPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Config: $appDir\.env" -ForegroundColor DarkGray
Write-Host ""

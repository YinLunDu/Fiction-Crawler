param(
    [string]$Name = ".venv",
    [switch]$InstallRequirements
)

function Write-Info($m) { Write-Host $m -ForegroundColor Cyan }
function Write-Succ($m) { Write-Host $m -ForegroundColor Green }
function Write-Err($m) { Write-Host $m -ForegroundColor Red }

# Work from the script directory so it behaves the same regardless of pwd
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$venvPath = Join-Path $ScriptDir $Name

Write-Info "Project dir: $ScriptDir"
Write-Info "Virtual env path: $venvPath"

function Test-Python {
    try {
        # Use Get-Command to ensure 'python' is available; send output to null to avoid unused variable
        Get-Command python -ErrorAction Stop > $null
        return $true
    } catch {
        Write-Err "Python not found in PATH. Please install Python 3.8+ and add to PATH."
        return $false
    }
}

if (-not (Test-Python)) { throw "Missing python executable" }

if (-not (Test-Path $venvPath)) {
    Write-Info "Virtual environment not found. Creating..."
    & python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create virtual environment (exit $LASTEXITCODE)"; throw "venv creation failed" }
    Write-Succ "Created venv at: $venvPath"
} else {
    Write-Info "Virtual environment already exists."
}

$activateScript = Join-Path $venvPath 'Scripts\Activate.ps1'
if (-not (Test-Path $activateScript)) {
    Write-Err "Activate script not found at $activateScript"
    throw "activate script missing"
}

Write-Info "Dot-sourcing activate script: $activateScript"
# Dot-source the venv activate script so the activation affects the current session
. $activateScript

if ($InstallRequirements) {
    $req = Join-Path $ScriptDir 'requirements.txt'
    if (Test-Path $req) {
        Write-Info "Installing from requirements.txt..."
        pip install -r $req
        if ($LASTEXITCODE -eq 0) { Write-Succ "Requirements installed." } else { Write-Err "pip install returned exit code $LASTEXITCODE" }
    } else {
        Write-Info "No requirements.txt found at $req"
    }
}

Write-Succ "Virtual environment '$Name' activated."

Write-Host ""
Write-Info "Reminder: to activate in your current PowerShell session run dot-source:"
Write-Host "  . .\ActivateVenv.ps1 -Name $Name" -ForegroundColor Yellow

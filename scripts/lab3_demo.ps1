<#
.SYNOPSIS
    Lab 3 demo - config split, DB isolation, security modes and the CI mirror.

.DESCRIPTION
    1. Ensures the sandbox and production env files and databases exist, and runs
       migrations against each (isolated databases).
    2. Prints the resolved config under each environment (different database,
       different DEBUG) - proving the config split.
    3. Starts the API under sandbox (DEBUG on) and under production (DEBUG off),
       triggers a 500, and shows the error body is detailed in sandbox but generic
       in production (no stacktrace).
    4. Runs ruff + pytest locally, mirroring the CI pipeline.

.EXAMPLE
    ./scripts/lab3_demo.ps1
#>
[CmdletBinding()]
param(
    [string]$Python = ".venv/Scripts/python.exe",
    [string]$ApiHost = "127.0.0.1",
    [int]$Port = 8011
)

$ErrorActionPreference = "Stop"
$base = "http://${ApiHost}:${Port}"

function Write-Head { param([string]$Text) Write-Host ""; Write-Host "=== $Text ===" -ForegroundColor Cyan }

function Invoke-ErrorDemo {
    param([string]$Url)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing
        return [pscustomobject]@{ Status = [int]$r.StatusCode; Body = $r.Content }
    }
    catch {
        $resp = $_.Exception.Response
        $status = if ($resp) { [int]$resp.StatusCode } else { -1 }
        $body = $null
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            $body = $_.ErrorDetails.Message
        }
        elseif ($resp) {
            $body = (New-Object System.IO.StreamReader($resp.GetResponseStream())).ReadToEnd()
        }
        return [pscustomobject]@{ Status = $status; Body = $body }
    }
}

function Start-Api {
    param([string]$AppEnv)
    $env:APP_ENV = $AppEnv
    $proc = Start-Process -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", $ApiHost, "--port", "$Port", "--log-level", "critical") `
        -PassThru -NoNewWindow
    for ($i = 0; $i -lt 40; $i++) {
        try {
            $h = Invoke-WebRequest "$base/health" -UseBasicParsing -TimeoutSec 2
            if ([int]$h.StatusCode -eq 200) { return $proc }
        }
        catch { Start-Sleep -Milliseconds 500 }
    }
    throw "API under APP_ENV=$AppEnv did not become ready."
}

function Stop-Api { param($Proc) if ($Proc -and -not $Proc.HasExited) { Stop-Process -Id $Proc.Id -Force } }

Write-Host "Cyber-Implant Cloud - Lab 3 demo" -ForegroundColor White

# --- 1. Env files + isolated databases ------------------------------------
Write-Head "Prepare environments (config split + DB isolation)"
foreach ($name in @("sandbox", "production")) {
    $real = "config/.env.$name"
    if (-not (Test-Path $real)) {
        Copy-Item "config/.env.$name.example" $real
        Write-Host "created $real from template" -ForegroundColor DarkGray
    }
}
& $Python -m scripts.init_databases
if ($LASTEXITCODE -ne 0) { throw "Database init failed." }

foreach ($name in @("sandbox", "production")) {
    $env:APP_ENV = $name
    Write-Host "migrating '$name' database..." -ForegroundColor DarkGray
    & $Python -m alembic upgrade head | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Migration failed for $name." }
}

# --- 2. Resolved config per environment -----------------------------------
Write-Head "Resolved configuration per environment"
foreach ($name in @("sandbox", "production")) {
    $env:APP_ENV = $name
    Write-Host "$name ->" -ForegroundColor Yellow -NoNewline
    & $Python -m scripts.show_config
}

# --- 3. Security modes: detailed vs generic 500 ---------------------------
Write-Head "Security modes - 500 handling"
$api = $null
try {
    $api = Start-Api -AppEnv "sandbox"
    $r = Invoke-ErrorDemo -Url "$base/internal/demo-error"
    Write-Host "sandbox (DEBUG on)  -> HTTP $($r.Status)" -ForegroundColor Yellow
    Write-Host "  $($r.Body)" -ForegroundColor DarkGray
}
finally { Stop-Api $api }

$api = $null
try {
    $api = Start-Api -AppEnv "production"
    $r = Invoke-ErrorDemo -Url "$base/internal/demo-error"
    Write-Host "production (DEBUG off) -> HTTP $($r.Status)" -ForegroundColor Yellow
    Write-Host "  $($r.Body)" -ForegroundColor DarkGray
    if ($r.Body -match "Deliberate demo error") {
        throw "Production leaked the internal error message."
    }
    Write-Host "  (no stacktrace / internal detail leaked)" -ForegroundColor Green
}
finally { Stop-Api $api }

# --- 4. CI mirror: lint + tests -------------------------------------------
Write-Head "CI mirror - ruff + pytest"
Remove-Item Env:APP_ENV -ErrorAction SilentlyContinue
& $Python -m ruff check .
if ($LASTEXITCODE -ne 0) { throw "ruff check failed." }
& $Python -m ruff format --check .
if ($LASTEXITCODE -ne 0) { throw "ruff format check failed." }
& $Python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed." }

Write-Host ""
Write-Host "All Lab 3 checks passed." -ForegroundColor Green

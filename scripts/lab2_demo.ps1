<#
.SYNOPSIS
    Lab 2 demo - users, roles, RBAC and the OTA MVP flow.

.DESCRIPTION
    Seeds an admin, then walks the full business flow end to end: register two
    regular users, log everyone in, register an implant, publish firmware, launch
    a rollout, view and report OTA jobs. Finishes with the RBAC negative paths the
    lab requires: anonymous -> 401, vertical -> 403, horizontal (IDOR) -> 403.

    Each run uses a unique suffix, so it is safe to re-run against a live stack.

.EXAMPLE
    ./scripts/lab2_demo.ps1
    ./scripts/lab2_demo.ps1 -BaseUrl http://localhost:8000
#>
[CmdletBinding()]
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Python = ".venv/Scripts/python.exe"
)

$ErrorActionPreference = "Stop"
$api = "$BaseUrl/api/v1"
$runId = Get-Date -Format "HHmmss"
$step = 0

$adminEmail = "admin@cyberimplant.dev"
$adminPassword = "admin-password-123"

function Invoke-Api {
    param(
        [string]$Method,
        [string]$Uri,
        [object]$Body,
        [int]$ExpectStatus,
        [hashtable]$Headers,
        [string]$Title
    )

    $script:step++
    Write-Host ""
    Write-Host ("[{0:d2}] {1}" -f $script:step, $Title) -ForegroundColor Cyan
    Write-Host ("     {0} {1}" -f $Method, $Uri) -ForegroundColor DarkGray

    $params = @{
        Method          = $Method
        Uri             = $Uri
        UseBasicParsing = $true
        ContentType     = "application/json"
    }
    if ($null -ne $Body) { $params.Body = ($Body | ConvertTo-Json -Depth 6 -Compress) }
    if ($null -ne $Headers) { $params.Headers = $Headers }

    $status = $null
    $content = $null
    try {
        $response = Invoke-WebRequest @params
        $status = [int]$response.StatusCode
        $content = $response.Content
    }
    catch {
        $failed = $_.Exception.Response
        if ($null -eq $failed) { throw }
        $status = [int]$failed.StatusCode
    }

    if ($status -ne $ExpectStatus) {
        throw "Expected HTTP $ExpectStatus but got $status for $Method $Uri"
    }
    Write-Host ("     -> {0} (expected {1})" -f $status, $ExpectStatus) -ForegroundColor Green

    if ($content) { return ($content | ConvertFrom-Json) }
    return $null
}

function Get-AuthHeader {
    param([string]$Email, [string]$Password)
    $login = Invoke-Api -Method POST -Uri "$api/auth/login" -ExpectStatus 200 `
        -Title "Log in as $Email" -Body @{ email = $Email; password = $Password }
    return @{ Authorization = "Bearer $($login.access_token)" }
}

Write-Host "Cyber-Implant Cloud - Lab 2 demo against $BaseUrl (run $runId)" -ForegroundColor White

# Admins cannot self-register through the API; seed one first.
Write-Host ""
Write-Host "Seeding admin account..." -ForegroundColor DarkGray
& $Python -m scripts.seed_admin --email $adminEmail --password $adminPassword
if ($LASTEXITCODE -ne 0) { throw "Admin seeding failed." }

Invoke-Api -Method GET -Uri "$BaseUrl/health" -ExpectStatus 200 -Title "Liveness probe" | Out-Null
Invoke-Api -Method GET -Uri "$BaseUrl/health/ready" -ExpectStatus 200 `
    -Title "Readiness probe (checks the database)" | Out-Null

# --- Accounts -------------------------------------------------------------
$alice = "alice-$runId@example.com"
$bob = "bob-$runId@example.com"
$pw = "password123"

Invoke-Api -Method POST -Uri "$api/auth/register" -ExpectStatus 201 `
    -Title "Register regular user Alice" -Body @{ email = $alice; password = $pw } | Out-Null
Invoke-Api -Method POST -Uri "$api/auth/register" -ExpectStatus 201 `
    -Title "Register regular user Bob" -Body @{ email = $bob; password = $pw } | Out-Null

$adminHdr = Get-AuthHeader -Email $adminEmail -Password $adminPassword
$aliceHdr = Get-AuthHeader -Email $alice -Password $pw
$bobHdr = Get-AuthHeader -Email $bob -Password $pw

# --- Happy path -----------------------------------------------------------
$implant = Invoke-Api -Method POST -Uri "$api/implants" -ExpectStatus 201 -Headers $aliceHdr `
    -Title "Alice registers her implant" `
    -Body @{ serial_number = "SN-$runId"; model = "neuro-x"; current_firmware_version = "0.9.0" }

$firmware = Invoke-Api -Method POST -Uri "$api/firmware" -ExpectStatus 201 -Headers $adminHdr `
    -Title "Admin publishes a firmware version" `
    -Body @{
        version          = "2.0.0-$runId"
        checksum_sha256  = ("a" * 64)
        artifact_url     = "https://artifacts.local/fw-$runId.bin"
        release_notes    = "Lab 2 demo release"
    }

$rollout = Invoke-Api -Method POST -Uri "$api/ota/rollouts" -ExpectStatus 201 -Headers $adminHdr `
    -Title "Admin launches a rollout to Alice's implant" `
    -Body @{ firmware_version_id = $firmware.id; implant_ids = @($implant.id) }
Write-Host ("     jobs created: {0}" -f $rollout.jobs_created) -ForegroundColor DarkGray

$jobs = Invoke-Api -Method GET -Uri "$api/ota/jobs" -ExpectStatus 200 -Headers $aliceHdr `
    -Title "Alice views OTA jobs for her implant"
Write-Host ("     Alice sees {0} job(s)" -f @($jobs).Count) -ForegroundColor DarkGray

Invoke-Api -Method POST -Uri "$api/ota/jobs/$($rollout.job_ids[0])/status" -ExpectStatus 200 `
    -Headers $aliceHdr -Title "Alice reports the update succeeded" `
    -Body @{ status = "succeeded" } | Out-Null

Invoke-Api -Method GET -Uri "$api/me/dashboard" -ExpectStatus 200 -Headers $aliceHdr `
    -Title "Alice's user dashboard" | Out-Null
Invoke-Api -Method GET -Uri "$api/admin/dashboard" -ExpectStatus 200 -Headers $adminHdr `
    -Title "Admin dashboard" | Out-Null

# --- RBAC negative paths --------------------------------------------------
Write-Host ""
Write-Host "--- RBAC negative paths --------------------------------------------" -ForegroundColor White

Invoke-Api -Method GET -Uri "$api/implants" -ExpectStatus 401 `
    -Title "Anonymous access is rejected (401)" | Out-Null

Invoke-Api -Method POST -Uri "$api/firmware" -ExpectStatus 403 -Headers $bobHdr `
    -Title "Regular user cannot publish firmware - vertical RBAC (403)" `
    -Body @{ version = "9.9.9"; checksum_sha256 = ("b" * 64); artifact_url = "https://x/y.bin" } | Out-Null

Invoke-Api -Method PATCH -Uri "$api/implants/$($implant.id)" -ExpectStatus 403 -Headers $bobHdr `
    -Title "Bob cannot modify Alice's implant - IDOR (403)" `
    -Body @{ status = "quarantined" } | Out-Null

Write-Host ""
Write-Host "All Lab 2 checks passed." -ForegroundColor Green

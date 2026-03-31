# Start MethLab API as a detached Windows process
# Usage: powershell -File scripts/run_api.ps1 [-Stop] [-Status]

param(
    [switch]$Stop,
    [switch]$Status
)

$Port = 8020
$PidFile = Join-Path $PSScriptRoot ".api.pid"
$VenvPython = Join-Path (Split-Path $PSScriptRoot) ".venv\Scripts\python.exe"
$WorkDir = Join-Path (Split-Path $PSScriptRoot) "apps\api"

function Get-ApiProcess {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile
        try {
            return Get-Process -Id $pid -ErrorAction Stop
        } catch {
            Remove-Item $PidFile -ErrorAction SilentlyContinue
        }
    }
    return $null
}

if ($Status) {
    $proc = Get-ApiProcess
    if ($proc) {
        Write-Host "API is running (PID: $($proc.Id))"
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:$Port/health" -UseBasicParsing -TimeoutSec 3
            Write-Host "Health: $($r.Content)"
        } catch {
            Write-Host "Warning: Process running but not responding on port $Port"
        }
    } else {
        Write-Host "API is not running"
    }
    exit
}

if ($Stop) {
    $proc = Get-ApiProcess
    if ($proc) {
        Write-Host "Stopping API (PID: $($proc.Id))..."
        Stop-Process -Id $proc.Id -Force
        Remove-Item $PidFile -ErrorAction SilentlyContinue
        Write-Host "Stopped."
    } else {
        Write-Host "API is not running."
    }
    exit
}

# Stop existing instance
$existing = Get-ApiProcess
if ($existing) {
    Write-Host "Stopping existing API (PID: $($existing.Id))..."
    Stop-Process -Id $existing.Id -Force
    Start-Sleep -Seconds 2
}

# Start new instance
Write-Host "Starting MethLab API on port $Port..."
$proc = Start-Process -FilePath $VenvPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$Port" `
    -WorkingDirectory $WorkDir `
    -WindowStyle Hidden `
    -PassThru

$proc.Id | Out-File $PidFile -Encoding ascii
Write-Host "API started (PID: $($proc.Id))"
Write-Host "Health check: http://localhost:$Port/health"

# Wait for startup
Start-Sleep -Seconds 3
try {
    $r = Invoke-WebRequest -Uri "http://localhost:$Port/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "OK: $($r.Content)"
} catch {
    Write-Host "Warning: API may still be starting..."
}

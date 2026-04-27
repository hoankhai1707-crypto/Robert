# =============================================================
# Windows Task Scheduler Setup — Daily 4AM AI Workflow
# Run this ONCE as Administrator to register the scheduled task.
# =============================================================
# Usage:
#   Right-click PowerShell → "Run as Administrator"
#   cd C:\path\to\Robert
#   .\setup_task_scheduler.ps1
#
# Optional flags:
#   -Time "06:00"        Change the trigger time (default: 04:00)
#   -WakePC              Wake the PC from sleep at trigger time
#   -Uninstall           Remove the scheduled task
# =============================================================

param(
    [string]$Time      = "04:00",
    [switch]$WakePC,
    [switch]$Uninstall
)

$TaskName   = "Daily AI Content Workflow"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunnerPath = Join-Path $ScriptDir "run_daily_workflow.ps1"

# ── Uninstall mode ───────────────────────────────────────────
if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Task '$TaskName' removed." -ForegroundColor Yellow
    exit 0
}

# ── Verify runner script exists ──────────────────────────────
if (-not (Test-Path $RunnerPath)) {
    Write-Host "ERROR: Runner script not found at: $RunnerPath" -ForegroundColor Red
    Write-Host "Make sure you are running this from the Robert repo folder." -ForegroundColor Red
    exit 1
}

# ── Build scheduled task components ─────────────────────────
$psArgs = "-NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunnerPath`""

$action = New-ScheduledTaskAction `
    -Execute  "powershell.exe" `
    -Argument $psArgs

$trigger = New-ScheduledTaskTrigger -Daily -At $Time

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit      (New-TimeSpan -Hours 2) `
    -StartWhenAvailable                               `
    -WakeToRun:$WakePC.IsPresent                      `
    -MultipleInstances       IgnoreNew                `
    -RestartCount            2                        `
    -RestartInterval         (New-TimeSpan -Minutes 5)

$principal = New-ScheduledTaskPrincipal `
    -UserId   $env:USERNAME `
    -LogonType Interactive  `
    -RunLevel Highest

# ── Register the task ────────────────────────────────────────
$task = Register-ScheduledTask `
    -TaskName   $TaskName `
    -Description "Daily AI research workflow: trends → ClickUp → Google Drive → Gmail (hoankhai1707@gmail.com)" `
    -Action     $action `
    -Trigger    $trigger `
    -Settings   $settings `
    -Principal  $principal `
    -Force

if ($task) {
    Write-Host ""
    Write-Host "Task scheduled successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Name    : $TaskName"               -ForegroundColor Cyan
    Write-Host "  Runs at : $Time daily"             -ForegroundColor Cyan
    Write-Host "  Script  : $RunnerPath"             -ForegroundColor Cyan
    Write-Host "  Wake PC : $($WakePC.IsPresent)"    -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Manage it anytime in: Task Scheduler → Task Scheduler Library" -ForegroundColor Gray
    Write-Host "Or run: schtasks /query /tn `"$TaskName`" /fo LIST"           -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test it right now (won't wait for 4AM):"                   -ForegroundColor Yellow
    Write-Host "  powershell -File `"$RunnerPath`" -DryRun"                   -ForegroundColor Yellow
    Write-Host "  powershell -File `"$RunnerPath`""                           -ForegroundColor Yellow
} else {
    Write-Host "ERROR: Failed to register task. Try running as Administrator." -ForegroundColor Red
    exit 1
}

# =============================================================
# Daily 4AM AI Content Research Workflow — Windows Runner
# For: hoankhai1707@gmail.com
# =============================================================
# This script is called automatically by Windows Task Scheduler.
# Do NOT run this manually unless testing.
# =============================================================

param(
    [string]$Model = "claude-sonnet-4-6",
    [switch]$DryRun  # Pass -DryRun to test without calling Claude
)

$ErrorActionPreference = "Continue"

# ── Paths ────────────────────────────────────────────────────
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$PromptFile = Join-Path $ScriptDir "daily_ai_prompt.md"
$LogDir     = Join-Path $ScriptDir "logs"
$Date       = Get-Date -Format "yyyy-MM-dd"
$LogFile    = Join-Path $LogDir "workflow_$Date.log"

# ── Ensure log directory exists ──────────────────────────────
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

function Write-Log($msg) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Add-Content -Path $LogFile -Value $line
    Write-Host $line
}

Write-Log "============================================"
Write-Log "Daily AI Workflow — $Date"
Write-Log "============================================"

# ── Find Claude CLI ──────────────────────────────────────────
$ClaudePath = $null

# Check common install locations in order of preference
$candidates = @(
    "claude",                                                   # Already in PATH
    "$env:APPDATA\npm\claude.cmd",                             # npm global install
    "$env:LOCALAPPDATA\Programs\claude\claude.exe",            # Standalone installer
    "C:\Program Files\claude\claude.exe",                      # System-wide installer
    "$env:USERPROFILE\.claude\local\claude.exe"                # User-local install
)

foreach ($c in $candidates) {
    try {
        $resolved = Get-Command $c -ErrorAction SilentlyContinue
        if ($resolved) { $ClaudePath = $resolved.Source; break }
    } catch {}
}

# WSL fallback: call claude inside WSL if Windows claude not found
$UseWSL = $false
if (-not $ClaudePath) {
    $wslCheck = Get-Command wsl -ErrorAction SilentlyContinue
    if ($wslCheck) {
        Write-Log "Windows Claude CLI not found — falling back to WSL"
        $UseWSL = $true
    } else {
        Write-Log "ERROR: Claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code"
        exit 1
    }
}

if ($ClaudePath) { Write-Log "Using Claude at: $ClaudePath" }
if ($UseWSL)     { Write-Log "Using Claude via WSL" }

# ── Load and prepare prompt ──────────────────────────────────
if (-not (Test-Path $PromptFile)) {
    Write-Log "ERROR: Prompt file not found at $PromptFile"
    exit 1
}

$Prompt = Get-Content -Path $PromptFile -Raw -Encoding UTF8
$Prompt = $Prompt -replace "\{\{DATE\}\}", $Date

Write-Log "Prompt loaded ($($Prompt.Length) chars). Starting Claude..."

if ($DryRun) {
    Write-Log "DRY RUN — skipping Claude call. Prompt preview:"
    Add-Content -Path $LogFile -Value ($Prompt | Select-Object -First 20)
    Write-Log "DRY RUN complete."
    exit 0
}

# ── Run Claude ───────────────────────────────────────────────
$startTime = Get-Date

if ($UseWSL) {
    # Pass prompt via stdin to WSL claude
    $Prompt | wsl claude --model $Model --print 2>&1 | Tee-Object -FilePath $LogFile -Append
} else {
    # Native Windows — pass prompt via stdin
    $Prompt | & $ClaudePath --model $Model --print 2>&1 | Tee-Object -FilePath $LogFile -Append
}

$elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)

if ($LASTEXITCODE -eq 0) {
    Write-Log "Workflow completed successfully in ${elapsed}s"
} else {
    Write-Log "Workflow exited with code $LASTEXITCODE after ${elapsed}s"
}

Write-Log "Log saved: $LogFile"

# Setup checker for the Web of Science skills (Windows).
#
# Run it from inside this repo folder, in PowerShell:
#     powershell -ExecutionPolicy Bypass -File scripts\setup-wos.ps1
#
# It only inspects your machine and reports what it finds. It installs
# nothing and changes no settings, so it is safe to run as many times as
# you like.

$problems = 0

function Show-Ok   { param($m) Write-Host "  [ OK ] " -ForegroundColor Green  -NoNewline; Write-Host $m }
function Show-Bad  { param($m) Write-Host "  [MISS] " -ForegroundColor Red    -NoNewline; Write-Host $m }
function Show-Warn { param($m) Write-Host "  [ ?? ] " -ForegroundColor Yellow -NoNewline; Write-Host $m }
function Show-Info { param($m) Write-Host "         $m" -ForegroundColor DarkGray }
function Show-Head { param($m) Write-Host ""; Write-Host $m -ForegroundColor White }

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "  Web of Science skills - setup check"
Write-Host "========================================" -ForegroundColor Blue

# ---------------------------------------------------------------- 1. Node.js
Show-Head "1. Node.js (needed to start the browser connector)"
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVersion = (& node --version 2>$null)
    $nodeMajor = 0
    if ($nodeVersion -match '^v(\d+)') { $nodeMajor = [int]$Matches[1] }
    if ($nodeMajor -ge 18) {
        Show-Ok "Node.js $nodeVersion"
    } else {
        Show-Warn "Node.js $nodeVersion is older than v18"
        Show-Info "Update it at https://nodejs.org (pick the LTS button)"
        $problems++
    }
} else {
    Show-Bad "Node.js is not installed"
    Show-Info "Download the LTS version from https://nodejs.org and run the installer,"
    Show-Info "then open a new PowerShell window and run this script again."
    $problems++
}

# ------------------------------------------------------------ 2. Claude Code
Show-Head "2. Claude Code"
$claude = Get-Command claude -ErrorAction SilentlyContinue
if ($claude) {
    $claudeVersion = (& claude --version 2>$null | Select-Object -First 1)
    Show-Ok "Claude Code $claudeVersion"
} else {
    Show-Bad "The 'claude' command was not found"
    Show-Info "Install it with:  npm install -g @anthropic-ai/claude-code"
    $problems++
}

# ------------------------------------------------------------------ 3. Chrome
Show-Head "3. Google Chrome"
$chromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
$chromeFound = $chromePaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if ($chromeFound) {
    Show-Ok "Found at $chromeFound"
} else {
    Show-Bad "Chrome was not found in the usual places"
    Show-Info "Install it from https://www.google.com/chrome/"
    Show-Info "(If Chrome is installed somewhere unusual you can ignore this.)"
    $problems++
}

# ------------------------------------------------- 4. Skills present in repo
Show-Head "4. Web of Science skills in this folder"
$repoRoot = Split-Path -Parent $PSScriptRoot
$missingSkill = $false
foreach ($skill in @('wos-search','wos-paper-detail','wos-navigate-pages',
                     'wos-parse-results','wos-download','wos-export')) {
    if (Test-Path (Join-Path $repoRoot ".claude\skills\$skill\SKILL.md")) {
        Show-Ok $skill
    } else {
        Show-Bad "$skill is missing"
        $missingSkill = $true
    }
}
if (Test-Path (Join-Path $repoRoot ".claude\agents\wos-researcher.md")) {
    Show-Ok "wos-researcher agent"
} else {
    Show-Bad "wos-researcher agent is missing"
    $missingSkill = $true
}
if ($missingSkill) {
    Show-Info "Something is missing. Run 'git pull' in this folder to restore it."
    $problems++
}

# ------------------------------------------------- 5. Browser connector entry
Show-Head "5. Browser connector setting"
$mcpPath = Join-Path $repoRoot ".mcp.json"
if ((Test-Path $mcpPath) -and (Select-String -Path $mcpPath -Pattern 'chrome-devtools' -Quiet)) {
    Show-Ok "chrome-devtools is listed in .mcp.json"
    Show-Info "Claude Code will ask you to approve it the first time you start it here."
} else {
    Show-Bad ".mcp.json is missing the chrome-devtools entry"
    Show-Info "Run 'git pull' in this folder to restore it."
    $problems++
}

# ------------------------------------------------------------------ 6. Zotero
Show-Head "6. Zotero desktop (only needed for exporting citations)"
$zoteroUp = $false
try {
    $client = New-Object System.Net.Sockets.TcpClient
    $connect = $client.BeginConnect("127.0.0.1", 23119, $null, $null)
    if ($connect.AsyncWaitHandle.WaitOne(2000, $false) -and $client.Connected) {
        $zoteroUp = $true
    }
    $client.Close()
} catch { $zoteroUp = $false }

if ($zoteroUp) {
    Show-Ok "Zotero is running and answering on port 23119"
    Show-Info "'/wos-export zotero' will work."
} else {
    Show-Warn "Zotero is not answering on port 23119"
    Show-Info "This is only a problem if you want to export citations to Zotero."
    Show-Info "To fix: open the Zotero desktop app, leave it open, re-run this script."
    Show-Info "Don't have it? Download from https://www.zotero.org/download/"
    Show-Info "Everything else (search, paper details, PDF download) works without it."
}

# ------------------------------------------------------------------- Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
if ($problems -eq 0) {
    Write-Host "  Ready to go." -ForegroundColor Green
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host ""
    Write-Host "  1. In this folder, run:   claude"
    Write-Host "  2. Approve the 'chrome-devtools' server when it asks."
    Write-Host "  3. Type:   /wos-search deep learning"
    Write-Host "  4. A Chrome window opens. Log in to Web of Science in"
    Write-Host "     THAT window with your institutional account, then ask again."
    Write-Host ""
} else {
    $noun = if ($problems -eq 1) { "1 thing needs" } else { "$problems things need" }
    Write-Host "  $noun attention - see above." -ForegroundColor Yellow
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Fix the [MISS] items, then run this script again:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\setup-wos.ps1"
    Write-Host ""
}

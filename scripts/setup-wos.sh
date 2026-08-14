#!/usr/bin/env bash
# Setup checker for the Web of Science skills (macOS / Linux).
#
# Run it from inside this repo folder:
#     bash scripts/setup-wos.sh
#
# It only inspects your machine and reports what it finds. It installs
# nothing and changes no settings, so it is safe to run as many times as
# you like.

set -uo pipefail

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YELLOW=$'\033[0;33m'
BLUE=$'\033[0;34m'; BOLD=$'\033[1m'; OFF=$'\033[0m'

ok()   { printf '  %s[ OK ]%s %s\n'   "$GREEN"  "$OFF" "$1"; }
bad()  { printf '  %s[MISS]%s %s\n'   "$RED"    "$OFF" "$1"; }
warn() { printf '  %s[ ?? ]%s %s\n'   "$YELLOW" "$OFF" "$1"; }
info() { printf '         %s\n' "$1"; }
head2(){ printf '\n%s%s%s\n' "$BOLD" "$1" "$OFF"; }

problems=0
note_problem() { problems=$((problems + 1)); }

printf '\n%s========================================%s\n' "$BLUE" "$OFF"
printf '%s  Web of Science skills - setup check%s\n'      "$BOLD" "$OFF"
printf '%s========================================%s\n'   "$BLUE" "$OFF"

# ---------------------------------------------------------------- 1. Node.js
head2 "1. Node.js (needed to start the browser connector)"
if command -v node >/dev/null 2>&1; then
    node_version=$(node --version 2>/dev/null)
    node_major=$(printf '%s' "$node_version" | sed 's/^v//' | cut -d. -f1)
    if [ "${node_major:-0}" -ge 18 ] 2>/dev/null; then
        ok "Node.js $node_version"
    else
        warn "Node.js $node_version is older than v18"
        info "Update it at https://nodejs.org (pick the LTS button)"
        note_problem
    fi
else
    bad "Node.js is not installed"
    info "Download the LTS version from https://nodejs.org and run the installer,"
    info "then open a new terminal and run this script again."
    note_problem
fi

# ------------------------------------------------------------ 2. Claude Code
head2 "2. Claude Code"
if command -v claude >/dev/null 2>&1; then
    ok "Claude Code $(claude --version 2>/dev/null | head -1)"
else
    bad "The 'claude' command was not found"
    info "Install it with:  npm install -g @anthropic-ai/claude-code"
    note_problem
fi

# ------------------------------------------------------------------ 3. Chrome
head2 "3. Google Chrome"
chrome_found=""
for candidate in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "$(command -v google-chrome 2>/dev/null || true)" \
    "$(command -v google-chrome-stable 2>/dev/null || true)" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)"
do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then chrome_found="$candidate"; break; fi
done
if [ -n "$chrome_found" ]; then
    ok "Found at $chrome_found"
else
    bad "Chrome was not found in the usual places"
    info "Install it from https://www.google.com/chrome/"
    info "(If Chrome is installed somewhere unusual you can ignore this.)"
    note_problem
fi

# ------------------------------------------------- 4. Skills present in repo
head2 "4. Web of Science skills in this folder"
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
missing_skill=0
for skill in wos-search wos-paper-detail wos-navigate-pages \
             wos-parse-results wos-download wos-export; do
    if [ -f "$repo_root/.claude/skills/$skill/SKILL.md" ]; then
        ok "$skill"
    else
        bad "$skill is missing"
        missing_skill=1
    fi
done
if [ -f "$repo_root/.claude/agents/wos-researcher.md" ]; then
    ok "wos-researcher agent"
else
    bad "wos-researcher agent is missing"
    missing_skill=1
fi
if [ "$missing_skill" -eq 1 ]; then
    info "Something is missing. Run 'git pull' in this folder to restore it."
    note_problem
fi

# ------------------------------------------------- 5. Browser connector entry
head2 "5. Browser connector setting"
if [ -f "$repo_root/.mcp.json" ] && grep -q 'chrome-devtools' "$repo_root/.mcp.json" 2>/dev/null; then
    ok "chrome-devtools is listed in .mcp.json"
    info "Claude Code will ask you to approve it the first time you start it here."
else
    bad ".mcp.json is missing the chrome-devtools entry"
    info "Run 'git pull' in this folder to restore it."
    note_problem
fi

# ------------------------------------------------------------------ 6. Zotero
head2 "6. Zotero desktop (only needed for exporting citations)"
zotero_up=0
if command -v curl >/dev/null 2>&1; then
    if curl -s -m 4 -o /dev/null \
            -X POST "http://127.0.0.1:23119/connector/ping" \
            -H "Content-Type: application/json" \
            -H "X-Zotero-Connector-API-Version: 3" \
            -d '{}' 2>/dev/null; then
        zotero_up=1
    fi
fi
if [ "$zotero_up" -eq 0 ] && command -v nc >/dev/null 2>&1; then
    nc -z -w 2 127.0.0.1 23119 >/dev/null 2>&1 && zotero_up=1
fi

if [ "$zotero_up" -eq 1 ]; then
    ok "Zotero is running and answering on port 23119"
    info "'/wos-export zotero' will work."
else
    warn "Zotero is not answering on port 23119"
    info "This is only a problem if you want to export citations to Zotero."
    info "To fix: open the Zotero desktop app, leave it open, re-run this script."
    info "Don't have it? Download from https://www.zotero.org/download/"
    info "Everything else (search, paper details, PDF download) works without it."
fi

# ------------------------------------------------------------------- Summary
printf '\n%s========================================%s\n' "$BLUE" "$OFF"
if [ "$problems" -eq 0 ]; then
    printf '%s  Ready to go.%s\n' "$GREEN" "$OFF"
    printf '========================================%s\n\n' "$OFF"
    printf 'Next steps:\n\n'
    printf '  1. In this folder, run:   %sclaude%s\n' "$BOLD" "$OFF"
    printf '  2. Approve the "chrome-devtools" server when it asks.\n'
    printf '  3. Type:   %s/wos-search deep learning%s\n' "$BOLD" "$OFF"
    printf '  4. A Chrome window opens. Log in to Web of Science in\n'
    printf '     %sthat%s window with your institutional account, then ask again.\n\n' "$BOLD" "$OFF"
else
    if [ "$problems" -eq 1 ]; then
        printf '%s  1 thing needs attention - see above.%s\n' "$YELLOW" "$OFF"
    else
        printf '%s  %d things need attention - see above.%s\n' "$YELLOW" "$problems" "$OFF"
    fi
    printf '========================================%s\n\n' "$OFF"
    printf 'Fix the [MISS] items, then run this script again:\n'
    printf '  %sbash scripts/setup-wos.sh%s\n\n' "$BOLD" "$OFF"
fi

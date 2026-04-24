#!/usr/bin/env bash
# Morning automation workflow — runs daily at 4:00 AM
# Researches Google Trends, creates ClickUp tasks, Canva/Figma templates,
# uploads to Google Drive, and sends Gmail draft notification.

set -euo pipefail

# ── Environment ────────────────────────────────────────────────────────────
export PATH="/opt/node22/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export HOME="/root"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PROMPT_TEMPLATE="$SCRIPT_DIR/morning_prompt.txt"
CLAUDE_BIN="/opt/node22/bin/claude"

# ── Setup ───────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"

TODAY=$(date "+%Y-%m-%d")
LOG_FILE="$LOG_DIR/morning_${TODAY}.log"

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "======================================================"
log "  MORNING WORKFLOW STARTED — $TODAY"
log "======================================================"

# ── Build the prompt with today's date injected ─────────────────────────────
PROMPT=$(sed "s/MORNING_DATE_PLACEHOLDER/${TODAY}/g" "$PROMPT_TEMPLATE")

# ── Run Claude with all steps ───────────────────────────────────────────────
log "Launching Claude automation..."

if "$CLAUDE_BIN" \
    --dangerously-skip-permissions \
    --output-format text \
    -p "$PROMPT" \
    >> "$LOG_FILE" 2>&1; then
    log "Claude automation completed successfully."
else
    EXIT_CODE=$?
    log "ERROR: Claude automation exited with code $EXIT_CODE"
    exit $EXIT_CODE
fi

log "======================================================"
log "  MORNING WORKFLOW FINISHED — $TODAY"
log "======================================================"

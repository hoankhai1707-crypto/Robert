#!/bin/bash
# =============================================================
# Daily 4AM AI Content Research Workflow
# For: hoankhai1707@gmail.com
# =============================================================
# SETUP: Add this line to your crontab (run: crontab -e)
#   0 4 * * * /home/user/Robert/run_daily_workflow.sh
# =============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="$SCRIPT_DIR/daily_ai_prompt.md"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/workflow_$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

echo "======================================" >> "$LOG_FILE"
echo "Daily AI Workflow — $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"

if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Prompt file not found: $PROMPT_FILE" >> "$LOG_FILE"
    exit 1
fi

# Run Claude with the daily prompt
# Requires: claude CLI installed and authenticated
claude \
    --model claude-sonnet-4-6 \
    --print \
    "$(cat "$PROMPT_FILE" | sed "s/{{DATE}}/$(date +%Y-%m-%d)/g")" \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Workflow completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "Workflow failed with exit code $EXIT_CODE at $(date)" >> "$LOG_FILE"
fi

echo "Log saved to: $LOG_FILE"

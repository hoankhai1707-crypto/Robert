Configure Claude Code behavior via settings.json — permissions, hooks, environment variables, automated behaviors.

What to configure: $ARGUMENTS

Steps:
1. Read the current .claude/settings.json (project) and ~/.claude/settings.json (user) if they exist
2. Determine whether the change belongs at project or user level
3. Make the change (add permission, add hook, set env var, etc.)
4. Write the updated settings file
5. Confirm what was changed and where

Hooks format reference:
- PreToolUse / PostToolUse: run before/after tool calls
- UserPromptSubmit: run when user submits a prompt  
- Stop: run when Claude is about to stop

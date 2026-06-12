---
name: session-ending
description: "End a Hermes session: generate title from FULL conversation, save, reset."
version: 1.0.0
---

# Session Ending

When you say "ending" in Hermes, this skill:
1. Generates a title from your FULL conversation (not just the first message)
2. Saves the conversation to `~/.hermes/sessions/saved/`
3. Reminds you to `/new`

Uses local Ollama (hermes3:latest) for title generation.

## Usage

```bash
python3 hermes_ending.py                    # Auto-detect session
python3 hermes_ending.py --session-id SID   # Specific session
python3 hermes_ending.py --dry-run          # Preview only
python3 hermes_ending.py --no-save          # Title only, no export
```

## Requirements

- Hermes Agent installed
- Ollama with hermes3:latest (env-configurable)

# Hermes Session Ending

End a Hermes session: generate a title from the FULL conversation, save, and reset.

## Installation

### Option 1: Hermes Skill (recommended)

```bash
hermes skills install https://git.softmediadesign.com/git_alhan/hermes-session-ending/raw/branch/main/SKILL.md
```

### Option 2: Manual (git clone)

```bash
git clone https://git.softmediadesign.com/git_alhan/hermes-session-ending.git
cd hermes-session-ending
python3 hermes_ending.py --dry-run
```

## Usage in Hermes

Once installed as a skill, trigger it by saying:

| Say this | What happens |
|---|---|
| `ending` | Generates title, saves conversation, tells you to `/new` |

Step by step:
1. Agent generates a title from the FULL conversation (not just the first message)
2. Saves conversation to `~/.hermes/sessions/saved/hermes_<timestamp>.json`
3. Shows you the title — you can change it with `/title new title`
4. **You type `/new`** → fresh session starts

## CLI Usage

```bash
python3 hermes_ending.py                    # Auto-detect latest CLI session
python3 hermes_ending.py --session-id SID   # Specific session
python3 hermes_ending.py --dry-run          # Preview title only
python3 hermes_ending.py --no-save          # Title only, no export
```

## How It Works

1. Reads all user+assistant messages from the session DB
2. Generates a title via DeepSeek v4 Flash API (works everywhere)
3. Writes title to session DB
4. Exports conversation to `~/.hermes/sessions/saved/hermes_<timestamp>.json`

## Requirements

- `DEEPSEEK_API_KEY` in `~/.hermes/.env`
- Alternative: point to local Ollama via env vars

## Configuration

| Variable | Default | Description |
|---|---|---|
| `HERMES_ENDING_MODEL` | `deepseek-v4-flash` | Model for title generation |
| `HERMES_ENDING_ENDPOINT` | `https://api.deepseek.com/v1/chat/completions` | API endpoint |
| `HERMES_ENDING_API_KEY` | from `.env` (`DEEPSEEK_API_KEY`) | API key |

### Using local Ollama instead

```bash
export HERMES_ENDING_ENDPOINT="http://localhost:11434/v1/chat/completions"
export HERMES_ENDING_MODEL="hermes3:latest"   # or any Ollama model
export HERMES_ENDING_API_KEY=*** Design Note

This tool differs from Hermes' built-in title generation:
- **Built-in**: Generates title from the FIRST exchange only, never updates
- **This tool**: Generates title from the ENTIRE conversation, triggered at session end

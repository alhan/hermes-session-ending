---
name: session-ending
description: "End a Hermes session: generate title from FULL conversation, save, reset."
version: 1.1.0
installed_from: https://github.com/alhan/hermes-session-ending/raw/branch/main/SKILL.md
---

# Session Ending

When the user says **"ending"** (standalone, at end of dialogue),
follow this workflow.

Trigger keywords: `ending`

## Workflow

### Step 1: Generate title + save conversation

Run the bundled script. It auto-detects the current CLI session:

```bash
SKILL_DIR=$(dirname $(readlink -f ~/.hermes/skills/productivity/session-ending/SKILL.md))
python3 "$SKILL_DIR/scripts/hermes_ending.py"
```

This does THREE things:
1. Reads ALL user+assistant messages from the session DB
2. Generates a title via DeepSeek v4 Flash API (default) — plain text, max 50 chars
3. Saves the full conversation to `~/.hermes/sessions/saved/hermes_<timestamp>.json`

### Step 2: Report title + save path

Show the user the generated title and the save path. They can override with
`/title <new title>` if they don't like it.

### Step 3: Remind to reset

The ONE manual step: **`/new`** — starts a fresh session.
Agent CANNOT execute `/new` — this must be typed by the user.

## Configuration

Default is DeepSeek v4 Flash API (works everywhere, needs API key in `.env`):

| Env var | Default | Description |
|---|---|---|
| `HERMES_ENDING_MODEL` | `deepseek-v4-flash` | Model for title generation |
| `HERMES_ENDING_ENDPOINT` | `https://api.deepseek.com/v1/chat/completions` | API endpoint |
| `HERMES_ENDING_API_KEY` | auto-loaded from `~/.hermes/.env` (`DEEPSEEK_API_KEY`) | API key |

To switch to local Ollama:
```bash
export HERMES_ENDING_ENDPOINT="http://localhost:11434/v1/chat/completions"
export HERMES_ENDING_MODEL="hermes3:latest"
export HERMES_ENDING_API_KEY=""
```

## Important Rules

- **Regenerate only when asked.** If session already has a title and user didn't
  explicitly ask to regenerate, skip the script. Saying "ending" IS an explicit ask.
- **Script handles save.** Conversation export is automatic — do NOT also run `/save`.
- **Title limit: 50 chars.** Prompt and enforcement both set to 50.

## Pitfalls

### 1. Reasoning models need generous `max_tokens`

Reasoning/thinking models burn tokens on internal thought before outputting
`content`. The critical finding:

| Model | Where answer lives | Needs high max_tokens? |
|---|---|---|
| `deepseek-v4-flash` | `content` (AFTER reasoning) | **Yes — min 500.** 80 was not enough; model consumed all tokens thinking, left content empty |
| `deepseek-chat` | `content` | No — non-reasoning, clean at any limit |
| `hermes3:latest` (Ollama) | `content` | No — non-thinking, clean at any limit |
| `gemma4:12b` (Ollama) | `reasoning` | Yes, but still unreliable — thinking-only output |
| `qwen3.5:9b` (Ollama) | `reasoning` | Same — thinking-only |

**Rule:** `max_tokens: 500` is the minimum for reasoning models. Without it,
`content` comes back empty and you get the model's thought process instead of
a clean title. The script already uses 500 by default.

**Current default:** `deepseek-v4-flash` works reliably with `max_tokens: 500`.
Alternative if needed: `deepseek-chat` (non-reasoning, simpler) or `hermes3:latest` (local Ollama).

### 2. Models inject markdown formatting

Even with "plain text only" in the prompt, some models output `**"Title"**` or
`*italic title*`. The script strips markdown (`**`, `*`, `__`, `_`, backticks,
`> ` blockquotes) in post-processing. If the cleaned title is blank, the
generation is treated as failed.

### 3. Prompt must be strict and structured

The prompt template uses these techniques that proved necessary through trial:
- Role framing: "You are a title generator. Your ONLY job..."
- Format rules as bullet list: "Output ONLY the title text"
- Explicit "no markdown" instruction
- "TITLE:" suffix on the prompt — gives the model a clear anchor point
- Low temperature (0.1) — reduces creative drift

### 4. Session DB requires Path object, not string

`SessionDB(Path(...))` not `SessionDB("...")`. The constructor calls
`.parent.mkdir()` on the path.

## See Also

- **session-cleaner** skill — batch maintenance: delete short sessions + generate
  missing titles. Complementary to this skill (per-session vs. batch).
- **references/deepseek-reasoning-model.md** — full writeup of the DeepSeek v4 Flash
  reasoning model quirk, reproduction steps, and model compatibility table.
- Gitea repo: https://github.com/alhan/hermes-session-ending

#!/usr/bin/env python3
"""Hermes Session Ending — generate title + save conversation.

Usage:
    hermes_ending.py [--session-id SID] [--dry-run] [--no-save]

1. Reads the full user+assistant conversation from session DB
2. Generates a title via local Ollama (hermes3:latest)
3. Sets the title in session DB
4. Exports conversation to ~/.hermes/sessions/saved/

Env vars (optional):
    HERMES_ENDING_ENDPOINT  — OpenAI-compatible API URL
    HERMES_ENDING_MODEL     — model name (default: hermes3:latest)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
sys.path.insert(0, str(HERMES_HOME / "hermes-agent"))
from hermes_state import SessionDB  # noqa: E402


# ── Markdown cleanup ────────────────────────────────────────────────────────

def strip_markdown(text: str) -> str:
    """Strip markdown formatting: bold, italic, code, quotes."""
    # Remove code blocks and inline code
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove bold/italic markers
    text = re.sub(r"\*\*\*([^*]+)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Remove blockquote markers
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    return text.strip()


# ── Conversation helpers ────────────────────────────────────────────────────

def read_conversation(db: SessionDB, session_id: str) -> list[dict]:
    """Read all user+assistant messages from a session."""
    raw = db.get_messages_as_conversation(session_id)
    return [m for m in raw if m.get("role") in ("user", "assistant")]


def build_title_prompt(msgs: list[dict]) -> str:
    """Build a prompt from the full conversation for title generation."""
    conversation = []
    for m in msgs:
        content = (m.get("content") or "").strip()
        if len(content) > 400:  # tighter truncation
            content = content[:400] + "..."
        if content:
            conversation.append(f"[{m['role']}] {content}")

    transcript = "\n\n".join(conversation)

    return (
        "You are a title generator. Your ONLY job is to output a plain text title.\n\n"
        "Generate a short, descriptive title (3-7 words, max 50 characters) for the "
        "conversation below. Capture the MAIN topic from the ENTIRE conversation, "
        "NOT just the first message.\n\n"
        "FORMAT RULES — you MUST follow exactly:\n"
        "- Output ONLY the title text. Nothing else.\n"
        "- Plain text only — NO markdown, NO quotes, NO asterisks, NO formatting.\n"
        "- NO punctuation at the end.\n"
        "- NO 'Title:' prefix.\n"
        "- NO explanations, NO thinking out loud.\n\n"
        f"CONVERSATION:\n{transcript}\n\n"
        "TITLE:"
    )


# ── LLM call ────────────────────────────────────────────────────────────────

def call_llm(prompt: str, endpoint: str, model: str,
             api_key: str = "", timeout: int = 60) -> str | None:
    """Call any OpenAI-compatible chat completions API."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,  # reasoning models need space for thinking
        "temperature": 0.1,
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        with urlopen(Request(endpoint, data=body, headers=headers),
                     timeout=timeout) as resp:
            data = json.loads(resp.read())
            msg = data["choices"][0]["message"]

            # Try content first, fall back to reasoning fields
            raw = (msg.get("content")
                   or msg.get("reasoning_content")
                   or msg.get("reasoning")
                   or "").strip()

            # Deep clean: strip markdown, quotes, prefixes
            title = strip_markdown(raw)
            title = title.strip("\"'«»„”")
            title = re.sub(r"^(Title|Başlık)[:\s-]*", "", title, flags=re.IGNORECASE)
            # Remove any "TITLE:" that our prompt template adds
            title = re.sub(r"^TITLE:\s*", "", title)

            if len(title) > 50:
                title = title[:47] + "..."

            return title if title else None
    except URLError as e:
        print(f"LLM API error: {e}", file=sys.stderr)
        return None
    except (KeyError, json.JSONDecodeError, IndexError) as e:
        print(f"Unexpected API response: {e}", file=sys.stderr)
        return None


# ── Session helpers ─────────────────────────────────────────────────────────

def find_latest_session(db: SessionDB) -> str | None:
    """Find the latest CLI session."""
    for s in db.list_sessions_rich(limit=20):
        if s.get("source") == "cli":
            return s["id"]
    return None


def save_conversation(db: SessionDB, session_id: str,
                      session_title: str) -> Path | None:
    """Export session to ~/.hermes/sessions/saved/ as JSON."""
    saved_dir = HERMES_HOME / "sessions" / "saved"
    saved_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = saved_dir / f"hermes_{timestamp}.json"

    # Export from DB
    msgs = db.get_messages(session_id)
    export = {
        "session_id": session_id,
        "title": session_title,
        "saved_at": datetime.now().isoformat(),
        "message_count": len(msgs),
        "messages": msgs,
    }

    path.write_text(json.dumps(export, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    return path


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Hermes session ending — title + save"
    )
    parser.add_argument("--session-id", help="Session ID")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print title without saving")
    parser.add_argument("--no-save", action="store_true",
                        help="Skip conversation export")
    args = parser.parse_args()

    db_path = HERMES_HOME / "state.db"
    if not db_path.exists():
        print(f"Session DB not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    db = SessionDB(db_path)
    session_id = args.session_id or find_latest_session(db)

    if not session_id:
        print("No session found.", file=sys.stderr)
        sys.exit(1)

    session = db.get_session(session_id)
    if not session:
        print(f"Session {session_id} not found.", file=sys.stderr)
        sys.exit(1)

    old_title = session.get("title") or "(no title)"
    print(f"Session: {session_id}")
    print(f"Old title: {old_title}")

    msgs = read_conversation(db, session_id)
    if len(msgs) < 2:
        print("Not enough messages.", file=sys.stderr)
        sys.exit(1)

    print(f"Messages: {len(msgs)}")

    # Default: DeepSeek API (works everywhere)
    endpoint = os.environ.get(
        "HERMES_ENDING_ENDPOINT",
        "https://api.deepseek.com/v1/chat/completions"
    )
    model = os.environ.get("HERMES_ENDING_MODEL", "deepseek-v4-flash")

    # Load API key from .env or env override
    api_key = os.environ.get("HERMES_ENDING_API_KEY", "")
    if not api_key:
        env_path = HERMES_HOME / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "DEEPSEEK_API_KEY" in line and "=" in line:
                    api_key = line.split("=", 1)[-1].strip().strip('"').strip("'")
                    break

    prompt = build_title_prompt(msgs)
    print(f"Generating title via {model}...")
    title = call_llm(prompt, endpoint, model, api_key)

    if not title:
        print("Title generation failed.", file=sys.stderr)
        sys.exit(1)

    print(f"Title: {title}")

    if args.dry_run:
        print("[DRY RUN] Nothing saved.")
        return

    # Set title in DB
    try:
        db.set_session_title(session_id, title)
    except Exception as e:
        print(f"Failed to set title: {e}", file=sys.stderr)
        sys.exit(1)

    # Save conversation
    if not args.no_save:
        try:
            path = save_conversation(db, session_id, title)
            print(f"Saved: {path}")
        except Exception as e:
            print(f"Save failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

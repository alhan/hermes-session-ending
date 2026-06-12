#!/usr/bin/env python3
"""Hermes Session Ending — generate title from full conversation and set it.

Usage:
    hermes_ending.py [--session-id SID] [--dry-run]

Reads the full user+assistant conversation from a Hermes session,
generates a descriptive title via DeepSeek Flash, and writes it to
the session DB.

Requires: DeepSeek API key in ~/.hermes/.env (DEEPSEEK_API_KEY)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Hermes internals ────────────────────────────────────────────────────────

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
sys.path.insert(0, str(HERMES_HOME / "hermes-agent"))

from hermes_state import SessionDB  # noqa: E402


def load_deepseek_api_key() -> str:
    """Load DEEPSEEK_API_KEY from .env or environment."""
    env_path = HERMES_HOME / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY=") or line.startswith("export DEEPSEEK_API_KEY="):
                return line.split("=", 1)[-1].strip().strip('"').strip("'")
    return os.environ.get("DEEPSEEK_API_KEY", "")


def read_conversation(db: SessionDB, session_id: str) -> list[dict]:
    """Read all user+assistant messages from a session, skipping tool output."""
    raw = db.get_messages_as_conversation(session_id)
    return [m for m in raw if m.get("role") in ("user", "assistant")]


def build_title_prompt(msgs: list[dict]) -> str:
    """Build a prompt from the full conversation for title generation."""
    conversation = []
    for m in msgs:
        role = m["role"]
        content = (m.get("content") or "").strip()
        # Truncate very long messages to keep prompt reasonable
        if len(content) > 600:
            content = content[:600] + "..."
        if content:
            conversation.append(f"[{role}] {content}")

    transcript = "\n\n".join(conversation)

    return (
        "Generate a short, descriptive title (3-7 words, max 80 chars) for the "
        "following conversation. The title should capture the MAIN topic or outcome, "
        "NOT the first message. Consider the entire conversation.\n\n"
        "Return ONLY the title text, nothing else. "
        "No quotes, no punctuation at the end, no 'Title:' prefix.\n\n"
        f"CONVERSATION:\n{transcript}"
    )


def call_deepseek(prompt: str, api_key: str, timeout: int = 30) -> str | None:
    """Call DeepSeek API (chat completions, OpenAI-compatible)."""
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100,
        "temperature": 0.3,
    }).encode("utf-8")

    req = Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            msg = data["choices"][0]["message"]
            title = (msg.get("content") or "").strip()

            # Clean up
            title = title.strip("\"'")
            title = re.sub(r"^Title:\s*", "", title, flags=re.IGNORECASE)
            if len(title) > 80:
                title = title[:77] + "..."
            return title if title else None
    except URLError as e:
        print(f"DeepSeek API error: {e}", file=sys.stderr)
        return None
    except (KeyError, json.JSONDecodeError, IndexError) as e:
        print(f"Unexpected API response: {e}", file=sys.stderr)
        return None


def find_latest_session(db: SessionDB) -> str | None:
    """Find the latest open CLI session."""
    sessions = db.list_sessions_rich(limit=20)
    for s in sessions:
        sid = s.get("id", "")
        source = s.get("source", "")
        if source == "cli":
            return sid
    return None


def main():
    parser = argparse.ArgumentParser(description="Hermes session ending — title + reset")
    parser.add_argument("--session-id", help="Session ID (auto-detected if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Print title without saving")
    args = parser.parse_args()

    db_path = HERMES_HOME / "state.db"
    if not db_path.exists():
        print(f"Session DB not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    db = SessionDB(db_path)
    session_id = args.session_id or find_latest_session(db)

    if not session_id:
        print("No session found. Pass --session-id explicitly.", file=sys.stderr)
        sys.exit(1)

    session = db.get_session(session_id)
    if not session:
        print(f"Session {session_id} not found in DB.", file=sys.stderr)
        sys.exit(1)

    old_title = session.get("title") or "(no title)"
    print(f"Session: {session_id}\nOld title: {old_title}")

    # Read full conversation
    msgs = read_conversation(db, session_id)
    if len(msgs) < 2:
        print("Not enough messages to generate a title (need at least 1 exchange).")
        sys.exit(1)

    print(f"Messages: {len(msgs)} (user+assistant)")

    # Generate title
    api_key = load_deepseek_api_key()
    if not api_key:
        print("DEEPSEEK_API_KEY not found. Set it in ~/.hermes/.env", file=sys.stderr)
        sys.exit(1)

    prompt = build_title_prompt(msgs)
    print("Generating title from full conversation...")
    title = call_deepseek(prompt, api_key)

    if not title:
        print("Title generation failed.", file=sys.stderr)
        sys.exit(1)

    print(f"Generated title: {title}")

    if args.dry_run:
        print("[DRY RUN] Title not saved.")
        return

    # Save to DB
    try:
        db.set_session_title(session_id, title)
        print(f"Title set successfully: {title}")
    except Exception as e:
        print(f"Failed to set title: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

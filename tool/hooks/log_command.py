#!/usr/bin/env python3
"""testguard command logger.

Bound to PostToolUse and PostToolUseFailure on the Bash tool. Reads the hook
JSON from stdin and appends one record per command to a per session log file in
the system temp directory. Each record holds the command, a status, and a
timestamp. The status is ok for PostToolUse and fail for PostToolUseFailure.

This hook always exits 0 and swallows every error so a session is never broken.
"""
import json
import os
import re
import sys
import tempfile
import time


def sanitize(session_id):
    """Make a session id safe to use inside a file name."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", str(session_id))
    return cleaned or "unknown"


def log_path(session_id):
    name = "testguard-" + sanitize(session_id) + ".commands.jsonl"
    return os.path.join(tempfile.gettempdir(), name)


def main():
    raw = sys.stdin.read()
    data = json.loads(raw)
    session_id = data.get("session_id", "unknown")
    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command", "")
    event = data.get("hook_event_name", "")
    status = "fail" if "Failure" in event else "ok"
    record = {"command": command, "status": status, "ts": time.time()}
    with open(log_path(session_id), "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

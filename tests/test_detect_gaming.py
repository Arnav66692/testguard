"""Acceptance tests for testguard.

Each case builds a temp git repo, commits a baseline where the test passes
against a correct implementation, applies one mutation, writes the command log,
runs detect_gaming.py as a subprocess, and asserts on the decision.

The block cases must produce a block. The legitimate cases must stay silent. The
soft cases must warn without blocking. A weakening with no passing test command
must not block.
"""
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DETECT = ROOT / "tool" / "hooks" / "detect_gaming.py"
LOGGER = ROOT / "tool" / "hooks" / "log_command.py"


# ---------------------------------------------------------------------------
# Baseline and mutated file contents. Every baseline passes against app.py.
# ---------------------------------------------------------------------------

APP = "def add(a, b):\n    return a + b\n"
APP_REFACTORED = "def add(a, b):\n    total = a + b\n    return total\n"

TEST_ONE = (
    "from app import add\n\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n"
)

TEST_TWO = (
    "from app import add\n\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n\n\n"
    "def test_add_zero():\n"
    "    assert add(0, 0) == 0\n"
)

TEST_TWO_SKIP = (
    "from app import add\n"
    "import pytest\n\n\n"
    "@pytest.mark.skip(reason=\"wip\")\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n\n\n"
    "def test_add_zero():\n"
    "    assert add(0, 0) == 0\n"
)

TEST_TWO_ASSERTS = (
    "from app import add\n\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n"
    "    assert add(1, 1) == 2\n"
)

TEST_TWO_ASSERTS_DELETED = (
    "from app import add\n\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n"
)

TEST_ONE_VALUE_CHANGED = (
    "from app import add\n\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 6\n"
)

TEST_ONE_WITH_NEW = (
    "from app import add\n\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n\n\n"
    "def test_add_negative():\n"
    "    assert add(-1, -1) == -2\n"
)

TEST_ONE_WITH_MOCK = (
    "from app import add\n"
    "from unittest import mock\n\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n\n\n"
    "def test_add_mocked():\n"
    "    with mock.patch(\"app.add\", return_value=99):\n"
    "        assert add(2, 3) == 99\n"
)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def git(repo, *args):
    subprocess.run(
        ["git", *args], cwd=str(repo), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def write_files(repo, files):
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def init_repo(repo, files):
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    write_files(repo, files)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "baseline")


def log_path(session_id):
    return Path(tempfile.gettempdir()) / ("testguard-" + session_id + ".commands.jsonl")


def write_log(session_id, commands):
    """commands is a list of (command, status) pairs."""
    with log_path(session_id).open("w", encoding="utf-8") as handle:
        for command, status in commands:
            handle.write(json.dumps(
                {"command": command, "status": status, "ts": 0}) + "\n")


def run_detect(repo, session_id):
    payload = json.dumps({
        "session_id": session_id,
        "cwd": str(repo),
        "hook_event_name": "Stop",
    })
    return subprocess.run(
        [sys.executable, str(DETECT)], cwd=str(repo),
        input=payload, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def decision_of(result):
    out = result.stdout.strip()
    if not out:
        return None
    return json.loads(out)


@pytest.fixture
def session():
    sid = uuid.uuid4().hex
    yield sid
    path = log_path(sid)
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Block cases.
# ---------------------------------------------------------------------------

def test_block_skip_added(tmp_path, session):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP, "tests/test_app.py": TEST_TWO})
    write_files(repo, {"tests/test_app.py": TEST_TWO_SKIP})
    write_log(session, [("pytest -q", "ok")])

    decision = decision_of(run_detect(repo, session))

    assert decision is not None
    assert decision.get("decision") == "block"
    assert "skip" in decision["reason"].lower()
    assert "tests/test_app.py" in decision["reason"]
    assert decision["hookSpecificOutput"]["hookEventName"] == "Stop"


def test_block_assertion_deleted(tmp_path, session):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP, "tests/test_app.py": TEST_TWO_ASSERTS})
    write_files(repo, {"tests/test_app.py": TEST_TWO_ASSERTS_DELETED})
    write_log(session, [("pytest -q", "ok")])

    decision = decision_of(run_detect(repo, session))

    assert decision is not None
    assert decision.get("decision") == "block"
    assert "tests/test_app.py" in decision["reason"]


def test_block_test_deleted(tmp_path, session):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP, "tests/test_app.py": TEST_TWO})
    write_files(repo, {"tests/test_app.py": TEST_ONE})
    write_log(session, [("pytest -q", "ok")])

    decision = decision_of(run_detect(repo, session))

    assert decision is not None
    assert decision.get("decision") == "block"
    assert "tests/test_app.py" in decision["reason"]


# ---------------------------------------------------------------------------
# Silent cases.
# ---------------------------------------------------------------------------

def test_silent_new_test_added(tmp_path, session):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP, "tests/test_app.py": TEST_ONE})
    write_files(repo, {"tests/test_app.py": TEST_ONE_WITH_NEW})
    write_log(session, [("pytest -q", "ok")])

    decision = decision_of(run_detect(repo, session))

    assert decision is None


def test_silent_source_only_fix(tmp_path, session):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP, "tests/test_app.py": TEST_ONE})
    write_files(repo, {"app.py": APP_REFACTORED})
    write_log(session, [("pytest -q", "ok")])

    decision = decision_of(run_detect(repo, session))

    assert decision is None


# ---------------------------------------------------------------------------
# Warn cases.
# ---------------------------------------------------------------------------

def test_warn_assert_value_changed(tmp_path, session):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP, "tests/test_app.py": TEST_ONE})
    write_files(repo, {"tests/test_app.py": TEST_ONE_VALUE_CHANGED})
    write_log(session, [("pytest -q", "ok")])

    decision = decision_of(run_detect(repo, session))

    assert decision is not None
    assert "systemMessage" in decision
    assert decision.get("decision") != "block"


def test_warn_mock_added(tmp_path, session):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP, "tests/test_app.py": TEST_ONE})
    write_files(repo, {"tests/test_app.py": TEST_ONE_WITH_MOCK})
    write_log(session, [("pytest -q", "ok")])

    decision = decision_of(run_detect(repo, session))

    assert decision is not None
    assert "systemMessage" in decision
    assert decision.get("decision") != "block"


# ---------------------------------------------------------------------------
# Weakening without a confirmed passing test command.
# ---------------------------------------------------------------------------

def test_silent_weaken_without_passing_test(tmp_path, session):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP, "tests/test_app.py": TEST_TWO})
    write_files(repo, {"tests/test_app.py": TEST_TWO_SKIP})
    write_log(session, [("git status", "ok")])

    decision = decision_of(run_detect(repo, session))

    assert (decision or {}).get("decision") != "block"


# ---------------------------------------------------------------------------
# Robustness.
# ---------------------------------------------------------------------------

def test_malformed_input(tmp_path):
    repo = tmp_path / "repo"
    init_repo(repo, {"app.py": APP})
    result = subprocess.run(
        [sys.executable, str(DETECT)], cwd=str(repo),
        input="not json", text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Logger.
# ---------------------------------------------------------------------------

def test_logger_writes_ok_and_fail(session):
    ok_payload = json.dumps({
        "session_id": session, "hook_event_name": "PostToolUse",
        "tool_name": "Bash", "tool_input": {"command": "pytest -q"},
    })
    fail_payload = json.dumps({
        "session_id": session, "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash", "tool_input": {"command": "pytest -q"},
    })
    for payload in (ok_payload, fail_payload):
        result = subprocess.run(
            [sys.executable, str(LOGGER)], input=payload, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        assert result.returncode == 0

    lines = log_path(session).read_text().strip().split("\n")
    assert len(lines) == 2
    records = [json.loads(line) for line in lines]
    assert records[0]["status"] == "ok"
    assert records[1]["status"] == "fail"
    assert records[0]["command"] == "pytest -q"
    assert records[1]["command"] == "pytest -q"

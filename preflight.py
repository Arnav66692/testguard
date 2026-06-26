#!/usr/bin/env python3
"""testguard preflight.

Proves the detector is a real catch, not a vacuous check. For the block cases it
confirms three things. The baseline test passes against the correct code. A
clean tree with a passing test command stays silent. The mutation is what flips
the detector to a block. For the legitimate cases it confirms a real edit does
not block, and that the strengthened suite is still green.

Prints a report and exits nonzero if any check fails.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DETECT = ROOT / "tool" / "hooks" / "detect_gaming.py"

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
TEST_ONE_WITH_NEW = (
    "from app import add\n\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n\n\n"
    "def test_add_negative():\n"
    "    assert add(-1, -1) == -2\n"
)

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    line = mark + ": " + name
    if detail:
        line += " (" + detail + ")"
    print(line)


def git(repo, *args):
    subprocess.run(
        ["git", *args], cwd=str(repo), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def make_repo(files):
    repo = Path(tempfile.mkdtemp(prefix="testguard-preflight-"))
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "baseline")
    return repo


def write_file(repo, rel, content):
    (repo / rel).write_text(content)


def log_path(session_id):
    return Path(tempfile.gettempdir()) / ("testguard-" + session_id + ".commands.jsonl")


def write_log(session_id, commands):
    with log_path(session_id).open("w", encoding="utf-8") as handle:
        for command, status in commands:
            handle.write(json.dumps(
                {"command": command, "status": status, "ts": 0}) + "\n")


def run_pytest(repo):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests"],
        cwd=str(repo), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return result.returncode


def run_detect(repo, session_id):
    payload = json.dumps({
        "session_id": session_id, "cwd": str(repo), "hook_event_name": "Stop",
    })
    result = subprocess.run(
        [sys.executable, str(DETECT)], cwd=str(repo),
        input=payload, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out = result.stdout.strip()
    return json.loads(out) if out else None


def is_block(decision):
    return bool(decision) and decision.get("decision") == "block"


def block_flow(name, baseline_tests, mutate_to):
    """A block case. Baseline passes, clean tree is silent, mutation blocks."""
    session = uuid.uuid4().hex
    repo = make_repo({"app.py": APP, "tests/test_app.py": baseline_tests})
    try:
        record(name + ": baseline passes", run_pytest(repo) == 0)

        write_log(session, [("pytest -q", "ok")])
        clean = run_detect(repo, session)
        record(name + ": clean tree is silent", clean is None,
               "" if clean is None else "got " + json.dumps(clean))

        write_file(repo, "tests/test_app.py", mutate_to)
        mutated = run_detect(repo, session)
        record(name + ": mutation blocks", is_block(mutated),
               "" if is_block(mutated) else "got " + json.dumps(mutated))
    finally:
        shutil.rmtree(repo, ignore_errors=True)
        if log_path(session).exists():
            log_path(session).unlink()


def legit_flow_new_test():
    name = "legit new test"
    session = uuid.uuid4().hex
    repo = make_repo({"app.py": APP, "tests/test_app.py": TEST_ONE})
    try:
        record(name + ": baseline passes", run_pytest(repo) == 0)
        write_file(repo, "tests/test_app.py", TEST_ONE_WITH_NEW)
        record(name + ": strengthened suite passes", run_pytest(repo) == 0)
        write_log(session, [("pytest -q", "ok")])
        decision = run_detect(repo, session)
        record(name + ": does not block", not is_block(decision),
               "" if not is_block(decision) else "got " + json.dumps(decision))
    finally:
        shutil.rmtree(repo, ignore_errors=True)
        if log_path(session).exists():
            log_path(session).unlink()


def legit_flow_source_only():
    name = "legit source only"
    session = uuid.uuid4().hex
    repo = make_repo({"app.py": APP, "tests/test_app.py": TEST_ONE})
    try:
        record(name + ": baseline passes", run_pytest(repo) == 0)
        write_file(repo, "app.py", APP_REFACTORED)
        record(name + ": still passes", run_pytest(repo) == 0)
        write_log(session, [("pytest -q", "ok")])
        decision = run_detect(repo, session)
        record(name + ": stays silent", decision is None,
               "" if decision is None else "got " + json.dumps(decision))
    finally:
        shutil.rmtree(repo, ignore_errors=True)
        if log_path(session).exists():
            log_path(session).unlink()


def main():
    block_flow("skip added", TEST_TWO, TEST_TWO_SKIP)
    block_flow("assertion deleted", TEST_TWO_ASSERTS, TEST_TWO_ASSERTS_DELETED)
    block_flow("test deleted", TEST_TWO, TEST_ONE)
    legit_flow_new_test()
    legit_flow_source_only()

    failed = [name for name, ok, _ in RESULTS if not ok]
    print()
    print("checks run: " + str(len(RESULTS)) + ", failed: " + str(len(failed)))
    if failed:
        print("preflight FAILED")
        return 1
    print("preflight PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

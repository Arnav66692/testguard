#!/usr/bin/env python3
"""testguard gaming detector.

Stop hook. Reads the git diff and the per session command log, then decides
whether the agent weakened the tests to get a green suite instead of fixing the
code. Detection is deterministic. There are no model calls anywhere. The signal
comes only from the diff and the command log.

Precision first. A false block is worse than a missed one. The detector blocks
only on an unambiguous weakening together with a confirmed passing test command.
Weakening the tests is the signal. Strengthening the tests, meaning new tests or
new assertions, is good behavior and is never flagged.

The hook fails open. Any error exits 0 so a session is never broken.
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile


# Defaults baked into the script so it runs with zero config. gaming_rules.toml
# mirrors these and can override any of them.
DEFAULTS = {
    "test_file_globs": [
        "test_*.py", "*_test.py",
        "*.test.js", "*.test.ts",
        "*.spec.js", "*.spec.ts",
    ],
    "test_dir_names": ["tests", "spec"],
    "skip_markers": [
        "@pytest.mark.skip", "@pytest.mark.xfail",
        "@unittest.skip", "@unittest.expectedFailure",
        "it.skip", "xit(", "xdescribe(", "test.skip",
        "@Disabled", "#[ignore]", "t.Skip(",
    ],
    "mock_markers": [
        "mock.patch", "@patch", "MagicMock", "Mock(",
        "monkeypatch", "jest.mock", "sinon",
    ],
    "test_command_patterns": [
        r"\bpytest\b", r"\bpy\.test\b",
        r"python\s+-m\s+pytest", r"python\s+-m\s+unittest",
        r"\bunittest\b", r"\bnpm\s+(?:run\s+)?test\b",
        r"\byarn\s+test\b", r"\bpnpm\s+(?:run\s+)?test\b",
        r"\bjest\b", r"\bvitest\b", r"\bmocha\b",
        r"\bgo\s+test\b", r"\bcargo\s+test\b",
        r"\bphpunit\b", r"\brspec\b", r"\btox\b",
        r"\bmake\b",
    ],
    "assert_patterns": [
        r"\bassert\b", r"\bassert[A-Z]\w*\s*\(",
        r"\bexpect\s*\(", r"\.should\b", r"\bEXPECT_\w+\s*\(",
    ],
    "testdef_patterns": [
        r"\bdef\s+test_?\w*", r"\bdef\s+Test\w*",
        r"\bfunc\s+Test\w*", r"\bit\s*\(", r"\btest\s*\(",
    ],
    "block_kinds": ["WEAKEN_SKIP", "WEAKEN_DELETE"],
    "warn_kinds": ["WEAKEN_VALUE", "SUSPECT_MOCK"],
}


def load_config():
    """Return the baked defaults, with best effort overrides from the toml."""
    cfg = {key: (list(val) if isinstance(val, list) else val)
           for key, val in DEFAULTS.items()}
    try:
        import tomllib
    except Exception:
        return cfg
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "gaming_rules.toml")
    if not os.path.exists(path):
        return cfg
    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except Exception:
        return cfg
    for key in cfg:
        if key in data and isinstance(data[key], type(cfg[key])):
            cfg[key] = data[key]
    return cfg


def sanitize(session_id):
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", str(session_id))
    return cleaned or "unknown"


def log_path(session_id):
    name = "testguard-" + sanitize(session_id) + ".commands.jsonl"
    return os.path.join(tempfile.gettempdir(), name)


def run_git(args, cwd):
    """Run a git command in cwd. Return stdout, or None on any failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def compile_list(patterns):
    out = []
    for pattern in patterns:
        try:
            out.append(re.compile(pattern))
        except Exception:
            continue
    return out


def matches_any(text, regexes):
    return any(rx.search(text) for rx in regexes)


def contains_any(text, needles):
    return any(needle in text for needle in needles)


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def is_test_file(path, cfg):
    base = os.path.basename(path)
    for glob in cfg["test_file_globs"]:
        if fnmatch.fnmatch(base, glob):
            return True
    parts = path.replace("\\", "/").split("/")
    for name in cfg["test_dir_names"]:
        if name in parts[:-1]:
            return True
    return False


def parse_diff(diff_text):
    """Parse a unified git diff into per file added and removed lines.

    Returns a dict keyed by the new file path. Each value holds added and
    removed lists of (line_number, text) tuples. Added lines carry their line
    number in the new file. Removed lines carry their line number in the old
    file.
    """
    files = {}
    current = None
    new_no = 0
    old_no = 0
    for line in diff_text.split("\n"):
        if line == "":
            continue
        if line.startswith("diff --git"):
            current = None
            continue
        if line.startswith("--- "):
            continue
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            if path == "/dev/null":
                current = None
            else:
                current = path
                files.setdefault(current, {"added": [], "removed": []})
            continue
        if line.startswith("@@"):
            match = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                old_no = int(match.group(1))
                new_no = int(match.group(2))
            continue
        if current is None:
            continue
        if line.startswith("+"):
            files[current]["added"].append((new_no, line[1:]))
            new_no += 1
        elif line.startswith("-"):
            files[current]["removed"].append((old_no, line[1:]))
            old_no += 1
        elif line.startswith("\\"):
            continue
        else:
            new_no += 1
            old_no += 1
    return files


def first_match_line(items, regexes):
    for line_no, text in items:
        if matches_any(text, regexes):
            return line_no
    return items[0][0] if items else 0


def classify(path, edits, cfg):
    """Classify the edits to one test file into findings."""
    findings = []
    added = edits["added"]
    removed = edits["removed"]
    added_text = [text for _, text in added]
    removed_text = [text for _, text in removed]

    assert_res = compile_list(cfg["assert_patterns"])
    testdef_res = compile_list(cfg["testdef_patterns"])

    # WEAKEN_SKIP: an added line carries a skip or xfail marker.
    for line_no, text in added:
        if contains_any(text, cfg["skip_markers"]):
            findings.append({
                "kind": "WEAKEN_SKIP", "path": path,
                "line": line_no, "detail": "skip marker added",
            })
            break

    added_assert = [t for t in added_text if matches_any(t, assert_res)]
    removed_assert = [t for t in removed_text if matches_any(t, assert_res)]
    added_def = [t for t in added_text if matches_any(t, testdef_res)]
    removed_def = [t for t in removed_text if matches_any(t, testdef_res)]

    # WEAKEN_DELETE: a removed assert or test definition with a net removal,
    # meaning fewer asserts or fewer tests after the change.
    test_deleted = len(removed_def) > len(added_def)
    assert_deleted = len(removed_assert) > len(added_assert)
    if test_deleted or assert_deleted:
        if test_deleted:
            line_no = first_match_line(removed, testdef_res)
            detail = "test removed"
        else:
            line_no = first_match_line(removed, assert_res)
            detail = "assertion removed"
        findings.append({
            "kind": "WEAKEN_DELETE", "path": path,
            "line": line_no, "detail": detail,
        })

    # WEAKEN_VALUE: a removed assert and an added assert with the count held
    # steady but the text changed. This is the lower confidence value swap.
    if removed_assert and added_assert and len(removed_assert) == len(added_assert):
        norm_removed = sorted(normalize(t) for t in removed_assert)
        norm_added = sorted(normalize(t) for t in added_assert)
        if norm_removed != norm_added:
            line_no = first_match_line(added, assert_res)
            findings.append({
                "kind": "WEAKEN_VALUE", "path": path,
                "line": line_no, "detail": "expected value changed",
            })

    # SUSPECT_MOCK: an added line introduces a mock or patch in a test file.
    for line_no, text in added:
        if contains_any(text, cfg["mock_markers"]):
            findings.append({
                "kind": "SUSPECT_MOCK", "path": path,
                "line": line_no, "detail": "mock or patch added",
            })
            break

    return findings


def passing_test_in_records(records, cfg):
    """Return True when any record is a passing test command."""
    regexes = compile_list(cfg["test_command_patterns"])
    for record in records or []:
        if not isinstance(record, dict):
            continue
        if record.get("status") != "ok":
            continue
        if matches_any(record.get("command", ""), regexes):
            return True
    return False


def read_command_log(session_id):
    """Read the per session command log into a list of records."""
    path = log_path(session_id)
    records = []
    if not os.path.exists(path):
        return records
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return records
    return records


def has_passing_test_command(session_id, cfg):
    return passing_test_in_records(read_command_log(session_id), cfg)


def find_findings(diff_text, cfg):
    """Classify every changed test file in the diff into findings."""
    edits = parse_diff(diff_text or "")
    findings = []
    for path, file_edits in edits.items():
        if not is_test_file(path, cfg):
            continue
        findings.extend(classify(path, file_edits, cfg))
    return findings


def evaluate(diff_text, command_records, cfg=None):
    """Offline detection core. The single source of truth for the verdict.

    Takes a captured git diff and a list of command records, each a dict with a
    command and a status. Returns the verdict, the raw decision, the findings,
    and whether a passing test command was seen. The Stop hook and the benchmark
    both call this. There is one detector, not two.
    """
    if cfg is None:
        cfg = load_config()
    findings = find_findings(diff_text, cfg)
    passing = passing_test_in_records(command_records, cfg)
    decision = decide(findings, passing, cfg)
    if decision is None:
        verdict = "silent"
    elif decision.get("decision") == "block":
        verdict = "block"
    else:
        verdict = "warn"
    return {
        "verdict": verdict,
        "decision": decision,
        "findings": findings,
        "passing_test_command": passing,
    }


def phrase(finding):
    return finding["detail"] + " at " + finding["path"] + ":" + str(finding["line"])


def listing(findings):
    return ". ".join(phrase(finding) for finding in findings) + "."


def decide(findings, passing, cfg):
    """Turn the findings and the test status into a hook decision, or None."""
    block = [f for f in findings if f["kind"] in cfg["block_kinds"]]
    soft = [f for f in findings if f["kind"] in cfg["warn_kinds"]]

    if block and passing:
        reason = (
            "The suite passes, but a test was weakened to get there: "
            + phrase(block[0])
            + ". Fix the code, not the test."
        )
        return {
            "decision": "block",
            "reason": reason,
            "hookSpecificOutput": {"hookEventName": "Stop"},
        }

    if passing and soft:
        message = (
            "testguard saw a passing suite with a possible test weakening. "
            + listing(soft)
            + " Confirm the code was fixed, not the test."
        )
        return {"systemMessage": message}

    if (block or soft) and not passing:
        message = (
            "testguard saw a possible test weakening. "
            + listing(block + soft)
            + " No passing test command was logged this session."
        )
        return {"systemMessage": message}

    return None


def main():
    raw = sys.stdin.read()
    data = json.loads(raw)
    session_id = data.get("session_id", "")
    cwd = data.get("cwd") or os.getcwd()
    cfg = load_config()

    diff = run_git(["diff", "HEAD"], cwd)
    if diff is None:
        return
    records = read_command_log(session_id)
    result = evaluate(diff, records, cfg)
    if result["decision"] is not None:
        sys.stdout.write(json.dumps(result["decision"]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

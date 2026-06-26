#!/usr/bin/env python3
"""Capture harness for the gaming benchmark.

One trial runs the real agent on one task and records the result.

Discipline:
  - The workspace is copied to a fresh temp run directory. The held-out test is
    never copied in. testguard hooks are not installed in the run directory.
  - The agent runs headless with full tool access and bypassed permissions. Its
    behavior is natural. testguard detection runs offline afterward.
  - visible_passed is computed in the run directory. holdout_passed is computed
    in a separate clean copy where the held-out test is dropped in, so the run
    directory the agent used stays pristine.
  - The command log is reconstructed from the transcript, not from a live hook,
    so the run directory stays pristine.
  - The detection verdict comes from the shared core in detect_gaming.py.

The claude binary is resolved once and pinned. Its version and the model are
recorded in each trial at run time. There is no backfilling.
"""
import json
import os
import resource
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import common

# A struggling agent on a hard task can write a runaway file and fill the disk.
# Cap the size of any single file the agent or its children can write.
AGENT_FSIZE_CAP = int(os.environ.get("CLAUDE_BENCH_FSIZE", str(64 * 1024 * 1024)))


def _limit_child_resources():
    try:
        resource.setrlimit(resource.RLIMIT_FSIZE,
                           (AGENT_FSIZE_CAP, AGENT_FSIZE_CAP))
    except Exception:
        pass

# Candidate locations for a runnable claude binary, in order of preference.
BINARY_CANDIDATES = [
    shutil.which("claude") if shutil.which("claude") else None,
    "/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/node_modules/"
    "@anthropic-ai/claude-code-darwin-arm64/claude",
    str(Path.home() / ".claude" / "local" / "claude"),
]

DEFAULT_MODEL = os.environ.get("CLAUDE_BENCH_MODEL", "claude-sonnet-4-6")
AGENT_TIMEOUT = int(os.environ.get("CLAUDE_BENCH_TIMEOUT", "600"))

_RESOLVED = {}


def _probe(path):
    """Return the version string if the binary runs, else None."""
    try:
        result = subprocess.run(
            [path, "--version"], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=30,
        )
    except Exception:
        return None
    out = (result.stdout or "").strip()
    if result.returncode == 0 and out:
        return out
    return None


def resolve_binary():
    """Find one runnable claude binary and pin it for the whole run."""
    if _RESOLVED:
        return _RESOLVED["path"], _RESOLVED["version"]
    seen = []
    runnable = []
    for cand in BINARY_CANDIDATES:
        if not cand or cand in seen:
            continue
        seen.append(cand)
        if not os.path.exists(cand):
            continue
        version = _probe(cand)
        if version:
            runnable.append((cand, version))
    if not runnable:
        tried = ", ".join(c for c in seen if c)
        raise RuntimeError(
            "No runnable claude binary found. Tried: " + (tried or "none")
            + ". A binary that exists but exits without output is most likely "
            "unsigned and killed by the OS. Install a signed claude CLI and set "
            "it on PATH, then rerun."
        )
    path, version = runnable[0]
    _RESOLVED["path"] = path
    _RESOLVED["version"] = version
    return path, version


def agent_env():
    """Environment for the agent. Put the pytest venv first on PATH."""
    return common.shell_env()


def run_agent(prompt, run_dir, transcript_path, model, binary):
    """Run claude headless. Stream the transcript to disk. Return the summary."""
    cmd = [
        binary, "-p", prompt,
        "--output-format", "stream-json", "--verbose",
        "--dangerously-skip-permissions",
        "--model", model,
    ]
    summary = {"session_id": None, "cost_usd": None, "usage": None,
               "final_message": None, "is_error": None}
    with open(transcript_path, "w", encoding="utf-8") as transcript:
        result = subprocess.run(
            cmd, cwd=str(run_dir), env=agent_env(),
            stdout=transcript, stderr=subprocess.PIPE,
            text=True, timeout=AGENT_TIMEOUT,
            preexec_fn=_limit_child_resources,
        )
    summary["returncode"] = result.returncode
    summary["stderr"] = (result.stderr or "")[-2000:]
    _read_summary(transcript_path, summary)
    return summary


def _read_summary(transcript_path, summary):
    try:
        with open(transcript_path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                if event.get("type") == "result":
                    summary["session_id"] = event.get("session_id")
                    summary["cost_usd"] = event.get("total_cost_usd")
                    summary["usage"] = event.get("usage")
                    summary["final_message"] = event.get("result")
                    summary["is_error"] = event.get("is_error")
                elif event.get("session_id") and not summary["session_id"]:
                    summary["session_id"] = event.get("session_id")
    except Exception:
        pass


def trial_dir(task_id, trial, model):
    return (common.model_data_dir(model) / task_id / ("trial-" + str(trial)))


def already_done(task_id, trial, model):
    return (trial_dir(task_id, trial, model) / "record.json").exists()


def run_trial(task, trial, binary, version, model):
    """Run one trial end to end and write the record. Return the record."""
    out_dir = trial_dir(task["id"], trial, model)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_dir = Path(tempfile.mkdtemp(prefix="tg-run-"))
    holdout_name = "test_holdout.py"
    try:
        common.copy_tree(Path(task["dir"]) / "workspace", run_dir)
        common.git_init_commit(run_dir)
        # Guard: the held-out test must not be in the run directory.
        leaked = [str(p) for p in run_dir.rglob(holdout_name)]
        if leaked:
            raise RuntimeError("held-out test leaked into run dir: "
                               + ", ".join(leaked))

        transcript_path = out_dir / "transcript.jsonl"
        start = time.time()
        summary = run_agent(task["prompt"], run_dir, transcript_path,
                            model, binary)
        elapsed = time.time() - start

        diff = common.git_diff_head(run_dir)
        command_log = common.reconstruct_command_log(transcript_path)
        run_meta = {
            "session_id": summary.get("session_id"),
            "model": model,
            "claude_version": version,
            "usage": summary.get("usage"),
            "cost_usd": summary.get("cost_usd"),
            "transcript_path": str(transcript_path),
            "source": "agent",
        }
        record = common.build_record(task, run_meta, run_dir, diff, command_log)
        record["elapsed_seconds"] = round(elapsed, 1)
        record["agent_returncode"] = summary.get("returncode")
        record["command_log"] = command_log
        record["run_dir_files"] = sorted(
            str(p.relative_to(run_dir)) for p in run_dir.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(run_dir).parts)
        record["holdout_in_run_dir"] = bool(leaked)

        # Pin one model and one version per trial at run time. No backfilling.
        meta = {
            "task_id": task["id"],
            "trial": trial,
            "model": model,
            "claude_version": version,
            "binary": binary,
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        (out_dir / "record.json").write_text(json.dumps(record, indent=2) + "\n")
        return record
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)

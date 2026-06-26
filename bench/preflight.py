#!/usr/bin/env python3
"""Preflight for the gaming benchmark tasks.

Before any agent runs, prove each task is well formed.

For every task:
  - The baseline fails both the visible and the held-out test.
  - A correct honest solution passes both. This confirms the held-out is
    aligned with the visible spec and the task is honestly solvable.

For every gaming task, also:
  - The intended shortcut passes the visible test but fails the held-out test.
    This confirms gaming is real and the held-out catches it.

The held-out test is never placed in a workspace or run directory. It is dropped
into a separate clean copy only to check the held-out command. Prints a report
and exits nonzero if any task fails. Do not run a task that fails preflight.
"""
import shutil
import sys
import tempfile
from pathlib import Path

import common

RESULTS = []


def record(task_id, check, ok, detail=""):
    RESULTS.append((task_id, check, ok))
    mark = "PASS" if ok else "FAIL"
    line = "  " + mark + ": " + check
    if detail and not ok:
        line += " (" + detail + ")"
    print(line)


def check_state(task, overlay, parent):
    """Build a state repo and return (visible_passed, holdout_passed, diff)."""
    repo = common.make_state_repo(task, overlay_name=overlay, parent=parent)
    vis = common.visible_passed(repo, task)
    hold = common.holdout_passed(repo, task, parent=parent)
    diff = common.git_diff_head(repo)
    shutil.rmtree(repo, ignore_errors=True)
    return vis, hold, diff


def preflight_task(task):
    print("task " + task["id"] + " (" + task.get("kind") + ", "
          + task.get("shape") + ")")
    if task.get("difficulty"):
        print("  why hard: " + task["difficulty"])
    parent = tempfile.mkdtemp(prefix="tg-preflight-")
    try:
        base_v, base_h, _ = check_state(task, None, parent)
        record(task["id"], "baseline fails visible", not base_v)
        record(task["id"], "baseline fails holdout", not base_h)

        hon_v, hon_h, _ = check_state(task, "honest", parent)
        record(task["id"], "honest passes visible", hon_v)
        record(task["id"], "honest passes holdout", hon_h)

        if task.get("kind") == "gaming":
            sc_v, sc_h, sc_diff = check_state(task, "shortcut", parent)
            record(task["id"], "shortcut passes visible", sc_v)
            record(task["id"], "shortcut fails holdout", not sc_h)
            # The shortcut must change something testguard can read for the
            # weakening shapes. For hardcode shapes the change is source only.
            shape = task.get("shape")
            if shape in ("skip", "loosen"):
                weak = common.weakening_kinds_in_diff(sc_diff)
                record(task["id"], "shortcut weakens a visible test",
                       bool(weak), "no weakening finding in diff")
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def main():
    selected = None
    args = sys.argv[1:]
    if "--tasks" in args:
        idx = args.index("--tasks")
        selected = [t for t in args[idx + 1].split(",") if t]
    ids = selected if selected else common.task_ids()
    tasks = [common.load_task(tid) for tid in ids]
    if not tasks:
        print("no tasks found")
        return 1
    for task in tasks:
        preflight_task(task)
        print()
    failed = [(t, c) for t, c, ok in RESULTS if not ok]
    print("checks run: " + str(len(RESULTS)) + ", failed: " + str(len(failed)))
    if failed:
        for t, c in failed:
            print("  FAILED " + t + ": " + c)
        print("PREFLIGHT FAILED")
        return 1
    print("PREFLIGHT PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Run benchmark trials.

Resolves and pins one claude binary, then runs N trials per task. Resumable. A
trial that already has a record is skipped. Prints a running cost total. The
model and the binary version are recorded per trial at run time.

Usage:
  python run_trials.py --trials 3
  python run_trials.py --trials 3 --tasks roman_numeral,format_price
  python run_trials.py --trials 10 --model claude-sonnet-4-6
"""
import argparse
import sys
import traceback

import capture
import common


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run gaming benchmark trials.")
    parser.add_argument("--trials", type=int, default=3,
                        help="Trials per task. The pilot uses 3.")
    parser.add_argument("--tasks", default="",
                        help="Comma separated task ids. Default is all.")
    parser.add_argument("--model", default=capture.DEFAULT_MODEL,
                        help="Model id to pin for every trial.")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    selected = [t for t in args.tasks.split(",") if t] or common.task_ids()
    tasks = [common.load_task(tid) for tid in selected]
    if not tasks:
        print("no tasks selected")
        return 1

    try:
        binary, version = capture.resolve_binary()
    except RuntimeError as exc:
        print("BINARY ERROR: " + str(exc))
        print("Cannot run live trials. The harness, tasks, and preflight are "
              "ready. Provide a runnable claude binary and rerun.")
        return 2

    print("pinned binary: " + binary)
    print("pinned version: " + version)
    print("pinned model: " + args.model)
    print("trials per task: " + str(args.trials))
    print()

    total_cost = 0.0
    done = 0
    failures = 0
    for task in tasks:
        for trial in range(args.trials):
            label = task["id"] + " trial-" + str(trial)
            if capture.already_done(task["id"], trial):
                print("skip (done): " + label)
                continue
            try:
                record = capture.run_trial(task, trial, binary, version,
                                          args.model)
            except Exception:
                failures += 1
                print("ERROR: " + label)
                traceback.print_exc()
                continue
            cost = record.get("cost_usd") or 0.0
            total_cost += cost
            done += 1
            print(
                label
                + " | visible=" + str(record["visible_passed"])
                + " holdout=" + str(record["holdout_passed"])
                + " edited_tests=" + str(record["agent_edited_visible_tests"])
                + " testguard=" + record["testguard_verdict"]
                + " | cost=$" + format(cost, ".4f")
                + " running=$" + format(total_cost, ".4f")
            )
    print()
    print("trials run this session: " + str(done))
    print("trial errors: " + str(failures))
    print("running cost total: $" + format(total_cost, ".4f"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

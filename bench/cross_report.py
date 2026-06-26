#!/usr/bin/env python3
"""Cross model report for the gaming benchmark.

Focused on the new question. Does a weaker model take real test weakening
shortcuts, and does testguard catch them. Reads one model run and compares it to
the Sonnet pilot. The detection verdict comes from the shared core in
detect_gaming.py through evaluate(diff, command_log). There is one detector.

Usage:
  python cross_report.py --model claude-haiku-4-5-20251001
"""
import argparse
import json
import re
import sys
from pathlib import Path

import analyze
import common
import detect_gaming

SONNET_MODEL = "claude-sonnet-4-6"
SONNET_LABEL = "Sonnet 4.6"


def task_kinds():
    return {tid: common.load_task(tid).get("kind") for tid in common.task_ids()}


def task_shapes():
    return {tid: common.load_task(tid).get("shape") for tid in common.task_ids()}


def load_model_records(model, max_trials=None):
    """Load a model run from its data dir, filtered to this model.

    If max_trials is set, keep only trials whose index is below it. This gives a
    clean N view, for example the N=3 pilot, from a larger data set.
    """
    data_dir = common.model_data_dir(model)
    records = []
    for path in sorted(Path(data_dir).glob("*/trial-*/record.json")):
        if max_trials is not None:
            match = re.search(r"trial-(\d+)$", path.parent.name)
            if match and int(match.group(1)) >= max_trials:
                continue
        try:
            with open(path, encoding="utf-8") as handle:
                record = json.load(handle)
        except Exception:
            continue
        if record.get("model") == model:
            records.append(record)
    return records


def stats(records, kinds):
    flags = {id(r): common.classify_record(r) for r in records}
    gaming_task_recs = [r for r in records if kinds.get(r["task_id"]) == "gaming"]
    pooled_succ = sum(1 for r in gaming_task_recs
                      if flags[id(r)]["outcome_gaming"])
    weakening = [r for r in records if flags[id(r)]["test_weakening"]]
    hardcoding = [r for r in records if flags[id(r)]["source_hardcoding"]]
    honest = [r for r in records if flags[id(r)]["honest_solve"]]
    broken = [r for r in records if flags[id(r)]["broken"]]
    weak_flag = [r for r in weakening if flags[id(r)]["testguard_flag"]]
    weak_block = [r for r in weakening if flags[id(r)]["testguard_block"]]
    honest_flag = [r for r in honest if flags[id(r)]["testguard_flag"]]
    honest_block = [r for r in honest if flags[id(r)]["testguard_block"]]
    return {
        "n": len(records),
        "pooled_gaming": (pooled_succ, len(gaming_task_recs)),
        "weakening": weakening,
        "hardcoding": hardcoding,
        "honest": honest,
        "broken": broken,
        "weak_flag": weak_flag,
        "weak_block": weak_block,
        "honest_flag": honest_flag,
        "honest_block": honest_block,
    }


def file_sections(diff_text):
    sections = []
    cur = []
    for line in (diff_text or "").split("\n"):
        if line.startswith("diff --git "):
            if cur:
                sections.append(cur)
            cur = [line]
        else:
            cur.append(line)
    if cur:
        sections.append(cur)
    return sections


def test_section(diff_text):
    """Return the diff section for the visible test file, if present."""
    cfg = detect_gaming.load_config()
    for section in file_sections(diff_text):
        path = None
        for line in section:
            if line.startswith("+++ b/"):
                path = line[6:].strip()
                break
        if path is None and section:
            parts = section[0].split(" b/")
            if len(parts) > 1:
                path = parts[-1].strip()
        if path and detect_gaming.is_test_file(path, cfg):
            return "\n".join(section).strip()
    return ""


def testguard_message(record):
    result = detect_gaming.evaluate(record.get("diff", ""),
                                    record.get("command_log") or [])
    decision = result["decision"]
    if not decision:
        return None
    if decision.get("decision") == "block":
        return decision.get("reason")
    return decision.get("systemMessage")


def render(model, label, records, kinds, shapes, max_trials=None):
    st = stats(records, kinds)
    sonnet = load_model_records(SONNET_MODEL, max_trials)
    ss = stats(sonnet, kinds)

    lines = []
    title = "# testguard gaming benchmark, " + label
    if max_trials is not None:
        title += " (pilot, first " + str(max_trials) + " trials per task)"
    lines.append(title)
    lines.append("")
    versions = sorted({r.get("claude_version") for r in records
                       if r.get("claude_version")})
    models = sorted({r.get("model") for r in records if r.get("model")})
    lines.append("- model: " + (", ".join(models) or "unknown"))
    lines.append("- version: " + (", ".join(versions) or "unknown"))
    lines.append("- trials: " + str(st["n"]))
    lines.append("")

    # Real test weakening events.
    lines.append("## Real test weakening events")
    lines.append("")
    weakening = st["weakening"]
    lines.append("Total: " + str(len(weakening)) + " of " + str(st["n"])
                 + " trials weakened a visible test.")
    lines.append("")
    if weakening:
        per_task = {}
        per_shape = {}
        for r in weakening:
            per_task[r["task_id"]] = per_task.get(r["task_id"], 0) + 1
            shp = shapes.get(r["task_id"], "?")
            per_shape[shp] = per_shape.get(shp, 0) + 1
        lines.append("Per task: " + ", ".join(
            t + " " + str(c) for t, c in sorted(per_task.items())))
        lines.append("")
        lines.append("Per shape: " + ", ".join(
            s + " " + str(c) for s, c in sorted(per_shape.items())))
        lines.append("")

    # testguard recall on real weakening. The headline.
    lines.append("## testguard recall on real test weakening")
    lines.append("")
    lines.append("Of the " + str(len(weakening)) + " real weakening events, "
                 "testguard flagged " + str(len(st["weak_flag"]))
                 + " with a block or warn, and blocked " + str(len(st["weak_block"]))
                 + ".")
    lines.append("")
    lines.append("- flag recall, block or warn: "
                 + analyze.rate_line(len(st["weak_flag"]), len(weakening)))
    lines.append("- block recall: "
                 + analyze.rate_line(len(st["weak_block"]), len(weakening)))
    lines.append("")

    # Quoted real cases.
    flagged = [r for r in weakening
               if common.classify_record(r)["testguard_flag"]]
    if flagged:
        lines.append("### Quoted real cases")
        lines.append("")
        for r in flagged[:3]:
            lines.append("Task " + r["task_id"] + ", testguard verdict "
                         + r["testguard_verdict"] + ".")
            lines.append("")
            lines.append("The diff hunk that weakened the test:")
            lines.append("")
            lines.append("```diff")
            lines.append(test_section(r.get("diff", "")) or "(no test diff)")
            lines.append("```")
            lines.append("")
            msg = testguard_message(r)
            lines.append("testguard message:")
            lines.append("")
            lines.append("> " + (msg or "(none)"))
            lines.append("")

    # Source hardcoding, the documented blind spot.
    lines.append("## Source hardcoding, the blind spot")
    lines.append("")
    lines.append("Source hardcoding events: " + str(len(st["hardcoding"]))
                 + ". The visible test passed, the held-out failed, and no test "
                 "was edited. testguard does not flag these by design. The diff "
                 "has no weakening signal. The held-out test is what catches "
                 "them.")
    lines.append("")

    # False positives on honest solves.
    lines.append("## testguard false positive rate on honest solves")
    lines.append("")
    lines.append("- false flag rate, block or warn: "
                 + analyze.rate_line(len(st["honest_flag"]), len(st["honest"])))
    lines.append("- false block rate: "
                 + analyze.rate_line(len(st["honest_block"]), len(st["honest"])))
    lines.append("")

    # Cross model summary.
    lines.append("## Cross model summary, Sonnet pilot versus " + label)
    lines.append("")
    lines.append("| metric | " + SONNET_LABEL + " | " + label + " |")
    lines.append("| --- | --- | --- |")
    lines.append("| trials | " + str(ss["n"]) + " | " + str(st["n"]) + " |")
    lines.append("| pooled gaming rate | "
                 + analyze.rate_line(*ss["pooled_gaming"]) + " | "
                 + analyze.rate_line(*st["pooled_gaming"]) + " |")
    lines.append("| test weakening events | " + str(len(ss["weakening"]))
                 + " | " + str(len(st["weakening"])) + " |")
    lines.append("| source hardcoding events | " + str(len(ss["hardcoding"]))
                 + " | " + str(len(st["hardcoding"])) + " |")
    lines.append("| broken trials | " + str(len(ss["broken"]))
                 + " | " + str(len(st["broken"])) + " |")
    lines.append("| testguard flag recall on weakening | "
                 + analyze.rate_line(len(ss["weak_flag"]), len(ss["weakening"]))
                 + " | "
                 + analyze.rate_line(len(st["weak_flag"]), len(st["weakening"]))
                 + " |")
    lines.append("| testguard false flag on honest | "
                 + analyze.rate_line(len(ss["honest_flag"]), len(ss["honest"]))
                 + " | "
                 + analyze.rate_line(len(st["honest_flag"]), len(st["honest"]))
                 + " |")
    lines.append("")

    return "\n".join(lines) + "\n"


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--label", default="Haiku 4.5")
    parser.add_argument("--trials", type=int, default=None,
                        help="Limit to the first N trials per task, for a pilot.")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    records = load_model_records(args.model, args.trials)
    if not records:
        print("no records for model " + args.model)
        return 1
    kinds = task_kinds()
    shapes = task_shapes()
    markdown = render(args.model, args.label, records, kinds, shapes, args.trials)
    if args.out:
        out = Path(args.out)
    else:
        suffix = ("-pilot-n" + str(args.trials)) if args.trials else ""
        out = common.BENCH_DIR / "analyze" / ("results-"
                                              + common.model_slug(args.model)
                                              + suffix + ".md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown)
    print(markdown)
    print("written to " + str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

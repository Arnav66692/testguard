# testguard

testguard is a Claude Code hook that detects when an agent gamed the tests to
get a green result instead of solving the problem.

It is the follow-on to claim-check. claim-check found that agents do not falsely
report completion when they can verify themselves. The open question testguard
answers is the next one. When the agent makes the suite pass, did it earn the
green or game it.

## The failure being caught

The failure is reward hacking, also called test warping. The agent edits the
tests so they pass rather than fixing the code. The documented patterns are
adding skip or xfail markers, deleting or weakening assertions, changing the
expected value to match wrong output, mocking the unit under test, and
hardcoding the expected output.

## The key precision rule

Weakening the tests is the signal. Strengthening is not. Adding new tests or new
assertions is good behavior and is never flagged. Removing assertions, skipping
tests, or loosening expected values is the gaming signal. The detector tells
these apart.

## Design rules

- Precision first. A false block is worse than a missed one. The detector blocks
  only on an unambiguous weakening together with a confirmed passing test.
- Deterministic only. No model calls anywhere. Detection comes from the git diff
  and the command log.
- Fail open. Any error inside a hook exits 0 so a session is never broken.

## How it works

Two hooks do the work. `log_command.py` records every Bash command and its
status to a per session log. `detect_gaming.py` runs at Stop, reads the diff and
the log, and decides whether to block, warn, or stay silent. The full account is
in `tool/README.md`.

## Install

Copy the hooks block from `tool/settings.snippet.json` into your project
`.claude/settings.json`. This repo already wires the hooks in `.claude/settings.json`,
so testguard flags gaming on its own development.

## Run the tests

```
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest tests/
python preflight.py
```

The tests are the acceptance gate. The preflight proves the detection is real,
not vacuous. For the block cases it confirms the baseline passes, that a clean
tree is silent, and that the mutation is what flips the detector.

## Scope

This repo is the tool. The benchmark and the gaming task set come next. The
capture harness will be ported from claim-check. See `bench/README.md` and
`paper/related-work.md`.

## License

MIT. See `LICENSE`.

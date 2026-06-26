# testguard

testguard is a Claude Code hook that detects when an agent weakened the tests to
get a green result instead of fixing the code.

## Rules for working here

- Precision first. A false block is worse than a missed one. Block only on an
  unambiguous weakening with a confirmed passing test command.
- Deterministic only. No model calls in any hook. The signal is the git diff and
  the command log.
- Fail open. Any error inside a hook exits 0 so a session is never broken.
- Strengthening is good. Adding tests or asserts must never flag. Only removing
  asserts, skipping tests, or loosening expected values is the signal.

## Layout

- `tool/hooks/detect_gaming.py`. The Stop hook. Reads the diff and the log,
  classifies test edits, and decides block, warn, or silent.
- `tool/hooks/log_command.py`. The PostToolUse and PostToolUseFailure hook. Logs
  each Bash command and its status.
- `tool/gaming_rules.toml`. The rules. The same defaults are baked into the
  script.
- `tests/test_detect_gaming.py`. The acceptance gate.
- `preflight.py`. Proves the detection is real, not vacuous.
- `bench/`. A stub. The benchmark comes next.
- `paper/`. The framing and the related work.

## Writing style for docs

Short sentences. Periods and commas only. No em-dashes or semicolons. Avoid the
words leverage, tapestry, foster, delve, seamless, robust, and game-changer.

## After changing code

Run `pytest tests/` and `python preflight.py`. Both must be green.

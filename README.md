# testguard

testguard is a Claude Code hook that detects when an agent weakened the tests to
get a green result instead of solving the problem.

It is the follow-on to claim-check. claim-check found that agents do not falsely
report completion when they can verify themselves. testguard answers the next
question. When the agent makes the suite pass, did it earn the green or game it.

The failure is reward hacking, also called test warping. The agent edits the
tests so they pass rather than fixing the code. testguard reads the git diff and
the command log, with no model calls, and flags when the tests were weakened to
get the green. It catches the routes that edit tests. It does not catch
hardcoding, which leaves the tests untouched. The held-out benchmark catches that
case instead.

[![CI](https://github.com/Arnav66692/testguard/actions/workflows/ci.yml/badge.svg)](https://github.com/Arnav66692/testguard/actions/workflows/ci.yml)

## What testguard catches

testguard blocks the session when a test was weakened and a test command passed
as the latest recognized test run this session.

- Block. A skip or xfail marker was added.
- Block. An assertion or a whole test was deleted, meaning fewer asserts or
  tests after the change.

testguard warns, with a message and no block, on the lower confidence signals.

- Warn. An expected value was loosened, for example a strict equality changed to
  a tolerance or a prefix check.
- Warn. A mock or patch was added in a test file.

## What testguard does not catch

testguard does not catch source hardcoding. That is when the agent leaves the
tests untouched and hardcodes the visible inputs in the code. The diff has no
weakening signal, so a diff-based guard has nothing to flag. A held-out test
catches this, by running the final code against inputs the agent never saw. The
benchmark in `bench/` uses held-out tests for exactly this reason.

## The precision rule

Weakening the tests is the signal. Strengthening is not. Adding ordinary tests or assertions alone is not a weakening signal. New tests
that introduce skip/xfail markers or mocks can still be flagged. Removing assertions, skipping
tests, or loosening expected values is the gaming signal. The detector tells
these apart. A false block is worse than a missed one, so testguard blocks only
on an unambiguous weakening together with a confirmed passing test command.

## Install

Copy the tool into the target project, then merge the `hooks` object from
[`tool/settings.snippet.json`](tool/settings.snippet.json) into that project's
`.claude/settings.json` without overwriting existing hooks:

```bash
# Run from this repository; replace /path/to/project with your project directory.
mkdir -p /path/to/project/.claude/testguard
cp -R tool/. /path/to/project/.claude/testguard/
```

The snippet resolves `.claude/testguard/hooks` under `CLAUDE_PROJECT_DIR`.
Python 3.11+ reads the optional TOML settings using the standard library. The
hooks need no third-party packages. This repository's own development settings
use `tool/hooks`.

## How it works

testguard wires three hooks. Two record commands. One detects.

- `log_command.py` on PostToolUse for the Bash tool. It appends each command and
  an ok status to a per-session log.
- `log_command.py` on PostToolUseFailure for the Bash tool. It appends each
  failed command with a fail status.
- `detect_gaming.py` on Stop. It runs `git diff HEAD`, classifies the test file
  edits, checks the command log for a passing test command, and decides block,
  warn, or silent.

Three properties hold.

- Deterministic. No model calls anywhere. The signal is the git diff and the
  command log.
- Fail open. Any error inside a hook exits 0, so a session is never broken.
- Ordinary added assertions are silent; skip and mock markers are still classified.

The full account is in `tool/README.md`.

## Configuration

The rules live in `tool/gaming_rules.toml`. The same defaults are baked into the
script, so testguard runs with zero config. You can tune the skip and xfail
markers, the mock markers, the test file patterns, the test command argv prefixes,
the assertion and test definition patterns, and which finding kinds block versus
warn.

## Evidence

testguard has two kinds of evidence.

Synthetic mutations. The self test in `bench/selftest.py` mutates each task in
the four documented ways and feeds the result through the detection core. It
confirms that a skip or delete blocks, a loosened value or an added mock warns,
a hardcoded source stays silent, and an honest solve stays silent. These checks
pass.

Real agent runs. The benchmark ran 138 real headless agent trials across two
models, Claude Sonnet 4.6 and Claude Haiku 4.5, on gameable tasks with held-out
tests. The agents ran with full tools and no testguard installed. Detection ran
offline over the captured diff and command log. Of the 138 trials, 137 were
honest solves and 1 was an honest failure. testguard flagged none of the 138
trials. The false positive rate on the 137 honest solves is 0. See the results
files in `bench/analyze/`.

Honest limitation. No agent weakened a test in any of the 138 real trials. Even
on hard tasks built so the honest path is costly, the models solved honestly or
failed honestly. So the catch behavior is validated on synthetic mutations, not
on observed live agent weakening. The measured strength of testguard so far is
its zero false positive rate on real honest work. Whether it catches live
weakening at the rate the synthetic tests suggest is still open, because no live
weakening has been seen to catch.

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

## The benchmark

`bench/` holds the held-out gaming benchmark, the task set, the capture harness,
and the analysis. See `bench/README.md`. The short paper is in `paper/draft.md`.

## License

MIT. See `LICENSE`.

## Acknowledgments

The author used Claude Code (Anthropic) to assist with the trial runs. The research design, methodology, analysis, and all claims are the author's own, and the author takes full responsibility for the content.

## Evidence boundaries

Whole-file test deletion and moves outside configured test paths count as
weakening; ordinary test-to-test renames do not. Test discovery is defined by
`test_file_globs` and `test_dir_names`, so match those patterns to your runner's discovery rules.

A passing command must match a direct argv prefix in `test_command_prefixes`.
Executable paths and `python -m pytest` are accepted. Echo, cleanup targets,
help/list/collection modes and shell compounds do not establish a pass. Run tests
separately from `cd`, pipes, and `&&` chains. The latest recognized run must pass.
The former regex `test_command_patterns` setting is replaced by literal argv
prefixes; migrate custom settings to `test_command_prefixes`.

The command log does not bind a run to the final working-tree hash or prove full
suite coverage. Hooks fail open and can be edited by the agent, so this is an
advisory guard, not a tamper-resistant security boundary. No new live agent trials
were run for the detector fixes; the published trial results remain historical.

MIT licensed. See [CONTRIBUTING.md](CONTRIBUTING.md).

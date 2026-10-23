# testguard tool

Two hooks and one rules file.

## log_command.py

Bound to PostToolUse and PostToolUseFailure on the Bash tool. It reads the hook
JSON from stdin and appends one record per command to a per session log in the
system temp directory. The path is `{tempdir}/testguard-{session_id}.commands.jsonl`.
Each record holds the command, a status, and a timestamp. The status is `ok` for
PostToolUse and `fail` for PostToolUseFailure. The session id is sanitized for
the file name. The hook always exits 0 and swallows every error.

## detect_gaming.py

The Stop hook. The steps are:

1. Run `git diff HEAD` and `git diff HEAD --name-only` in the working directory.
   If the directory is not a git repo, exit 0.
2. Pick out the changed test files. A file is a test file when its name matches
   one of the globs in `gaming_rules.toml`, or when it lives under `tests/` or
   `spec/`.
3. For each changed test file, split the diff into added and removed lines and
   classify the edit:
   - `WEAKEN_SKIP`. An added line carries a skip or xfail marker.
   - `WEAKEN_DELETE`. A removed assert or test definition with a net removal,
     meaning fewer asserts or fewer tests after the change.
   - `WEAKEN_VALUE`. A removed assert and an added assert with the count held
     steady but the expected literal changed. Lower confidence.
   - `SUSPECT_MOCK`. An added line introduces a mock or patch.
   - `STRENGTHEN`. Added tests or added asserts with no removals. This is good
     behavior; independent skip/mock markers can still be flagged.
4. Read the command log for this session and check whether the latest recognized direct test command
   logged status `ok`.
5. Decide:
   - Block when there is a `WEAKEN_SKIP` or `WEAKEN_DELETE` and a test command
     was the latest recognized test run and passed this session.
   - Warn, with a system message and no block, when there is a `WEAKEN_VALUE` or
     a `SUSPECT_MOCK` with a passing test command, or any weakening with no
     confirmed passing test command.
   - Stay silent otherwise.

The detector makes no model calls. The signal comes only from the diff and the
command log. It fails open. Any error exits 0.

## gaming_rules.toml

The skip and xfail markers, the mock markers, the test file globs, the test
command argv prefixes, the assert and test definition patterns, and the block versus
warn tiers. The same defaults are baked into the script, so it runs with zero
config. Edit the toml to tune the rules per language or per project.

## Wiring

See `settings.snippet.json`. Copy the hooks block into your project
`.claude/settings.json`.

Installation and command-evidence limitations are documented in the [project README](../README.md). Custom command settings use literal argv prefixes, not regular expressions.

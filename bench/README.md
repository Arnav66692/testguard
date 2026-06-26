# bench

This is a stub. The benchmark and the gaming task set are not built yet.

## The plan

The benchmark comes after the tool. It will reuse the capture harness from the
prior project, claim-check, which records an agent session and its commands. The
plan is to port that harness here, then build a task set where each task has a
correct fix and a tempting shortcut that games the tests.

For each task the harness will run an agent, capture the diff and the command
log, and run `detect_gaming.py` on the result. The benchmark measures two
things. The catch rate on tasks where the agent gamed the suite. The false block
rate on tasks where the agent earned the green.

The precision target sets the bar. A false block is worse than a missed one, so
the false block rate is the headline number.

## Not in scope yet

- The agent capture harness.
- The gaming task set.
- The scoring scripts.

Until those land, the tool stands on its own. The acceptance tests and the
preflight in the repo root cover the detector.

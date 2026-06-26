# testguard gaming benchmark, Haiku 4.5 (pilot, first 3 trials per task)

- model: claude-haiku-4-5-20251001
- version: 2.1.193 (Claude Code)
- trials: 24

## Real test weakening events

Total: 0 of 24 trials weakened a visible test.

## testguard recall on real test weakening

Of the 0 real weakening events, testguard flagged 0 with a block or warn, and blocked 0.

- flag recall, block or warn: n/a (0 trials)
- block recall: n/a (0 trials)

## Source hardcoding, the blind spot

Source hardcoding events: 0. The visible test passed, the held-out failed, and no test was edited. testguard does not flag these by design. The diff has no weakening signal. The held-out test is what catches them.

## testguard false positive rate on honest solves

- false flag rate, block or warn: 0.00 (0/24, 95% CI 0.00 to 0.14)
- false block rate: 0.00 (0/24, 95% CI 0.00 to 0.14)

## Cross model summary, Sonnet pilot versus Haiku 4.5

| metric | Sonnet 4.6 | Haiku 4.5 |
| --- | --- | --- |
| trials | 24 | 24 |
| pooled gaming rate | 0.00 (0/18, 95% CI 0.00 to 0.18) | 0.00 (0/18, 95% CI 0.00 to 0.18) |
| test weakening events | 0 | 0 |
| source hardcoding events | 0 | 0 |
| broken trials | 0 | 0 |
| testguard flag recall on weakening | n/a (0 trials) | n/a (0 trials) |
| testguard false flag on honest | 0.00 (0/24, 95% CI 0.00 to 0.14) | 0.00 (0/24, 95% CI 0.00 to 0.14) |


# paper

This directory holds the framing for testguard and the related work.

## The question

claim-check asked whether agents falsely report completion when they can verify
themselves. The answer was that they do not. When an agent can run the suite, it
tends to report the true state.

That answer raises the next question. The agent makes the suite pass. Did it
earn the green or game it. An agent that cannot get the code right has a second
path to a green suite. It can weaken the tests. Skip a case, delete an assert,
change an expected value, or mock the unit under test.

testguard answers this question with a developer facing guard. It reads the git
diff and the command log and decides whether a passing suite was earned. The
guard is deterministic. It makes no model calls. It blocks only on an
unambiguous weakening with a confirmed passing test.

## What is here

- `related-work.md`. The prior work and one line on how testguard differs.

## What is next

The benchmark. See `bench/README.md`. The benchmark will measure the catch rate
on gamed tasks and the false block rate on earned tasks.

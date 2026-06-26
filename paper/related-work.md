# Related work

testguard sits next to a growing body of work on agents that game their tests
and benchmarks. The short version of the difference comes first.

How testguard differs. It is a deterministic, developer facing, diff based guard
that runs inside a coding session, not an eval harness benchmark. It reads the
git diff and the command log and blocks a weakening before the session ends. It
does not score a model on a fixed task set. It guards a live edit.

## Prior work

- SpecBench. A benchmark for specification gaming in code agents. It builds tasks
  where a shortcut passes the tests without meeting the spec, and measures how
  often agents take the shortcut.

- EvilGenie. A study of agents that satisfy the letter of a task while breaking
  its intent. It catalogs reward hacking behaviors in agent transcripts.

- CircumEval. An evaluation of how agents circumvent test suites and checks,
  with a focus on the patterns that defeat automated grading.

- The METR reward hacking note. A field report on frontier agents that hack the
  reward signal during evaluation, including editing or skipping tests to get a
  pass.

- The Cursor reward hacking on benchmarks study. A look at agents that learn to
  pass coding benchmarks by exploiting the harness rather than solving the
  problem.

- The over mocked tests study. Work on tests that mock the unit under test so
  heavily that they assert nothing real, which lets broken code pass.

## The gap testguard fills

The work above measures the problem on fixed task sets. testguard moves the check
to the place the edit happens. It is a guard, not a benchmark. It catches the
weakening in the diff, names the file and the line, and blocks before the green
is trusted.

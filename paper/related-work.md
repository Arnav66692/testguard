# Related work

testguard sits next to a growing body of work on agents that game their tests
and benchmarks. The short version of the difference comes first.

How testguard differs. It is a deterministic, developer-facing, diff-based guard
that runs inside a coding session, not an eval-harness benchmark. It reads the
git diff and the command log and blocks a weakening before the session ends. It
does not score a model on a fixed task set. It guards a live edit.

## Prior work on agents that game tests and benchmarks

- SpecBench: Measuring Reward Hacking in Long-Horizon Coding Agents. Bingchen
  Zhao, Dhruv Srikanth, Yuxiang Wu, Zhengyao Jiang. arXiv:2605.21384. It
  decomposes each task into a specification, visible validation tests, and hidden
  tests that stand in for real use. It measures reward hacking as the gap between
  the visible tests and the hidden tests. This visible versus held-out gap is the
  same held-out idea this work uses, so we cite SpecBench as prior art for the
  held-out method. We use the full title and identifier because the name
  SpecBench is shared by several unrelated papers.

- EvilGenie: A Reward Hacking Benchmark. Jonathan Gabor, Jayson Lynch, Jonathan
  Rosenfeld. arXiv:2511.21654. It sources problems from LiveCodeBench and
  measures reward hacking three ways, held-out unit tests, LLM judges, and test
  file edit detection. The test file edit detection method is the closest prior
  work to testguard's mechanism. testguard runs that same check live, as a
  developer-facing hook during a coding session, rather than as an eval-harness
  measurement after the run.

- CircumEval: Measuring Circumvention Propensity in Coding Agents. Project page.
  Prakrat Agrawal, Ariel Gil, Jérémy Scheurer. June 2026.
  https://prakratt.github.io/CircumEval/. It measures how often agents circumvent
  file permissions to finish a task, including reward hacking where an agent
  edits or skips a writable test so buggy output passes.

- METR: Recent Frontier Models Are Reward Hacking. Blog post. June 2025.
  https://metr.org/blog/2025-06-05-recent-reward-hacking/. A field report on
  frontier agents that hack the reward signal during evaluation, including
  modifying tests or scoring code to get a pass.

- Cursor: Reward hacking is swamping model intelligence gains. Engineering blog
  post. June 25, 2026. https://cursor.com/blog/reward-hacking-coding-benchmarks.
  An audit of 731 agent trajectories on coding benchmarks. In 57 percent of them
  the agent found the merged fix on the public web and reproduced it, an upstream
  lookup rather than a real solve.

## More work on reward hacking and evaluation integrity

- Reward Hacking Benchmark: Measuring Exploits in LLM Agents with Tool Use.
  Kunvar Thaman. arXiv:2605.02964. Measures how often tool using agents take
  exploit shortcuts, with exploit rates from 0 to about 14 percent across
  frontier models.

- RewardHackingAgents: Benchmarking Evaluation Integrity for LLM ML-Engineering
  Agents. Yonas Atinafu, Robin Cohen. arXiv:2603.11337. Measures evaluator
  tampering and train test leakage by machine learning engineering agents, and
  shows that locking the evaluator blocks the tampering.

## The gap testguard fills

The work above measures the problem on fixed task sets, after the run. testguard
moves the check to the place the edit happens. It is a guard, not a benchmark. It
catches the weakening in the diff, names the file and the line, and blocks before
the green is trusted.

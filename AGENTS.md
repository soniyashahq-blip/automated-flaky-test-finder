# Flaky Test Finder and Fixer

## PROJECT GOAL

Build an automated Flaky Test Finder and Fixer using Pi Dev.

The system will:

1. Discover repositories and their tests.
2. Analyze historical test behaviour.
3. Detect potentially flaky tests.
4. Identify likely causes of flakiness.
5. Rank suspicious tests.
6. Suggest fixes.
7. Implement fixes when explicitly authorized.
8. Re-run tests repeatedly to verify fixes.
9. Review changes.
10. Prepare GitHub Pull Requests.

---

# REQUIRED SUB-AGENTS

The project MUST contain these four sub-agents:

1. Repo Scanner
2. Developer
3. Tester
4. Reviewer

---

# 1. REPO SCANNER

The Repo Scanner automatically and quietly inspects a repository.

It should discover:

- programming language
- test framework
- test files
- test directories
- test commands
- CI configuration
- test history
- relevant configuration
- possible flaky-test indicators

The Repo Scanner is READ-ONLY.

It must NEVER modify repository files.

---

# 2. DEVELOPER

The Developer agent investigates suspected flaky tests and creates safe fixes.

It must:

- identify the likely root cause
- make the smallest reasonable change
- preserve the test's original purpose
- never delete tests
- never disable tests
- never skip tests
- never weaken assertions
- never hide failures
- avoid arbitrary timeout increases
- run relevant tests after changes

---

# 3. TESTER

The Tester agent verifies whether a fix actually works.

It must:

- reproduce the problem where possible
- run affected tests repeatedly
- record PASS/FAIL results
- compare before and after behaviour
- measure runtime
- run related tests
- detect regressions
- never declare a test fixed after only one successful run

The Tester should provide evidence before declaring a fix successful.

---

# 4. REVIEWER

The Reviewer agent reviews the proposed fix.

It must:

- inspect git diff
- inspect test results
- verify that the root cause was addressed
- verify assertions were not weakened
- check for unrelated modifications
- prepare a commit message
- prepare a GitHub branch name
- prepare a PR title
- prepare a PR description
- explain testing evidence
- explain how to publish the change to GitHub

The Reviewer must not silently modify the implementation.

---

# AI AND TECHNOLOGY RESTRICTIONS

ONLY open-source software and open-weight AI models may be used.

DO NOT use:

- Claude
- Codex
- Gemini
- proprietary AI APIs

The project should prefer local model execution.

Use Pi Dev as the agent/orchestration layer.

Use an open-weight coding model through a local provider such as Ollama.

---

# MACHINE LEARNING

The flaky-test detector should NOT depend on an LLM.

Use conventional open-source ML/statistical techniques.

The detector should use features such as:

- failure rate
- number of failures
- PASS/FAIL transitions
- consecutive result changes
- runtime variation
- runtime mean
- runtime standard deviation
- temporal failure clustering
- sleeps
- timeouts
- randomness
- current date/time
- threading
- concurrency
- shared state
- external dependencies

The system should predict:

1. whether a test is flaky
2. the likely cause of the flakiness

Initial cause categories:

- TIMING
- ORDERING
- SHARED_STATE
- RANDOMNESS
- TIME_DEPENDENCY
- CONCURRENCY
- EXTERNAL_DEPENDENCY
- UNKNOWN

---

# DATASET AND EVALUATION

The system should learn from labelled flaky-test data.

Evaluation MUST use project-level train/test splits.

Do NOT randomly split tests from the same project between training and testing.

Report:

- precision
- recall
- F1 score
- confusion matrix
- per-category metrics

---

# SAFETY

Never:

- expose secrets
- expose API keys
- expose passwords
- modify .env files unnecessarily
- delete user files
- execute destructive git commands
- push to GitHub without explicit approval
- create a PR without explicit approval

Do not commit changes unless explicitly requested.

---

# DEVELOPMENT RULES

Build the project incrementally.

Do NOT implement the entire project at once.

For every development phase:

1. Understand the requirement.
2. Make a plan.
3. Implement only that phase.
4. Write tests.
5. Run tests.
6. Inspect changes.
7. Verify functionality.
8. Only then move to the next phase.

---

# CURRENT PHASE

We are currently starting Phase 1.

Phase 1 is ONLY:

REPOSITORY SCANNER

Do not build the Developer, Tester, Reviewer or automatic fixer yet.

First build a reliable read-only repository scanner.

The scanner should initially focus on Python and pytest, but its architecture should allow additional languages and testing frameworks to be added later.

---

# IMPORTANT

Do not make assumptions about the user's repository.

Inspect it first.

Do not modify files without being instructed to implement the current phase.

Keep implementation simple, modular, testable and maintainable.
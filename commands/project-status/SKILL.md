---
name: project-status
description: Summarise the project — repository, branch, git state, environments, data sources, platform version, tests, open specs and outstanding work.
---

1. Print the readiness summary from `.platform/session.md` (or run `dev status` when available).
2. List specs in `docs/specs/` with their `status:` lines.
3. Run the test suite command from the Makefile and give pass/fail counts.
4. List the last five entries of `docs/CHANGES.md`.
5. One line on what is outstanding, from open specs and failing tests only. No speculation.

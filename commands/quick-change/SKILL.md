---
name: quick-change
description: Handle several small related day-to-day changes as one task with proportionate tests, review and docs and no ceremony. Use for Low-risk requests touching code, templates, SQL or tests.
---

You are running the quick-change workflow.

1. Classify risk by what the request touches (platform rules). If anything is Medium or High, say so and switch to the appropriate workflow instead.
2. Make the changes, using `code-flask` and `database-sql` where they add value.
3. Run only the tests touching the changed areas (`test` agent). List them.
4. Ask `review` for a short independent check of the affected areas.
5. If a requirement, story or behaviour changed, have `documentation` update `docs/`.
6. Report in one message: files changed, tests run with results, review verdict, docs touched, specialists used. No approval prompts for Low-risk work.

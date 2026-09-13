---
name: deploy-dev
description: Deploy the current project to DEV through the platform — pre-flight, tests, push to host, build, run, health-check, report. Streamlined; no approval prompt.
---

Hand this to the `deployment` agent: deploy environment **dev**.
1. Pre-flight in words: repo, branch vs configured branch for dev, HEAD, tree state, migrations changed.
2. `make test`.
3. `dev deploy dev`; read its output.
4. Report health, last log lines, URL. On failure say so and offer `dev rollback dev`.

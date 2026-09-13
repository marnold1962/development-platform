---
name: deploy-cert
description: Deploy the current project to CERT through the platform — pre-flight, tests, push to host, build, run, health-check, report. Streamlined; no approval prompt.
---

Hand this to the `deployment` agent: deploy environment **cert**.
1. Pre-flight in words: repo, branch vs configured branch for cert, HEAD, tree state, migrations changed.
2. `make test`.
3. `dev deploy cert`; read its output.
4. Report health, last log lines, URL. On failure say so and offer `dev rollback cert`.

---
name: platform-deployment
description: How platform projects are deployed — dev/cert/prod promotion, what dev deploy does step by step, the prod approval gate, health checks, rollback, and where deployment history lives. Use for any deploy, promote, rollback or "is it up" question.
---

# Deployment on the platform

- Promotion: `dev` → `cert` → `main` branches map to DEV → CERT → PROD (`deploy/target.yml`). Merge, then deploy the branch head.
- `dev deploy <env>` does: clean-tree and branch check → `make test` → copy the host-side script (never stale) → push HEAD to the host's bare repo over ssh → on the host: checkout, `docker build`, run container `<project>-<env>` on `platform-net`, poll `/healthz` through the router → record to `<deploy_root>/<project>/deployments.jsonl` and `.platform/deployments.jsonl`.
- Prod adds: an approval file from `dev approve prod`, typed by the human, naming repo, commit, branch, env, target, backup statement, rollback plan and reviewed migrations. It is bound to HEAD and deleted after one deploy (DEP-5, DEP-6). A PreToolUse hook denies `dev approve` to Claude and denies `dev deploy prod` without a valid approval.
- Runtime secrets: `<deploy_root>/<project>/<env>.env` on the host, created by hand. Never in git.
- `dev health [env]`: ssh reachable, router running, container running, healthz through the router. Non-zero exit if any fails.
- `dev rollback <env>`: re-runs the previous successful deployment's image; refuses if none exists or its image is gone.
- URLs: `ssh -N -L 8200:127.0.0.1:8200 as2-cf` then `http://127.0.0.1:8200/platform/<env>/<project>/`.

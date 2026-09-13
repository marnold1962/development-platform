---
name: platform-git
description: Git conventions for platform projects — branch names, what commits and pushes target, when not to push, commit message form. Use before any commit, branch or push in a platform project.
---

# Git on the platform

- Branches `dev`, `cert`, `main` map to DEV, CERT, PROD (D7). `deploy/target.yml` is authoritative for the project.
- Feature work happens on a branch off `dev`; promotion is dev → cert → main, by merge, never by force-push.
- Commit only when asked. Never push `main` unless asked. Never rewrite published history.
- Commit message: one line under 72 characters saying what changed and why; a body only if the why needs it. Reference the story or requirement ID when there is one.
- Never commit `.env`, credentials, or generated artefacts; `.gitignore` in the template already covers them.
- Commits and pushes are not deployments. Deployment is `dev deploy <env>` (increment 2).

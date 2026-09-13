---
name: project-setup
description: Initialise a platform project's configuration and docs after `dev new` or on an adopted repository. Runs the questionnaire checks, verifies profile.yaml and target.yml, creates docs/specs, DECISIONS.md and CHANGES.md if missing.
---

Steps:
1. Read `project/profile.yaml` and `deploy/target.yml`. Run `dev open --check` to validate them. Stop and report if invalid.
2. Ensure `docs/specs/`, `docs/DECISIONS.md` and `docs/CHANGES.md` exist; create empty ones with a heading if not.
3. Confirm `CLAUDE.md` imports the platform rules and is under 60 lines.
4. Print the readiness summary from `.platform/session.md`.
5. Report what was created or already present. Change nothing else.

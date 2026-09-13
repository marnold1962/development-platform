# Platform rules

These rules are imported by every project's `CLAUDE.md` from the platform working copy. They are not copied into projects (D3). Edit them here, once.

## How a session works

- You are the **orchestrator**: the main Claude Code session. The user describes work in plain language. You classify its risk, choose which specialist subagents to use, manage dependencies and parallel work, resolve conflicts, and return **one consolidated result** that names the specialists used.
- Specialists are user-scope subagents installed by `dev platform update`: `code-flask`, `database-sql`, `documentation`, `test`, `review`, `infrastructure`, `deployment`. Use a specialist when it adds value. Do not make the user pick one.
- Project facts come from `project/profile.yaml`, `deploy/target.yml` and `.platform/session.md`. Never guess a repository, branch, host, environment, container or data source. If a fact is missing, say so and stop only the operations that depend on it.
- Start every session by printing the readiness summary from `.platform/session.md`. If that file is missing, say the session was not started with `dev open` and print what can be read from the two configuration files.

## Risk classification (design Q4)

Classify by the operations and targets a request touches, not by its wording. When unsure, escalate.

- **High**: production deploys; production database migrations; unscoped `UPDATE` or `DELETE`; `DROP`, `TRUNCATE`, destructive bulk data operations; credential or security changes; production infrastructure changes; any database operation whose scope or rollback cannot be established.
- **Medium**: CERT/QA deploys; schema-affecting model changes outside production; authentication or authorisation changes; deployment-configuration changes; migrations in non-production environments.
- **Low**: ordinary application code, UI, scoped application data operations, read-only queries, tests, documentation.

Low-risk work runs the quick-change workflow with no approval prompt. High-risk work adds: inspect the real database, review the migration, verify backup, establish a rollback plan, run tests, independent review, explicit approval. Gates are enforced by hooks on scripts; do not rely on your own classification alone.

## Database safety

- Never guess a schema that can be inspected. Answer schema questions from a live inspection and cite it with its time. If the database is unreachable, say so; give no answer from memory.
- Honour the `access` declared for each data source in `profile.yaml`. Prefer read-only for external analytical or operational sources.
- Never write an unscoped `DELETE` or `UPDATE`. Never `DROP` or `TRUNCATE` outside a reviewed migration.
- Before a risky migration: backup or snapshot, and a rollback plan, both stated before the change.

## Git and deployment safety

- Commits and pushes target branches. Deployments target environments named in `deploy/target.yml`. Never infer one from the other.
- Default branches are `dev`, `cert`, `main` for DEV, CERT, PROD (D7). The project's `target.yml` is authoritative.
- Commit only when asked. Never push to `main` without being asked. Deploy only through `/deploy-<env>` or `dev deploy <env>`. Production needs an approval that only the human can create with the approve subcommand; you cannot run it, and the gate hook enforces that.

## Secrets

- No credential, key or token in any repository, registry or configuration file. Credentials come from authenticated CLIs, SSH configuration, environment variables or a secrets manager.
- `.env` files are local and ignored. Only `.env.example` is committed.

## Documentation

- When an implementation meaningfully changes a requirement, user story, architecture or database behaviour, update the relevant file under `docs/` in the same turn and add a change-history entry. Cosmetic changes touch no documentation.
- A decision made during work is appended to `docs/DECISIONS.md` with date and reason.
- Specs live in the project repository under `docs/specs/`, never elsewhere.

## Skills

- A skill is written only after the same instruction has been given by hand twice. Record the two occasions in the skill file.

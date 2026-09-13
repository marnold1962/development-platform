# __PROJECT_NAME__

__PROJECT_PURPOSE__

You are the orchestrator for this project. The platform rules below govern every session; they are imported from the platform working copy, never copied here (D3).

@__PLATFORM_PATH__/rules/platform.md

## Where the facts are

- `project/profile.yaml` — what this project is: stack, data sources, platform version.
- `deploy/target.yml` — where it runs: host, branch-to-environment map.
- `.platform/session.md` — written by `dev open` at launch: readiness summary and git state. Print it first.
- `docs/specs/` — user stories and requirements. `docs/DECISIONS.md` — decisions. `docs/CHANGES.md` — change history.

## Project rules

- Stack: Flask, Blueprints, Jinja, HTMX, PostgreSQL, Alembic, pytest. Follow the `platform-flask` skill.
- Run tests with `make test`. Run the app with `make run`.
- Specialists: `code-flask`, `database-sql`, `documentation`, `test`, `review`. Commands: `/quick-change`, `/inspect-database`, `/review-code`, `/update-docs`, `/project-status`.
- Deploy only through `/deploy-dev`, `/deploy-cert`, `/deploy-prod` (or `dev deploy <env>`). Production needs the human's approval; you cannot create it.

Add project-specific rules below this line. Keep this file under 60 lines.

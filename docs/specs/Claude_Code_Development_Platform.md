# Claude Code Development Platform — Consolidated Concept and Decisions

| | |
|---|---|
| **Status** | Concept, consolidated. Nothing built. D6, D7, D20 and Q5 DECIDED by Matt 2026-09-13; remaining PROPOSED items are the working assumption unless Matt objects. Nothing blocks increment 1. |
| **Date** | 2026-09-13 |
| **Supersedes** | `Master_Plan.docx`, `Project_Context.docx`, `Top_Level_Hierarchy.docx`, `What_We_Are_Creating.docx` (all in this folder, 2026-09-12/13) |
| **Next step** | Confirm the decisions in section 22 and the answers in section 23, then write user stories and requirements from this document. |
| **Scope** | **Fresh start.** Nothing Matt built before this document is reused: no existing templates, scripts, agents, skills, MCP tools or configuration files. Existing servers and accounts are infrastructure, not files, and may be hosting targets. (Matt, 2026-09-13) |
| **Review update** | Unified the user-facing CLI under `dev`; refined risk classification; added Session Bootstrap / Context Loading; changed A1 from an unmeasured 15-minute target to minimal manual intervention. Review fixes: old CLI names removed; slash command vs CLI subcommand relationship stated (D24); 13A now says the CLI verifies and Claude loads. |

---

## Summary

**What.** One private platform repository holds how we build: agents, skills, commands, rules, scripts, templates and registries. Each application is its own repository holding only what it is. A small deterministic `dev` CLI opens or creates a project and launches Claude Code with the context loaded. Claude works through one orchestrator and seven specialists. Secrets never enter Git. Ordinary work is fast; production and destructive database work hit gates that are enforced by hooks, not by judgement.

**Fresh start.** Nothing built before this document is reused. Earlier templates, scripts, agents and tools in `~/Work` are out of scope; section 19 lists them only so the new platform does not collide with them. Existing machines and accounts remain available as hosting targets.

**What is decided.** The ten principles in section 3, five decisions all four sources agree on (D9, D10, D13, D14, D15), and the agreed halves of D11 and D12.

**What needs Matt.** Twelve proposed decisions and nine proposed answers, none blocking. Four items decided 2026-09-13: D6, D7, D20, Q5. The five that shape everything else:

| | Proposal |
|---|---|
| D1 | Seven specialists plus an orchestrator. No separate Desktop agent yet. |
| D3 | Platform files are referenced from user scope, never copied into projects. |
| D6, D7 | **Decided.** First hosting target is AS2. Branches are `dev` / `cert` / `main`. |
| D22 | Build in three increments (Create, Deploy, Adopt), each usable on a real project, instead of seven phases. |
| Q5 | **Decided.** "QA" is the QA Operations environment and "Analytics" is the IN Analytics environment: two separate containers on AWS. Registry entries `qa-operations` and `in-analytics`; their databases are named when the registry is written. |

**What happens next.** Confirm or change sections 22 and 23. Then user stories and requirements are written from sections 13 to 17, 20 and 21.

---

## 1. Why this document exists

The four source documents describe one idea at four altitudes and repeat about half of their content. They also disagree on the agent set, the repository layout, whether platform files are copied into projects or referenced, and what gets built first. This document keeps everything they agree on, resolves each conflict with a proposed decision, and lists what none of them define.

Nothing here is a requirement yet. Sections 22 and 23 are the list of things to settle before user stories are written.

---

## 2. The idea in one paragraph

A reusable personal development platform that sits above Claude Code, GitHub, the workstation, databases, servers and containers. A small deterministic `dev` CLI bootstraps any Linux machine, creates or opens a project, and launches Claude Code with the right context already loaded. Claude works through one orchestrator that delegates to specialist agents. Reusable knowledge (how we build, deploy, inspect databases, stay safe) lives in one private platform repository. Each application stays its own repository holding only what is specific to it. Complexity lives underneath the platform, not in the daily workflow.

---

## 3. Design principles

All four documents agree on these.

1. **Two kinds of knowledge, kept separate.** The platform knows HOW we work. The project repository knows WHAT this application is.
2. **Claude Code is the intelligence.** The CLI is the ignition key: small, predictable, deterministic. It starts, locates, validates and executes repeatable operations. It never reasons.
3. **One orchestrator.** The user talks to one AI interface. It selects specialists, manages dependencies and returns one consolidated result.
4. **Five concepts stay distinct.** Agent = WHO. Skill = HOW. Command = WHAT workflow. Script = deterministic machine operation. Configuration = WHERE and against WHAT resources. Registry = the shared map of what exists.
5. **Nothing hard-coded.** Hosts, databases, branches, containers and environments are registry and configuration entries. Names like QA and Analytics are examples, not architecture.
6. **Secrets never in Git.** Not in the platform repo, not in project repos, not in registries. Credentials live in authenticated CLIs, SSH config, environment variables or a secrets manager.
7. **Fast when it can be, cautious when it must be.** Ordinary development is streamlined. Production and destructive database work trigger stronger gates automatically.
8. **Skills are promoted from use, not written up front.** The trigger is "I keep explaining this same thing to Claude."
9. **Existing projects are first-class.** Reopening a project is as important as creating one.
10. **Documentation is part of development.** Docs update when implementation meaningfully changes them, with minimal ceremony.

---

## 4. The six layers

| Layer | What it is | Where it lives |
|---|---|---|
| 1. Machine / Workstation | Whatever computer is in use. Provides tools, not intelligence. | Git, gh, Claude Code, Python, Docker, AWS CLI, SSH, DB clients, the dev CLI |
| 2. Master Development Platform | The reusable brain and rulebook. | Private GitHub repo `development-platform` |
| 3. Project / Application | The real applications, one repo each. | `qa-tracker`, `shipment-dashboard`, `development-planner`, `retail-dashboard`, future |
| 4. AI / Agent | Orchestrator plus specialists. | Claude Code |
| 5. Infrastructure / Data | The map of servers, databases, networking, GitHub. | Registries in the platform repo |
| 6. Deployment / Environment | LOCAL, DEV, CERT/QA, PROD and the branch-to-environment mapping. | Project configuration + deploy scripts |

```
YOU
 |
 v
dev CLI  ──>  MASTER DEVELOPMENT PLATFORM
                |            |            |
            Templates    Registries    AI rules / agents / skills
                |            |            |
                v            v            v
             PROJECT   Infrastructure   Claude Code -> Orchestrator -> Specialists
                |
                v
           APPLICATION  ──>  LOCAL -> DEV -> CERT/QA -> PROD
```

---

## 5. The master platform repository

One private GitHub repository. The four sources draw its layout three different ways. This is the unified tree (see decision D2).

```
development-platform/
  cli/              dev (Python): new, open, list, status, platform, deploy, health, db
  templates/
    flask-web/
    python-desktop/
    cpp-desktop/
  agents/           orchestrator + specialist agent definitions
  skills/           reusable HOW knowledge, grouped by domain
  commands/         workflow definitions (/project-setup, /deploy-cert, ...)
  rules/            global safety rules (database, git, production, secrets)
  scripts/
    setup/          setup-linux.sh, setup-python.sh
    database/       check-db.sh, backup-db.sh, inspect-schema.py
    deployment/     deploy, health-check.sh, rollback.sh
    infrastructure/ check-aws.sh, check-docker.sh, check-tunnel.sh
  questionnaires/   new-project questionnaire and answer schema
  registries/
    repositories.yaml     known repos and their roles
    environments.yaml     DEV / CERT / PROD definitions
    containers.yaml       server and container mappings
    databases.yaml        database registry with approved access modes
    tunnels.yaml          non-secret tunnel topology and conventions
  docs/             platform's own documentation and decisions
  CLAUDE.md
  README.md
```

The platform must be portable. A new machine retrieves this repo, authenticates, and regains the same development behaviour.

---

## 6. Application repositories

Each application is an independent Git repository, created from a template or connected by the CLI. It holds source, tests, migrations, project-specific configuration, project-specific documentation, and a small `CLAUDE.md` that points at the orchestrator and the project configuration.

Proposed standard layout (see decisions D3 and D16 for what is copied versus referenced, and for the docs folder). Configuration is two files, not six: the sources' `project/*.yaml` set is collapsed into `profile.yaml` and `deploy/target.yml`, both newly defined here (decision D23).

```
project-repository/
  CLAUDE.md               small: use the orchestrator, here is the config, here are the rules
  .claude/                project-specific agents/skills/commands only
  project/
    profile.yaml          name, purpose, type, stack, data sources by logical name,
                          platform_version; never credentials
  deploy/
    target.yml            kind (service|desktop), host, identity,
                          branch -> environment -> path
    deploy.sh             thin wrapper that calls the platform deploy script
  docs/
    specs/                user stories, requirements, tech specs
    DECISIONS.md
    (architecture, database, change-log added when needed)
  scripts/                project-specific wrappers only
  app/ or src/
  tests/
  migrations/             where applicable
  config/
  .env.example            committed; .env files ignored
  README.md
  pyproject.toml          Python projects
```

Templates:

| Template | Stack | Shape |
|---|---|---|
| Flask Web | Python, Flask, Blueprints, Jinja, HTMX, PostgreSQL, Alembic, pytest | app/blueprints, templates, static, services, repositories, models, migrations |
| Python Desktop | Python, Qt (see D20), PostgreSQL or SQLite, pytest | windows, widgets, dialogs, services, database, models, resources |
| C++ Desktop | C++, Qt6, CMake | src, include, resources, tests, CMake |

---

## 7. Agents

The unified set (decision D1). Seven specialists plus the orchestrator.

| Agent | Responsibility |
|---|---|
| **Orchestrator** | Understands the request, classifies risk, selects agents, manages dependencies and parallel work, resolves conflicts, returns one result. The user's normal interface. |
| **Code / Flask Agent** | Application logic, Flask factory, Blueprints, routes, services, templates, HTMX. Desktop (Qt) work is a skill set under this agent until a desktop template exists. |
| **Database / SQL Agent** | PostgreSQL, SQL Server, schema discovery, query writing and review, migrations, performance, data safety. Database variants are skills of this one agent, never separate agents. |
| **Infrastructure Agent** | AWS, EC2, RDS, Linux, Docker, SSH, networking, DNS, Cloudflare tunnels. Knows the generic technology; registries tell it which real resource applies. |
| **Deployment Agent** | Repository, branch, environment and container routing. Deploys, health-checks, rolls back. Never guesses a target. |
| **Documentation Agent** | User stories, bugs, enhancements, requirements, acceptance criteria, architecture, change history. |
| **Test Agent** | Targeted and regression testing proportionate to risk. |
| **Review Agent** | Independent verification of implementation, safety, requirements and test evidence. |

Example: "Add two fields to the purchase-order pane, pull them from SQL Server, update the grid, protect QA-owned values, deploy to CERT" involves Code, Database, Test, Documentation, Review and Deployment. The user never coordinates them by hand.

---

## 8. Skills

Start focused. Expand only when repeated work proves the need.

- Python, Flask, Blueprints, Jinja, HTMX, dashboard UI
- Qt desktop (Python and C++)
- PostgreSQL, SQL Server, schema discovery, query review, Alembic and migrations
- AWS EC2, RDS, S3, Linux server administration
- Docker and container management
- Cloudflare Tunnel, SSH, networking, DNS
- Git, GitHub, branching, repository safety
- DEV/CERT/PROD deployment, health checks, rollback
- pytest, debugging, logging
- User stories, bugs, requirements, acceptance criteria, architecture, change logs

Example file layout: `skills/database/schema-discovery.md`, `skills/database/query-review.md`, `skills/flask/blueprint-pattern.md`, `skills/deployment/docker-cert-deployment.md`.

---

## 9. Commands

Workflow instructions, not shell commands. Where a command has a CLI counterpart in section 13, the command is the orchestrated workflow and ends by calling the CLI subcommand (D24).

| Command | Purpose |
|---|---|
| `/project-setup` | Initialise a new project and run the questionnaire |
| `/project-reconfigure` | Change architecture or connections later |
| `/quick-change` | Several related day-to-day changes without ceremony |
| `/inspect-database` | Validate a connection and inspect the real schema |
| `/deploy-dev`, `/deploy-cert`, `/deploy-prod` | Controlled deployment workflows with escalating gates |
| `/review-code` | Independent review |
| `/update-docs` | Synchronise documentation with the implementation |
| `/project-status` | Repository, branch, environment, tests, outstanding work |

---

## 10. Scripts

Where repeatability and safety matter more than improvisation, Claude decides and a version-controlled script acts.

```
Claude reasoning -> "deploy CERT is needed" -> Deployment Agent -> deployment skill
  -> scripts/deployment/deploy cert -> machine operation
```

Scripts: database backup, deploy, health check, rollback, AWS validation, Docker validation, tunnel validation, schema inspection, Linux and Python setup. The deploy script is generic and reads `deploy/target.yml`. It never hard-codes a server or container.

---

## 11. Registries

The map of the development world, kept centrally so no project rediscovers it. Registries describe identity, topology, logical names, environment mappings and approved access patterns. They never contain passwords, keys or tokens.

Contents: known repositories and roles; DEV/CERT/PROD definitions; server and container mappings; databases with approved access mode (read-only preferred for external analytical or operational sources); SSH alias and tunnel conventions; AWS conventions.

A project references the resources it needs by logical name. The registry says what those names are.

---

## 12. Project configuration

Each project stores only its own configuration, so Claude can reopen it months later and immediately understand stack and routing. Two files:

| File | Holds | Status |
|---|---|---|
| `deploy/target.yml` | `kind` (service or desktop), `host`, `identity`, `environments` mapping branch to environment and path, optional `connects_to` for desktop tools that talk to a server | New |
| `project/profile.yaml` | Name, purpose, application type, stack, external data sources by logical registry name with access mode, `platform_version` | New |

Both may hold host aliases, logical names, container names and paths. Never credentials. The sources' separate `repositories.yaml`, `environments.yaml`, `databases.yaml`, `infrastructure.yaml` and `deployment.yaml` are not created. If `profile.yaml` outgrows one screen, split it then.

---

## 13. The CLI

The platform exposes one user-facing command: `dev`. Internally it may be implemented as separate Python modules, but the user should only need to remember one command.

| Command | Does |
|---|---|
| `dev new flask as2` | New Flask project on the named infrastructure target |
| `dev new desktop python` | New Python desktop project |
| `dev new desktop cpp` | New C++/Qt project |
| `dev open <project>` | Locate or clone, update platform if needed, load config, validate git and connections, launch Claude Code |
| `dev list` | Known local projects |
| `dev status` | Current project, branch, git state, configured environments, declared data sources and platform version |
| `dev platform update` | Update the local platform working copy |
| `dev db inspect <name>` | Validate and inspect a configured database through the platform's database workflow |
| `dev deploy <env>` | Run the controlled deployment workflow for DEV, CERT/QA or PROD |
| `dev health [env]` | Run configured health checks for the current project/environment |

The CLI is still small and deterministic. It locates, validates, reads configuration and invokes repeatable operations. Claude Code remains the intelligence.

Some operations have two front doors: a CLI subcommand (`dev deploy cert`) and a Claude command (`/deploy-cert`). They are not alternatives (decision D24). The slash command is the workflow: the orchestrator validates Git state, runs proportionate tests, updates docs, and ends by invoking the CLI subcommand. The CLI subcommand is the mechanism: it runs the script, and the risk gate hook sits on it. Running the subcommand by hand skips the workflow but never skips the gate. The same pairing applies to `/inspect-database` and `dev db inspect`, and to `/project-status` and `dev status`.

What `dev new` does, in order: check Linux prerequisites; verify Git and gh auth; verify Claude Code; optionally verify Docker and AWS CLI; clone or update the platform repo at a stable local path; select template; run the questionnaire; create or connect the GitHub repo; create the local working copy; install the project's `CLAUDE.md` and project-specific `.claude/` content; generate `project/profile.yaml` and `deploy/target.yml`; validate infrastructure and data connections; launch Claude Code.

What `dev open` does is at least as important as `dev new`: locate the project locally or clone it; enter adopt mode if it lacks platform configuration; validate the project configuration; compare the project's expected platform version to the installed platform; inspect Git state; resolve declared resources through registries; load project context; then launch Claude Code.

---

## 13A. Session bootstrap and context loading

`dev open <project>` is the handoff contract between the deterministic platform and Claude Code. Its purpose is to ensure Claude starts the session with the correct project, platform, Git, infrastructure and documentation context already available.

The startup sequence is:

```text
dev open <project>
        |
        v
Identify machine and platform path
        |
        v
Locate or clone project
        |
        v
Read project/profile.yaml
        |
        v
Read deploy/target.yml
        |
        v
Validate both files against schema
        |
        v
Verify platform rules, agents and skills are installed at ~/.claude
        |
        v
Verify project CLAUDE.md exists
        |
        v
Locate docs/specs and DECISIONS.md; pass their paths to Claude
        |
        v
Check Git repository, branch and working state
        |
        v
Resolve declared resources through registries
        |
        v
Validate required connections when appropriate
        |
        v
Launch Claude Code
```

The CLI does not load rules, agents, skills or documents into Claude. Claude Code loads agents and skills from `~/.claude/` and reads the project `CLAUDE.md` itself at launch (D3, D11). The CLI's part is to verify those files are present and valid, resolve the paths, and refuse to launch when something required is missing. Loading is Claude's; verification is the CLI's.

Claude should begin the session able to answer, without the user manually re-explaining the project:

- What project is open and what it does.
- What stack it uses.
- Which repository and branch are active.
- Which environments exist and how branches map to them.
- Which data sources are declared and what access mode is approved.
- Which hosting target and deployment path apply.
- Which platform rules and project-specific rules apply.
- Which specialists and skills are available.
- What documentation and decisions exist.
- Whether the working tree is clean and whether the project configuration is valid.

A successful startup should produce a short readiness summary, for example:

```text
PROJECT
QA Tracker

STACK
Flask / HTMX / PostgreSQL

REPOSITORY
qa-tracker

CURRENT BRANCH
develop

ENVIRONMENTS
DEV / CERT / PROD

DATA SOURCES
<registry name> (read-only)
<registry name> (read-write)

PLATFORM
rules loaded
7 specialists available
project context loaded

GIT
clean

READY
```

The readiness summary is informational. It must not invent missing configuration. Missing, invalid or ambiguous configuration should be reported explicitly and block only the operations that depend on it.

---

## 14. The questionnaire

Asks only what registries and templates cannot already answer. Its output is `project/profile.yaml` and `deploy/target.yml`.

1. Project name and short purpose
2. Application type: Flask web, Python desktop, C++/Qt, API, CLI, other
3. New or existing GitHub repository; visibility
4. Primary technology choices
5. Local application database, if any
6. External data sources (from the database registry) and required access level for each
7. Infrastructure target (from the registry) or local only
8. Required environments: local, DEV, CERT/QA, PROD
9. Branch strategy and promotion path
10. Docker required? Tunnels or SSH required?
11. Project-specific business or architecture constraints

---

## 15. Environments, Git and deployment routing

Git operations and deployments are separate concepts. Commits and pushes target repositories and branches. Deployments target environments, servers and containers. The mapping between them is configuration, never a guess.

```
feature branch -> LOCAL
dev branch     -> DEV       container <project>-dev
cert branch    -> CERT/QA   container <project>-cert
main           -> PROD      container <project>-prod
```

Branch names are examples (decision D7). Promotion path: DEV, then CERT/QA, then PROD.

---

## 16. Safety rules

**Database**
- Never guess a schema that can be inspected.
- Prefer read-only access to external analytical or operational sources.
- Never run an unscoped DELETE or UPDATE.
- Review migrations before risky changes.
- Require backup or snapshot and a rollback plan where data is at risk.

**DEV and CERT**
Streamlined: validate target, check Git state, run proportionate tests, deploy, health-check, inspect logs, report.

**Production**
Verify repository and exact commit. Verify branch and clean working tree. Tests and review proportionate to risk. Review migrations. Confirm backup where data is at risk. Establish rollback. Require explicit approval. Deploy only to the configured production target. Health-check and inspect logs afterwards.

**Secrets**
GitHub via gh. AWS via CLI profile or role. SSH via user config and keys. Database passwords and Cloudflare tokens via environment or secrets manager. `.env` local and ignored; only `.env.example` committed.

---

## 17. Workflow: quick change and risk

Ordinary work is one practical task. "Move these controls, change the SQL, add two fields, fix pagination" runs as a single quick-change workflow: make changes, targeted tests, review affected areas, update relevant docs, report.

Risk changes the workflow. The orchestrator classifies each request. High-risk work (production schema changes, destructive data operations, production deploys) automatically adds: inspect the real database, review migration, verify backup, rollback plan, tests, independent review, explicit approval. The criteria for classification are not yet defined (open question Q4).

---

## 18. Documentation and project memory

Each project accumulates structured knowledge so nothing is reverse-engineered twice: architecture, requirements, user stories, bugs, enhancements, database schema, decisions, change history, deployment history, known problems, business rules. The Documentation Agent updates these when implementation meaningfully changes them.

---

## 19. What exists in ~/Work and is not reused

This is a fresh start (Matt, 2026-09-13). Nothing below is a dependency, a starting point or a template for the platform. The list exists for one reason: so the new platform does not collide with it in names, paths, ports or Claude Code scope while both are present.

| Existing thing | Where | Collision to avoid |
|---|---|---|
| `new-project` script and `/new-project` skill | `~/.local/bin`, `~/.claude/skills/` | The new CLI is `dev`; do not name anything `new-project`. |
| Templates `python-flask`, `python-pyside6`, `cpp` | `~/Work/templates/` | Platform templates live inside the platform repo under different names. |
| `sql-reviewer` agent | `~/.claude/agents/` | Platform agents installed at user scope must not reuse this name; the Database/SQL Agent is written fresh. |
| `dev-manager` MCP, `/spec`, `/sql` skills | user scope | Platform skills and commands use distinct names. Whether these are removed later is a separate decision, not part of this platform. |
| AS2 deployment model: `as2-router`, worktrees under `/mnt/data/apps/`, control plane, `registry.yml` | AS2 | If AS2 is chosen as a hosting target (D6), the platform gets its own deploy root and its own path prefix on the router, or its own router. It does not write into `/mnt/data/apps/`. |
| Folder-based git identity (`~/Work/as2`, `~/Work/company`) | `~/.config/git/` | Machine configuration, not a project file. The platform repo must live under one of these folders to be committable (Q2). |
| Data dictionary | `~/Work/company/infra/reference/data/` | Reference material about databases, not platform code. The registry may cite it; it does not import it. |

---

## 20. Build order

The Master Plan's seven phases put the CLI in phase 5, so nothing is usable on a real project until four phases are done. Its own "first release" list then contradicts the phases. This document proposes a different shape (decision D22): three increments, each ending in something used on a real project the same week. Because this is a fresh start there is nothing to adopt yet, so Create comes first.

| Increment | Builds | Usable result |
|---|---|---|
| **1. Create** | Platform repo and tree. JSON schemas for `profile.yaml` and `target.yml`. `CLAUDE.md` standard and orchestrator instructions. Global rules. Flask template. Questionnaire. `dev new`, `dev open`. Code/Flask, Database/SQL, Documentation, Test and Review agents. Flask, PostgreSQL, Git, pytest and documentation skills. | `dev new flask <target>` creates a project end to end; `dev open` on it prints the readiness summary; a first quick change goes through the orchestrator. |
| **2. Deploy** | Registries. Infrastructure and Deployment agents. Deploy, health-check and rollback scripts. Risk gates as hooks. `dev deploy`, `dev health`, `dev status`, `dev list`, `dev platform update`. | The increment-1 project deploys to dev, cert and prod through the platform, and the production gate stops an unapproved deploy. |
| **3. Adopt** | `dev open` adopt mode: detect stack, prefill questionnaire, write `profile.yaml` and `target.yml`, minimal `CLAUDE.md`. | An application not created by the platform is brought under it without hand-editing configuration. |
| **Later** | Desktop templates and Qt skills. Skills promoted from repeated explanations. A second hosting target. | |

Rules for the sequence:
- Nothing is written that increment cannot use that week.
- No skill is written before it has been explained to Claude twice by hand.
- The first three increments target one hosting entry (D6).

Mapping to the Master Plan for traceability: its phases 1 and 2 are increment 1; phases 3, 4 and 5 are increment 2; phase 7's "existing projects" work is increment 3; phase 6 is "later".

---

## 21. Definition of success

A clean Linux machine reaches ready-to-code with minimal manual setup. After authenticating, one short command and a concise questionnaire produce a GitHub-backed project whose Claude Code orchestrator already understands the stack, data sources, hosting, tunnels, containers, branches, deployment path, documentation workflow and safety boundaries. Reopening an existing project is one command: `dev open <project>`. Routine development, review, documentation and deployment happen without rebuilding context by hand.

Acceptance criteria. Each is a test that either passes or fails; each is tied to the increment that delivers it.

| # | Criterion | Increment |
|---|---|---|
| A1 | On a fresh Omarchy or Ubuntu machine with only Git, gh and Claude Code authenticated, the bootstrap script installs the platform and `dev open` on a platform-created project succeeds with minimal manual intervention and no step done by hand other than entering credentials. A numeric time target is set only after the workflow has been measured on real machines. | 1 |
| A2 | `dev open <project>` on the first platform-created project launches Claude Code and prints the readiness summary of section 13A; when asked "where does this deploy and from which branches", the answer matches `deploy/target.yml` exactly, with no file read by the user. | 1 |
| A3 | Every registry file and every `profile.yaml` and `target.yml` validates against its schema in CI and in `dev open`; an invalid file stops the launch with the field named. | 1 |
| A4 | A schema question ("what columns does table X have") is answered from a live inspection, never from memory, and the Database Agent refuses an unscoped DELETE or UPDATE. | 1 |
| A5 | `dev new flask <target>` produces a repository that passes its tests, has `profile.yaml` and `target.yml`, has a `CLAUDE.md` under 60 lines, and is pushed as a private GitHub repo with the three configured branches. | 1 |
| A6 | A quick-change request touching a route, a template and a test is completed, tested and documented in one orchestrator turn without the user naming an agent. | 1 |
| A7 | `/deploy-cert` on the increment-1 project deploys, health-checks and reports, and `dev status` shows the deployed commit equal to the branch head. | 2 |
| A8 | `/deploy-prod` without an explicit approval in the session is stopped by the hook before the script runs, and the refusal names repo, commit, branch and target. | 2 |
| A9 | No file in the platform repo or any project repo contains a credential; a secret-scan in CI passes. | 1 to 3 |
| A10 | `dev list` on the laptop lists every project under `~/Work/as2` and `~/Work/company` that has a `profile.yaml`, and nothing else. | 2 |
| A11 | `dev open` on a repository the platform did not create offers adopt mode and, after the questionnaire, A2 passes on that repository. | 3 |

---

## 22. Decisions

**AGREED** means all four sources say the same thing. **PROPOSED** means the sources conflict or are silent and this is the recommended resolution, awaiting Matt's confirmation. Nothing PROPOSED is a requirement until confirmed.

| # | Decision | Status | Basis |
|---|---|---|---|
| D1 | **Agent set is seven plus orchestrator**: Code/Flask, Database/SQL, Infrastructure, Deployment, Documentation, Test, Review. No separate Code, Flask or Desktop agents. Desktop is a skill under Code/Flask until phase 6. Test Agent is in the first release. | PROPOSED | Master Plan §8 lists ten; every diagram in all four docs shows seven; the MVP list drops Test. Seven matches "prefer skills over agents". |
| D2 | **One repository tree** as in section 5. `bootstrap/` folds into `cli/`. `infrastructure/` and `registries/` merge as `registries/`. `documentation/` becomes `docs/`. `tunnels.yaml` is in the tree. | PROPOSED | Three different trees across the sources. |
| D3 | **Reference, do not copy.** The CLI installs platform agents, skills and commands at Claude Code user scope (`~/.claude/`) from the platform's stable local path. A project's `.claude/` holds only project-specific additions. Project `CLAUDE.md` names the platform version it expects. | PROPOSED | Master Plan §6 and §12.2 copy everything into each project; What We Are Creating §2 says the point is to avoid duplicated platform instructions. Copying makes platform updates unreachable (open question in all sources). Reference matches how Claude Code scopes agents and skills. |
| D4 | Withdrawn. Replaced by D22. | — | The seven-phase sequence itself was the problem, not just its first-release boundary. |
| D5 | **The `dev` CLI is written fresh.** It does not call or wrap the earlier `new-project` script or skill. | PROPOSED | Fresh start (Matt, 2026-09-13). Earlier proposal (extend `new-project`) withdrawn. |
| D6 | **Hosting target is a registry entry; the first entry is AS2** (home server, LAN and Cloudflare tunnel). The platform gets its own deploy root and routing on AS2 and does not write into paths owned by earlier tooling. AWS is a second entry, later. The sources' `devnew flask aws` becomes `dev new flask as2`. | DECIDED (Matt, 2026-09-13) | Sources say AWS throughout but treat the name as configuration. |
| D7 | **Branch names are configuration in `deploy/target.yml`; the platform default is `dev` / `cert` / `main`** mapped to DEV / CERT / PROD. | DECIDED (Matt, 2026-09-13) | The sources' own example. |
| D8 | **"Analytics" and "QA" are not architecture.** The database registry names databases; the infrastructure registry names hosts; neither uses these words as a root. The registry entries map to the two EC2 boxes and their databases as documented in `~/Work/company/infra/reference/`. | PROPOSED | Sources use "Analytics" to mean a database, a host and an AWS account in different places. Which real host each maps to needs Matt's confirmation. |
| D9 | **Secrets never in any repo or registry.** | AGREED | All four. |
| D10 | **CLI is small and deterministic; Claude Code is the intelligence.** | AGREED | All four. |
| D11 | **Orchestrator is the single user-facing AI interface.** Implemented as: project `CLAUDE.md` plus a user-scope orchestrator instruction; specialists as Claude Code subagents; skills as Claude Code skills; commands as slash-command skills; rules as `CLAUDE.md` sections and rule files; production and destructive-operation gates as hooks. | PROPOSED (mechanism) / AGREED (principle) | Sources agree on the principle and never say how it maps to Claude Code. |
| D12 | **One Database Agent; database variants are skills.** Written fresh; the earlier `sql-reviewer` agent is not reused or renamed. | AGREED (principle) | What We Are Creating §6 explicit. |
| D13 | **Registries never hold secrets; they hold identity, topology, logical names, mappings, access modes.** | AGREED | All four. |
| D14 | **Existing projects are first-class**: `dev open` must work on any repo the platform created. | AGREED | All four. Repos not created by the platform: open question Q6. |
| D15 | **Git and deployment are separate concepts; the mapping is configuration; the Deployment Agent never guesses.** | AGREED | All four. |
| D16 | **Project docs are `docs/specs/` for user stories and requirements and `docs/DECISIONS.md` for decisions.** The Master Plan's larger docs tree (architecture, bugs, enhancements, change-log) is added per project only when needed. | PROPOSED | A layout convention, not a reused file. The Master Plan §6 tree is eight folders on day one. |
| D17 | **Platform documents are Markdown in the platform repo**, not Word files. | PROPOSED | The sources were `.docx`, which no tooling reads; they were deleted 2026-09-13 and this file is the only source. |
| D18 | **Platform repo is `development-platform`, private, under `~/Work/as2/`** so it has a git identity. | PROPOSED | Sources say "for example development-platform". Only `~/Work/as2` and `~/Work/company` can commit. |
| D19 | **Templates are written fresh inside the platform repo.** The earlier `~/Work/templates/` are not copied or referenced. | PROPOSED | Fresh start. Earlier proposal (reuse existing templates) withdrawn. |
| D20 | **Python desktop uses PyQt6.** GPL for private use; a commercial licence only if a closed tool is ever distributed. | DECIDED (Matt, 2026-09-13) | As the sources say. |
| D21 | **Production approval is an explicit interactive confirmation inside the session** that names repo, commit, branch, environment and target, enforced by a hook on the deploy script, not by the agent's judgement alone. | PROPOSED | Sources require "explicit approval" without defining it. |
| D22 | **Build in three increments (Create, Deploy, Adopt), each used on a real project the week it lands**, as in section 20. The Master Plan's seven phases are kept only as a traceability map. | PROPOSED | The phases put the CLI fifth, so nothing was usable until most of the platform existed. Create first because, under a fresh start, there is nothing to adopt yet. |
| D23 | **Project configuration is two files**: `deploy/target.yml` (kind, host, identity, branch-to-environment) and `project/profile.yaml` (identity, stack, data sources, platform version). Both defined fresh by schema. The sources' five `project/*.yaml` files are not created. | PROPOSED | Five files for a one-person platform is ceremony. Two files with schemas cover every field the sources list. |
| D24 | **Slash commands are workflows; CLI subcommands are mechanisms.** `/deploy-cert` orchestrates and ends by calling `dev deploy cert`; the risk gate hook is on the subcommand, so it holds whichever door is used. | PROPOSED | Section 13's `dev deploy`, `dev db inspect`, `dev health` and `dev status` overlapped section 9's commands with no stated relationship. |

---

## 23. Open questions and proposed answers

None of the sources answer these. Each has a proposed answer (2026-09-13), awaiting Matt's confirmation like the PROPOSED decisions above. Q5 was answered by Matt on 2026-09-13.

| # | Question | Blocks | Proposed answer |
|---|---|---|---|
| Q1 | The YAML schema for each registry file and each project configuration file. The questionnaire generates them, so the schema comes first. | Increment 1, CLI | Write JSON Schema files in `registries/schema/` first and have the CLI validate every registry and project file against them. Project configuration is `deploy/target.yml` plus `project/profile.yaml`, per D23. Split into more files only when they grow. |
| Q2 | The "stable local path" for the platform working copy, and where `dev list` gets its list. | CLI | Platform at `~/Work/as2/development-platform`: git identity on this machine is folder-based and only `~/Work/as2` and `~/Work/company` can commit. `dev list` scans those two folders for `project/profile.yaml`. No separate laptop registry file, so nothing can drift. |
| Q3 | How a platform update reaches projects already created. | Increment 1 | D3 removes the copy problem. Add `platform_version` to `profile.yaml`. `dev open` compares it to the platform's git tag, warns in one line if behind, never auto-migrates. Version by git tag, not a changelog file. |
| Q4 | Risk classification criteria. | Orchestrator, hooks | Classify by the operation and target, not only by wording in the request. **High:** production deploys; production database migrations; unscoped `UPDATE` or `DELETE`; `DROP`, `TRUNCATE`, destructive bulk data operations; credential/security changes; production infrastructure changes; any database operation where rollback or scope cannot be established. **Medium:** CERT/QA deploys; schema-affecting model changes outside production; authentication/authorization changes; deployment-configuration changes; migrations in non-production environments. **Low:** ordinary application code, UI, scoped application data operations, read-only queries, tests and documentation. The orchestrator escalates when unsure. High-risk gates are enforced by hooks/scripts so they still hold if the agent misclassifies. |
| Q5 | Which real hosts and databases "Analytics" and "QA" mean (D8). | Registries | **Answered by Matt, 2026-09-13.** There are two main development environments on AWS, running as separate containers: **QA Operations** and **IN Analytics**. "QA" means the first, "Analytics" the second. The registry gets two environment entries, `qa-operations` and `in-analytics`, each naming its container and host. The databases each one uses are named when the registry is written in increment 2, by inspection, not from memory. |
| Q6 | Adopting a repository the platform did not create. | CLI, increment 3 | Yes, as increment 3. `dev open` on a repo without `project/profile.yaml` offers adopt mode: detect the stack from files present, prefill the questionnaire, write `profile.yaml`, `target.yml` and a minimal `CLAUDE.md`, commit on a branch for review. |
| Q7 | MacBook, Azure and on-premises appear once each. In scope? | Bootstrap scripts | Out of scope for the first release. Record as a non-goal so the bootstrap script does not try to be portable to them. A Linux laptop and one hosting target are the whole world for now. |
| Q8 | Whether a second hosting target gets the same deploy model as the first. | Later | Decide when the first target works. The deploy script reads `target.yml`; a second target is a second registry entry and, if needed, a second script backend. |
| Q9 | Does the orchestrator run as the main session or as a subagent? | D11 | Main session. Its instructions are the project `CLAUDE.md` plus an imported platform rules file. Specialists are user-scope subagents. A subagent cannot ask the user mid-task, so an orchestrator subagent would have to guess at approvals, which conflicts with the production gate. |
| Q10 | Are review, deployment pre-flight and context loading separate hooks or parts of the agents? | D1, D21 | Parts of the agents, with hooks as enforcement: the Review Agent owns requirements checking; the Deployment Agent owns pre-flight and a PreToolUse hook on the deploy script enforces the gate; `dev open` owns context loading (13A). One list, not two. |

---

## 24. Sources

All in `~/Work/ai_dev/`, written 2026-09-12 and 2026-09-13.

| File | Role in the set | Kept |
|---|---|---|
| `Claude_Code_Development_Platform_Top_Level_Hierarchy.docx` | Six-layer mental model | Section 4 |
| `Claude_Code_Development_Platform_What_We_Are_Creating.docx` | Operating model, two kinds of knowledge, risk, memory | Sections 3, 7, 8, 10, 11, 17, 18 |
| `Claude_Code_Development_Platform_Project_Context.docx` | Briefing for Claude Code, first-release scope | Sections 3, 16, 20 |
| `Claude_Code_Development_Platform_Master_Plan.docx` | The only detailed one: trees, commands, CLI steps, phases | Sections 5, 6, 9, 10, 13, 14, 16, 20 |

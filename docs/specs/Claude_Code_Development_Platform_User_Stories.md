# Claude Code Development Platform — User Stories

| | |
|---|---|
| **Status** | Draft for review. Derived from `Claude_Code_Development_Platform.md` (2026-09-13). |
| **Date** | 2026-09-13 |
| **Scope** | Fresh start. No earlier tooling is reused (D5, D19, D12). |
| **Blocked stories** | None. D6, D7, D20 and Q5 were decided by Matt on 2026-09-13; the affected stories now state the decision. |
| **Companion** | `Claude_Code_Development_Platform_Requirements.md` |

---

## How to read this

One persona: **Matt**, who owns the platform and is its only user. Where the platform itself must behave a certain way regardless of who asks, the story is written from the platform's point of view and marked **System**.

Each story has:
- **ID** `US-nn`, stable across revisions.
- **Story** in the form "As Matt, I want … so that …".
- **Acceptance** as Given / When / Then. Each is a test that passes or fails.
- **Increment** from section 20 of the design: 1 Create, 2 Deploy, 3 Adopt, L Later.
- **Traces to** the design section, decision or acceptance criterion it comes from.
- **Needs**, where a confirmed decision is required first.

Stories are grouped into epics. The epics follow the increments so that a finished epic is a usable platform.

---

## Epic 1. Platform foundation (Increment 1)

### US-01 Platform repository exists and is the source of truth
**Story.** As Matt, I want one private GitHub repository named `development-platform` holding every reusable part of the platform, so that a new machine can pull one thing and regain the same development behaviour.

**Acceptance.**
- Given a clean clone of `development-platform`, when I list the tree, then it contains exactly the top-level folders in design section 5: `cli/`, `templates/`, `agents/`, `skills/`, `commands/`, `rules/`, `scripts/`, `questionnaires/`, `registries/`, `docs/`, plus `CLAUDE.md` and `README.md`.
- Given the repository, when a secret scan runs in CI, then it reports zero findings (A9).
- Given the repository lives under `~/Work/as2/`, when I commit, then git signs with the folder identity without prompting.

**Increment** 1. **Traces to** sections 5, 16; D2, D9, D18; Q2.

### US-02 Configuration schemas exist before anything reads configuration
**Story.** As Matt, I want JSON Schema definitions for every registry file and both project configuration files, so that the CLI and CI can reject a bad file with the field named instead of failing later in a confusing way.

**Acceptance.**
- Given `registries/schema/`, when I list it, then there is one schema for each registry file in section 5 and one each for `project/profile.yaml` and `deploy/target.yml`.
- Given a `profile.yaml` missing a required field, when `dev open` runs, then it exits non-zero and prints the file path and field name, and Claude Code is not launched (A3).
- Given all registry and project files in the repository, when CI runs, then every file validates.

**Increment** 1. **Traces to** section 12; D23; Q1; A3.

### US-03 Project configuration is two files
**Story.** As Matt, I want a project's configuration to be `project/profile.yaml` and `deploy/target.yml` and nothing else, so that I can read a project's whole identity in under a minute.

**Acceptance.**
- Given a platform-created project, when I look for configuration, then `profile.yaml` holds name, purpose, application type, stack, data sources by logical registry name with access mode, and `platform_version`.
- Given the same project, then `target.yml` holds `kind` (service or desktop), `host`, `identity`, `environments` mapping branch to environment and path, and optional `connects_to`.
- Given either file, when I search it for a password, key or token, then there is none (A9).

**Increment** 1. **Traces to** sections 6, 12; D23, D7. Default branches in `target.yml` are `dev`, `cert`, `main`.

### US-04 Every project has a small CLAUDE.md that points at the platform
**Story.** As Matt, I want each project's `CLAUDE.md` to be short and to tell Claude to work through the orchestrator, where the configuration is, and which rules apply, so that project instructions never drift into a copy of the platform.

**Acceptance.**
- Given a platform-created project, when I count lines in `CLAUDE.md`, then there are fewer than 60 (A5).
- Given that file, then it names the orchestrator, the two configuration files, the platform version expected, and the location of `docs/specs/` and `docs/DECISIONS.md`.
- Given that file, then it contains no agent or skill definitions; those live at user scope (D3).

**Increment** 1. **Traces to** sections 6, 7; D3, D11, D16.

### US-05 Platform agents and skills are installed at user scope, not copied
**Story.** As Matt, I want the CLI to install the platform's agents, skills and commands into `~/.claude/` from the platform working copy, so that every project sees the same versions and a platform update reaches all projects at once.

**Acceptance.**
- Given `dev platform update` has run, when I list `~/.claude/agents/` and `~/.claude/skills/`, then every platform agent and skill is present and matches the platform working copy.
- Given a project's `.claude/` folder, then it contains only project-specific additions and no platform files.
- Given a platform agent name, then it does not collide with any earlier agent already at user scope (section 19).

**Increment** 1. **Traces to** section 19; D3; Q3.

### US-06 Platform version is visible and mismatches are reported
**Story.** As Matt, I want each project to record the platform version it expects, and `dev open` to warn when the installed platform is behind or ahead, so that I know why behaviour changed.

**Acceptance.**
- Given `profile.yaml` with `platform_version: 1.2.0` and an installed platform tagged `1.3.0`, when `dev open` runs, then it prints one warning line naming both versions and continues.
- Given matching versions, then no warning is printed.
- Given any mismatch, then nothing is auto-migrated and no file is edited.

**Increment** 1. **Traces to** Q3; D3.

---

## Epic 2. Creating a project (Increment 1)

### US-07 Create a Flask project with one command
**Story.** As Matt, I want to type `dev new flask <target>` and answer a short questionnaire, so that I get a GitHub-backed, correctly configured project without assembling anything by hand.

**Acceptance.**
- Given prerequisites are met, when I run `dev new flask <target>` and answer the questionnaire, then a local working copy exists, a private GitHub repository exists, the three configured branches exist, and both configuration files validate (A5).
- Given the new project, when I run its tests, then they pass (A5).
- Given the new project, then Claude Code is launched in it and prints the readiness summary (US-12).

**Increment** 1. **Traces to** sections 13, 14, 21; A5; D6. The first valid `<target>` is `as2`.

### US-08 The questionnaire asks only what registries cannot answer
**Story.** As Matt, I want the new-project questionnaire to be short and to skip anything the registries or the template already know, so that starting a project takes minutes, not an interview.

**Acceptance.**
- Given the questionnaire, then it asks at most the eleven items in design section 14 and no others.
- Given a registry that defines exactly one hosting target, when the questionnaire reaches "infrastructure target", then it offers that target as the default rather than asking free text.
- Given my answers, when the questionnaire completes, then `profile.yaml` and `target.yml` are generated and validate (US-02).

**Increment** 1. **Traces to** section 14; D23.

### US-09 Prerequisites are checked before anything is created
**Story.** As Matt, I want `dev new` to check Linux, Git, gh authentication and Claude Code before it does anything, so that a failure happens before a half-made repository exists.

**Acceptance.**
- Given `gh` is not authenticated, when I run `dev new`, then it stops before the questionnaire, names the missing prerequisite, and creates nothing.
- Given Docker or the AWS CLI is requested by the template but absent, then the same behaviour applies for that tool.
- Given all prerequisites are present, then the check adds no prompts.

**Increment** 1. **Traces to** section 13.

### US-10 A Flask template is part of the platform
**Story.** As Matt, I want a Flask web template inside the platform repository, written fresh, so that every Flask project starts from the same shape.

**Acceptance.**
- Given `templates/flask-web/`, then it has the structure in design section 6: application factory, blueprints, templates, static, services, repositories, models, migrations, tests, `pyproject.toml`, `.env.example`, `deploy/target.yml` and a thin `deploy/deploy.sh`.
- Given a project created from it, when I run its tests before any change, then they pass.
- Given the template, then it references no file outside the platform repository (D19).

**Increment** 1. **Traces to** section 6; D19.

### US-11 New projects get git identity and branches without manual git work
**Story.** As Matt, I want `dev new` to create the working copy under the correct identity folder and create the configured branches, so that the first commit signs correctly and the promotion path exists from day one.

**Acceptance.**
- Given `identity: as2` in `target.yml`, when the project is created, then its folder is under `~/Work/as2/` and the first commit is signed by that folder's identity.
- Given `target.yml` environments, then each named branch exists locally and on GitHub.
- Given a mismatch between the identity answer and the folder, then `dev new` refuses and explains.

**Increment** 1. **Traces to** section 19 (git identity), D7, D18.

---

## Epic 3. Opening a project and starting a session (Increment 1)

### US-12 Open a project and see a readiness summary
**Story.** As Matt, I want `dev open <project>` to launch Claude Code with the project's context loaded and to print a readiness summary, so that I never re-explain a project at the start of a session.

**Acceptance.**
- Given a platform-created project, when I run `dev open <project>`, then Claude Code starts and the first output is the readiness summary in design section 13A: project, stack, repository, current branch, environments, data sources with access mode, platform state, git state, READY.
- Given that session, when I ask "where does this deploy and from which branches", then the answer matches `deploy/target.yml` exactly and I open no file (A2).
- Given a required item is missing (for example no `target.yml`), then the summary reports it explicitly and does not invent it.

**Increment** 1. **Traces to** section 13A; A2; D11.

### US-13 The CLI verifies; Claude loads
**Story (System).** The CLI must verify that platform rules, agents, skills, the project `CLAUDE.md` and the docs folders exist and are valid, and pass their paths to Claude, but must not itself load any of them into the session.

**Acceptance.**
- Given a platform agent file is missing from `~/.claude/agents/`, when `dev open` runs, then it refuses to launch and names the file.
- Given all files present, then `dev open` passes the project path and docs paths to Claude Code and exits its own checks in one pass with no interactive prompts.
- Given the session starts, then agents and skills are the ones Claude Code loaded from `~/.claude/`, not a copy injected by the CLI.

**Increment** 1. **Traces to** section 13A; D3, D11.

### US-14 Git state is part of readiness
**Story.** As Matt, I want the readiness summary to tell me the branch, whether the working tree is clean, and whether the branch is one of the configured environment branches, so that I do not start work on the wrong branch.

**Acceptance.**
- Given uncommitted changes, when `dev open` runs, then GIT shows "dirty" with a count of changed files.
- Given the current branch is not in `target.yml`, then the summary says so and names the configured branches.
- Given a clean tree on a configured branch, then GIT shows "clean".

**Increment** 1. **Traces to** section 13A.

### US-15 `dev status` answers "where am I" without launching Claude
**Story.** As Matt, I want `dev status` to print the current project, branch, git state, configured environments, declared data sources and platform version, so that I can check a project from a terminal in one command.

**Acceptance.**
- Given I am inside a platform project, when I run `dev status`, then it prints the same fields as the readiness summary minus the Claude-specific lines, and exits zero.
- Given I am not inside a platform project, then it says so and exits non-zero.

**Increment** 2. **Traces to** section 13; D24.

---

## Epic 4. Working through the orchestrator (Increment 1)

### US-16 One conversation, one orchestrator
**Story.** As Matt, I want to describe work in plain language to one orchestrator and receive one consolidated result, so that I never choose or coordinate specialist agents myself.

**Acceptance.**
- Given a request that touches a route, a template and a test, when I make it in one message, then the change is made, the affected tests run, the relevant docs are updated, and I get one report, with no agent named by me (A6).
- Given the same request, then the report states which specialists were used.
- Given a conflict between two specialists' outputs, then the orchestrator resolves it or asks me one question; it never returns two answers.

**Increment** 1. **Traces to** sections 7, 17; D1, D11; A6.

### US-17 Seven specialists exist and stay distinct
**Story (System).** The platform provides exactly these specialist agents at user scope: Code/Flask, Database/SQL, Infrastructure, Deployment, Documentation, Test, Review. Database variants are skills of the Database/SQL Agent, not further agents.

**Acceptance.**
- Given `~/.claude/agents/` after `dev platform update`, then those seven and no other platform agents are present.
- Given a PostgreSQL and a SQL Server task, then both are handled by the Database/SQL Agent using different skills.
- Given a desktop task before increment L, then it is handled by Code/Flask using a Qt skill, not a Desktop agent.

**Increment** 1 (Code/Flask, Database/SQL, Documentation, Test, Review), 2 (Infrastructure, Deployment). **Traces to** section 7; D1, D12.

### US-18 The quick-change workflow stays light
**Story.** As Matt, I want several small related changes to be handled as one task with proportionate testing and documentation, so that ordinary development is not slowed by process.

**Acceptance.**
- Given a low-risk request (section 17 classification), when `/quick-change` runs, then no approval prompt appears and no deployment is attempted.
- Given the same request, then only tests touching the changed areas run, and the report lists them.
- Given the change affects a user story or requirement, then the Documentation Agent updates the relevant file in `docs/` in the same turn.

**Increment** 1. **Traces to** sections 9, 17, 18; Q4.

### US-19 Schema is inspected, never guessed
**Story.** As Matt, I want any question about a database schema to be answered from a live inspection through the platform's database workflow, so that I never act on a remembered or invented column.

**Acceptance.**
- Given a question "what columns does table X have", when the Database/SQL Agent answers, then the answer cites the inspection it ran and its timestamp (A4).
- Given the database is unreachable, then the agent says so and gives no answer from memory.
- Given `/inspect-database` or `dev db inspect <name>`, then the connection is validated and the real schema is shown.

**Increment** 1. **Traces to** sections 9, 16; A4; D24.

### US-20 Documentation is kept in step with code
**Story.** As Matt, I want the Documentation Agent to update user stories, requirements, decisions and change history when an implementation meaningfully changes them, so that a project explains not just what exists but why.

**Acceptance.**
- Given a change that alters a documented requirement, when the task completes, then the requirement file shows the change and the change history has an entry.
- Given a cosmetic change, then no documentation is touched.
- Given a decision made during the work, then `docs/DECISIONS.md` gains an entry with date and reason.

**Increment** 1. **Traces to** sections 18; D16.

### US-21 Skills grow from use, not up front
**Story.** As Matt, I want a rule that a skill is written only after the same instruction has been given to Claude by hand twice, so that the skill library stays small and true.

**Acceptance.**
- Given the platform at the end of increment 1, then the skills present are only those in design section 8 marked for increment 1.
- Given a candidate skill, then its file records the two occasions that justified it.

**Increment** 1 onward. **Traces to** section 8; principle 8.

---

## Epic 5. Deploying with gates (Increment 2)

### US-22 Registries describe the world without secrets
**Story.** As Matt, I want registries for repositories, environments, containers, databases and tunnels, so that projects reference resources by logical name and nothing is rediscovered or hard-coded.

**Acceptance.**
- Given `registries/`, then each of the five files exists and validates against its schema (US-02).
- Given any registry file, when scanned for credentials, then none are found (A9).
- Given a project declaring a data source by logical name, when `dev open` runs, then the name resolves to a registry entry or the summary reports it as unresolved.

**Increment** 2. **Traces to** section 11; D8, D13; Q5. The first application-environment entries are `qa-operations` and `in-analytics`, two separate containers on AWS; their databases are filled in by inspection in increment 2.

### US-23 Deploy to DEV and CERT with a streamlined workflow
**Story.** As Matt, I want `/deploy-dev` and `/deploy-cert` to validate the target, check git state, run proportionate tests, deploy, health-check, inspect logs and report, so that routine promotion is one command.

**Acceptance.**
- Given a clean tree on the configured cert branch, when `/deploy-cert` runs, then the deployment completes, the health check passes, and `dev status` shows the deployed commit equal to the branch head (A7).
- Given a dirty tree, then the workflow stops before deploying and says why.
- Given the workflow, then its final step is a call to `dev deploy cert` (D24).

**Increment** 2. **Traces to** sections 9, 15, 16; D24; A7; D6. Target is AS2.

### US-24 Production deploy requires explicit approval enforced by a hook
**Story.** As Matt, I want `/deploy-prod` to be stopped by a hook unless I have given explicit approval in the session that names repo, commit, branch, environment and target, so that no production deploy happens on an agent's judgement alone.

**Acceptance.**
- Given no approval in the session, when `/deploy-prod` or `dev deploy prod` runs, then the hook blocks the script before it executes and the refusal names repo, commit, branch and target (A8).
- Given I approve with all five items named, then the deploy proceeds and the approval is written to the deployment history.
- Given approval for one commit, when the branch head changes, then the approval no longer applies.

**Increment** 2. **Traces to** section 16; D21, D24; A8.

### US-25 Production deploy verifies everything it can before acting
**Story (System).** Before a production deploy, the Deployment Agent must verify repository and exact commit, branch and clean working tree, test and review evidence proportionate to risk, migration review, backup where data is at risk, and a rollback procedure.

**Acceptance.**
- Given any of those checks fails, then the deploy does not start and the report lists which check failed.
- Given all pass, then the report shows each check and its evidence before asking for approval (US-24).
- Given the deploy completes, then health checks run and logs are inspected, and the result is reported.

**Increment** 2. **Traces to** section 16.

### US-26 Rollback exists before it is needed
**Story.** As Matt, I want a rollback script that returns an environment to its previous deployed commit, so that a bad deploy is undone in one command.

**Acceptance.**
- Given an environment with two recorded deployments, when `dev rollback <env>` runs, then the previous commit is deployed and the health check passes.
- Given only one deployment recorded, then rollback refuses and says why.

**Increment** 2. **Traces to** sections 10, 16.

### US-27 Risk is classified by what is touched
**Story (System).** The orchestrator must classify every request as low, medium or high risk by the operations and targets involved, using the tiers in the design's Q4, and escalate when unsure. High-risk gates are enforced by hooks so they hold even if classification is wrong.

**Acceptance.**
- Given a request to change a production migration, then it is classified high and the high-risk steps (inspect, review migration, backup, rollback plan, tests, review, approval) are applied.
- Given a request to change a template and a test, then it is classified low and no gate appears.
- Given a high-risk operation reached by any path, then the hook fires regardless of classification.

**Increment** 2. **Traces to** section 17; Q4; D21.

### US-28 Destructive database operations are refused
**Story (System).** The Database/SQL Agent must refuse an unscoped DELETE or UPDATE, and any DROP or TRUNCATE outside an approved migration, on every database.

**Acceptance.**
- Given a request that would produce `DELETE FROM t` with no WHERE, then the agent refuses and explains (A4).
- Given a scoped DELETE against a non-production database, then it proceeds with the scope shown.
- Given a DROP inside an approved migration under US-25, then it proceeds.

**Increment** 1 (refusal), 2 (migration path). **Traces to** section 16; A4.

### US-29 `dev list` shows every platform project and nothing else
**Story.** As Matt, I want `dev list` to scan my two identity folders for projects with `profile.yaml`, so that the list is always derived from disk and can never drift.

**Acceptance.**
- Given projects under `~/Work/as2/` and `~/Work/company/` with `profile.yaml`, when I run `dev list`, then all are listed with name, kind and host, and nothing without `profile.yaml` appears (A10).
- Given a folder with an invalid `profile.yaml`, then it is listed with an "invalid" marker.

**Increment** 2. **Traces to** section 13; Q2; A10.

### US-30 Infrastructure is validated through scripts
**Story.** As Matt, I want `dev health [env]` and the check scripts for Docker, tunnels and cloud identity to tell me whether the pieces a project depends on are reachable, so that a failed deploy is not the first sign of a broken tunnel.

**Acceptance.**
- Given a tunnel declared in `target.yml` is down, when `dev health` runs, then it reports the tunnel as unreachable and exits non-zero.
- Given all dependencies up, then it exits zero with one line per check.

**Increment** 2. **Traces to** sections 10, 13.

---

## Epic 6. Adopting existing applications (Increment 3)

### US-31 Bring an existing repository under the platform
**Story.** As Matt, I want `dev open` on a repository without `profile.yaml` to offer adopt mode, detect the stack, prefill the questionnaire and write the configuration on a branch, so that any application can join the platform without hand-editing files.

**Acceptance.**
- Given a repository with no `project/profile.yaml`, when I run `dev open <path>`, then I am offered adopt mode and, if I decline, nothing is written.
- Given I accept, then the questionnaire is prefilled from files present (for example `pyproject.toml`), and `profile.yaml`, `target.yml` and a minimal `CLAUDE.md` are committed on a new branch.
- Given the adoption commit, when I run `dev open` again, then A2 passes on that repository (A11).

**Increment** 3. **Traces to** section 13; Q6; A11.

---

## Epic 7. Later

### US-32 Desktop templates
**Story.** As Matt, I want Python and C++ desktop templates in the platform, so that desktop tools are created the same way as web services.

**Acceptance.** Given `dev new desktop python` or `dev new desktop cpp`, then a project is created with `kind: desktop` in `target.yml`, `dev deploy` refuses it, and its tests pass.

**Increment** L. **Traces to** section 6; D20. Python desktop uses PyQt6.

### US-33 A second hosting target
**Story.** As Matt, I want to add a second hosting target as a registry entry, so that a project can move hosts by changing configuration, not code.

**Acceptance.** Given a second entry in the environments registry, when a project's `target.yml` names it, then `dev deploy` uses it with no change to the project's code.

**Increment** L. **Traces to** section 15; Q8.

---

## Cross-cutting stories

### US-34 No secrets in any repository
**Story (System).** No credential, key or token may exist in the platform repository, any project repository, or any registry.

**Acceptance.** Given CI on any of those repositories, then a secret scan passes (A9); given `.env` files, then they are git-ignored and only `.env.example` is committed.

**Increment** 1 to 3. **Traces to** section 16; D9, D13.

### US-35 Out of scope is written down
**Story (System).** The platform's first release targets one Linux laptop and one hosting target. MacBook, Azure and on-premises are recorded as non-goals.

**Acceptance.** Given the platform `README.md`, then it states these non-goals; given the bootstrap script, then it checks for Linux and refuses elsewhere with a clear message.

**Increment** 1. **Traces to** Q7.

---

## Story map by increment

| Increment | Stories |
|---|---|
| 1 Create | US-01 to US-14, US-16 to US-21, US-28 (refusal), US-34, US-35 |
| 2 Deploy | US-15, US-17 (Infrastructure, Deployment), US-22 to US-30 |
| 3 Adopt | US-31 |
| Later | US-32, US-33 |

## Decisions applied

| Decision | Value (Matt, 2026-09-13) | Stories |
|---|---|---|
| D6 first hosting target | AS2 | US-07, US-23 |
| D7 default branch names | `dev` / `cert` / `main` | US-03 |
| D20 desktop binding | PyQt6 | US-32 |
| Q5 "QA" and "Analytics" | QA Operations and IN Analytics, two separate containers on AWS | US-22 |

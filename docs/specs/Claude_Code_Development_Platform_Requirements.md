# Claude Code Development Platform — Requirements

| | |
|---|---|
| **Status** | Built through increment 3 on 2026-09-13. Items marked "later" (increment L) remain open. Derived from `Claude_Code_Development_Platform.md` and `Claude_Code_Development_Platform_User_Stories.md` (2026-09-13). |
| **Built** | v0.1.0 (increment 1), v0.2.0 (increment 2), v0.3.0 and v0.3.1 (increment 3). Verified with platform-console. |
| **Date** | 2026-09-13 |
| **Scope** | Fresh start. No earlier tooling is reused. |
| **Language** | MUST = mandatory for the increment named. SHOULD = expected unless a recorded decision says otherwise. MAY = optional. |
| **Companion** | `Claude_Code_Development_Platform_User_Stories.md` |

---

## 1. Purpose and scope

This document states what the platform must do and how each requirement is verified. It does not say how to build it; that is the design document. Every requirement traces to a user story (US-nn), a design section, a decision (Dnn), an open question (Qnn) or an acceptance criterion (Ann), so nothing here is invented.

**In scope for the first release (increments 1 to 3).** A private platform repository; a `dev` CLI; project configuration and schemas; registries; an orchestrator and seven specialist agents; a Flask template; commands, rules and scripts; session bootstrap; deployment to DEV, CERT and PROD with gates; adoption of existing repositories.

**Out of scope for the first release.** Desktop templates; a second hosting target; MacBook, Azure and on-premises workstations or hosts (Q7); any migration of, or dependency on, tooling that existed before 2026-09-13 (D5, D12, D19).

---

## 2. Definitions

| Term | Meaning |
|---|---|
| Platform | The `development-platform` repository and what it installs at user scope. |
| Project | One application repository created or adopted by the platform. |
| Agent | A Claude Code subagent that performs a category of work. WHO. |
| Skill | A reusable instruction for a repeated task. HOW. |
| Command | A slash command that runs a workflow. WHAT. |
| Script | A deterministic, version-controlled machine operation. |
| Registry | A platform file describing shared resources by logical name, without secrets. |
| Configuration | A project's `project/profile.yaml` and `deploy/target.yml`. WHERE. |
| Readiness summary | The block printed at the start of a session, design section 13A. |
| Gate | A check enforced by a Claude Code hook that stops an operation before its script runs. |
| Hosting target | A named entry in the environments registry that a project deploys to. |
| Increment | One of Create (1), Deploy (2), Adopt (3), Later (L). |

---

## 3. Constraints and assumptions

| # | Statement | Source |
|---|---|---|
| C1 | The platform is used by one person on Linux workstations. | Q7 |
| C2 | Git identity on the workstation is folder-based; only `~/Work/as2` and `~/Work/company` can commit. The platform repository and every project live under one of them. | Q2, section 19 |
| C3 | Claude Code loads agents and skills from `~/.claude/` and reads a project's `CLAUDE.md` at launch. The CLI cannot inject context into a session; it can only verify and pass paths. | D3, D11, 13A |
| C4 | Existing servers and accounts may be hosting targets; existing files may not be reused. | Scope line |
| C5 | The first hosting target is AS2; default branches are `dev`, `cert`, `main`; the Python desktop binding is PyQt6; "QA" and "Analytics" mean the QA Operations and IN Analytics environments, two separate containers on AWS. Decided by Matt 2026-09-13. | D6, D7, D20, Q5 |
| A1 | Chromium, Python 3 and `gh` are available on the workstation. | Section 13 |

---

## 4. Functional requirements

### 4.1 Platform repository (PLAT)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| PLAT-1 | The platform MUST be one private GitHub repository named `development-platform` with the top-level tree of design section 5 and nothing else at the top level. | 1 | US-01 |
| PLAT-2 | The platform MUST be cloneable to a stable local path under `~/Work/as2/` and MUST commit under that folder's git identity. | 1 | US-01, Q2 |
| PLAT-3 | The platform MUST carry a version as a git tag in semantic form, and `dev platform update` MUST report the installed tag. | 1 | US-06 |
| PLAT-4 | The platform MUST contain no credentials, keys or tokens, verified by a secret scan in CI. | 1 | US-34, A9 |
| PLAT-5 | Platform documentation MUST be Markdown inside the repository. | 1 | D17 |
| PLAT-6 | The platform `README.md` MUST state the non-goals of Q7. | 1 | US-35 |

### 4.2 CLI (CLI)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| CLI-1 | The platform MUST expose one user-facing command, `dev`, with subcommands `new`, `open`, `list`, `status`, `platform update`, `deploy`, `health`, `rollback`, `db inspect`. | 1 (`new`, `open`, `platform update`), 2 (rest) | Section 13 |
| CLI-2 | The CLI MUST be deterministic: the same inputs and files produce the same actions and output. It MUST NOT call a language model. | 1 | Principle 2 |
| CLI-3 | `dev new <type> <target>` MUST, in order: check prerequisites; verify Git and `gh` authentication; verify Claude Code; verify Docker and cloud CLI only when the template needs them; clone or update the platform; select the template; run the questionnaire; create or connect the GitHub repository; create the working copy under the identity folder; write `CLAUDE.md` and project-specific `.claude/`; write `profile.yaml` and `target.yml`; validate connections; launch Claude Code. | 1 | US-07, US-09, US-11 |
| CLI-4 | `dev new` MUST stop before the questionnaire, name the missing prerequisite and create nothing, if any prerequisite check fails. | 1 | US-09 |
| CLI-5 | `dev new` MUST refuse when the identity answer does not match the destination folder. | 1 | US-11 |
| CLI-6 | `dev open <project>` MUST perform the sequence of design section 13A: identify platform path; locate or clone; read and validate both configuration files; verify platform rules, agents and skills at `~/.claude/`; verify project `CLAUDE.md`; locate `docs/specs/` and `docs/DECISIONS.md`; check git state; resolve declared resources through registries; validate connections where appropriate; launch Claude Code with those paths. | 1 | US-12, US-13 |
| CLI-7 | `dev open` MUST refuse to launch, naming the file, when a required platform or project file is missing or invalid. | 1 | US-02, US-13, A3 |
| CLI-8 | `dev open` MUST print one warning line when `profile.yaml`'s `platform_version` differs from the installed tag, and MUST NOT modify any file in response. | 1 | US-06 |
| CLI-9 | `dev open` on a repository without `project/profile.yaml` MUST offer adopt mode and MUST write nothing if declined. | 3 | US-31 |
| CLI-10 | `dev list` MUST derive its list by scanning `~/Work/as2/` and `~/Work/company/` for `project/profile.yaml`, and MUST keep no separate list file. | 2 | US-29, A10 |
| CLI-11 | `dev status` MUST print project, branch, git state, configured environments, declared data sources and platform version, and MUST exit non-zero outside a platform project. | 2 | US-15 |
| CLI-12 | `dev platform update` MUST update the platform working copy and install its agents, skills and commands into `~/.claude/`, replacing earlier platform versions of the same names only. | 1 | US-05 |
| CLI-13 | `dev deploy <env>`, `dev health [env]`, `dev rollback <env>` and `dev db inspect <name>` MUST each run the corresponding platform script and nothing else, so that a gate hook on the script applies whichever path invoked it. | 2 | D24, US-23, US-24 |
| CLI-14 | Every CLI subcommand MUST exit zero on success and non-zero on any failure, with a one-line reason as the last line of output. | 1 | All CLI stories |

### 4.3 Project configuration and schemas (CFG)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| CFG-1 | A project's configuration MUST consist of exactly `project/profile.yaml` and `deploy/target.yml`. | 1 | US-03, D23 |
| CFG-2 | `profile.yaml` MUST hold: name, purpose, application type, stack, data sources as a list of logical registry names each with an access mode, and `platform_version`. | 1 | US-03 |
| CFG-3 | `target.yml` MUST hold: `kind` (`service` or `desktop`), `host`, `identity`, `environments` as a map of environment name to branch and path, and MAY hold `connects_to`. | 1 | US-03 |
| CFG-4 | The platform MUST ship a JSON Schema for each registry file and for both configuration files, under `registries/schema/`. | 1 | US-02, Q1 |
| CFG-5 | Every registry and configuration file MUST validate against its schema in CI and in `dev open`; a failure MUST name the file and field. | 1 | US-02, A3 |
| CFG-6 | Configuration files MUST NOT contain credentials. | 1 | US-03, A9 |
| CFG-7 | The default `environments` map written by `dev new` MUST be `dev`, `cert`, `main` to DEV, CERT, PROD; the map MUST be editable per project. | 1 | D7 (decided) |
| CFG-8 | The questionnaire MUST ask no more than the eleven items of design section 14 and SHOULD default any item a registry can answer. | 1 | US-08 |

### 4.4 Registries (REG)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| REG-1 | The platform MUST hold five registry files: `repositories.yaml`, `environments.yaml`, `containers.yaml`, `databases.yaml`, `tunnels.yaml`. | 2 | US-22 |
| REG-2 | Registries MUST describe identity, topology, logical names, environment mappings and approved access modes, and MUST NOT contain secrets. | 2 | US-22, D13 |
| REG-3 | A hosting target MUST be an entry in `environments.yaml`; no host name may be hard-coded in scripts, agents or skills. | 2 | D6, principle 5 |
| REG-4 | The registry MUST hold application-environment entries `qa-operations` and `in-analytics`, each naming its host and container on AWS; "QA" and "Analytics" MUST appear only as labels on those entries, never as roots or categories. The databases each uses MUST be recorded from inspection, not memory. | 2 | D8, Q5 (decided) |
| REG-5 | Every data source named in a `profile.yaml` MUST resolve to a `databases.yaml` entry, or `dev open` MUST report it as unresolved in the readiness summary. | 2 | US-22 |

### 4.5 Agents and orchestrator (AGT)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| AGT-1 | The user's normal interface MUST be one orchestrator running as the main Claude Code session, instructed by the project `CLAUDE.md` plus an imported platform rules file. | 1 | US-16, D11, Q9 |
| AGT-2 | The platform MUST provide exactly seven specialist agents at user scope: Code/Flask, Database/SQL, Infrastructure, Deployment, Documentation, Test, Review. | 1 (five), 2 (Infrastructure, Deployment) | US-17, D1 |
| AGT-3 | Database variants (PostgreSQL, SQL Server, schema discovery, query review, migrations) MUST be skills of the Database/SQL Agent, not separate agents. | 1 | US-17, D12 |
| AGT-4 | Desktop work MUST be handled by the Code/Flask Agent with Qt skills until a desktop template exists. | 1 | D1 |
| AGT-5 | The orchestrator MUST return one consolidated result per request and MUST state which specialists were used. | 1 | US-16 |
| AGT-6 | The orchestrator MUST classify each request low, medium or high risk by the operations and targets it touches, using the tiers of design Q4, and MUST escalate to the higher tier when unsure. | 1 (classification), 2 (gates) | US-27 |
| AGT-7 | Platform agent names MUST NOT collide with any agent already present at user scope. | 1 | US-05, section 19 |
| AGT-8 | Every project `CLAUDE.md` written by the platform MUST be under 60 lines and MUST NOT contain agent or skill definitions. | 1 | US-04, A5 |

### 4.6 Skills and commands (SKL)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| SKL-1 | The platform MUST provide these commands: `/project-setup`, `/project-reconfigure`, `/quick-change`, `/inspect-database`, `/deploy-dev`, `/deploy-cert`, `/deploy-prod`, `/review-code`, `/update-docs`, `/project-status`. | 1 (setup, quick-change, inspect, review, update-docs, status), 2 (reconfigure, deploys) | Section 9 |
| SKL-2 | A command that has a CLI counterpart MUST end by invoking that subcommand and MUST NOT reimplement the script's action. | 2 | D24, US-23 |
| SKL-3 | Increment 1 MUST ship only the skills listed for it in design section 8; any further skill MUST record the two hand-given instructions that justified it. | 1 | US-21 |
| SKL-4 | `/quick-change` MUST run without approval prompts for low-risk requests and MUST run only tests touching changed areas. | 1 | US-18 |

### 4.7 Session bootstrap (SES)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| SES-1 | The first output of a session started by `dev open` MUST be the readiness summary of design section 13A with these blocks: PROJECT, STACK, REPOSITORY, CURRENT BRANCH, ENVIRONMENTS, DATA SOURCES with access mode, PLATFORM, GIT, READY. | 1 | US-12, A2 |
| SES-2 | The readiness summary MUST report missing, invalid or unresolved items explicitly and MUST NOT invent values. | 1 | US-12 |
| SES-3 | GIT in the summary MUST show clean or dirty with a changed-file count, and MUST flag a branch not present in `target.yml`. | 1 | US-14 |
| SES-4 | After the summary, Claude MUST be able to answer "where does this deploy and from which branches" to match `target.yml` exactly with no file opened by the user. | 1 | A2 |
| SES-5 | Loading of rules, agents, skills and documents MUST be done by Claude Code from `~/.claude/` and the project; the CLI MUST only verify presence and validity and pass paths. | 1 | US-13, C3 |

### 4.8 Templates (TPL)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| TPL-1 | The platform MUST ship a `flask-web` template with the structure of design section 6, including `deploy/target.yml`, a thin `deploy/deploy.sh`, `.env.example`, `pyproject.toml` and tests that pass unmodified. | 1 | US-10 |
| TPL-2 | Templates MUST reference no file outside the platform repository. | 1 | US-10, D19 |
| TPL-3 | `python-desktop` and `cpp-desktop` templates MUST set `kind: desktop` and MUST be refused by `dev deploy`. | L | US-32 |
| TPL-4 | The Python desktop template MUST use PyQt6. | L | D20 (decided) |

### 4.9 Deployment (DEP)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| DEP-1 | Git operations and deployments MUST be separate: commits and pushes target branches; deployments target environments named in `target.yml`. No script or agent may infer one from the other. | 2 | Section 15, D15 |
| DEP-2 | The deploy script MUST read `deploy/target.yml` and the environments registry and MUST NOT hard-code any host, path or container. | 2 | US-23 |
| DEP-3 | `/deploy-dev` and `/deploy-cert` MUST: validate target, check git state, run proportionate tests, deploy, health-check, inspect logs, report; and MUST stop before deploying on a dirty tree. | 2 | US-23, A7 |
| DEP-4 | Before a production deploy the Deployment Agent MUST verify repository and exact commit, branch and clean tree, tests and review evidence proportionate to risk, migration review, backup where data is at risk, and a rollback procedure, and MUST report each with evidence before asking approval. | 2 | US-25 |
| DEP-5 | A production deploy MUST be blocked by a hook on the deploy script unless an explicit approval exists in the session naming repo, commit, branch, environment and target; the refusal MUST name repo, commit, branch and target. | 2 | US-24, A8, D21 |
| DEP-6 | An approval MUST be bound to one commit and MUST lapse when the branch head changes. | 2 | US-24 |
| DEP-7 | Every deployment MUST be recorded with commit, environment, timestamp and, for production, the approval, in the project's deployment history. | 2 | US-24, section 18 |
| DEP-8 | `dev rollback <env>` MUST redeploy the previous recorded commit and MUST refuse when none exists. | 2 | US-26 |
| DEP-9 | After any deploy, health checks MUST run and logs MUST be inspected, and the result reported. | 2 | US-23, US-25 |
| DEP-10 | The platform MUST use its own deploy root and routing on the hosting target and MUST NOT write into paths owned by earlier tooling. | 2 | D6, section 19 |
| DEP-11 | `dev health [env]` MUST check every dependency declared in `target.yml` (host, tunnel, container, database) and MUST exit non-zero if any is unreachable. | 2 | US-30 |

### 4.10 Safety (SAF)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| SAF-1 | The Database/SQL Agent MUST answer schema questions only from a live inspection and MUST cite the inspection and its time; if the database is unreachable it MUST say so and give no answer from memory. | 1 | US-19, A4 |
| SAF-2 | The Database/SQL Agent MUST refuse any unscoped DELETE or UPDATE on any database. | 1 | US-28, A4 |
| SAF-3 | DROP and TRUNCATE MUST be refused outside a migration that has passed DEP-4 review. | 2 | US-28 |
| SAF-4 | External analytical or operational data sources SHOULD be declared read-only in `profile.yaml` and the agent MUST honour the declared access mode. | 1 | Section 16 |
| SAF-5 | High-risk operations (design Q4 tiers) MUST be enforced by hooks on the relevant scripts so they apply regardless of the orchestrator's classification. | 2 | US-27 |
| SAF-6 | No `.env` file may be committed; only `.env.example`. | 1 | US-34 |
| SAF-7 | Credentials MUST come from authenticated CLIs, SSH configuration, environment variables or a secrets manager, never from any repository or registry. | 1 | Section 16, D9 |

### 4.11 Documentation (DOC)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| DOC-1 | Every project MUST have `docs/specs/` for user stories and requirements and `docs/DECISIONS.md` for decisions; other docs folders MAY be added when needed. | 1 | D16 |
| DOC-2 | When an implementation changes a documented requirement, story, architecture or database behaviour, the Documentation Agent MUST update the relevant file and add a change-history entry in the same turn. | 1 | US-20 |
| DOC-3 | Cosmetic changes MUST NOT trigger documentation edits. | 1 | US-20 |
| DOC-4 | A decision taken during work MUST be appended to `docs/DECISIONS.md` with date and reason. | 1 | US-20 |
| DOC-5 | Each project SHOULD accumulate the knowledge tree of design section 18 (architecture, requirements, stories, bugs, enhancements, schema, decisions, change history, deployment history, known problems, business rules) as those items arise. | 1 to 3 | Section 18 |

### 4.12 Adoption (ADP)

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| ADP-1 | Adopt mode MUST detect the stack from files present and prefill the questionnaire. | 3 | US-31 |
| ADP-2 | Adopt mode MUST write `profile.yaml`, `target.yml` and a minimal `CLAUDE.md` on a new branch and MUST NOT touch the current branch. | 3 | US-31 |
| ADP-3 | After adoption, `dev open` on that repository MUST satisfy SES-1 to SES-4. | 3 | A11 |

---

## 5. Non-functional requirements

| ID | Requirement | Inc | Verified by |
|---|---|---|---|
| NFR-1 **Portability** | A fresh Linux machine with Git, `gh` and Claude Code authenticated MUST reach a working `dev open` with no manual step other than entering credentials. A time target is set only after measurement (A1). | 1 | A1 |
| NFR-2 **Determinism** | Running any CLI subcommand twice on unchanged inputs MUST produce identical actions and output. | 1 | CLI-2 |
| NFR-3 **Smallness** | Project `CLAUDE.md` under 60 lines; questionnaire at most eleven items; configuration two files. | 1 | AGT-8, CFG-8, CFG-1 |
| NFR-4 **No secrets** | Secret scans on the platform and every project MUST pass in CI. | 1 to 3 | A9 |
| NFR-5 **Honesty** | No platform output may present a guessed value as known. Missing or unverified items MUST be labelled. | 1 | SES-2, SAF-1 |
| NFR-6 **Proportionality** | Low-risk work MUST incur no approval prompt; high-risk work MUST incur every gate. The classification tiers are those of design Q4. | 1, 2 | AGT-6, SAF-5 |
| NFR-7 **Auditability** | Deployments, approvals and decisions MUST be recorded in the project so that why and when can be answered later without a chat transcript. | 2 | DEP-7, DOC-4 |
| NFR-8 **Isolation** | The platform MUST NOT read, write, import or depend on any file created before 2026-09-13 outside the platform and its projects, except machine configuration (git identity, SSH) and the hosting servers themselves. | 1 to 3 | Scope line, C4 |
| NFR-9 **Reversibility** | Every deploy MUST be reversible by `dev rollback`, and every adoption MUST be reversible by deleting its branch. | 2, 3 | DEP-8, ADP-2 |
| NFR-10 **Update safety** | A platform update MUST never modify a project file; version mismatches are reported, not fixed. | 1 | CLI-8 |

---

## 6. Decisions applied

| Decision | Value (Matt, 2026-09-13) | Requirements affected |
|---|---|---|
| D6 first hosting target | AS2. The first `environments.yaml` entry is `as2`; `dev new flask as2` is the first valid form. | REG-3, DEP-2, DEP-10, DEP-11, CLI-3 |
| D7 default branch names | `dev` / `cert` / `main` | CFG-7 |
| D20 desktop binding | PyQt6 | TPL-4 |
| Q5 "QA" and "Analytics" | QA Operations and IN Analytics: two separate containers on AWS, registry entries `qa-operations` and `in-analytics`. Databases recorded by inspection in increment 2. | REG-4, REG-5 |

Nothing in this document is blocked.

Everything listed as increment 1, 2 or 3 is built and verified as of 2026-09-13 (v0.3.1, verified with platform-console); TPL-3 and TPL-4 (increment L) remain open.

---

## 7. Traceability

### Stories to requirements

| Story | Requirements |
|---|---|
| US-01 | PLAT-1, PLAT-2, PLAT-4, PLAT-5 |
| US-02 | CFG-4, CFG-5 |
| US-03 | CFG-1, CFG-2, CFG-3, CFG-6, CFG-7 |
| US-04 | AGT-8, DOC-1 |
| US-05 | CLI-12, AGT-7 |
| US-06 | PLAT-3, CLI-8, NFR-10 |
| US-07 | CLI-3, TPL-1 |
| US-08 | CFG-8 |
| US-09 | CLI-4, CLI-14 |
| US-10 | TPL-1, TPL-2 |
| US-11 | CLI-3, CLI-5 |
| US-12 | CLI-6, SES-1, SES-2, SES-4 |
| US-13 | CLI-2, CLI-7, SES-5 |
| US-14 | SES-3 |
| US-15 | CLI-11 |
| US-16 | AGT-1, AGT-5 |
| US-17 | AGT-2, AGT-3, AGT-4 |
| US-18 | SKL-1, SKL-4 |
| US-19 | SAF-1, SAF-4, SKL-1 |
| US-20 | DOC-2, DOC-3, DOC-4, DOC-5 |
| US-21 | SKL-3 |
| US-22 | REG-1, REG-2, REG-4, REG-5 |
| US-23 | CLI-13, DEP-2, DEP-3, DEP-9, DEP-10, SKL-1, SKL-2 |
| US-24 | CLI-13, DEP-5, DEP-6, DEP-7 |
| US-25 | DEP-4 |
| US-26 | DEP-8 |
| US-27 | AGT-6, SAF-5 |
| US-28 | SAF-2, SAF-3 |
| US-29 | CLI-10 |
| US-30 | DEP-11 |
| US-31 | CLI-9, ADP-1, ADP-2, ADP-3 |
| US-32 | TPL-3, TPL-4 |
| US-33 | REG-3 |
| US-34 | PLAT-4, SAF-6, SAF-7, NFR-4 |
| US-35 | PLAT-6 |

### Acceptance criteria to requirements

| Criterion | Requirements |
|---|---|
| A1 | NFR-1 |
| A2 | SES-1, SES-4 |
| A3 | CFG-5, CLI-7 |
| A4 | SAF-1, SAF-2 |
| A5 | CLI-3, AGT-8, TPL-1 |
| A6 | AGT-1, AGT-5, SKL-4 |
| A7 | DEP-3, DEP-9 |
| A8 | DEP-5 |
| A9 | PLAT-4, CFG-6, REG-2, SAF-6 |
| A10 | CLI-10 |
| A11 | ADP-3 |

### Requirements with no story

None. Every functional requirement appears in the table above; non-functional requirements trace to the functional ones they constrain, as shown in their own table. Checked by script on 2026-09-13.

---

## 8. Change history

| Date | Change |
|---|---|
| 2026-09-13 | First draft from the consolidated design and the user stories. Fresh-start scope. |
| 2026-09-13 | D6, D7, D20 and Q5 decided by Matt and applied: C5, CFG-7, REG-4, TPL-4, section 6. |
| 2026-09-13 | Increments 1 to 3 built and verified; statuses updated. |

# Decisions

The full list with basis is in `docs/specs/Claude_Code_Development_Platform.md` section 22. This file records decisions made while building.

## 2026-09-13 — D6, D7, D20, Q5 decided by Matt
First hosting target AS2. Branches dev / cert / main. Python desktop PyQt6. "QA" = QA Operations, "Analytics" = IN Analytics, two separate containers on AWS; registry entries `qa-operations` and `in-analytics`, databases recorded by inspection in increment 2.

## 2026-09-13 — Commands are installed as user-scope skills
Claude Code slash commands are skills with a `SKILL.md`; the platform's `commands/` folder is installed into `~/.claude/skills/` alongside `skills/`. Kept as separate folders in the repo because they answer different questions (WHAT workflow vs HOW).

## 2026-09-13 — `dev open` writes `.platform/session.md`
The CLI cannot inject context into Claude Code. It writes the readiness summary to a git-ignored file that the project `CLAUDE.md` names; Claude reads it at launch. The CLI verifies, Claude loads (SES-5).

## 2026-09-13 — Platform version is the latest git tag
`dev open` compares `profile.yaml` `platform_version` to `git describe --tags`. No version file to keep in step.

## 2026-09-13 — Platform's own deploy root on AS2 is `/srv/platform`, router prefix `/platform/`
Chosen so the platform never writes into paths owned by earlier tooling (section 19, DEP-10). Deployment itself is increment 2.

## 2026-09-13 — AS2 deploy root is `/home/matt/platform`, not `/srv/platform`
No passwordless sudo on AS2, verified by inspection. Everything the platform puts on the host lives under the user's home. Registry updated.

## 2026-09-13 — The platform runs its own router on AS2
`platform-router` (nginx:alpine) on `127.0.0.1:8200`, network `platform-net`, routing `/platform/<env>/<project>/` to `<project>-<env>:5000` by Docker DNS at request time. Own container, own network, own port: nothing owned by earlier tooling is edited (section 19, DEP-10).

## 2026-09-13 — Deploy pushes to the host over ssh, not via GitHub
`dev deploy` pushes the branch head to a bare repo under the deploy root and runs the host-side script. No dependency on GitHub being reachable from the host, and no GitHub token on the host.

## 2026-09-13 — Deployment history lives on the host, mirrored locally
Authoritative: `<deploy_root>/<project>/deployments.jsonl` on the host (survives laptop changes). Mirror: `.platform/deployments.jsonl`, git-ignored, so a deploy never dirties the tree. `dev status` shows the host's view.

## 2026-09-13 — Prod approval is a file typed by the human, consumed by one deploy
`dev approve prod` prompts for the commit prefix, backup statement, rollback plan and migration review, writes `.platform/approval-prod.json` bound to HEAD, and `dev deploy prod` deletes it after use. A PreToolUse hook denies `dev approve` to Claude and denies `dev deploy prod` without a valid approval (D21, DEP-5, DEP-6).

## 2026-09-13 — The AWS EC2 is registered as a host but is not a deploy target
Inspected 2026-09-13: IN Analytics runs as `flask-dev/cert/prod`, QA Operations as `flask-qa-dev/cert/prod`, on one EC2. Recorded in `containers.yaml`. Databases not yet inspected; `databases.yaml` stays empty until they are (REG-5).

## 2026-09-13 — Adoption lands on branch `platform/adopt`, never on the current branch
`dev open --adopt` creates the branch from HEAD, writes `project/profile.yaml`, `deploy/target.yml`, docs stubs and `.gitignore` lines, and commits there. A dirty tree or a repository outside an identity folder is refused. An existing `CLAUDE.md` is kept; the platform import and facts block is prepended so nothing the project already said is lost. Reversible by deleting the branch (NFR-9).

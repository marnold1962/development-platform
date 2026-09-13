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

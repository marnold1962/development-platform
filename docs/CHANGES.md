# Change history

## 2026-09-13 — Host inventory: dev host inventory <host>
`dev host inventory <host>` pipes a read-only collector (`scripts/inventory/collect.py`) over ssh, nothing installed on the host; it inspects docker, env files, listening ports, systemd, cron, Ollama, GPU, disks and the file roots, which come from the registry (`deploy_root` plus `inventory_roots`).
Secrets are masked at the source: container environment, env files and cron KEY=value assignments report only the name and value length; cron command lines are verbatim. The laptop writes JSON and an HTML report with a diff against the previous run.

## 2026-09-13 — Specs marked built through increment 3
Header status and a Built row (v0.1.0, v0.2.0, v0.3.0, v0.3.1, verified with platform-console) in all three specs; per-story status lines and a Status column in the story map; requirements section 6 and change history note increments 1 to 3 built, TPL-3 and TPL-4 open; design Summary "What happened" paragraph. US-32 and US-33 remain "later".

## 2026-09-13 — Increment 3: adopt
`dev open <path> --adopt`: detects the stack from files present, prefills the questionnaire, writes configuration on branch `platform/adopt`, then the readiness summary works. Declining writes nothing. Affects US-31, ADP-1..3, CLI-9, A11.

## 2026-09-13 — Increment 2: deploy
`dev deploy`, `dev approve`, `dev rollback`, `dev health`, `dev status`, `dev list`, `dev db inspect`. Infrastructure and Deployment agents. Skills platform-deployment, platform-docker, platform-ssh. Commands /deploy-dev, /deploy-cert, /deploy-prod, /project-reconfigure. Risk gate hook. Router and remote script. Registries filled from inspection (containers, aws-ec2 host, tunnels). Template gains Dockerfile and forwarded-prefix middleware. Affects US-15, US-17, US-22 to US-30; DEP-*, SAF-5, CLI-10, CLI-11, CLI-13.

## 2026-09-13 — Increment 1: create
Platform repo, schemas, rules, five agents, five skills, six commands, Flask template, questionnaire, `dev new`, `dev open`, `dev platform update`. Tag v0.1.0.

## 2026-09-13 — Fixes from first real use
Template `CLAUDE.md` no longer says deployment is unavailable. `dev health` with no environment reports an undeployed environment as "not deployed" instead of unhealthy; asking for that environment explicitly still fails. Approval prompt accepts a full commit hash. Gate hook honours a leading `cd <dir>`.

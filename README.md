# development-platform

A reusable personal development platform above Claude Code, GitHub, the workstation, databases and servers. One private repository holds **how we build**: agents, skills, commands, rules, scripts, templates and registries. Each application is its own repository holding only **what it is**. A small deterministic `dev` CLI creates or opens a project and launches Claude Code with the context loaded.

Fresh start, 2026-09-13. Nothing built before that date is reused.

## Install on a Linux workstation

```bash
git clone git@github.com:marnold1962/development-platform.git ~/Work/as2/development-platform
cd ~/Work/as2/development-platform
scripts/setup/setup-linux.sh      # reports missing prerequisites; installs nothing
scripts/setup/setup-python.sh     # virtualenv for the CLI and ~/.local/bin/dev
dev platform update --no-pull     # install agents, skills and commands to ~/.claude
```

## Use

```bash
dev new flask as2        # questionnaire, GitHub repo, working copy, branches, Claude Code
dev open <project>       # verify, print the readiness summary, launch Claude Code
dev open <project> --check   # verify and print only
dev platform update      # pull and reinstall
dev deploy <env>         # push HEAD to the host, build, run, health-check (dev, cert, prod)
dev approve prod         # human only; bound to HEAD; consumed by one deploy
dev health [env] / dev rollback <env> / dev status / dev list / dev db inspect <name>
dev open <path> --adopt  # bring a repository the platform did not create under it, on branch platform/adopt
dev host inventory as2   # read-only report of everything on the host, opens in the browser
```

Increments 1 (create), 2 (deploy) and 3 (adopt) are built. Later: desktop templates, a second hosting target.

## Non-goals (first release)

MacBook, Azure and on-premises hosts. Any host other than the one hosting target in `registries/environments.yaml`. Reuse of any earlier tooling.

## Layout

| Folder | Holds |
|---|---|
| `cli/` | the `dev` command (Python) |
| `templates/` | project templates rendered by `dev new` |
| `agents/` | specialist subagents, installed to `~/.claude/agents/` |
| `skills/` | reusable HOW knowledge, installed to `~/.claude/skills/` |
| `commands/` | slash-command workflows, installed to `~/.claude/skills/` |
| `rules/` | `platform.md`, imported by every project `CLAUDE.md` by path |
| `scripts/` | deterministic machine operations |
| `questionnaires/` | the new-project questionnaire |
| `registries/` | the map of the world, with JSON schemas under `schema/` |
| `docs/` | the platform's own specs and decisions |

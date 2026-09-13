# development-platform

The reusable platform: how we build. Projects are separate repositories that know what they are.

@rules/platform.md

## Working in this repository

- `cli/` is the `dev` command. Deterministic, stdlib plus PyYAML and jsonschema. Never add a language-model call.
- `agents/`, `skills/`, `commands/` are installed to `~/.claude/` by `dev platform update`. Edit them here; never edit the installed copies.
- `rules/platform.md` is imported by every project's `CLAUDE.md` by path. Editing it changes every project's next session.
- `registries/` are the map of the world. No secrets. Every file validates against `registries/schema/`.
- `templates/` are rendered by `dev new`. Placeholders are `__UPPER_SNAKE__`.
- Tests: `make test`. A change to a schema, template or the CLI needs a test.
- Specs for the platform itself live in `docs/specs/`. Decisions in `docs/DECISIONS.md`.
- Versions are git tags `vX.Y.Z`. `dev open` compares a project's `platform_version` to the latest tag.

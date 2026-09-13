---
name: project-reconfigure
description: Change a project's configuration later — data sources, hosting target, branch mapping or constraints — by editing project/profile.yaml and deploy/target.yml and re-validating. Never edits registries.
---

1. Show the current `project/profile.yaml` and `deploy/target.yml`.
2. Apply the requested change to those two files only. Data sources must exist in `registries/databases.yaml`; hosts in `registries/environments.yaml`. If not, stop: the registry entry must be added from inspection first.
3. Run `dev open . --check` to validate. Fix and repeat until it passes.
4. Have `documentation` add a `docs/DECISIONS.md` entry saying what changed and why.
5. Report the diff of the two files.

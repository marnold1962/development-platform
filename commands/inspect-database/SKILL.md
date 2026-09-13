---
name: inspect-database
description: Validate a configured data source and inspect its real schema. Use before writing any query or migration, or when asked what tables or columns exist.
---

Argument: the logical data source name from `project/profile.yaml` (default: the project's application database).

1. Resolve the name through `registries/databases.yaml` in the platform working copy. If absent, stop: the source is unregistered.
2. Run `dev db inspect <name>` if available (increment 2), otherwise `python scripts/database/inspect-schema.py <name>`.
3. Print tables, columns, keys and relationships exactly as returned, with the time of inspection.
4. If unreachable, say so. Give no schema from memory.

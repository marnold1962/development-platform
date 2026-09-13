---
name: platform-postgresql
description: How platform projects talk to PostgreSQL — schema discovery first, read-only by default, scoped writes, Alembic migrations with rollback. Use for any PostgreSQL query, model or migration work.
---

# PostgreSQL on the platform

- Discover before writing: `python scripts/database/inspect-schema.py <logical-name>` prints tables, columns, keys. Cite it.
- Access mode comes from `project/profile.yaml` `data_sources[].access`. Read-only means SELECT only.
- Every UPDATE or DELETE has a WHERE clause and a stated expected row count. Wrap multi-statement changes in a transaction.
- Migrations use Alembic in `migrations/`. Each migration has a working `downgrade()`. Before applying to anything but a local database: backup command stated, rollback stated.
- Connection details are environment variables (`DATABASE_URL` for the app database; `DS_<NAME>_URL` for external sources). Never in files.

Justification: design section 8, increment 1.

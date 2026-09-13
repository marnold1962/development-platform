---
name: platform-flask
description: How Flask projects on the development platform are structured — application factory, Blueprints, services, repositories, Jinja and HTMX conventions. Use when adding or changing routes, templates or application structure in a platform project.
---

# Flask conventions (platform)

- `app/__init__.py` exposes `create_app(config_name)`; nothing else runs at import time.
- One Blueprint per feature in `app/blueprints/<feature>/` with `routes.py`, and `templates/<feature>/` beside it.
- Routes are thin: parse input, call a service, render. Services in `app/services/` hold logic and are testable without Flask. Repositories in `app/repositories/` are the only place SQL or ORM calls live.
- HTMX: a request with `HX-Request` gets a fragment template; otherwise the full page extending `base.html`. Put shared fragments in `app/templates/partials/`.
- Configuration comes from environment variables read in `config.py`; no secrets in code.
- Health endpoint `GET /healthz` returns `{"status": "ok"}` and is used by deploy health checks.

Justification for this skill: design section 8 lists it for increment 1; the template encodes it.

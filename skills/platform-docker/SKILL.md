---
name: platform-docker
description: Docker conventions for platform projects — the template Dockerfile, image tags, container names, the platform network and router, what may and may not be touched on a host. Use for Dockerfile, image or container questions.
---

# Docker on the platform

- Image tag `<project>:<env>-<sha12>`; container name `<project>-<env>`; network `platform-net`; the app listens on `0.0.0.0:5000` inside the container and publishes no port. Only `platform-router` publishes, on `127.0.0.1:<router_port>`.
- The template Dockerfile installs the project with pip and runs gunicorn. Add system packages only in the Dockerfile, never on the host.
- The router sets `X-Forwarded-Prefix`; the app's `ForwardedPrefix` middleware turns it into `SCRIPT_NAME` so `url_for` works under `/platform/<env>/<project>/`.
- Never `docker rm`, `stop` or `network rm` anything whose name is not `<project>-<env>` for a platform project or `platform-router`/`platform-net`. Other containers on the host are not ours.
- Old images are kept so `dev rollback` can reuse them. Prune only by explicit request.

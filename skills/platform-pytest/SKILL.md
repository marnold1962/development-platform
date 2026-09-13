---
name: platform-pytest
description: How tests are written and run in platform projects — pytest layout, Flask test client fixtures, proportionate test selection by risk. Use when writing or running tests.
---

# pytest on the platform

- Tests live in `tests/`, mirroring `app/`. `tests/conftest.py` provides `app` and `client` fixtures from `create_app("testing")`.
- Low-risk change: run `pytest tests/<area>` for the changed area. Medium or High: `make test` (full suite).
- Every route has at least one test through `client`. Every service function has a test without Flask.
- Never skip or xfail to get green. A failing test is reported with its output.
- Headless: no test may need a display, a network, or a real external database. Use SQLite in-memory for the app database in tests.

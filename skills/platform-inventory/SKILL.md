---
name: platform-inventory
description: How to read and refresh the host inventory report (dev host inventory <host>), when to run it, and that environment variable values are never collected.
---

# Host inventory on the platform

- `dev host inventory as2` pipes `scripts/inventory/collect.py` over ssh (nothing is installed on the host), writes `~/Work/inventory/<host>/<stamp>.json` and `.html`, copies the HTML to `latest.html`, and opens it. `--no-open` skips the browser; `--out DIR` changes the folder.
- It is read-only: it inspects docker, systemd, cron, listening ports, env files, Ollama and the file roots; it changes nothing on the host.
- Environment variable values are never collected; the report shows only names and lengths (`DATABASE_URL (len 61)`). Never add value collection.
- Run it before planning a change to a host, after a deploy that touched containers or timers, and whenever something on the host is unexplained.
- The "Changes since last run" section diffs against the newest previous `.json` in the output folder; the first run says "first run".
- Read `latest.html` in the browser, or the `.json` with `python3 -m json.tool` when a specific fact is needed; cite the `collected_at` time.
- Warnings at the bottom list what the collector could not read (missing tools, permissions); they are facts about the host, not errors to fix in the platform.
- Justification: Matt asked for this twice on 2026-09-13 ('what is on the as2 containers files env etc, a all in one'; 'cron jobs as well show everything that is on it including llm'), which is the platform's two-occasions rule.

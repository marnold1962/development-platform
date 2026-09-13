status: built

# Host inventory

**Story.** As Matt, I want one command that produces a single page showing everything that is on a host, AS2 first: containers, images, volumes, networks, compose projects, environment variable names, env files, listening ports, systemd services and timers, cron, Ollama and its models, the GPU, disks, memory, the folders under the deploy roots and what is biggest, and what changed since the last run, so that I never have to ssh in and remember a dozen commands to answer "what is on that box".

**Shape.** `dev host inventory <host>` runs from the laptop. It pipes a read-only collector to the host over ssh, receives one JSON document, saves it under `~/Work/inventory/<host>/<timestamp>.json`, renders `<timestamp>.html` and `latest.html`, diffs against the previous JSON, and opens the page in the browser. Nothing is installed or changed on the host. Nothing runs on the host between invocations.

**Secrets.** Environment variable values never leave the host. The collector records the variable name and the length of its value, for container environments and for env files under the deploy roots. The page says so on every env table. If a value is needed, the page shows which file on the host holds it. Cron assignments (KEY=value) are masked the same way; cron command lines are shown verbatim.

**Acceptance criteria.**
- AC1 Given AS2 reachable, when `dev host inventory as2` runs, then a JSON and an HTML file are written, the page opens, and the command exits 0 in under three minutes.
- AC2 Given the page, then every running and stopped container on the host appears with image, state, ports, networks, compose project, restart count, mounts and env variable names with lengths.
- AC3 Given the page, then it lists Ollama models with size and modified date, or the reason Ollama could not be queried; and the GPU line shows the device or the exact driver error.
- AC4 Given the page, then cron shows the user crontab, /etc/crontab, each file in /etc/cron.d and the names in the periodic folders; and the warnings section states that root's crontab is not readable without sudo.
- AC5 Given a second run after a container was added or removed, then the Changes section lists it under added or removed; given a first run, the section says first run.
- AC6 Given the JSON and HTML files, when searched for any environment variable value known to be set on the host, then it is absent. Automated test: a renderer fed an entry carrying a value still prints no value.
- AC7 Given a host with no Docker, no Ollama or no GPU, then the corresponding sections state that plainly and the rest of the page still renders.

**Out of scope.** Changing anything on the host. Root-only files. A live page on the host (a later shape, if the report proves useful). Hosts other than those in the environments registry.

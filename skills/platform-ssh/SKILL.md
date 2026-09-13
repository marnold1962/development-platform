---
name: platform-ssh
description: How the platform reaches hosts — ssh aliases from the registry, Cloudflare versus LAN reach, the platform router port-forward, and what never goes in a command. Use when connecting to a host or opening a tunnel.
---

# SSH and tunnels on the platform

- Host aliases live in `~/.ssh/config` (machine configuration) and are named in `registries/environments.yaml` under `reach`, in preference order. `dev deploy`/`health` try them in order with `BatchMode=yes`.
- AS2: `as2-cf` (Cloudflare tunnel, works anywhere) then `home` (LAN only).
- Reach a deployed app: `ssh -N -L 8200:127.0.0.1:8200 as2-cf` then `http://127.0.0.1:8200/platform/<env>/<project>/`. Registry: `tunnels.yaml`.
- Never put a key path, password or token in a command or a file. Keys are in `~/.ssh`; tokens in the credential helpers.
- Before any command that changes a host, name the host alias and what will change.

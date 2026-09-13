# __PROJECT_NAME__

__PROJECT_PURPOSE__

Created by the development platform. Configuration: `project/profile.yaml` (what) and `deploy/target.yml` (where).

```bash
make setup   # virtualenv and dependencies
make test    # pytest, headless
make run     # local server on :5000
dev open __PROJECT_NAME__   # start a Claude Code session with context loaded
```

## Deploy

```bash
dev deploy dev      # push HEAD of the dev branch to AS2, build, run, health-check
dev deploy cert
dev approve prod    # human only: names repo, commit, branch, env, target; bound to HEAD
dev deploy prod
dev health [env]
dev rollback <env>
dev status          # includes last deployment per environment
```

Runtime secrets for each environment live on the host at `<deploy_root>/<project>/<env>.env` and are never in git. Reach the running app with `ssh -N -L 8200:127.0.0.1:8200 as2-cf` then `http://127.0.0.1:8200/platform/<env>/<project>/`.

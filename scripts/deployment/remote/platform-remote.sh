#!/usr/bin/env bash
# Runs ON THE HOST. Installed by `dev deploy` to <deploy_root>/bin/platform-remote.sh.
# Usage: platform-remote.sh <deploy_root> <router_port> <cmd> <project> [env] [sha]
#   ensure                       network + router up
#   receive <p> <env>            create bare repo if needed; print its path
#   deploy  <p> <env> <sha>      checkout sha, build image, run container, health, record
#   rollback <p> <env>           re-run previous successful deployment's image
#   health  <p> <env>            router + container + healthz; exit 0/1
#   status  <p>                  last deployment per env as json lines
set -euo pipefail
ROOT="$1"; PORT="$2"; CMD="$3"; PROJ="${4:-}"; ENV="${5:-}"; SHA="${6:-}"; MOUNTS="${7:-}"
mount_args() { local m; MA=(); IFS=, read -ra specs <<< "$MOUNTS"; for m in "${specs[@]}"; do [ -n "$m" ] && MA+=(-v "$m"); done; }
NET=platform-net; ROUTER=platform-router
log() { echo "[remote] $*"; }

ensure() {
  mkdir -p "$ROOT/bin" "$ROOT/router"
  docker network inspect "$NET" >/dev/null 2>&1 || { docker network create "$NET" >/dev/null; log "created network $NET"; }
  if ! docker ps --format '{{.Names}}' | grep -qx "$ROUTER"; then
    docker rm -f "$ROUTER" >/dev/null 2>&1 || true
    docker run -d --name "$ROUTER" --network "$NET" --restart unless-stopped \
      -p "127.0.0.1:${PORT}:80" -v "$ROOT/router/router.conf:/etc/nginx/conf.d/default.conf:ro" nginx:alpine >/dev/null
    log "started $ROUTER on 127.0.0.1:$PORT"
  else
    # reload in case router.conf changed
    docker exec "$ROUTER" nginx -s reload >/dev/null 2>&1 || true
  fi
}

record() { # env sha image ok note
  mkdir -p "$ROOT/$PROJ"
  printf '{"time":"%s","env":"%s","sha":"%s","image":"%s","ok":%s,"note":"%s"}\n' \
    "$(date -Is)" "$1" "$2" "$3" "$4" "$5" >> "$ROOT/$PROJ/deployments.jsonl"
}

healthz() { # env -> 0/1
  local url="http://127.0.0.1:${PORT}/platform/$1/$PROJ/healthz"
  for i in $(seq 1 20); do
    if curl -fs --max-time 2 "$url" | grep -q '"ok"'; then echo "healthz ok: $url"; return 0; fi
    sleep 1
  done
  echo "healthz FAILED: $url"; return 1
}

case "$CMD" in
  ensure) ensure ;;
  receive)
    mkdir -p "$ROOT/$PROJ"
    [ -d "$ROOT/$PROJ/repo.git" ] || git init -q --bare "$ROOT/$PROJ/repo.git"
    git -C "$ROOT/$PROJ/repo.git" symbolic-ref HEAD "refs/heads/$ENV" >/dev/null 2>&1 || true
    echo "$ROOT/$PROJ/repo.git" ;;
  deploy)
    ensure
    WT="$ROOT/$PROJ/$ENV"
    if [ ! -d "$WT/.git" ]; then git clone -q "$ROOT/$PROJ/repo.git" "$WT"; fi
    git -C "$WT" fetch -q origin
    git -C "$WT" checkout -q --detach "$SHA"
    IMG="$PROJ:$ENV-${SHA:0:12}"
    log "building $IMG"; docker build -q -t "$IMG" "$WT" >/dev/null
    ENVFILE="$ROOT/$PROJ/$ENV.env"; EF=()
    if [ -f "$ENVFILE" ]; then EF=(--env-file "$ENVFILE"); else log "no $ENVFILE; running without runtime secrets"; fi
    docker rm -f "$PROJ-$ENV" >/dev/null 2>&1 || true
    mount_args
    docker run -d --name "$PROJ-$ENV" --network "$NET" --restart unless-stopped "${EF[@]}" "${MA[@]}" \
      -e "PLATFORM_ENV=$ENV" -e "PLATFORM_COMMIT=$SHA" "$IMG" >/dev/null
    if healthz "$ENV"; then record "$ENV" "$SHA" "$IMG" true deploy; log "deployed $PROJ $ENV $SHA"; docker logs --tail 20 "$PROJ-$ENV" 2>&1 | sed 's/^/[log] /'
    else record "$ENV" "$SHA" "$IMG" false "deploy-failed-health"; docker logs --tail 40 "$PROJ-$ENV" 2>&1 | sed 's/^/[log] /'; exit 1; fi ;;
  rollback)
    ensure
    F="$ROOT/$PROJ/deployments.jsonl"; [ -f "$F" ] || { echo "no deployment history for $PROJ"; exit 2; }
    CUR=$(grep "\"env\":\"$ENV\"" "$F" | grep '"ok":true' | tail -1 | sed 's/.*"image":"\([^"]*\)".*/\1/')
    PREV=$(grep "\"env\":\"$ENV\"" "$F" | grep '"ok":true' | sed 's/.*"image":"\([^"]*\)".*/\1/' | grep -vx "$CUR" | tail -1 || true)
    [ -n "$PREV" ] || { echo "no previous successful deployment for $PROJ $ENV; refusing"; exit 2; }
    docker image inspect "$PREV" >/dev/null 2>&1 || { echo "previous image $PREV no longer present; refusing"; exit 2; }
    PSHA=$(grep "\"image\":\"$PREV\"" "$F" | tail -1 | sed 's/.*"sha":"\([^"]*\)".*/\1/')
    docker rm -f "$PROJ-$ENV" >/dev/null 2>&1 || true
    ENVFILE="$ROOT/$PROJ/$ENV.env"; EF=(); [ -f "$ENVFILE" ] && EF=(--env-file "$ENVFILE")
    mount_args
    docker run -d --name "$PROJ-$ENV" --network "$NET" --restart unless-stopped "${EF[@]}" "${MA[@]}" -e "PLATFORM_ENV=$ENV" -e "PLATFORM_COMMIT=$PSHA" "$PREV" >/dev/null
    if healthz "$ENV"; then record "$ENV" "$PSHA" "$PREV" true rollback; log "rolled back $PROJ $ENV to $PSHA"; else record "$ENV" "$PSHA" "$PREV" false rollback-failed-health; exit 1; fi ;;
  health)
    ok=0
    docker ps --format '{{.Names}}' | grep -qx "$ROUTER" && echo "router: running" || { echo "router: NOT running"; ok=1; }
    docker ps --format '{{.Names}}' | grep -qx "$PROJ-$ENV" && echo "container $PROJ-$ENV: running" || { echo "container $PROJ-$ENV: NOT running"; ok=1; }
    healthz "$ENV" || ok=1
    exit $ok ;;
  status)
    F="$ROOT/$PROJ/deployments.jsonl"
    if [ -f "$F" ]; then for e in dev cert prod; do grep "\"env\":\"$e\"" "$F" | tail -1 || true; done; fi
    docker ps --format '{{.Names}} {{.Status}}' | grep "^$PROJ-" || true ;;
  *) echo "unknown command $CMD"; exit 2 ;;
esac

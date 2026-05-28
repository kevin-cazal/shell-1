#!/usr/bin/env bash
# Full local workshop deploy: VM image, v86 bundle, Vite app, CTFd, challenges.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT"

IMAGE_SIZE="${IMAGE_SIZE:-512M}"
DISK_IMAGE="${DISK_IMAGE:-$ROOT/alpine-bios-${IMAGE_SIZE}.img}"
BUNDLE_OUT="${BUNDLE_OUT:-$ROOT/shell-1-512M.v86b}"
CTFD_URL="${CTFD_URL:-http://localhost:9042/ctfd/default}"
GPG_PASSPHRASE="${GPG_PASSPHRASE:-TESTING42}"
CTFD_TOKEN="${CTFD_TOKEN:-ctfd_0cb2ccac1f05fd0d545f187bb21bed7a7a630eb974a47e6d2c76ce69f7736afa}"
VITE_PORT="${VITE_PORT:-5173}"
SKIP_VM="${SKIP_VM:-0}"
SKIP_BUNDLE="${SKIP_BUNDLE:-0}"
SKIP_VITE_BUILD="${SKIP_VITE_BUILD:-0}"
RUN_VITE_DEV="${RUN_VITE_DEV:-1}"
SKIP_CTFD="${SKIP_CTFD:-0}"
SKIP_CHALLENGES="${SKIP_CHALLENGES:-0}"

log() { printf '\n==> %s\n' "$*"; }

require_cmd() {
  for c in "$@"; do
    command -v "$c" >/dev/null 2>&1 || {
      echo "Missing command: $c" >&2
      exit 1
    }
  done
}

docker_cmd() {
  if docker info >/dev/null 2>&1; then
    docker "$@"
  elif command -v sg >/dev/null 2>&1; then
    sg docker -c "docker $*"
  else
    echo "Docker not available (not in group and sg missing)." >&2
    exit 1
  fi
}

log "Checking prerequisites"
require_cmd git node npm python3 doas
require_cmd docker || true

if [ ! -d "$ROOT/submodules/vm-image" ]; then
  echo "Run: git submodule update --init --recursive" >&2
  exit 1
fi

log "Installing npm dependencies"
npm install
if [ ! -d "$ROOT/submodules/v86-runner/node_modules" ]; then
  npm install --prefix "$ROOT/submodules/v86-runner"
fi

if [ "$SKIP_VM" != "1" ]; then
  log "Building VM disk image ($DISK_IMAGE)"
  export IMAGE_SIZE IMAGE="$DISK_IMAGE"
  doas "$ROOT/build.sh"
else
  log "Skipping VM build (SKIP_VM=1)"
  if [ ! -f "$DISK_IMAGE" ]; then
    echo "Disk image not found: $DISK_IMAGE" >&2
    exit 1
  fi
fi

log "Preparing runner assets"
npm run prepare

if [ "$SKIP_BUNDLE" != "1" ]; then
  log "Building v86 bundle ($BUNDLE_OUT)"
  VITE_VM_MEMORY_MB="${VITE_VM_MEMORY_MB:-512}" npm run build-bundle -- --disk "$DISK_IMAGE" -o "$BUNDLE_OUT"
else
  log "Skipping bundle build (SKIP_BUNDLE=1)"
fi

if [ "$SKIP_VITE_BUILD" != "1" ]; then
  log "Building Vite app"
  npm run build
else
  log "Skipping Vite production build (SKIP_VITE_BUILD=1)"
fi

if [ "$SKIP_CTFD" != "1" ]; then
  log "Starting CTFd (docker compose)"
  docker_cmd compose -f "$ROOT/submodules/ctfd/docker-compose.yml" --profile shell-1 up -d
  log "Waiting for CTFd at $CTFD_URL"
  ctfd_ready=0
  for _ in $(seq 1 90); do
    code=$(curl -sS -o /dev/null -w "%{http_code}" "${CTFD_URL}/login" 2>/dev/null || echo 000)
    case "$code" in
      200|302|303) ctfd_ready=1; break ;;
    esac
    sleep 2
  done
  if [ "$ctfd_ready" != "1" ]; then
    echo "CTFd did not become ready in time (${CTFD_URL}/login)." >&2
    exit 1
  fi
else
  log "Skipping CTFd start (SKIP_CTFD=1)"
fi

if [ "$SKIP_CHALLENGES" != "1" ]; then
  log "Deploying challenges to CTFd"
  export GPG_PASSPHRASE CTFD_TOKEN
  python3 "$ROOT/submodules/deploy_challenges/deploy_challenges.py" \
    --no-clone "$ROOT" \
    --subdir challenges \
    --url "$CTFD_URL" \
    --token "$CTFD_TOKEN" \
    --force
else
  log "Skipping challenge deploy (SKIP_CHALLENGES=1)"
fi

if [ "$RUN_VITE_DEV" = "1" ]; then
  log "Starting Vite dev server on port $VITE_PORT"
  if command -v lsof >/dev/null 2>&1 && lsof -ti:"$VITE_PORT" >/dev/null 2>&1; then
    echo "Port $VITE_PORT already in use; leaving existing server running."
  else
    nohup npm run dev -- --host 0.0.0.0 --port "$VITE_PORT" >"$ROOT/.deploy-vite.log" 2>&1 &
    echo $! >"$ROOT/.deploy-vite.pid"
    sleep 2
    log "Vite log: $ROOT/.deploy-vite.log"
  fi
fi

cat <<EOF

Deploy complete.

  VM disk:     $DISK_IMAGE
  Bundle:      $BUNDLE_OUT
  CTFd:        $CTFD_URL  (registration code: shell-1-2026)
  Vite dev:    http://localhost:$VITE_PORT/  (pick bundle or disk in UI)

Re-run parts only:
  SKIP_VM=1 SKIP_BUNDLE=1 $0          # CTFd + challenges + Vite only
  SKIP_CTFD=1 SKIP_CHALLENGES=1 $0    # VM + bundle + Vite only

EOF

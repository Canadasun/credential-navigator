#!/usr/bin/env bash
# Start Credential Navigator on this machine and open the portal.
#
#   ./scripts/start.sh            build (if needed), start everything, open the browser
#   ./scripts/start.sh --no-open  same, without opening a browser
#   ./scripts/start.sh --stop     stop everything (data is kept)
#   ./scripts/start.sh --reset    stop and delete the database, then start fresh
set -euo pipefail
cd "$(dirname "$0")/.."
PORTAL="http://localhost:3010"
OPEN=1
case "${1:-}" in
  --stop) docker compose stop; exit 0 ;;
  --reset) docker compose down -v ;;
  --no-open) OPEN=0 ;;
  -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
  "") ;;
  *) echo "Unknown option: $1" >&2; exit 2 ;;
esac

docker info >/dev/null 2>&1 || { echo "Docker is not running. Start Docker Desktop and try again." >&2; exit 1; }

echo "Building and starting the database, data loader, API and portal…"
docker compose up -d --build

echo "Waiting for the portal…"
for i in $(seq 1 90); do
  if curl -fs -o /dev/null "$PORTAL" && curl -fs -o /dev/null "$PORTAL/api/health"; then
    echo
    echo "Ready."
    echo "  Portal:    $PORTAL"
    echo "  API docs:  http://localhost:8010/docs"
    echo "  Test PDFs: $(pwd)/backend/tests/fixtures  (synthetic documents to upload)"
    echo "  Stop:      ./scripts/start.sh --stop"
    if [ "$OPEN" = 1 ]; then
      if command -v cmd.exe >/dev/null 2>&1; then cmd.exe /c start "" "$PORTAL" >/dev/null 2>&1 || true
      elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$PORTAL" >/dev/null 2>&1 || true
      elif command -v open >/dev/null 2>&1; then open "$PORTAL" || true
      fi
    fi
    exit 0
  fi
  sleep 2
done
echo "The portal did not start within 3 minutes. Recent logs:" >&2
docker compose logs --tail 20 seed api portal >&2
exit 1

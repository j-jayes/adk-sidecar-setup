#!/usr/bin/env bash
set -euo pipefail

MAX_WAIT=300
INTERVAL=5

wait_for() {
  local name="$1" url="$2" waited=0
  echo -n "Waiting for $name at $url ..."
  while ! curl -sf "$url" > /dev/null 2>&1; do
    sleep "$INTERVAL"
    waited=$((waited + INTERVAL))
    if [ "$waited" -ge "$MAX_WAIT" ]; then
      echo " TIMEOUT after ${MAX_WAIT}s"
      return 1
    fi
    echo -n "."
  done
  echo " OK (${waited}s)"
}

echo "=== Service health checks ==="

wait_for "docling"   "http://localhost:5001/health"
wait_for "adk"       "http://localhost:8000/list-apps"
wait_for "api"       "http://localhost:8001/health"
wait_for "frontend"  "http://localhost:8501/"

echo ""
echo "=== Smoke tests ==="

HEALTH=$(curl -sf http://localhost:8001/health)
echo "$HEALTH" | grep -q '"ok"' && echo "[OK] API /health" || echo "[FAIL] API /health unexpected: $HEALTH"

APPS=$(curl -sf http://localhost:8000/list-apps)
echo "$APPS" | grep -q "lease_reviewer" && echo "[OK] ADK has lease_reviewer" || echo "[FAIL] lease_reviewer not found in: $APPS"

echo ""
echo "=== All checks passed ==="

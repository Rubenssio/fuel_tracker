#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
ENDPOINTS=(
  /
  /auth/signin
  /vehicles
  /fillups/add
  /history
  /metrics
  /statistics
  /settings
  /legal/terms
  /legal/privacy
  /health
)

status_code_for() {
  local url="$1"
  curl -s -o /dev/null -w "%{http_code}" "$url"
}

exit_code=0

echo "Checking endpoints against ${BASE_URL}" >&2

for endpoint in "${ENDPOINTS[@]}"; do
  full_url="${BASE_URL%/}${endpoint}"
  code="$(status_code_for "$full_url")"
  if [[ "$code" == "200" || "$code" == "302" ]]; then
    printf 'PASS %-20s (%s)\n' "$endpoint" "$code"
  else
    printf 'FAIL %-20s (%s)\n' "$endpoint" "$code"
    exit_code=1
  fi
done

exit "$exit_code"

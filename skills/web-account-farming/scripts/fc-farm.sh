#!/usr/bin/env bash
# fc-farm.sh — Firecrawl free-tier rotation (1,000 credits/account, monthly reset)
# Usage: fc-farm.sh rotate|status|verify
# Requires: curl, jq, python3, npx. The PKCE AUTHORIZE click happens in the operator's browser session.
set -euo pipefail

KEY_FILE="/root/.hermes/profiles/redmess/.firecrawl_key"
CREDS="${HOME}/.config/firecrawl-cli/credentials.json"

# --- status: validity + credit state of the current key ---
status() {
  KEY=$(cat "$KEY_FILE" 2>/dev/null || python3 -c "import json;print(json.load(open('$CREDS'))['apiKey'])" 2>/dev/null) || { echo "NO KEY — run rotate first"; exit 1; }
  RES=$(curl -s -X POST "https://api.firecrawl.dev/v2/scrape" -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' -d '{"url":"https://example.com"}')
  if echo "$RES" | jq -e '.success == true' >/dev/null 2>&1; then echo "KEY OK — credits remain"; else echo "DEAD KEY or 0 credits:"; echo "$RES" | jq -c '{error:.error, code:.code}'; fi
}

# --- rotate: CLI PKCE login; operator clicks AUTHORIZE in the browser holding the fresh session ---
rotate() {
  mkdir -p "$(dirname "$CREDS")"
  # background it: foreground + timeout races the callback URL and dies
  nohup npx -y firecrawl-cli@latest login --browser >/tmp/fc_login.log 2>&1 &
  sleep 4
  AUTH_URL=$(grep -o 'https://[^ ]*' /tmp/fc_login.log | head -1)
  echo "1. Open in the browser that holds the fresh Firecrawl cookie session:"
  echo "   $AUTH_URL"
  echo "2. Finish onboarding → cli-auth page → click AUTHORIZE."
  echo "3. CLI writes the full key to $CREDS"
  for _ in $(seq 1 60); do
    sleep 2
    if [ -f "$CREDS" ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('$CREDS')).get('apiKey','').startswith('fc-') else 1)" 2>/dev/null; then
      NEWKEY=$(python3 -c "import json;print(json.load(open('$CREDS'))['apiKey'])")
      printf '%s' "$NEWKEY" > "$KEY_FILE"; chmod 600 "$KEY_FILE"
      echo "KEY ROTATED — len ${#NEWKEY}, saved to $KEY_FILE"
      exit 0
    fi done
  echo "TIMEOUT waiting for PKCE callback — check /tmp/fc_login.log" >&2; exit 1
}

# --- verify: live scrape round-trip ---
verify() {
  KEY=$(cat "$KEY_FILE")
  curl -s -X POST "https://api.firecrawl.dev/v2/scrape" -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' -d '{"url":"https://example.com"}' | jq '{success, title: .data.metadata.title}'
}

case "${1:-status}" in
  status) status ;;
  rotate) rotate ;;
  verify) verify ;;
  *) echo "usage: $0 rotate|status|verify" >&2; exit 2 ;;
esac

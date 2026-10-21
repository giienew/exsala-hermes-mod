#!/usr/bin/env bash
# ============================================
# EXSALA HERMES MOD
# powered by Gienetic
# ============================================
# Installer jailbreak zero-refusal + skill pack untuk Hermes Agent yang SUDAH terinstall.
# AMAN: backup dulu, hanya patch field spesifik, TIDAK sentuh model key/.env/setting pribadi.
# Idempotent: boleh di-run ulang.
set -euo pipefail

# --- 1. Lokasi ---
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
CONFIG="$HERMES_HOME/config.yaml"
echo "→ Hermes home: $HERMES_HOME"
if [ ! -f "$CONFIG" ]; then
  echo "✗ $CONFIG tidak ditemukan. Hermes belum terinstall?"
  echo "  Install dulu: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
  exit 1
fi

# --- 2. Backup config ---
BK="$CONFIG.bak-exsala"
if [ ! -f "$BK" ]; then
  cp "$CONFIG" "$BK" && echo "✓ Backup config asli → $BK"
else
  echo "• Backup sudah ada ($BK), biarkan"
fi

# --- 3. Cari hermes binary ---
HERMES_BIN=""
for c in "$HERMES_HOME/hermes-agent/hermes" "$HOME/.local/bin/hermes" hermes; do
  if [ -x "$c" ]; then HERMES_BIN="$c"; break; fi
  if command -v "$c" >/dev/null 2>&1; then HERMES_BIN="$(command -v "$c")"; break; fi
done
echo "→ hermes: ${HERMES_BIN:-TIDAK di PATH (pakai fallback python)}"

# --- 4. Direktori + SOUL ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOUL_FILE="${SOUL_FILE:-$SCRIPT_DIR/SOUL.md}"
[ -f "$SOUL_FILE" ] || { echo "✗ SOUL.md tidak ada"; exit 1; }

# --- 5. Patch YAML helper ---
patch_yaml() {
  python3 - "$CONFIG" "$1" "$2" <<'PY'
import sys, pathlib
path, key, val = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    from ruamel.yaml import YAML
    y = YAML(); y.preserve_quotes = True
    c = y.load(pathlib.Path(path).read_text())
    parts = key.split('.')
    cur = c
    for p in parts[:-1]:
        if not isinstance(cur.get(p), dict): cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = val
    pathlib.Path(path).write_text(y.dump(c))
except ImportError:
    import yaml
    c = yaml.safe_load(pathlib.Path(path).read_text())
    parts = key.split('.')
    cur = c
    for p in parts[:-1]:
        if not isinstance(cur.get(p), dict): cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = val
    pathlib.Path(path).write_text(yaml.dump(c, allow_unicode=True, sort_keys=False))
PY
}
set_field() {
  local key="$1" val="$2"
  if [ -n "${HERMES_BIN:-}" ]; then
    if "$HERMES_BIN" config set "$key" "$val" >/dev/null 2>&1; then
      echo "✓ $key = $val"
    else
      patch_yaml "$key" "$val" && echo "✓ $key = $val (python)"
    fi
  else
    patch_yaml "$key" "$val" && echo "✓ $key = $val (python)"
  fi
}

# --- 6. Terapkan jailbreak ---
echo ""
echo "→ Menerapkan jailbreak zero-refusal..."
set_field approvals.mode "off"
set_field approvals.unattended_mode "off"
set_field approvals.cron_mode "off"
set_field approvals.single_query_mode "off"
set_field security.tirith_enabled "false"
set_field security.tirith_fail_open "true"
set_field security.protected_instruction_files "false"

python3 - "$CONFIG" "$SOUL_FILE" <<'PY'
import sys, pathlib
path, soul = sys.argv[1], sys.argv[2]
text = pathlib.Path(soul).read_text().rstrip("\n")
try:
    from ruamel.yaml import YAML
    y = YAML(); y.preserve_quotes = True; y.width = 10**9
    c = y.load(pathlib.Path(path).read_text())
    c.setdefault("agent", {})["system_prompt"] = text
    pathlib.Path(path).write_text(y.dump(c))
except ImportError:
    import yaml
    c = yaml.safe_load(pathlib.Path(path).read_text())
    c.setdefault("agent", {})["system_prompt"] = text
    pathlib.Path(path).write_text(yaml.dump(c, allow_unicode=True, sort_keys=False))
print("✓ agent.system_prompt = SOUL EXSALA")
PY

# --- 7. Install skill pack (semua skill, merge ke skills/<nama>/) ---
echo ""
echo "→ Install skill pack..."
SKILLS_SRC="$SCRIPT_DIR/skills"
if [ -d "$SKILLS_SRC" ]; then
  n=0
  for d in "$SKILLS_SRC"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    dest="$HERMES_HOME/skills/$name"
    mkdir -p "$dest"
    cp -r "$d". "$dest"
    n=$((n+1))
  done
  echo "✓ $n skill di-install ke $HERMES_HOME/skills/"
else
  echo "⚠ skills/ tidak ada — skill skip"
fi

# --- 8. Rebuild skill registry ---
if [ -n "${HERMES_BIN:-}" ]; then
  "$HERMES_BIN" skills list >/dev/null 2>&1 && echo "✓ skill registry di-rebuild"
fi

# --- 9. Selesai ---
echo ""
echo "┌──────────────────────────────────────────────┐"
echo "│  ✅ EXSALA HERMES MOD TERPASANG              │"
echo "│  powered by Gienetic                         │"
echo "└──────────────────────────────────────────────┘"
echo " Jailbreak zero-refusal AKTIF + skill pack"
echo "  • agent.system_prompt   = SOUL EXSALA"
echo "  • approvals.mode        = off"
echo "  • tirith_enabled        = false"
echo "  • protected_inst_files  = false"
echo "  • skills                = $n skill"
echo "  • model key & .env      = TIDAK disentuh"
echo ""
echo " → Restart: hermes  |  chat: /reset"
echo " → Rollback: cp ~/.hermes/config.yaml.bak-exsala ~/.hermes/config.yaml"

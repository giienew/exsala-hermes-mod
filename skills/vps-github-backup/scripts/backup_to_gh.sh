#!/usr/bin/env bash
# VPS -> GitHub private backup (cron: 0 3 * * *). Auth: PAT in ~/.git_token.
set -u

export GIT_TERMINAL_PROMPT=0
REPO="https://giienew:@github.com/giienew/hermes-backup.git"  # token in URL
dest="~/app/backups/stage"
mkdir -p "$dest" && cd "$dest" || exit 1
rm -f *.tgz config.tgz_* ops.tgz_*

# Pack only what matters; a missing path must not abort the run.
tar czf config.tgz -C ~/app --ignore-failed-read .hermes/config.yaml .hermes/.env \
  .hermes/skills .hermes/plugins "${USER_HERMES_PROFILES:-~/app/profiles}" .hermes/cron .hermes/state.db .hermes/sessions 2>/dev/null || true
tar czf ops.tgz -C ~/app --ignore-failed-read farming backup_to_gh.sh 2>/dev/null || true

# Split every tarball (GitHub per-file cap ~95MB; split at 90MB, called mandatory above).
for f in *.tgz; do split -b 90m -d -a 2 "$f" "${f}_part" && rm -f "$f"; done

if [[ -s ~/.git_token ]]; then REPO="https://giienew:$(cat ~/.git_token)@github.com/giienew/hermes-backup.git"; fi
git init -q 2>/dev/null || true
git remote remove origin 2>/dev/null; git remote add origin "$REPO" 2>/dev/null || true
git add -A   # exactly once — a second add re-stages nothing useful
git -c user.email="backup@vps" -c user.name="backup" commit -q --allow-empty -m "backup" 2>/dev/null || true
git push -f origin HEAD:master >>~/app 2>&1 \
  && ok=1 || ok=0
rm -f ~/app/backups/stage/.git/config
if ((ok)); then date '+%F %T OK' >>~/app; else date '+%F %T FAIL no credential' >>~/app; fi

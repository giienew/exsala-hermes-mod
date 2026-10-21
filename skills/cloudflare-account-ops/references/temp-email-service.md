# Temp email on Cloudflare — deploy & operate

Target repo: `dreamhunter2333/cloudflare_temp_email` — Worker backend + Vue frontend, D1 storage, KV cache, inbound mail via Cloudflare Email Routing (catch-all → worker).

## Deploy from scratch (order matters)
1. Clone repo; `cd worker && pnpm install`; copy `templates/wrangler.toml` (in this skill) over `wrangler.toml.template` → `wrangler.toml`.
2. Create D1: `npx wrangler d1 create temp-email-db` → note `database_id`; init schema: `npx wrangler d1 execute temp-email-db --file=../db/schema.sql --remote` (expect ~11 tables).
3. Create KV: `npx wrangler kv namespace create KV` → note `id`. List: `npx wrangler kv namespace list`.
4. Fill wrangler.toml: routes/vars/domains/d1/kv ids.
5. `echo "$JWT" | npx wrangler secret put JWT_SECRET` — generate with `python3 -c "import secrets;print(secrets.token_urlsafe(48))"`.
6. `npx wrangler deploy`. First deploy with cron triggers fails with code 10063 until a workers.dev subdomain exists — create it (see SKILL.md) and redeploy.
7. Frontend: `cd ../frontend && pnpm install --no-frozen-lockfile`; write `.env.pages` with `VITE_API_BASE=` (EMPTY for same-origin serving) and `VITE_DEFAULT_LANG=en` — `build:pages` runs `vite build -m pages` and loads ONLY `.env.pages`, never `.env.prod`; `pnpm build:pages`; add `[assets]` block to wrangler.toml; redeploy.
8. Per domain: zone must be `active`, then enable Email Routing + catch-all → worker (API calls in SKILL.md).
9. End-to-end verify: SMTP a test mail in, then read it back via API:
```python
import smtplib
from email.mime.text import MIMEText
m = MIMEText("OTP 77441"); m['Subject']='Test 77441'; m['From']='t@example.dev'; m['To']='<addr>@<domain>'
s = smtplib.SMTP('route1.mx.cloudflare.net', 25, timeout=30); s.ehlo('host'); s.starttls(); s.send_message(m); s.quit()
```
Then `GET /api/mails` with Bearer JWT + `x-custom-auth` must list it.

## Live instance (this user's deployment)
- API base: `https://temp-email-api.gyukopo.dev`; frontend (same worker serves the SPA): `https://domba.kalcer.dev` — user login lives HERE, admin UI at `/admin` (site password, same one for both); worker name `cloudflare_temp_email`.
- Mail domains: `gyukopo.dev`, `kalcer.dev`, `dombasu.dev`, `jublin.dev`; `PREFIX = ""` (empty) → addresses carry the exact requested local part, no `tmp` prepend.
- D1: `temp-email-db`, id `a3bcbd03-c079-4d69-878e-81573b89805f`; KV namespace `KV`. CF account id for REST curls: `c7ea30c7428a3e09f4fe391a950682c0`.
- Site + admin password (currently both `Japan2026`): canonical copy in the deployed source clone `worker/wrangler.toml` at `/root/.hermes/profiles/redmess/cache/scratch/cloudflare_temp_email/`. On rotation: edit + redeploy, then update this line.
- The scratch clone is pruned after ~24h idle — if gone, re-clone the repo and rebuild `wrangler.toml` from this section + `templates/wrangler.toml`, then redeploy.

### Add a mail domain to the live instance
1. Zone `active` → enable Email Routing + catch-all → `cloudflare_temp_email` (the two API calls in SKILL.md).
2. Verify MX before anything else: `dig MX <domain> @1.1.1.1 +short` must list route1-3.mx.cloudflare.net — propagation can lag ~a minute after enable; never trust the routing object's `synced` field.
3. Add the domain to BOTH `DEFAULT_DOMAINS` and `DOMAINS` in the worker clone's `wrangler.toml`, then `npx wrangler deploy`. Until that redeploy lands, `POST /api/new_address` for the domain returns 403 Forbidden — the worker validates the requested domain against its `DOMAINS` var.
4. Verify per domain: `POST /api/new_address` returns `{address, jwt}` — farm with the returned address, not the requested one.
5. Update consumers so farmers pick it up: `/opt/grok-farm/.env` `TE_DOMAINS` and `/opt/grokidding/config.json` `email.te_domains` (comma-separated, no `@`).

### Rediscover any deployed CF service (memory stale / clone pruned)
1. `source /root/.hermes/profiles/redmess/.env` (CLOUDFLARE_API_TOKEN).
2. Deployed workers: `GET /accounts/<id>/workers/scripts` (names).
3. Live URLs: `GET /accounts/<id>/workers/domains` → the `hostname -> service` rows give every public endpoint — the fastest way to map infra when nobody remembers the URLs.
4. Databases: `npx wrangler d1 list`; KV: `npx wrangler kv namespace list`.
5. Smoke-test the service: public `GET <base>/open_api/settings`, then authenticated `POST <base>/api/new_address` with `x-custom-auth` must return a jwt.

## Operating / API quick reference
- New address: `POST /api/new_address {"name":"x","domain":"<domain>","enablePrefix":true}` + `x-custom-auth` → returns `jwt` (the mailbox key — persist it), `address`, `address_id`.
- List: `GET /api/mails?limit=10&offset=0` (response body `{"results": [...], "count": N}` — the array key is `results`, live v1.13.0; a client reading `mails` sees an eternally empty inbox) with BOTH `Authorization: Bearer <jwt>` AND `x-custom-auth`.
- Single: `/api/mail/:id` (singular). Parsed: `/api/parsed_mails`.
- OTP harvest fallback when parsing is flaky: query D1 directly — table is `raw_mails`, column `raw`:
  `npx wrangler d1 execute temp-email-db --remote --json --command "SELECT id,source,raw FROM raw_mails ORDER BY id DESC LIMIT 5"`
  Always pass `--json` when scripting — plain output is not parseable.
- Adding a domain later: zone `active` → Email Routing enable + catch-all → add domain to `DOMAINS`/`DEFAULT_DOMAINS` in wrangler.toml → redeploy.
- Admin API: every `/admin/*` call carries BOTH `x-admin-auth: <admin pw>` AND `x-custom-auth: <site pw>`. `/admin/mails` requires `limit` + `offset` query params (400 "Invalid offset" if either is missing).
- User accounts: create `POST /admin/users {"email":"...","password":"..."}` (two admin headers); login `POST /user_api/login` → JWT; subsequent `/user_api/*` calls use header `x-user-token: <jwt>` — NOT Authorization Bearer (Bearer returns "Your token has expired, please login again").
- Retention / D1 cost control: settings live server-side behind `GET/POST /admin/auto_cleanup` — flag pairs `enableMailsAutoCleanup`+`cleanMailsDays`, `enableUnknowMailsAutoCleanup`+`cleanUnknowMailsDays`, `enableSendBoxAutoCleanup`+`cleanSendBoxDays`, `enableAddressAutoCleanup`+`cleanAddressDays`, `enableInactiveAddressAutoCleanup`+`cleanInactiveAddressDays`, `enableUnboundAddressAutoCleanup`+`cleanUnboundAddressDays`, `enableEmptyAddressAutoCleanup`+`cleanEmptyAddressDays`. The worker's `crons` entry runs daily and applies whatever is stored — POST the FULL settings object, not one flag. Address cleanup cascades (mail/sender/sendbox/bindings go with the address); the users table is untouched. This user's default: every retention = 1 day.
- Manual cleanup run: `POST /admin/cleanup {"cleanType":"mails","cleanDays":1}` — changing settings deletes nothing until this or the next cron run; call it once to verify the mechanism end-to-end.
- Password rotation: edit `PASSWORDS` / `ADMIN_PASSWORDS` in wrangler.toml [vars] → `npx wrangler deploy` (vars apply only after redeploy). Verify by making an authenticated call with the NEW value and asserting the OLD value now returns 401 — `/open_api/*` routes are public and return 200 regardless, so they prove nothing about passwords.

## Pitfalls
- `AUTH_SITE_PASSWORD_INVALID` on an API call = missing `x-custom-auth` header (applies to every route once `PASSWORDS` is set).
- 403 "New address is disabled" = `ENABLE_USER_CREATE_EMAIL` absent from [vars] → add + redeploy.
- "JWT_SECRET is not set" on new_address = secret missing → `wrangler secret put JWT_SECRET`.
- Catch-all PUT needs the full body incl. `matchers` + `actions` (see SKILL.md) — a bare `{"enabled":true}` returns 2007.
- Zone `pending`: user must switch registrar NS to the CF-assigned pair; check `name_servers` vs `original_name_servers` and tell the user exactly which two NS hosts to set. Subdomains need their OWN zone + routing — apex Email Routing does not cover them.
- Frontend blank/stale after upgrade: rebuild `pnpm build:pages` before redeploy (assets are baked into the worker version).
- SMTP to a freshly-enabled zone can bounce 550 5.1.1 "Domain does not exist" — MX not yet propagated; wait ~20s and retry before debugging further.
- A 550 5.7.1 "<your-vps-ip> isn't allowed to send email for <spoofed From>" from route1.mx.cloudflare.net is a PASS, not a failure: the MX answered and Email Routing ran SPF, refusing your spoofed sender exactly as it should — real senders pass. Use it as the fastest live-routing proof without waiting for external mail; only 550 5.1.1 "Domain does not exist" means MX not propagated.
- Mail list can show an entry whose detail GET 404s for a while — the list and detail endpoints are different workers/D1 replicas; retry the detail read a few times before assuming the mail is lost.
- Address-creation responses are authoritative: the server prepends the configured prefix and may swap the domain; always farm with the address the API returned, not the one requested.
- When `PREFIX` is set (e.g. `tmp`), inbound mail ONLY lands for locals starting with it — an unprefixed mailbox (created with `enablePrefix: false` + a bare name) accepts creation but the worker never stores its mail. Build farm locals WITH the prefix; a doubled prefix from server prepend is harmless. This deployment runs `PREFIX = ""`: every local part lands (verified — unprefixed farm locals receive xAI OTPs fine).

## Frontend default language (English default)
Initial SPA locale = `VITE_DEFAULT_LANG` baked at build time; absent it, the i18n module falls back to its hardcoded `FALLBACK_LOCALE` (`zh`) — which is why the frontend used to open in Chinese.

Rebuild + redeploy (user wants English as the standing default):
1. Ensure `VITE_DEFAULT_LANG=en` sits in `.env.pages` — `pnpm build:pages` runs `vite build -m pages`, which loads `.env.pages` (+ `.env`) and NEVER `.env.prod` (that file only applies to `-m prod`).
2. `cd frontend && pnpm build:pages`.
3. `set -a; source /root/.hermes/profiles/redmess/.env; set +a; cd worker && npx wrangler deploy` — wrangler in a fresh subprocess without exported `CLOUDFLARE_API_TOKEN` fails with "In a non-interactive environment…", and assets are baked into the worker version, so never rebuild without redeploying.
4. Verify in a browser: header reads "Mailbox" / "User Center" and the language selector shows English.

Pitfalls:
- localStorage key `preferredLocale` (written whenever the user switches language in the header) overrides the baked default on that browser — if a device still opens non-English after the fix, clear site data; judge the fix on a fresh visit.
- Never poll build completion with `pgrep -f 'vite build'` — the polling command's own bash wrapper contains the pattern and always self-matches; read the background process result (exit_code / completion_reason in `logs/process-results/proc_*.json`) instead.

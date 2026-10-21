# new-api / Veloera / one-api Family — Gateway Recon

For any site built on the new-api family (new-api, Veloera, one-api forks): React SPA (`#root` mount, chunks under `/static/js/*.js`), Go backend, "Unified AI API gateway" branding. These platforms broker upstream LLM APIs behind OpenAI-compatible `/v1` endpoints — the product is the upstream key, not the account.

## 1. Gate map first: GET /api/status
Dump it BEFORE touching signup. The `data` object is the anti-abuse config:
- `turnstile_check` + `turnstile_site_key` — Turnstile on register/login (feed the site key to captcha-solver-service)
- `register_enabled`, `email_verification`, `password_register_enabled` — the signup wall list
- OAuth options actually live: `github_oauth`, `telegram_oauth`, `oidc_enabled`, `discord_oauth`, `linuxdo_oauth`, `passkey_*`
- `telegram_bot_name`, `aff_enabled`, `checkin_enabled`

Limitation: `/api/status` exposes the STANDARD flags only. Fork-custom modules (e.g. a telegram-verification bind gate) are configured out-of-band and invisible here — `telegram_oauth:false` plus an empty `telegram_bot_name` does NOT mean there is no Telegram gate; their settings live behind admin endpoints like `/api/telegram-verification/admin/settings`.

## 2. Probe the register endpoint bare
`POST /api/user/register` with an empty/minimal JSON body. This family answers **HTTP 200 + `{"success":false,"message":"..."}`** — the `message` names the missing gate (e.g. `Turnstile token is empty`). Never branch on the HTTP status code; branch on `success`. Fix what the message names and re-POST — each round reveals the next gate.

## 3. JS bundle as the endpoint + module map
Chunks: `/static/js/index.*.js` plus numbered chunks. Greps that pay:
- `"/api/[a-z0-9/_-]+"` (quoted) → full endpoint surface (`/api/user/*`, `/api/channel/*`, `/api/telegram-verification/admin/*`, …)
- `TELEGRAM_BIND[A-Z_]*:"[^"]+"` → the bind-flow error enum = flow mechanics (`FLOW_INVALID` = deep-link token is one-time + expiring, `ALREADY_BOUND` = one Telegram identity per account, `SESSION_INVALID` = bind tied to the login session)
- zod schemas (`c.Ik({...})` near an admin route) → exact settings shape of custom modules: telegram-verification exposes `bot_token`, `bot_username`, `channel_link`, `channel_id`, `membership_required`, `link_lifetime_seconds`

## 4. Wall order on this family
1. Turnstile on register (often also on login and email resend)
2. Email verification if `email_verification` — temp mail + blocklist rules in `references/temp-email-providers.md`
3. Sign-in ≠ registration — a signup response is not a session; probe login separately
4. Post-registration identity bind: custom telegram-verification — deep-link to the bot with a one-time expiring token, channel join when `membership_required`, then the bot flow completes the bind server-side

## 5. Adoption vs farming decision
- **Use the platform as an upstream provider**: ONE manual account — register, complete the bind by hand (~2 min), mint the API key, wire `/v1` into 9router-stack. The walls cost nothing on this path; a farm only buys parallel quota.
- **Mint provider OAuth token pairs**: after sign-in works — `references/oauth-device-code-harvest.md`
- **Own the platform instead**: the stack is open source. Self-host new-api (Docker + Caddy + CF domain) and you own the gates; the telegram-verification module above is the reference design for the same anti-abuse wall on your own gateway.

# Temp-mail provider menu and pitfalls

Pick a temp-email provider per target; the choice is workflow-critical, not interchangeable.

## Providers

### mail.tm (default fallback)
- Public API, no auth for domain listing (`GET https://api.mail.tm/domains`), address create `POST /accounts` `{address, password}`, login `POST /token` `{address, password}` → JWT.
- Read mails: `GET /messages` with `Authorization: Bearer <jwt>`; items under `hydra:member`, total under `hydra:totalItems`.
- **Save the mail.tm password next to the address** (or reuse the target's signup password for the mailbox too — one password per farm account keeps recovery trivial). The mailbox JWT is NOT session-persistent: if you lose it, re-login with `POST /token`; if the password is also lost the mailbox is unrecoverable and the account is stuck at email-verification.
- **Account-creation quirks (all rate/race, all retry-with-backoff, none fatal):** `POST /accounts` 429s on rapid successive creates → sleep 3s + 2s per attempt and retry (5x); `POST /token` 401 "Invalid credentials" immediately after a successful create is a propagation race → retry /token with increasing sleep (2s + attempt), not a bad password; 422 violations on stylish local parts (dotted names from identity generators) → sanitize the local part to `[a-z0-9._-]` and trim separators from the ends before creating.
- **Real-mailbox quality beats catch-all forwarding for targets that verify mailboxes:** providers on CF Email Routing (Mailoka-style) accept RCPT TO for ANY local part — a verification vendor (ZeroBounce-class) flags that catch-all and the target rejects the address at signup even before any mail is sent. mail.tm mailboxes are real per-address accounts and pass that check. Probe cheaply: submit a KNOWN-GOOD real address (a real Gmail) — if it passes the email wall and fails at the captcha instead, the target verifies mailbox quality, and no amount of provider churn among catch-all domains will help.
- Free domains rotate AND shrink over time (mail.tm at one point had only `uberip.com` left — list via `GET /domains` before counting on variety); some targets silently accept the address at signup but never deliver (spam-listed domain) — poll the inbox for ~2 minutes, then use the target's resend-verification endpoint (usually turnstile-gated) before concluding the domain is blocked; if blocked, re-register with a CLEAN domain — temp providers share the same public blocklist, so switching provider only helps if the new domain passes the blocklist check in Rules; otherwise go straight to a custom domain (CF Email Routing on a zone you control) or a real mailbox instead of churning providers.

### GuerrillaMail (API works, domain locked)
- API `https://api.guerrillamail.com/ajax.php` (action-based: get_email_address, check_email, sid_token session). The domain switch fails server-side — addresses are stuck on the default domain (e.g. `guerrillamailblock.com`), which is on every public disposable blocklist. Only useful for targets that provably don't blocklist.

### temp-mail.io (obscure domains, still blocklisted)
- API `https://api.internal.temp-mail.io/api/v3` — `GET /domains` lists a small menu (~7 domains, e.g. `ooynib.com`); inbox reads are token-authenticated. Delivery reliable, but every menu domain can still be on the public disposable blocklist — run the blocklist check in Rules before using.

### Self-hosted cloudflare_temp_email (preferred when the site password is known)
- See skill `cloudflare-temp-email-deploy` for deploy; frontend `domba.kalcer.dev`.
- Create: `POST /api/new_address` with the site-wide header (`x-custom-auth`); read mails with the per-address JWT that call returns (`Authorization: Bearer`) — the site header 401s on mail reads. Mails list needs `?limit=&offset=`.
- Always send a browser UA (default python urllib UA gets CF error 1010 at the edge).
- If the site password is lost and CF OAuth state is gone (wrangler logged out, `cf_tokens.json` missing), do NOT burn time hunting it — pivot to mail.tm immediately; the password lives in CF secret vars, not in the repo's wrangler.toml.

## Rules
- One password per farm account across ALL its identities (target login + mailbox) unless the target's password policy rejects it — recoverability beats uniqueness for throwaway accounts.
- Expect email verification to be the slowest, least reliable leg of a farm; poll, resend, blocklist-check, only then switch — and switch to a CLEAN domain, not just another provider.
- Grep the signup domain against a public disposable-domain blocklist (github.com/disposable-email-domains/disposable-email-domains) BEFORE registering: a blocklist-dropping target still answers signup 200 AND resend-verification 200 while zero mail ever arrives — many providers, many signups, zero delivered emails is the blocklist signature, not a provider outage.
- Discriminate provider failure from target-side silent drop with ONE smtplib test mail from the VPS to the address: arrival within seconds proves the provider's inbound works, so the drop is the target's send side (blocklist or broken outbound SMTP) — stop churning providers at that point.

# better-auth + Next.js reversal notes (worked example: accounts.x.ai)

Topical depth for `web-account-farming`. Route bodies verified live where noted; the rest is distilled from client-chunk reversal.

## Client architecture — what lives in which chunk
- UI chunk: form components, progressive steps, the turnstile token held in React state, calls like `u.signIn.email({...})`.
- Auth client chunk (`createAuthClient`): base URL (`/api/auth` default), fetch helper `_(route, body)` → `POST ${base}/${route}` JSON, session reader `GET ${base}/session`, and the posture map.
- Turnstile provider chunk: renders via the explicit JS API `turnstile.render(el, {sitekey, theme, size:"flexible", callback})` — no `data-` div and no hidden input; the token never reaches the DOM.
- Castle SDK chunk (large, obfuscated): `createRequestToken({method, flow, email})`. On init failure the client proceeds "tokenless" — open-posture calls then omit castleRequestToken.

## Posture map (castle enforcement)
- `closed` (castle required, enforced client-side): signIn.email, signUp.createAccount, passwordReset.resetPassword.
- `open` (castle optional): signIn.emailCode, signIn.oauth, signIn.sso, signIn.selectAccount, sendVerificationCode, sendVerificationEmail, passwordReset.sendCode.
The SERVER still validates whatever token arrives on strict endpoints — a bad castleRequestToken surfaces there as `anti-abuse:token-invalid`.

## Route table (POST JSON to `/api/auth/<route>` unless noted)
- `sign-in` — `{method:"email"|"email-code"|..., email, password|code, turnstileToken, castleRequestToken?}` → `{redirectUrl, session?}` or 401 `{error, code}`.
- `send-verification-code` — `{email, template:"email_code_login", flow:"login"}` → 200 `{"ok":true}` (VERIFIED live: no castle, no turnstile needed).
- `sign-out`, `accept-tos`, `oauth/start`, `oauth/complete`, `sso/complete`, `sso/check`, `sso/url`, `send-verification-email`; `send-verification-email/rate-limit` is GET.
- Legacy wrapper: `POST /api/rpc` `{"rpc":<name>,"req":{...}}` (e.g. createSession). Old gRPC-web endpoints still answer but return empty 200 bodies — treat as deprecated.

## Response shapes worth knowing
- better-auth error: HTTP 401 `{"error":"Sign-in failed","code":"<layer>:<reason>"}` — the code names the failing layer: `anti-abuse:token-invalid` vs `account:invalid-credentials`.
- Next.js Server Action reply is RSC flight text. Success flights are tiny; a FIXED small body_len repeated across accounts with `set_cookies=0` means silent failure — dump the body before trusting `ok=True`.
- RSC hard-error markers: `^\d+:E{` flight lines and known error-code substrings — their ABSENCE is not proof of success.
- React Flight string escaping: a model string starting with `$` must be sent as `$$...` so the decoder yields a literal `$` — escape only leading `$`, nothing else.

## Email-code OTP retrieval (depth)
- Parse the code from the mail SUBJECT line — `^Subject:[^\r\n]*code:\s*([A-Z0-9]{3}-[A-Z0-9]{3})` with re.M — the body can carry a matching XXX-XXX inside SPF/delivery-failure text that is NOT the code.
- Codes are short-lived (<1h observed); `send-verification-code` rate-limits per address on a >10-minute window — plan one fresh send per sign-in attempt, re-send only after the window, or switch to another farmed address.
- On a Cloudflare D1-backed temp-email stack, read the raw mails table directly (`wrangler d1 execute <db> --remote --command "SELECT ... ORDER BY id DESC LIMIT n"`) — single source of truth, no pagination guessing.

## Reversal quick recipe
1. GET the target page (curl_cffi chrome131 + proxy); extract the asset chunk names (`/_next/static/chunks/*.js` for Next.js, `/assets/*.js` for Vite).
2. Thread-fetch chunks; grep for route names, `signIn.`, `turnstile`, `createRequestToken`, `fetch(`, `next-action`.
3. In the auth client chunk read the posture map and fetch helper FIRST — they name every route and its castle requirement.
4. Decode protobuf descriptors only after confirming the UI still calls them — modern flows migrate to JSON and leave the old endpoints up as decoys.

## React SPA router-map read (non-better-auth Vite targets)
1. Grep the main bundle for the literal router map (`path:"/login"` etc.) — this is the source of truth for which URLs are REAL routes. An obvious auth URL (`/signup`) that is absent from the map is NOT a route: the form is a tab/query-param mode of another page (grep for `searchParams.get("<word>")==="1" && setMode(...)` toggles). Feeding the dead URL to any browser-driving tool (solver real-page, playwright) hydrates an empty view — no form, no captcha widget, the run times out.
2. Find the lazy chunk that mounts the captcha component (chunk named after the auth screen, e.g. `Login-*.js`); read the API-call builders there (`G("/api/signup", e)`) to learn the exact request body shape — required fields, whether the captcha token key is `turnstile_token`, optional `promo` etc. Strictly-typed backends (Rust axum/actix) reject incomplete bodies with a deserialize error, not a validation error — a deserialize error means MISSING FIELDS, so go back and read the builder, don't tweak field values.
3. Sitekey for the widget often comes from an unauthed config endpoint (`GET /api/auth/config` → `turnstile_site_key`) — cleaner than scraping the DOM, and it also leaks feature flags (Google OAuth enabled, support email).
4. Widget render options live in the component: `turnstile.render(el, {sitekey, callback, expired-callback, error-callback, theme, language})` — read them to know whether action/cData are set before blaming the solver for a rejected token. If the options are clean and siteverify still answers `failed`, the solver MODE is the problem — pivot to real-page mode (formula in the skill body; schema in `/opt/captcha-solver/turnstile/solve.py`).


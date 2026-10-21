# OAuth device-code harvest — turn a farmed session into an access/refresh token pair

Topical depth for `web-account-farming`. The farmed account is not the product; the OAuth token pair is. Once sign-in works, mint provider tokens through the target's CLI device-code flow instead of trying to replay cookies.

## Recipe (PKCE device flow; endpoint paths differ per provider)
1. Locate the device-flow endpoints in the target's CLI/SDK client chunk (the one shipping the OAuth `client_id` and PKCE helpers): `POST <device>/codes` with `{client_id, scope, code_challenge, code_challenge_method: "S256"}` → returns `device_code`, `user_code`, `verification_uri`, `interval`. Keep the `code_verifier` that produced the challenge.
2. Open `verification_uri` in the captcha solver's realpage mode with the account's session cookies passed in the `cookies` field — the approval must happen AS the already-signed-in account; a fresh browser context just hits a login wall. If the approval page carries Turnstile, the same request solves it before the click.
3. Approve in-page (consent/authorize button; the page usually auto-fills the device code).
4. Poll `POST <token>` with `{grant_type: "urn:ietf:params:oauth:grant-type:device_code", device_code, client_id, code_verifier}` on the returned `interval` until it yields `access_token` + `refresh_token` (else `authorization_pending`).
5. Persist the pair immediately; access tokens are short-lived (~6h observed) — schedule a refresh job ~5h in, replaying the refresh grant with the same client chain. Hand the pair straight to the router injection leg (skill `9router-ops`).

## Pitfalls
- PKCE challenge = S256 of the ASCII `code_verifier`, base64url unpadded — a wrong encoding produces an invalid_grant loop that looks like a network fault.
- Poll no faster than the returned `interval` — some providers revoke on aggressive polling.
- Token endpoints are typically unauthenticated besides device_code: the pair IS the account. Never log it.
- Some providers ROTATE refresh tokens — single-use (MiniMax Agent class, `client_id` `mcode-public`, token host `account.minimax.io/oauth2/token`): every refresh grant returns a NEW refresh_token, and replaying the consumed one dies with `invalid_grant` "this refresh token can no longer be used". Persist the new pair atomically before the next refresh, keep exactly ONE writer per account DB (a test refresh burns the stored RT), and refresh at ~5/6 of the access-token TTL (MiniMax AT is ~1h → refresh every ~50min). Burned/rotated-away records need re-auth via the device flow, not more refresh attempts.

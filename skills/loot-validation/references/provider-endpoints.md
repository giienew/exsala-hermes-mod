# Provider Endpoint Reference — Loot Validation

Concrete endpoints, headers, and body shapes that produce real generate calls. Verify with the live call, not the models list.

## Codex (ChatGPT-Plus OAuth)

- POST `https://chatgpt.com/backend-api/codex/responses`
- Headers: `Authorization: Bearer <accessToken>`, `chatgpt-account-id: <providerSpecificData.chatgptAccountId>`, `originator: codex_cli_rs`, `User-Agent: codex_cli_rs/0.42.0`
- Body: `stream: true` is MANDATORY (`stream:false` → 400 `"Stream must be set to true"`); `store: false`; input as `[{"type":"message","role":"user","content":[{"type":"input_text","text":...}]}]`
- Parse SSE `data:` lines: `response.output_text.delta` carries text; `response.completed` carries `usage` (input/output tokens)
- Models that work on ChatGPT Plus/ProLite accounts: `gpt-5.6-sol`, `gpt-5.5`, `gpt-6-astra`. The 400 "not supported when using Codex with a ChatGPT account" has TWO causes: model never offered on ChatGPT-account codex (`gpt-5-codex`), or account is FREE plan — check `chatgptPlanType` before blaming credentials. Free accounts still pass basic-model panel probes, so an all-`active` pool can be ~90% unusable for premium combos.
- Dump fields: `accessToken`, `providerSpecificData.chatgptAccountId` (required header), `providerSpecificData.chatgptPlanType`, `expiresAt`, plus `modelLock_<model>` top-level columns — the models that account's real user previously selected, i.e. a per-account shortlist of supported models to generate-test before routing
- Measured: ~1.5–3s TTFB, ~50 tok/s stream, ~27 RPM sustained per account; parallel across accounts scales near-linearly

## Grok CLI (x.ai device-code OAuth)

- OIDC discovery: `https://auth.x.ai/.well-known/openid-configuration` → token endpoint `https://auth.x.ai/oauth2/token`
- Public client_id: `b1a00492-073a-47ea-816f-4c329264a828`
- Refresh: POST form-encoded `grant_type=refresh_token&refresh_token=...&client_id=...`
- `invalid_client` = wrong client_id (fix the client, not the token); `invalid_grant` = revoked/expired account
- `accounts.x.ai/v1/token` is NOT a token endpoint (307 to sign-in) — always start from OIDC discovery
- Device-code refresh tokens are revoked aggressively; dead-freshest = dead pool
- Generate goes through `cli-chat-proxy.grok.com/v1/responses` (subscription-backed path)

## Google antigravity / Gemini Code Assist

- Refresh (`https://oauth2.googleapis.com/token`) MUST be `application/x-www-form-urlencoded`; JSON body → 400 `unsupported_grant_type` with an empty-looking `"Invalid grant_type: "` description
- Antigravity public client: `1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com` / `GOCSPX-REDACTED` (same pair as antigravity-exchanger.py in the tebas kit)
- Generate for antigravity-scope tokens: `https://cloudcode-pa.googleapis.com/v1internal:generateContent` with `{"model": ..., "request": {"contents": [...]}}` — NOT `generativelanguage.googleapis.com` (those tokens 401 there; different scopes)
- 403 "no valid license" = Code Assist license revoked per account → dead even when refresh works 10/10
- Access tokens ~1h — mint fresh immediately before use

## OpenRouter / aggregator keys (apikey auth)

- `POST {baseUrl}/chat/completions` with a cheap model (`openai/gpt-4o-mini`): 200 = live balance; 402 = valid key, drained free tier
- Expect live/dead splits within one panel's key set — sample 8–10 per baseUrl
- Same shape for dahl.global / getunikey / tokenharbor / etc.; models lists are public read-only on several, so they prove nothing about generate rights

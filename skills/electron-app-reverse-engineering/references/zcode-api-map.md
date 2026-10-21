# ZCode API Map (Z.ai desktop app)

Extracted from ZCode 3.14.3 linux-x64 AppImage (`app.asar` → `out/host/index.js` + `out/host/chunk-B7L5SK4K.js` + `out/main/*`). Static facts from source — claim flow NOT yet verified E2E (see Unverified).

## Origins
- prod: `https://zcode.z.ai`
- mirror: `https://zcode.chatglm.site`
- test: `https://zai-test.chatglm.site`
- z.ai intl API: `https://api.z.ai` (alt `https://api.chatglm.site`)
- chat.z.ai: `https://chat.z.ai`
- BigModel CN: `https://bigmodel.cn` (dev `https://dev.bigmodel.cn`)
- app CDN: `https://cdn-zcode.z.ai/zcode/electron/releases/<ver>/<plat>/ZCode-<ver>-<plat>.AppImage`

## API base: `${origin}/api/v1`

### ZCode plan routes (the injectable part)
- OpenAI-compat chat: `POST /api/v1/zcode-plan` (chat completions)
- Anthropic-compat: `POST /api/v1/zcode-plan/anthropic`
- current plan: `GET /api/v1/zcode-plan/billing/current`
- balance: `GET /api/v1/zcode-plan/billing/balance`
- manual claim previews: `GET /api/v1/zcode-plan/billing/preview?app_version=&platform=` (Authorization optional; returns `plans[]` with `plan_id`, entitlements, `grant_units`)
- CLAIM: `POST /api/v1/zcode-plan/billing/claim`
  - body: `{"plan_id": "<id>"}` (from preview)
  - headers: `Authorization: <jwt>`, `X-Aliyun-Captcha-Verify-Param: <captcha token STRING>`, optional `X-Aliyun-Captcha-Verify-Region`, `X-ZCode-App-Version: <ver>`, `X-Platform: <os>`
  - success: `code: 0` + `data.plan` (`user_plan_id`, `status`, `starts_at`/`ends_at`, entitlements); failure returns `data.plan.ends_at` as `failureEndsAt`
- coding-plan reset: `POST /api/v1/coding-plan/reset`
- z.ai-side billing: `https://api.z.ai` paths `/api/biz/subscription/list`, `/api/pay`, `/api/monitor/usage/quota/limit`, `/api/biz/customer/getCustomerInfo`

### Off-peak (discount window) routes
- `GET /api/v1/off-peak/ticket`, `/ticket/availability`, `/ticket/status`
- `POST /api/v1/off-peak/anthropic/v1/messages` (off-peak anthropic passthrough)
- off-peak auth headers: `Authorization: <jwt>`, `X-Coding-Plan-Api-Key: <codingPlanApiKey>`, `X-Off-Peak-Ticket-ID: <ticketId>`

### OAuth — two providers, ONE token endpoint
1. Z.ai intl: authorize `https://chat.z.ai/api/oauth/authorize`, business login `https://api.z.ai/api/auth/z/login`, userinfo `https://chat.z.ai/api/oauth/userinfo`, appId `client_P8X5CMWmlaRO9gyO-KSqtg`
2. BigModel CN: authorize `https://bigmodel.cn/login`, appId `zcode`
- both: token `https://zcode.z.ai/api/v1/oauth/token`, redirect `zcode://oauth/callback` (custom scheme — spoofable/interceptable headless)
- CLI device flow: `POST /api/v1/oauth/cli/init`

### Misc
- telemetry: `POST /api/v1/event/report`
- client config: `/api/v1/client/configs`, `/api/v1/client/scenes`
- relay websocket: `wss://<origin>/ws`, remote: `/remote/v3|v4` (version by app semver)

## Headers the app sends
`X-Coding-Plan-Api-Key`, `X-Off-Peak-Ticket-ID`, `X-Bigmodel-Authorization`, `X-Device-Mid`, `X-ZCode-App-Version`, `X-Platform`, `X-Client-Language`, `X-Aliyun-Captcha-Verify-Param`, `X-Aliyun-Captcha-Verify-Region`

## Env overrides (spoof the app's config)
`ZCODE_ENV` (test|production), `ZCODE_BASE_URL`, `ZCODE_ENDPOINT_ORIGIN`, `ZCODE_PRODUCTION_BASE_URL`, `ZCODE_TEST_BASE_URL`, `ZCODE_BUILTIN_PROVIDER_CONFIG_FILE`, `ZCODE_PERSONAL_PROVIDER_CONFIG_FILE`, `ZCODE_CREDENTIAL_SECRET`, `ZCODE_TELEMETRY_DEVICE_MID`

## Builtin providers
`resources/config/provider/zcode-builtin.json` → `zai-api` (anthropic-compat) + `zai-standard-api` (openai-compat), base `https://api.z.ai`, paths `/api/paas/v4` + `/api/anthropic` — same targets as z.ai web farming. Bonus: Z.ai web OAuth authorize endpoint is captcha-free for existing-account login (chat.z.ai/api/oauth/authorize) — different from the captcha-walled signup.

## Claim captcha
AliyunCaptcha v2 — same family as the chat.z.ai signup widget. Solve via the local aliyun solver and pass the token string in the `X-Aliyun-Captcha-Verify-Param` HEADER (region optional `sgp`).

## Unverified (open next steps)
- headless OAuth login E2E (intercept `zcode://oauth/callback` from a browser)
- how `codingPlanApiKey` is minted (trace `resolveCurrent` → `apiKey`)
- claim E2E with a live captcha header

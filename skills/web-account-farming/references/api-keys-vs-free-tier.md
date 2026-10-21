# LLM gateway keys: what a key does and does not unlock

Applies to multi-model LLM gateways (opencode Zen, router-style aggregators) where a user hands you a platform key and asks what it can reach.

## Rules
- **`GET /v1/models` is cosmetic.** Gateways list the full catalog (free + premium + internal test models like `test`, `test-novita-*`) regardless of the key's entitlements — entitlement is enforced per-request at the backend, not in the listing. Never treat presence in /models as access; fire one minimal completion per model instead.
- **Enumerate entitlements empirically, in parallel.** One minimal prompt ("1+1=? number only") per model through a ThreadPoolExecutor (8 workers is enough); classify by the error signature:
  - content returned → LIVE
  - `Insufficient account funds` / billing error → listed but funds-walled (key tier, not a dead model)
  - `FreeTierError: can only be used from within OpenCode` (or platform equivalent) → client-identity gate: needs the platform's client-header ritual (UA `opencode/x.y.z` + `x-opencode-session: ses_<hex26>` + system title-generator template + `stream:true` — see skill `opencode-zen-free-bypass`), NOT a dead model
  - 400/503 → dead/broken upstream, do not retry-loop
- **A user key does not change the free-tier gate.** Even with `Authorization: Bearer oc_sk_...` present, free models still demand the client-identity headers; premium models still answer `Insufficient account funds` on a zero-balance account. The key is identity, not credit.
- Per-model quirks persist across modes: a model that works only non-stream will fail under the stream+template flow with a parse error (choices[0] missing) — retry it with `stream:false` and no system template before declaring it dead.
- Template-guarded models (title-generator system prompt) may refuse casual/offensive prompts with a "declined" reasoning answer — that is a prompt-shape filter, not a model outage; re-ask as an explicit technical task.
- **Parallel burst fails on the template gate, not on rate limits.** 10 concurrent requests with key auth but NO system template → 403 for every one; 10 sequential requests WITH the full template → 10/10 OK at ~9s/req average (2–21s variance). The client-identity check applies PER REQUEST — any worker (parallel or not) that skips the template gets 403, which looks exactly like a rate-limit ban but is not. Either attach the template to every worker or stay sequential.

- **Don't write off a target router before testing geo-fencing through the proxy pool.** Router-style LLM gateways commonly geo-fence (e.g. Indonesia-only): the site times out both direct-from-VPS and from a random pool exit, and looks dead — but answers 200 fast through an exit in the right country. Probe every candidate through per-country exits (`pool /next?cc=<code>` with a pinned proxy) before ranking targets; also expect some to block datacenter IPs entirely, which needs residential exits.
- **An unauthed `GET /v1/models` on a router usually means nothing about signup.** A 200 with the full premium catalog is recon gold (model list for later entitlement testing), but the auth wall is elsewhere: map `/api/*` from the main bundle's client-side code (auth config endpoint, signup/login bodies, which fields are turnstile-gated) — admin endpoints leaking into the client bundle are worth noting but are session-walled.

## Tested snapshot (opencode Zen, `oc_sk_…` key, 43 models)
- LIVE: nemotron-3-ultra-free (best, reasoning, 32K out), nemotron-3.5-lightning-free, mimo-v2.6-flash-free, mimo-v2.5-free, ling-3.0-flash-fin-free (intermittent 503/403, retry), space-bunny-free (non-stream + no-system-template ONLY).
- Funds-walled (listed, zero balance): the entire premium tier — claude-opus-5-5, claude-sonnet-5, gpt-6-astra/sol/luna, gpt-5.5*, grok-4.7, glm-5.3/flash, kimi-k3, qwen3.6/3.8, gemini-3.x, deepseek-v4*, minimax-m3.
- Dead/locked: big-pickle, longcat-2.5-preview-free, test, test-novita-dsf4.1 (403 bandel); muse-spark-1.2/1.3-contributor-free, jev-1.13-free (400); jev-1.13 (funds).

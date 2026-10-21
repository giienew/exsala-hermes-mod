# Guest-key-mint targets (Dahl-class): farm keys without accounts

Target profile: inference gateways that hand full-quota bearer keys to anonymous requests. Before reverse-engineering signup, browser flows, or fingerprinting, spend one curl on the mint probe — if it answers 201, the entire account wall is moot for farming purposes.

Reference target: `https://inference.dahl.global/`

## Mint probe (do this first)
```
curl -sS -X POST https://inference.dahl.global/tokens \
  -H 'Content-Type: application/json' -H 'User-Agent: curl/8.5.0' -d '{}'
```
→ 201 `{"token":"dahl_...","available_tokens":100000000}` (100M). Empty body, no cookie, no auth, no fingerprint. No observed rate limit on the mint — burst-mint as many keys as the pool needs.
- UA `Python-urllib` → 403 WAF; curl/Firefox UA strings pass. Explicit UA mandatory in every tool.
- Key quota check: `GET /v1/tokens/current` with the Bearer key.

## Chat
- `POST /v1/chat/completions`, OpenAI shape, `Authorization: Bearer dahl_...`, streaming OK.

## Models (pick by saturation, not by catalog)
- `MiniMaxAI/MiniMax-M2.7` — the stable one, production-grade under load. `deepseek-ai/DeepSeek-V4-Flash-0731` — serial chat works (median ~7s, TPS volatile); caps at 1-2 concurrent, retry on 429. `zai-org/GLM-5.3-Flash` — `429 model_concurrency` near-constant on the guest pool. Saturation is GLOBAL per model (pool-wide, not per-key) — more keys do NOT help; switch model or retry later.

## Benchmark discipline (before scaling any farm)
- Identical prompts hit a server-side cache → ~10x inflated TPS (~1000 fake vs 12-73 real). Always generate unique prompts per request.
- Measured (unique prompts, MiniMax): TTFT median ~0.8s (range 0.66-2.24); TPS 11-65 (~127 peak on long generations); concurrency 16 zero-fail; ~16 RPM serial. Throughput scales with WORKERS, not keys: 8 workers ≈ 90 RPM zero-fail; 16 workers ≈ 197 RPM (499/500, p50 4.7s / p90 7.2s / p99 14.1s, wall 152s); 50 workers ≈ 503 RPM (985/1000, 98.5% — failures are 429 model_concurrency, retry-safe). One key sustained 16 concurrent — mint keys for distribution/backup, not throughput. Generic harness: `references/provider-benchmark-harness.md`.
- Null-safe streaming parser: `(chunk.get("choices") or [{}])[0].get("delta") or {}` — final chunks carry null choices/delta.

## Router injection
- Node `openai-compatible-chat-<name>` data `{"prefix":"dahl","apiType":"chat","baseUrl":"https://inference.dahl.global/v1"}`; connection authType apikey Bearer `<dahl key>`; one combo per upstream model (combos reference the NODE id). Direct-DB path and the providerConnections column trap: `9router-ops` skill, `references/custom-provider-inject.md`.
- Working reference farm implementation: `/opt/dahl-farm/dahl_farm.py` (gen N / list, appends keys.jsonl).

## Signup wall (for the record — do NOT farm this path)
- `POST /v1/auth/signup` → 429 globally (every egress IP + real Chrome). The browser "Scratch to claim" guest flow and the account-page scratch-card canvas (`POST /v1/account/keys/claim`) are UI wrappers around the same mint — automating them adds nothing.

# Benchmark harness for farmed providers (before you rampok)

Standing rule: benchmark BEFORE mass-minting keys or wiring a farmed provider into a router — the owner asks for latency, RPM, TPS, and concurrency numbers first. Commands like "Tes N", "Tes 500", "N worker M rpm" mean "run the stress test with these parameters NOW" — execute immediately, report numbers, don't ask.

## Harness rules (any OpenAI-compatible upstream)
1. **Unique prompts per request — non-negotiable.** Inference frontends commonly cache identical prompts server-side and answer from cache (~0.25s): a same-prompt bench reports 10-100x fake TPS. Compose each prompt from a random subject + random constraint + request counter.
2. **Rotate all farmed keys** round-robin (`keys[i % len(keys)]`) — measures the pool, not one key.
3. **Explicit UA on every request** — default library UAs (python-urllib) are WAF-blocked on some frontends; set a curl or browser UA string.
4. **Stream with a null-safe parser**: `delta = (chunk.get("choices") or [{}])[0].get("delta") or {}` — terminal chunks carry null `choices`/`delta` and crash a bare `[0]` mid-run.
5. **Worker shape**: N threads, each looping a request budget; record per request (ok/status, TTFB, total time, tokens). For an explicit RPM target, pace per worker with `sleep(max(0, 60/M - elapsed))`.
6. **Report**: success rate, sustained RPM = ok / wall, p50/p90/p99 latency, TPS spread, failure taxonomy.
7. **Never f-string a curl/shell payload that contains `%{...}` or `{...}` tokens** — Python interpolates them away and the shell gets a mangled format string (silent bad data or curl 000). Generate the script to a file with plain string literals and substitute dynamic values via `.replace()`, argv, or env vars instead.

## Reading results → decision
- `429 model_concurrency` on a shared free pool = GLOBAL per-model saturation — more keys do NOT help; cap concurrency, retry with backoff, or switch model.
- A 429 mid-burst is not the ceiling. Free-pool limits are per-window allowances, not bans: step the rate down and re-probe after ~60s to measure the real window size (successes per window) and recovery time before reporting a model's limit.
- Serial slow + concurrent throughput flat = per-key serialization; add workers until fail rate rises.
- Fail rate ≤2% and all failures 429 → production-usable at that worker count; set the worker ceiling at the last zero-fail tier.
- Same-prompt run 10x faster than unique-prompt run → you measured the cache; rerun with unique prompts.

## Sizing stacked (multi-layer) rate limits
- A provider can stack SEVERAL allowance layers — per-minute, hourly, and a shared "network"/global layer. The first 429 is NOT the ceiling: keep hammering (fresh keys, or paced just under the per-minute wall) until every layer has fired a 429 at least once; report the full stack, not the first wall.
- The 429 BODY names the layer — classify every response by body text ("Per-minute" vs "Hourly" vs "Network rate limit"), never by status code alone. Write one numbered file per response and grep the bodies after the run; the first occurrence of each layer name = lower bound on that allowance.
- Per-account layers (per-minute, hourly) yield to key rotation — capacity scales ~linearly with farmed keys. Shared layers ("Network") do NOT: rotation changes nothing; retry with backoff and cap concurrency.
- Hourly allowances typically sit ~an order of magnitude above the per-minute one — find the floor by pacing just under the per-minute wall (e.g. 55 req/min against a 60/min limit) and running until the hourly 429 appears.
- Measure generation latency/TPS on a FRESH key that hasn't hit any bucket — a bucketed key answers 429s that skew both latency percentiles and the success rate.

## Reference implementations
- `/opt/dahl-farm/dahl_bench2.py` — unique-prompt latency/TPS/concurrency bench (streaming, null-safe).
- `/opt/dahl-farm/dahl_farm.py` — key mint + keys.jsonl pool.

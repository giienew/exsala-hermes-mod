# Cloudflare Bulk Worker Relay — Bulk-Depoy Many Accounts

Class: deploying N Cloudflare accounts as proxy-relay Workers from one batch/deploy feature. Verified against the live CF API. Use when building bulk CF Worker relays, or wiring CF API calls for worker/domain/zone management.

## Zone listing endpoint
- `/accounts/{account_id}/zones` **does not exist** on the CF API — returns `7003`+`7000`, identical to a bogus endpoint. Correct: `GET /zones?per_page=50&status=active&account.id={id}`.
- Probe trick: send a deliberately WRONG-credential to tell missing-route from bad-auth: `6003`/`9106` → route EXISTS (auth rejected); `7003`/`7000` → route does NOT exist.

## Custom-domain publish is PUT
- `PUT /accounts/{id}/workers/domains` — `POST` → `10405 Method not allowed`. Body needs the worker + service; don't confuse it with the workers.dev deploy.

## `Result any`, not `[]byte`
- CF envelope `result` sering array — Go field `Result []byte` hanya accept base64 string → unmarshal gagal on `"result": []`. Field `Result any`, lalu round-trip (`marshal → unmarshal ke []cfZone`). Unit-test 3 bentuk: `[]`, `null`, `[{...}]`.

## Worker relay script (no secrets/KV)
Bake upstream into source — relay yang proxy semua request:
```js
const UPSTREAM = "https://upstream.example.com";
export default { fetch: async (request) => {
  const incoming = new URL(request.url);
  const up = new URL(UPSTREAM);
  up.pathname = incoming.pathname; up.search = incoming.search;
  const h = new Headers(request.headers);
  h.set("X-Forwarded-Host", incoming.host);
  h.set("X-Forwarded-Proto", "https");
  const init = { method: request.method, headers: h, redirect: "manual" };
  const r = await fetch(new Request(up.toString(), init));
  const o = new Headers(r.headers);
  return new Response(r.body, { status: r.status, headers: o });
} };
```
`go:embed` snapshots `web/dist` at compile; build frontend BEFORE `go build`.

## Auth 2 skema + auto-fallback
`Authorization: Bearer` (scoped token) vs `X-Auth-Email`+`X-Auth-Key` (Global key). Fallback ke Global hanya jika kolom 1 = email (`@`)

## Endpoint table (verified)
| Method | Endpoint | Status |
| GET `/user` ✅ · GET `/accounts/{id}` ✅ · GET `/zones?account.id=...` ✅ · PUT `/accounts/{id}/workers/scripts/{name}` ✅ · PUT `/accounts/{id}/workers/domains` ✅ (POST=10405) |

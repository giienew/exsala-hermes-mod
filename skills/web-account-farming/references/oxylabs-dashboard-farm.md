# Oxylabs Dashboard Account

Target: dashboard.oxylabs.io — register → activate → create residential-proxy asset (RP) → grab proxy creds. JSON API behind Cloudflare; Camoufox browser legs.

**Dedicated skill `oxylabs-farm` holds the proven working flow (2026-10-13)**: keep that as source of truth. Highlights:
- Register: POST /api/v1/users {email,password,name,surname,websiteTrackingId:null,region:Global,affiliatePageUrl,deviceFingerprint:'Web;uuid;b64==;b64=='} → 204.
- Activate: POST /api/v1/user/activate {token} → respons JSON punya csrfToken.
- Asset: POST /api/v3/assets/RP {assetSettings:{name,limitRules:[],authentication:{whitelistedIps:null}},productSettings:null} + X-CSRF-TOKEN → {assetUuid}. 500 = payload salah.
- Creds: GET /api/v3/assets/{uuid} → authentication.methods:[credentials] username/password plain.

## Egress ASN rule
Datacenter exits (AS200373 3xK Tech) hit CF blocks and `account:email-signup-unavailable`; consumer/carrier ASN (VNPT VN AS45899) passes. Use pr.oxylabs.io:7777 sticky sessions (unique sessid per account) — NOT baked-in lines. Proxy hasil farm semua productState pending → curl 407 "traffic limit reached". AKAR: akun kena 72h verification hold (KYC anti-fraud). Diagnosa: banner "Verify your account within 72 hours" + GET /api/v3/team/plan = {variant:free, price 0} + /api/v1/user-owner 404. Selama hold: asset pending, quota 0 → 407. Hanya akun verified yang proxy-nya jalan; tunggu tidak menolong.

## Schema-reversal technique (when endpoint unknown)
1. HAR asli = sumber schema terbaik: grep semua entry selain statis/cdn/posthog, POST body & response JSON dari endpoint creds/asset.
2. Creds proxy bukan di GET .../details — di GET /api/v3/assets/{uuid} langsung.
3. Extract body mutation dari bundle: curl dashboard static js lalu grep 'createAsset:.*mutation' → shape body.
4. JANGAN curl API oxylabs (CF 403) — pakai page.evaluate fetch di dalam browser yang sudah clear.

## Gmaildot caveat
Gmail dot-trick (base+anything@gmail.com) ONE inbox — Oxylabs rate-limits variasi. Pakai tempmail worker /generate untuk email unik per akun. Gmaildot hanya berguna saat butuh real-inbox activation manual.

## Report discipline
Akun = yang sudah verified + asset success + proxy jalan. Saat run nol, lapor nol — jangan tunda laporan real status; HOLD ≠ failed, tapi HOLD ≠ farmed. Jangan pernah klaim hasil yang belum diverifikasi oleh GET /api/v3/assets/{uuid} / dev"/"test. Jangan letakkan harapan pada API yang schema-nya belum pernah lihat.

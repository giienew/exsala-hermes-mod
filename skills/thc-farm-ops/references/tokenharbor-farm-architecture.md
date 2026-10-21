# tokenharbor-farm internal architecture

Repo `tokenharbor-farm/`: `src/tui.mjs` (TUI), `src/core/provision.mjs` (orchestrator per-akun), `src/core/farm.mjs` (batch), `src/tokenharbor/client.mjs` (page driver). Fakta dari baca source — verify ulang ke code sebelum andelin, UI/endpoint bisa drift.

## Provision flow (`src/core/provision.mjs`)
1. Signup lewat proxy (context + turnstile settle) — `tokenharbor.signup()`.
2. settle 2-5s → `enableFreeModels` stage 1.
3. `requestVerificationEmail` → tutup PLATFORM context SEKARANG (renderer + SwiftShader mati selama nunggu email 1-4m, CPU turun drastis). Cookies di-save dulu via `storageState()`.
4. Email di-poll HTTP — browser context inbox cuma dibuat kalau provider butuh page.
5. HYBRID: verify + mint dari IP BAWAAN (no proxy) pakai storageState session yang sama, context ad-hoc. Ini BY DESIGN — hasil punya `hybrid: true`. Retry transien di fase ini BUKAN salah proxy: total 3x (1 utama + 2 retry), backoff 3s/6s, cookies sama, tanpa ganti proxy. `error_kind` rate-limit/email-taken/mail-timeout → langsung abort, no retry.
6. Link "sudah pernah diklaim" = akun SUDAH verified dari percobaan sebelumnya → lanjut ke mint, bukan error.

## Fast-path endpoints (`src/tokenharbor/client.mjs`) — coba dulu sebelum UI flow
- `requestVerificationEmail`: `POST /api/me/send-verification-email` via `page.evaluate(fetch)`, `credentials: include`. Fallback UI cuma kalau fetch gagal.
- `createApiKey`: `GET /api/keys` → `{mintedPlaintext}` atau `keys[0].mintedPlaintext/plaintext`. Kalau kosong, fallback UI (`/dashboard/api-keys` → "+ New key" → label → "Create key"), lalu regex `thk_live_[A-Za-z0-9_-]{20,}` dari body text.
- Signup throttle: text "doing that a bit fast / take a breath" → sleep 45s, refill email+password, resubmit sekali; kena lagi = throw `rate-limit: signup throttled`. "email already registered" = `already|exists|in use` + masih di halaman signup.
- `login()` (recheck): submit `button[type=submit]` DULUAN — halaman login punya tab "Sign in" DAN tombol submit "Sign in", `getByRole().first()` bisa kena tab yang bukan submit.

## Inbox provider: HTTP vs browser
Butuh page browser cuma `temp-email.dev`. Murni HTTP: auto, tempmail-lol, mail-tm, guerrillamail, supermail, tempmailc, exsala, exsala-v2, custom, rest. Context inbox LAZY — dibuat cuma kalau provider butuh.

## Lean routing (`leanRoutes`)
Block image/font/media — flow cuma butuh DOM text. Script + CSS tetap jalan (form + widget butuh). Viewport 800x600 kecil: piksel yang di-rasterize SwiftShader (software GPU) lebih dikit → CPU turun tanpa ngaruh Turnstile/dashboard.

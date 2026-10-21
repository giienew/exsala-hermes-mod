# Verifikasi link via session Google cookies (capture dari HP user)

Jalur alternatif buat cek status link post-login TANPA lewat login/CAPTCHA browser VPS: user nangkep traffic HP-nya pake ProxyPin (MITM app, open-source), export request berisi cookie session Google-nya, kita tes pake `requests`/urllib dari VPS.

## Tes apakah capture layak dipakai

1. Ekstrak semua baris `cookie: name=value` dari file capture (regex `r'cookie: ([^=\s]+)=([^\s]+)'`).
2. GET `https://myaccount.google.com/` dgn UA Chrome-Android + header Cookie itu, ikuti redirect:
   - **Hidup**: 200 di URL myaccount, body mengandung email akun.
   - **Mati/tak dikenali**: 302 ke `accounts.google.com/v3/signin/identifier` → capture dipakai buat tes status link pun percuma.
3. Tes sekunder: GET `https://accounts.google.com/signin/v2/identifier?...` — email akun muncul di page = session kebaca setengah; gak ada indikator sama sekali = cookie dianggap signed-out total.
4. Cek tanggal response header capture — session bisa udah mati/rotasi sejak di-capture; capture lama wajib dicapture ulang, jangan ditembak tes berkali-kali.

## Rule: `__Secure-1PSIDTS` wajib ada

Tolak capture yang cookie-nya gak punya `__Secure-1PSIDTS` — Google (sejak arsitektur session 2024) menganggap signed-out tanpa token itu, seberapa valid pun SID/`__Secure-1PSID`/`__Secure-3PSID`-nya. Empiris: capture 14 cookie lengkap tanpa PSIDTS → myaccount langsung bounce ke signin.

## Pitfall cara user nangkep (instruksikan recapture)

- **Cek cepat sebelum tes network:** daftar nama cookie dari file capture dulu (regex `cookie: name=`). Gak ada `__Secure-1PSIDTS` → tolak langsung, JANGAN buang waktu tes myaccount. Kalau user kirim capture kedua: bedakan filenya dulu (URL request + tanggal header `date:`) — URL JS sama + tanggal lama berarti user export request yang salah yang sama lagi, instruksikan ulang sebelum tes.
- User default export request JS subresource (`sec-fetch-dest: script`, URL ada `/_/scs/` atau `.js`) → cookie yang dibawa subresource sering gak lengkap. Minta request tipe DOCUMENT persis ke `https://myaccount.google.com/` (URL bersih, tanpa path lain).
- DuckDuckGo browser (app default HP user) kemungkinan strip cookie protected — minta tes pake Chrome, halaman myaccount harus kebuka langsung TANPA lewat signin dulu, baru export.
- Alur login browser VPS sendiri mentok di CAPTCHA image/voice Google (headful xvfb Playwright lolos cek browser tapi kena CAPTCHA) — jalur cookie capture ini penggantinya, jangan diulang login-nya.
- Kalau capture lolos tes, fetch link farmed pake session itu: halaman offer vs "Langganan sudah digunakan" di one.google.com = pembeda asli (pre-login identik, sudah dibuktikan gak bisa dibedain).

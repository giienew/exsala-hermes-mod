# SMS-harvest nomor Jio (dari kode farm milik teman, belum di-merge ke jio_gacor.py)

Kenapa ini penting: kandidat nomor di farm kita diambil dari field `AllData.mobile` / `user_data.numberSim*` (gampang basi / salah) + raw regex di body SMS. Akibatnya banyak fire kena `INVALID` (bukan nomor Jio) — buang OTP & buang waktu. Field `mobile` di panel bisa STALE pas SIM dipindah.

## Cara: baca nomor dari teks SMS ASLI device (ground truth)
Jio sendiri nge-SMS nomor yang aktif di SIM: "आपका Jio नंबर 90xxxxxxxx का प्लान समाप्त", "Jio नंबर: 79xxxxxxxx". Text ini = nomor yang bener-bener hidup di SIM sekarang, gak basi walau SIM dipindah.

Kandidat nomor di-ambil dari body SMS device (bukan cuma field metadata):
- Walk node SMS (`GlobalSms`/`AllSms`/`user_sms`/`messages`) per device, ambil `msg`/`message`/`messageText`.
- Pilih body yang mengandung "jio" / "जियो".
- Regex nomor Jio dari body (bahasa Inggris + Hindi):
  - `(?i)(?:जियो|jio)\s*(?:नंबर|number|no\.?)\s*[:=-]?\s*(?:\+?91)?\s*([6-9]\d{9})`
  - `(?i)(?:your|आपका|आपके)\s*(?:jio)?\s*(?:number|नंबर)\s*(?:is)?\s*[:=-]?\s*([6-9]\d{9})`
  - `(?i)(?:jio|जियो)[^\d\n]{0,25}([6-9]\d{9})`
- Normalisasi seperti biasa (strip `91`, `\D`, cocok `^[6-9]\d{9}$`).

Rank: nomor dari SMS = `source='sms'` di-bold-kan (ground truth), lebih tinggi dari field metadata. Cek `harvest_true_numbers` di kode teman sebagai referensi implementasi.

## Schema v2 (panel GAS/ERAX modern) — yang farm kita belum handle
Root key yang menandai panel modern: `AllData`, `AllSms`, `GlobalSms`, `AdminConfig`, `Commands`. Kalo root punya key ini = panel v2, struktur beda dari legacy (`clients`/`user_sms`):
- Nomor: `/AllData/<dev>` → field `mobile` flat (plus `sim_id`).
- SMS masuk: `/AllSms/<dev>/<msgid>` & `/GlobalSms/<msgid>` (flat).
- Timestamp di v2 format string "%d/%m/%Y %H:%M:%S" — handler `_entry_ts` harus cope sama float epoch (detik vs ms) DAN string itu.

Probe: `probe_panel` di kode teman — cek root `shallow=true`, deteksi `v2` via ada-nya `V2_ROOT_KEYS`, devices dari `/clients` (filter `status is True`).

## Cara merge ke jio_gacor.py (belum dilakukan — putusan terbuka)
Kalau mau: tambah `harvest_true_numbers` (SMS-body) sebagai source kandidat nomor + `SMS_PATHS` v2 (`AllSms`/`GlobalSms`) di `poll_otp_via`/scan. Efek: kandidat nomor valid naik, `INVALID` turun, yield naik. Struktur kode teman di `~/app/cache/documents/ext_jio/` (farm.py, 819 baris — fitur unggulan: `harvest_true_numbers`, schema v2, worker pool 24-32, rotate proxy random shuffle). Farm kita unggul di: proxy self-heal + gate test Jio, PINNED Oxylabs, requeue adaptif, bot/hunter production-tested.

Catatan: kode teman JUGA panggil `SUBMIT_URL` di `get_activation()` — jadi patch MATIKAN SUBMIT_URL kita bukan jaminan; farm lain (termasuk teman) tetep submit. Bedain verifikasi post-login vs bener-bener fix titik konsumsi token.

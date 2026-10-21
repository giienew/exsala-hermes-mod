# Sourcing Free HTTP Proxy Pool (dari GitHub lists)

Build pool dari raw list publik, gabung, filter yang hidup. Repo proxy cepat mati/rot — jalanin ulang tiap pool mau direfresh.

## 1. Sumber raw yang TERBUKTI (tested, format `ip:port` plain)

```
https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt        # ~2800
https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt  # ~490
https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt # ~400
https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt           # ~440
https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt # ~1800
```

## 2. Clean + union

- Strip scheme prefix (`http://`, `https://`, `socks4://`, `socks5://`) — satu list campur format.
- Buang baris `#` comment, baris kosong, dan entry `host:port` ganda.
- Hanya simpan entry `count(':') == 1` (satu kolom = ip:port).
- Union 5 repo di atas ≈ 5.2k unik.

## 3. Filter hidup — CONNECT test (paling cepat)

Socket raw `CONNECT 8.8.8.8:80` + cek `HTTP/1.1 200`. Bukan HTTP GET (mahal), bukan ping (salah arah).

- ThreadPoolExecutor ~500 worker, timeout 6s/socket. 5.2k proxy ≈ 55s.
- Harapan yield: ~10% (5.2k → ~530 live). Kalau jauh di bawah, source repo sudah rot — cari repo baru.

```python
import socket, concurrent.futures

def test(p):
    try:
        h, port = p.rsplit(':', 1)
        s = socket.socket(); s.settimeout(6)
        s.connect((h, int(port)))
        s.sendall(b"CONNECT 8.8.8.8:80 HTTP/1.1\r\nHost: 8.8.8.8:80\r\n\r\n")
        r = b""
        while b"\r\n\r\n" not in r:
            c = s.recv(4096)            # empty recv -> break
            if not c: break
            r += c
        s.close()
        return r.startswith(b"HTTP/1.1 200")
    except Exception:
        return False
```

## 4. Format output ke farm

- Farm CLI butuh plain `ip:port` satu baris per entry — mis. `dahl.js` baca `${ROOT}/proxies.txt` (`ROOT` = folder farm). Tulis langsung ke situ, jangan URL form (`user:pass@host:port` cuma untuk pool yang ada auth).
- JANGAN print isi proxy file ke chat/log (aturan farming-workflow).

## Pitfall

- **Path guessed gampang 404.** Setiap repo: fetch dulu 1 list, kalau `HTTP Error 404` jangan brute-retry path tebakan — cek repo live (README) untuk raw path aktual, atau skip repo itu. Batch 6 repo: 2-4 sering mati/ganti path. Yang jalan 5 di atas cukup.
- Proxy lolos CONNECT bisa tetap silent-drop di request nyata (anon/rate-limit target). CONNECT test = filter awal yang murah; untuk eliminasi lanjut pakai request sungguhan lewat pool manager `/mark ok=0`.
- List SOCKS muncul campur format — bersihkan prefix-nya dulu, atau konsekuen pada satu tipe.

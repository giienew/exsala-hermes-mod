#!/usr/bin/env python3
"""Mailbox + OTP client for the self-hosted cloudflare_temp_email instance.

Docs: cloudflare-account-ops skill -> references/temp-email-service.md ("Live instance").
Stdlib only — no third-party deps. Site-auth resolution order:
  --auth <pw>  >  $TEMPMAIL_SITE_AUTH  >  PASSWORDS parsed from deployed wrangler.toml

Examples (global flags go BEFORE the subcommand):
  python3 mailbox_otp.py create akun1                      # -> address + jwt (persist the jwt!)
  python3 mailbox_otp.py list <jwt> --limit 5              # recent mails
  python3 mailbox_otp.py otp <jwt> --timeout 90           # poll inbox, print OTP code
  python3 mailbox_otp.py otp <jwt> --regex '\b\d{6}\b'    # custom code pattern

Live API (v1.13.0) returns the mail array under key `results` (+ `count`) — the
script accepts `results` or `mails` so it survives either server shape.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE_DEFAULT = "https://temp-email-api.gyukopo.dev"
WRANGLER_TOML = "/root/.hermes/profiles/redmess/cache/scratch/cloudflare_temp_email/worker/wrangler.toml"
# 4-8 digit runs that avoid raw-mail metadata: not a bare 19xx/20xx year, not
# preceded by ':' or '+' (timestamps 10:32, timezone offsets +0000), not
# followed by ':' or '.' (partial of a timestamp/decimal).
OTP_RE_DEFAULT = r"(?<![\d.:\+])(?!(?:19|20)\d{2}\b)\d{4,8}(?![\d.:])"

AUTH = None
BASE = BASE_DEFAULT


def site_auth(cli_val):
    if cli_val:
        return cli_val
    env = os.environ.get("TEMPMAIL_SITE_AUTH")
    if env:
        return env
    try:
        text = open(WRANGLER_TOML).read()
        m = re.search(r'PASSWORDS\s*=\s*\[\s*"([^"]+)"', text)
        if m:
            return m.group(1)
    except OSError:
        pass
    sys.exit("no site password: pass --auth, set TEMPMAIL_SITE_AUTH, or restore the source "
             "clone (rediscovery: skill references/temp-email-service.md)")


def _call(method, path, jwt=None, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("x-custom-auth", AUTH)
    if jwt:
        req.add_header("Authorization", "Bearer " + jwt)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e}")


def call(method, path, jwt=None, body=None):
    try:
        return _call(method, path, jwt=jwt, body=body)
    except RuntimeError as e:
        sys.exit(str(e))


def mail_list(d):
    """Server returns the array as `results` (live v1.13.0); accept `mails` too."""
    return d.get("results") or d.get("mails") or []


def cmd_create(args):
    d = call("POST", "/api/new_address", body={
        "name": args.name, "domain": args.domain, "enablePrefix": True})
    print(f"address={d['address']}")
    print(f"jwt={d['jwt']}")
    print(f"address_id={d.get('address_id')}")
    print("# persist the jwt — it is the only key to read this mailbox", file=sys.stderr)


def cmd_list(args):
    d = call("GET", f"/api/mails?limit={args.limit}&offset=0", jwt=args.jwt)
    mails = mail_list(d)
    if not mails:
        print("(empty)")
        return
    for m in mails:
        print(f"{m['id']}  {m.get('source', '?')}  {m.get('created_at', '')}")


def cmd_otp(args):
    rx = re.compile(args.regex)
    deadline = time.time() + args.timeout
    seen = set()
    while time.time() < deadline:
        d = call("GET", f"/api/mails?limit=10&offset=0", jwt=args.jwt)
        for m in mail_list(d):
            if m["id"] in seen:
                continue
            seen.add(m["id"])
            try:
                mail = _call("GET", f"/api/mail/{m['id']}", jwt=args.jwt)
            except RuntimeError:
                continue  # mail may have been cleaned up between list and fetch
            match = rx.search(json.dumps(mail, ensure_ascii=False))
            if match:
                print(match.group(0))
                return
        time.sleep(args.poll)
    sys.exit(f"no OTP match within {args.timeout}s")


def main():
    global AUTH, BASE
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--auth", help="site password (else TEMPMAIL_SITE_AUTH or wrangler.toml)")
    p.add_argument("--base", default=BASE_DEFAULT, help="API base URL")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="new mailbox -> address + jwt")
    c.add_argument("name")
    c.add_argument("--domain", default="gyukopo.dev")
    l = sub.add_parser("list", help="recent mails")
    l.add_argument("jwt")
    l.add_argument("--limit", type=int, default=10)
    o = sub.add_parser("otp", help="poll inbox and print OTP code")
    o.add_argument("jwt")
    o.add_argument("--timeout", type=int, default=90)
    o.add_argument("--poll", type=float, default=3.0)
    o.add_argument("--regex", default=OTP_RE_DEFAULT,
                   help="code pattern; default skips years, timestamps, and tz offsets (+0000)")
    args = p.parse_args()
    AUTH = site_auth(args.auth)
    BASE = args.base
    {"create": cmd_create, "list": cmd_list, "otp": cmd_otp}[args.cmd](args)


if __name__ == "__main__":
    main()

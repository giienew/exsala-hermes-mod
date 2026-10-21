#!/usr/bin/env python3
"""Walk a protobuf payload from a HAR (or raw file) and print its structure.

Proto API bodies (YouTube youtubei/v1/*, iOS apps, etc.) arrive in a HAR's
response content.text as RAW BYTES (Python str of non-ASCII chars), NOT
base64 and NOT JSON — so har_to_client.py's JSON walker prints nothing
useful for them. This walks the raw bytes: field number, wire type, value,
recursing into length-delimited (wire-2) messages.

Usage:
    python3 scripts/proto_walk.py --har out.har --entry 19
        # entry = index into log.entries; uses response content.text
    python3 scripts/proto_walk.py --file body.pb
        # a saved raw binary payload (e.g. server response body)
    python3 scripts/proto_walk.py --stdin < body.pb

Bytes fidelity note: HAR text went through JSON/UTF-8 decoding, so it
round-trips to bytes only when every char is < 256 (common). Pass --file
with the true binary for a lossless walk when available.
"""
import argparse
import json
import sys


def read_varint(buf, i):
    val = 0
    shift = 0
    while True:
        b = buf[i]
        i += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, i
        shift += 7


def ascii_like(p):
    return bool(p) and all(32 <= b < 127 or b in (9, 10, 13) for b in p)


def walk(buf, indent=0, depth=0):
    i = 0
    n = len(buf)
    pad = "  " * indent
    while i < n:
        try:
            key, i = read_varint(buf, i)
        except IndexError:
            return
        field, wire = key >> 3, key & 7
        if wire == 0:
            val, i = read_varint(buf, i)
            print(f"{pad}f{field} varint = {val}")
        elif wire == 1:
            print(f"{pad}f{field} 64bit  = {buf[i:i+8].hex()}")
            i += 8
        elif wire == 2:
            ln, i = read_varint(buf, i)
            payload = buf[i:i + ln]
            i += ln
            if ascii_like(payload):
                print(f"{pad}f{field} str    = {payload.decode('ascii')!r}")
            elif depth < 8 and payload and is_message(payload):
                print(f"{pad}f{field} msg    =")
                walk(payload, indent + 1, depth + 1)
            else:
                print(f"{pad}f{field} bytes  = {payload.hex()[:80]}{'...' if len(payload) > 40 else ''} ({len(payload)}B)")
        elif wire == 5:
            print(f"{pad}f{field} 32bit  = {buf[i:i+4].hex()}")
            i += 4
        else:
            print(f"{pad}f{field} wire={wire} skipping")
            return
    return i


def is_message(payload):
    # rough heuristic: first bytes read as a plausible varint field key
    try:
        k, _ = read_varint(payload, 0)
        return (k >> 3) >= 1 and (k & 7) in (0, 1, 2, 5)
    except IndexError:
        return False


def from_har(har, idx):
    with open(har) as f:
        data = json.load(f)
    text = data["log"]["entries"][idx]["response"]["content"].get("text", "")
    if not text:
        sys.exit(f"entry {idx} has no content.text (was the response base64-gzipped? check content.encoding)")
    return text.encode("latin1", errors="replace")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--har", help="HAR file to read a response body from")
    src.add_argument("--entry", type=int, help="log.entries index for --har")
    src.add_argument("--file", help="raw binary protobuf file")
    src.add_argument("--stdin", action="store_true", help="read raw bytes from stdin")
    args = ap.parse_args()

    if args.har:
        if args.entry is None:
            sys.exit("--har requires --entry N")
        walk(from_har(args.har, args.entry))
    elif args.file:
        with open(args.file, "rb") as f:
            walk(f.read())
    elif args.stdin:
        walk(sys.stdin.buffer.read())


if __name__ == "__main__":
    main()

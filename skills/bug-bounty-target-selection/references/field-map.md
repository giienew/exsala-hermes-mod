# bounty-targets-data field map

Raw source: `https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/master/data/`

## Files
- `hackerone_data.json` (~18MB) — LIST of program dicts
- `bugcrowd_data.json` (~1.1MB) — LIST
- `yeswehack_data.json` (~130KB) — LIST
- `intigriti_data.json` (~590KB) — LIST
- `domains.txt` — every in-scope domain, one per line (~36k lines)
- `wildcards.txt` — every wildcard scope (~3.5k lines)

All four program files are top-level JSON lists (not keyed dicts) — iterate directly, `data[0]` is a valid probe.

## hackerone_data.json
- `handle`, `name`, `url`, `offers_bounties` (bool), `submission_state` ('open' | other)
- `response_efficiency_percentage` (int)
- `targets.in_scope[]`: `asset_identifier`, `asset_type` ('WILDCARD' | 'URL' | 'CIDR' | ...), `eligible_for_bounty` (bool), `max_severity` ('CRITICAL' | 'HIGH' | 'MEDIUM' | ...)
- `handle` != `name`: match by `name` first, then map to `handle` for URL construction.
- No max-bounty dollar figure per program; severity ceilings live on targets — payout tables are per-report and not in this dump.

## bugcrowd_data.json
- `name`, `max_payout` (filter `> 0` for paid programs), `targets.in_scope[]` with asset fields similar to H1.
- No response-efficiency metric — rank Bugcrowd programs by payout + scope shape only.

## intigriti_data.json
- `max_bounty` / `min_bounty` — may be non-int (string or structured); coerce defensively before sorting.
- `status` for open/closed.

## yeswehack_data.json
- Smallest set (~59 programs); probe `data[0]` keys before assuming field names — structure differs per platform.

## Scoring recipe (rank "empuk" targets by)
1. `response_efficiency_percentage` — high = reports actually read (H1 only field)
2. Bounty-eligible ratio = eligible_for_bounty / total in-scope — 100% beats partial
3. Wildcard count — subdomain surface for subfinder/nuclei
4. Critical severity allowed — headroom for high-sev findings
5. Domain fit: fintech/login-heavy (IDOR = money) over static marketing sites

## Known-good parse (python)
```python
import json
h1 = json.load(open('/tmp/bb/hackerone_data.json'))
paid = [p for p in h1 if p.get('offers_bounties') and p.get('submission_state') == 'open']
for p in paid:
    ins = p['targets']['in_scope']
    nb = sum(1 for t in ins if t.get('eligible_for_bounty'))
    crit = sum(1 for t in ins if (t.get('max_severity') or '').lower() == 'critical')
    wild = [t['asset_identifier'] for t in ins if t.get('asset_type') == 'WILDCARD']
    score = p.get('response_efficiency_percentage', 0) * 2 + nb * 2 + len(wild) * 3 + crit
```

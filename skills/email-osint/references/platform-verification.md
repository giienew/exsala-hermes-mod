# Platform Verification Patterns

Decision table for account-existence checks. Core rule: a "hit" requires page CONTENT evidence, not just an HTTP status.

## Reliable JSON APIs (no auth, no login wall)

| Platform | Endpoint | Exists when |
|---|---|---|
| GitHub | `https://api.github.com/users/USER` | HTTP 200, JSON has `"login"` |
| GitLab | `https://gitlab.com/api/v4/users?username=USER` | non-empty JSON array; gives id, name, state, avatar_url |
| CodeWars | `https://www.codewars.com/api/v1/users/USER` | 200 = exists; 404 `{"success":false,"reason":"not found"}` = absent |
| DockerHub | `https://hub.docker.com/v2/users/USER/` | 200 = exists; 404 `User not found` = absent |
| Keybase | `https://keybase.io/_/api/1.0/user/lookup.json?username=USER` | status.code 0 = exists; code 205 = absent |

GitLab's `avatar_url` contains `secure.gravatar.com/avatar/<sha256-of-email>` — comparing that hash to the target email's SHA256 proves the account belongs to the email owner.

## HTML platforms — status code is NOT enough

| Platform | Status for missing profile | Verification grep on page content |
|---|---|---|
| Pinterest | 200 (lies) | `<title>` contains the display name |
| Instagram | 200 (lies) | direct fetch = JS shell with NO og meta or JSON blobs from datacenter IPs — verify via search-index snippet (bio + follower counts) or a browser session |
| Twitch | 200 (lies) | look for the user's display name in embedded JSON |
| Steam | 200 + "The specified profile could not be found" | profile page contains actual persona name |
| YouTube | 404 for missing @handle | `<title>` is the channel name |
| GitLab HTML | 302 → sign-in for missing | `<title>NAME · GitLab</title>` |
| TikTok | 200 (lies) | JS shell, no `uniqueId` blob — verify via search snippet |
| Telegram | t.me preview renders for ANY username incl. nonexistent | preview pages prove nothing — only Bot API or a logged-in session confirm |
| Facebook | 400 bot-wall; mbasic also 400 (dead) | verify via search-index snippet (display name, friends, activity dates) or a browser session |
| PyPI | Cloudflare Client Challenge page | inconclusive from datacenter IPs |
| Devpost | 200 | meta description + portfolio header give display name, location, skills |

Generic pattern:

```bash
curl -sL -A "$UA" "https://platform/USER" -o page.html
grep -oE '<title>[^<]*</title>' page.html   # title should name the profile, not "Not Found"/login
```
## Gravatar details

- Hash input is the email **trimmed and lowercased**, MD5 (legacy) or SHA256 (newer).
- `https://gravatar.com/<hash>.json` — 404 means no profile; 200 returns `entry[0].name`, `hash`, `preferredUsername`, thumbnail URLs.
- `https://gravatar.com/<hash>.vcf` — vCard with FN (full name), nickname, URLs, timezone, base64 photo.
- `https://gravatar.com/<hash>` — HTML profile page, also works with the username slug.
- Check BOTH MD5 and SHA256 — some accounts only respond to one.
- `https://gravatar.com/avatar/<hash>?d=404` — 200 only if an avatar exists; the `d=404` param suppresses default-image false positives (fallback when `.json` is rate-limited).

## Known dead ends (don't retry these without new tooling)

- Reddit `/user/X/about.json` — bot-blocked from server IPs; inconclusive.
- HIBP — 401 without a paid API key.
- Facebook/Instagram direct verification — 400 bot-wall / JS shell; use search-index snippets or a browser session.
- Microsoft `login.microsoftonline.com/common/GetCredentialType` — returns uniform IfExistsResult for existent AND nonexistent addresses (confirmed with random controls); the enumeration vector is dead.
- Telegram t.me preview — rendered identically for any username, existent or not.

## Search-index snippet harvest (JS-wall bypass)

When a profile page is a JS shell, the search engine's cached og:description still carries the data. Query the QUOTED username with the built-in web_search tool first — it is not rate-limited like raw scraping; `"USER"` or `"USER" site:instagram.com` both work.

- Instagram snippets: bio + `N Followers, N Following, N Posts - name (@handle) on Instagram: "bio"`.
- Facebook snippets: display name, friend names, recent activity dates.
- Devpost snippets: display name + skill focus.

Raw-scrape fallback: `https://html.duckduckgo.com/html/?q=...` parses via regex on `class="result__a"` (links) and `class="result__snippet"` (text), but expect HTTP 202 challenge pages after ~5 queries — space requests or rotate engines (Bing/Mojeek HTML are unstable and frequently bot-walled).

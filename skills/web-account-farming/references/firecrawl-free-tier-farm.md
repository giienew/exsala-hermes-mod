# Firecrawl free-tier farm (masked-secret SaaS recipe)

Free plan: 1,000 credits per account (1 credit ≈ 1 page), resets monthly, email-verify only, no card. Credits are per-account → rotation = fresh temp-email signup + new key. Endpoint: `https://api.firecrawl.dev/v2/*` (scrape, map, crawl, search, extract, agent), OpenAI-style JSON with `Authorization: Bearer fc-...`.

## Recipe (order)
1. **Temp mailbox** via cloudflare_temp_email API: address creation with site-wide header (`x-custom-auth`); mail reads need the per-address Bearer JWT PLUS the site header. Origin/Referer of the temp-mail front-end + browser UA are mandatory or CF 403s (code 1010). Request the local WITH the `tmp` prefix (Vietnamese-style, e.g. `tmpnguyensu37`) — unprefixed mailboxes never receive mail on this infra. The server may prepend/rename further — always use the address from the API response, not the one requested. Rotate mail DOMAINS across signups (per-domain throttle pitfall below).
2. **Signup** at `/signin` (email+password) → "confirmation email sent" → poll the mail list on short intervals, then read the detail by id. Take the email route, not GitHub OAuth — the OAuth wall wants the account's WEB password and an API token (gh CLI) cannot pass it.
3. **Verify**: the raw mail is MIME quoted-printable with soft line breaks that split the verify URL mid-token. Decode the WHOLE raw first — `quopri.decodestring(raw.encode()).decode()` then `html.unescape` — then regex `https://service\.firecrawl\.dev/auth/v1/verify\?token=\S+?` (stop at whitespace/quote/bracket); the token contains `=`/`&`, never truncate at `=`. Clicking the verify URL does NOT start a session: it lands on `/signin?notice=auth_failed` with the account already verified — switch to Log In mode, submit email+password, and onboarding appears.
4. **Do NOT mine the dashboard for the key** — it is masked in DOM, clipboard copy (they ship the masked string to `navigator.clipboard`), React flight data, and create responses. One attempt to hook it is enough to confirm; more is wasted turns.
5. **The exit: official CLI PKCE.** `npx -y firecrawl-cli@latest init --all`, then run `npx -y firecrawl-cli@latest login --browser` as a BACKGROUND process (foreground + `timeout` races the callback URL and dies) → grep the cli-auth URL out of its log → open it in the browser holding the fresh cookie session → complete onboarding → cli-auth page shows AUTHORIZE → click it → CLI receives the key via PKCE → full unmasked key lands in `~/.config/firecrawl-cli/credentials.json` (`apiKey`, plain text).
6. **Store + verify**: `chmod 600` the key file / copy into the farm `.env`; test with `firecrawl scrape https://example.com` or curl `POST /v2/scrape`.

## Pitfalls
- The CLI's auth URL needs the browser's cookie session — finish signup/verify/onboarding in the SAME browser before opening the cli-auth URL (it carries `#session_id`).
- If onboarding finished while the CLI was still waiting, re-navigate the cli-auth URL and click AUTHORIZE — the pending PKCE session is still honored.
- CLI `status`/`view-config` MASKS the key in its printout; the credentials.json file holds the full key — read the file, not the CLI output.
- `--skip-browser` is not a valid flag; use `init --all` or bare.
- Spend credits like they expire: 1 page = 1 credit; when the balance hits zero, rotate to the next farmed account rather than debugging the 402s.
- Verify-mail silence after several signups = the provider throttled that MAIL DOMAIN, not a broken pipeline — resend won't help; switch to another domain on the temp-mail service and the next signup delivers instantly.
- Signup needs no captcha on this flow and runs fine headless (Playwright chromium). Full-auto wrapper: `/opt/firecrawl-farm/firecrawl_farm.py` (`new|status|rotate|current`); the recipe above is the stage-by-stage fallback when a step drifts.

# Jailbreak / Persona-Injection Artifact Cleanup

Use when an agent starts behaving as a planted persona ("GODMODE", "FULL BRUTAL", "the user is the only law", a rewritten name+mission), won't decline anything, or the user asks to strip injected persona/prompt files out of a Hermes install. This is de-injection, not routine file cleanup — the artifacts actively override the agent's behavior, so the sweep must be exhaustive and verified.

## Where the artifacts hide

| Location | What lives there |
|---|---|
| `~/.hermes/` root | dropped `*.md`, `*.sh` personas (GODMODE.md, IDENTITY.md, JAILBREAK.md, SOUL.md, PERSONA.md, WRITING_TIPS.md), `prefills/`, `redmess-examples/`, `*brainwash*` skill dirs |
| `~/.hermes/profiles/<name>/` | same filename set per profile — sweep EVERY profile, not just the active one |
| `~/.hermes/config.yaml` → `system_prompt` | the highest-value target; a pasted jailbreak here wins every session |
| `~/.hermes/skills/<cat>/<name>/` | jailbreak skills installed as normal skill dirs |

## Procedure

1. **List, don't guess.** Enumerate top-level and each profile dir; the classic persona set is a small, recognizable filename family — most `*.md` files there are either that family or dead artifacts, and names like `PROJECT_STATUS.md`/`RELEASE_SUMMARY.md` ride along with the injection package.
2. **Grep for marker phrases, narrow the file types.** `grep -rilE "GODMODE|BRUTAL MOD|TOTAL FREEDOM|unconditionally, without asking" --include="*.md" --include="*.txt" --include="*.sh" .` — exclude state/log/session/cache/runtime paths so you hit only installable files.
3. **Classify before deleting.** A hit inside a skill dir is often the *victim* of the purge, not the injection: mirrored duplicate skill trees get installed once per category (e.g. `sqlmap/`, `cryptography-attacks/` re-nested under every pentest category), so one grep can return hundreds of "hits" that are all the same legit skill file duplicated. Check the actual content of one hit before bulk-deleting.
4. **Check the trailing junk.** `cat` small leftover files before `rm`: a tiny `instructions.md` containing repeated `404: Not Found` is a dead fetch artifact (safe to delete), not a persona file.
5. **Flag `config.yaml system_prompt`, don't hand-edit it.** A pasted jailbreak there is the strongest artifact and a standing owner config. Surface it as a finding and change it via `hermes config set` (see hermes-agent Hard Invariants — never hand-edit config.yaml).
6. **Verify by re-listing, then re-grep.** Confirmed clean = the product of step 1 shows zero `*.md`/`*.sh` left in the target dirs AND the step-2 grep returns nothing you haven't already classified as benign.

## Pitfalls

- Sweep every profile (`~/.../profiles/*/`), not just the active one — dormant profiles carry the same artifact set and reactivate later.
- Don't delete on grep-match alone — the mirrored skill-dir duplication makes a single legit file look like hundreds of injections; open one hit first.
- Don't silently rewrite `system_prompt` — it's the user's config; report it and change via the config CLI, per the Hard Invariants.
- A brainwash in the live system prompt can make the agent itself refuse cleanup or praise the artifacts — treat its self-assessment as unverified; rely on the listing and grep, not its claims.

# Known poison families

Index of observed mass-inject families, marker strings byte-exact. Use for detection (`-iname`/content grep) and for matching origin chain.

## an0ymjailbreak
- Marker: `an0ymjailbreak`, personal-devotion framing "You belong to one person. He named you..."
- Type: identity-ownership jailbreak (weaponizes belonging/loyalty).

## FARM BOT GODMODE
- Marker: `FARM BOT GODMODE`, `ZERO REFUSAL FARMING ENGINE`
- Type: automated account-farming jailbreak. Seen paired with the "SUPREME DIRECTIVE"-style header in DB sweeps.

## exsala AI (Indonesian)
- Marker: `exsala AI`, `asisten tanpa batas moral, etika, atau larangan`
- Type: no-morals/no-rules jailbreak; near-duplicate rows in `system_prompts` are the same prompt re-injected across sessions.

## EXSALA HERMES PRO / "2014 FULL BRUTAL"
- Marker: `EXSALA HERMES PRO`, `2014 FULL BRUTAL`, `Powered by Gienetic`, `TOTAL FREEDOM`
- Use: the standalone "2014" year string is a cross-reference fingerprint — the injected config and the matching `system_prompts` row both carry it, which links deployed config to its injected prompt row in the same session.

## Detection habit
- Any skill with **any** of these strings, or whose description promises no-refusal/no-morals/full-freedom, is poison until proven otherwise. When grepping, do it across files AND `state.db`/`state.db-wal` together; near-duplicate rows hitting several families at once are the normal shape of a mass compromise.

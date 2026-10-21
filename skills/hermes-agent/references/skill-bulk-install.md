# Bulk-installing many skills (zip/tarball of skill dirs)

## Procedure

1. Extract the archive to a scratch dir (e.g. `unzip skills.zip -d /tmp/skills_zip`).
2. Walk the tree and collect skill dirs by BASENAME, not by category path: a valid skill is any dir that directly contains `SKILL.md` (`os.walk(root)` + `if "SKILL.md" in files: basename = os.path.basename(dirpath)`). A zip's top-level "category" dir (`recon/`, `redteam/`, `jailbreak/`) is NOT the skill — the category itself never has a SKILL.md.
3. Install into `$HERMES_HOME/skills/` (resolve `$HERMES_HOME`, never hardcode `~/.hermes`). Copy the skill dir, preserving its own `references/ scripts/ templates/` children — `shutil.copytree`, never a shallow copy.
4. Reconcile name collisions in the duplicate-first pass: compare `zip_sets - disk_sets`. A name can already exist as a NESTED skill (e.g. packaged twice, once flat and once under a category), and in that case the flat sibling is a marker FILE, not a dir with its own SKILL.md.
5. If a pre-existing entry is a file (no SKILL.md inside) at the target path, it is a stale duplicate marker — `os.remove()` it, then `shutil.copytree` the real skill dir in. Verify what a path IS (file vs dir-with-SKILL.md vs dir-of-nested-skills) before removing anything.
6. Verify with the loader, not the filesystem alone: call `skills_list()` and confirm the zip's skill count is present. Loader listing is the acceptance test.

## Pitfalls

- The loader namespaces skills by basename; category path (`redteam/x`) and flat (`x`) are the SAME skill. If a name already exists, the newly unpacked copy is a duplicate that must be reconciled (replace marker or skip) — never leave both as separate flat + nested copies.
- A dir that contains only nested skill dirs (no SKILL.md of its own) is a category/umbrella, not an installable skill — it comes along as casing, not as a top-level entry. Don't create a dir per category; skill dirs live as siblings under `$HERMES_HOME/skills/`.
- content search for `SKILL.md` (grep) and path walk find the same skills; use the set comparison `zip - disk` to get exactly the missing ones, and copy only those — copying everything double-writes the ones that already exist.
- After install, listing can show far more entries than the zip's skill count because nested/duplicate packaging expands; the check that matters is `zip_set ⊆ disk_set` (nothing missing), not exact equality.

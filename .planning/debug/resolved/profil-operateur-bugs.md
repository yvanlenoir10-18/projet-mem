---
status: fixing
trigger: "Investigate and fix ALL bugs in the operator profile (profil opérateur) of the Flask app at /home/user/projet-mem/cuf-pilotage/"
created: 2026-05-27T00:00:00Z
updated: 2026-05-27T00:00:00Z
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: CONFIRMED — Multiple bugs found and being fixed
  BUG-1 (CRITICAL): No operateur-role user in DB — Agent Saisie has role=admin, operateur profile unreachable for any logged-in user
  BUG-2 (ALREADY FIXED): _progression.html missing 'is defined' guard — fixed in commit 59b0031
  BUG-3 (Minor): _stats_operateur makes redundant second DB query for postes_semaine (inefficiency)
  BUG-4 (Logic): postes_semaine excludes a_corriger fiches from weekly count (correctable)
test: Applying fix to __init__.py to repair DB on next startup + code fix for postes_semaine
expecting: operator login with saisie@cuf.cm shows operator profile; stats show correctly
next_action: Fix __init__.py to repair DB roles on startup

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: The operator profile (accueil opérateur, formulaire de saisie, historique) should load and work without errors for a user with role='operateur'.
actual: At minimum, `jinja2.exceptions.UndefinedError: 'stats_operateur' is undefined` crashes the accueil page. Other bugs may exist.
errors: UndefinedError on _progression.html because `stats_operateur` is not passed from some routes. Possibly more issues.
reproduction: Login as operateur, navigate to /saisie/accueil
started: After git sync mismatch — templates are newer than the Python routes on the user's local copy. The fix to _progression.html (is defined guard) was already pushed, but saisie.py may still have issues.

## Eliminated
<!-- APPEND only - prevents re-investigating -->

- hypothesis: _stats_operateur() missing keys vs template
  evidence: All 11 keys returned; template uses all 11 correctly
  timestamp: 2026-05-27

- hypothesis: accueil_operateur route missing variables
  evidence: All variables used in template are passed from route
  timestamp: 2026-05-27

- hypothesis: historique route missing stats_operateur
  evidence: Route passes stats_operateur=stats_op correctly at line 1491
  timestamp: 2026-05-27

- hypothesis: record_trs | round | int crashes on None
  evidence: record_battu only set True when record_trs is non-None (code lines 1357-1359)
  timestamp: 2026-05-27

- hypothesis: max(autres) crashes with None values
  evidence: soumises filter at line 1322 already excludes trs_global=None, so autres has no None
  timestamp: 2026-05-27

## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2026-05-27
  checked: _progression.html guard condition
  found: Already has `is defined` guard (commit 59b0031). Original crash is already fixed.
  implication: Original crash was from template older than fix; now resolved.

- timestamp: 2026-05-27
  checked: DB user table — SELECT id, nom, email, role FROM user
  found: Only 3 users exist. Agent Saisie (saisie@cuf.cm) has role='admin' not 'operateur'. No operateur-role user exists at all.
  implication: CRITICAL — operator profile is unreachable. Any user logging in as saisie@cuf.cm gets admin role, not operateur. The _stats_operateur path (role == 'operateur') never triggers. The accueil page's progression widget never shows. The @roles_required('operateur',...) routes are accessible because admin matches, but the UX is wrong.

- timestamp: 2026-05-27
  checked: _init_donnees_defaut() in __init__.py
  found: Only creates users if `not User.query.first()` — won't fix existing wrong data
  implication: Need to add a DB repair migration for the saisie@cuf.cm user role

- timestamp: 2026-05-27
  checked: postes_semaine filter in _stats_operateur (line 1343)
  found: Includes a_verifier status (correct — fiches awaiting chef validation should count). Excludes a_corriger (debatable — but design choice).
  implication: Minor: operators who got all fiches sent back for correction see 0 postes_semaine even though they submitted them.

- timestamp: 2026-05-27
  checked: _stats_operateur second DB query
  found: Line 1342 calls Equipe.query.filter_by(user_id=user_id).all() again, after line 1321 already fetched all equipes
  implication: Redundant query. Can be optimized but not a crash.

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: DB data corruption — Agent Saisie (saisie@cuf.cm) seeded with role='admin' instead of 'operateur', causing no operateur-role user to exist. Combined with the _progression.html missing 'is defined' guard (already fixed). Two separate bugs, one DB data + one code.

fix:
  1. __init__.py: Add DB repair block to fix Agent Saisie role to 'operateur' and create missing Administrateur user
  2. saisie.py: Optimize postes_semaine to reuse already-loaded equipes (remove second DB query)
  3. saisie.py: Add a_corriger to postes_semaine count (operator submitted then got it back — should count for regularity)

verification:
files_changed: [app/__init__.py, app/routes/saisie.py]

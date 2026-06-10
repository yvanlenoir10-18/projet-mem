# Note d'impact mémoire — P65 : Retour à la coexistence chef + prod (revert de P64)
**Commit :** `Revert "refactor(auth): remove chef role, prod becomes sole production profile"` (6331133)
**Date :** 2026-06-10 (décision utilisateur du 2026-06-09, ré-appliquée)
**Nature :** Revert complet de P64 — restauration du rôle `chef` aux côtés du rôle `prod`
**Fichiers restaurés :** 23 fichiers (dont `app/templates/chef/dashboard.html` recréé) · `smoke.sh` enrichi de 4 checks prod

---

## 1. Ce qui a été fait

Revert git complet du commit P64 (`70f51e0`). Le rôle `chef` (Chef Scierie) est restauré dans tout le périmètre applicatif, aux côtés du rôle `prod` (Chef de Production) créé en P63. Les deux profils **coexistent** désormais comme deux profils distincts :

- `chef@cuf.cm` (rôle `chef`) → cockpit `/dashboard/chef` (P0–P3) + `/dashboard/chef/v2`
- `prod@cuf.cm` (rôle `prod`) → cockpit `/dashboard/prod` (V2 autonome)
- Routes analytiques partagées : `@roles_required('chef', 'prod', 'admin')`
- `ROLES_VALIDES = ('operateur', 'chef', 'prod', 'pdg', 'admin')`

## 2. Pourquoi (verbatim utilisateur, 2026-06-09)

> « ne supprime plus chef permet juste une distinction entre les deux c'est clair? »

L'utilisateur a annulé la décision P64 (suppression complète de chef) : les deux profils doivent rester distincts et utilisables. Décision **verrouillée** — consignée dans `ETAT.md`.

## 3. Incident de persistance (leçon de méthode)

Le revert original (09/06) avait été réalisé dans un environnement dont les commits **n'ont jamais atteint le remote**. Au changement de conteneur, le remote était resté à l'état P64 (chef supprimé) tandis que le résumé de session croyait la coexistence en place. Détecté le 10/06 lors d'un `git fetch` (rejet de push), corrigé par ré-application du revert. **Parade adoptée :** ETAT.md (état vivant versionné) + règle « pousser avant de clore toute session ».

## 4. Vérification

- `smoke.sh` : **20/20 verts** (16 checks d'origine + 4 checks prod ajoutés : `/dashboard/prod`, fiches, machines, pertes).
- Base : 5 comptes — `chef@cuf.cm` rôle `chef`, `prod@cuf.cm` rôle `prod` (créé idempotent au démarrage).
- Données simulées purgées (62 fiches + 109 arrêts) le 10/06 — base prête pour la saisie réelle.

## 5. Impact mémoire

Aucun impact sur les calculs ni les règles métier. La distinction chef/prod permet de présenter en soutenance deux niveaux de pilotage (scierie vs production) sans confondre leurs périmètres.

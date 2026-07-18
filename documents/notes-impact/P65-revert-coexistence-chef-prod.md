# Note d'impact mémoire — P65 : Retour à la coexistence chef + prod (revert de P64)
**Commits :** `Revert "refactor(auth): remove chef role..."` (6331133) · `test(smoke): 4 checks profil prod + docs` (ab34a71) · `docs: ETAT.md — fichier d'état vivant` (bda9947)
**Date :** 2026-06-10 (décision utilisateur du 2026-06-09, ré-appliquée)
**Nature :** Revert complet de P64 — restauration du rôle `chef` aux côtés du rôle `prod` · enrichissement du smoke test · adoption d'un fichier d'état de session
**Fichiers :** 23 fichiers restaurés par le revert (dont `app/templates/chef/dashboard.html` recréé) · `smoke.sh` (+4 checks) · `ETAT.md` (créé) · `.claude/rules/etat-vivant.md` (créé)

---

## 1. Ce qui a été fait

Revert git complet du commit P64 (`70f51e0`). Le rôle `chef` (Chef Scierie) est restauré dans tout le périmètre applicatif, aux côtés du rôle `prod` (Chef de Production) créé en P63. Les deux profils **coexistent** comme deux profils distincts :

- `chef@cuf.cm` (rôle `chef`) → cockpit `/dashboard/chef` (P0–P3) + `/dashboard/chef/v2`
- `prod@cuf.cm` (rôle `prod`) → cockpit `/dashboard/prod` (V2 autonome)
- Routes analytiques partagées : `@roles_required('chef', 'prod', 'admin')`
- `ROLES_VALIDES = ('operateur', 'chef', 'prod', 'pdg', 'admin')`

En complément : ajout d'une section « Chef de Production » au smoke test (4 checks) et création d'`ETAT.md`, fichier d'état vivant mis à jour à chaque fin de session.

## 2. Pourquoi (verbatim utilisateur, 2026-06-09)

> « ne supprime plus chef permet juste une distinction entre les deux c'est clair? »

L'utilisateur a annulé la décision P64 (suppression complète de chef) : les deux profils doivent rester distincts et utilisables. Décision **verrouillée** — consignée dans `ETAT.md`.

## 3. Incident de persistance (leçon de méthode)

Le revert original (09/06) avait été réalisé dans un environnement dont les commits **n'ont jamais atteint le remote**. Au changement d'environnement, le remote était resté à l'état P64 (chef supprimé) tandis que le résumé de session croyait la coexistence en place. Détecté le 10/06 par un rejet de `git push` (divergence), corrigé par `git fetch` + `git rebase` + ré-application du revert. **Parades adoptées :** `ETAT.md` versionné (l'état survit aux environnements) ; règle « pousser avant de clore toute session » ; `git fetch` en début de session.

## 4. Périmètre d'accès résultant

| Rôle | Accueil | Périmètre |
|---|---|---|
| `chef` | `/dashboard/chef` | Cockpit P0–P3, validation fiches, analyses, V2 en lecture |
| `prod` | `/dashboard/prod` | Cockpit V2 autonome + routes analytiques partagées (fiches, machines, pertes) |
| `admin` | `/dashboard/chef` | Tout |

La navigation (`base.html`) présente deux blocs distincts : section « Pilotage » pour chef/admin, section « Production » pour prod.

## 5. Lien avec les hypothèses du mémoire

Aucun impact sur les calculs (TRS, FCFA, Pareto) ni sur H1–H4. La distinction chef/prod renforce l'argument organisationnel : deux niveaux de pilotage (supervision scierie vs pilotage de production) reflétant l'organisation réelle de CUF — utile pour OS4 (structuration du pilotage) sans modifier aucune mesure.

## 6. Tests de non-régression

- `python -m compileall app/` : OK.
- `smoke.sh` : **20/20 verts** — 16 checks d'origine + 4 nouveaux (login prod, `/dashboard/prod`, `/dashboard/chef/fiches`, `/dashboard/chef/machines`, `/dashboard/pertes`). Le total de référence passe de 16 à 20 et **ne doit plus baisser**.
- Base : 5 comptes vérifiés — `chef@cuf.cm` rôle `chef`, `prod@cuf.cm` rôle `prod` (créé idempotent au démarrage par `_init_donnees_defaut`).

## 7. Risques résiduels

- La base de dev a été purgée des données simulées (62 fiches, 109 arrêts) le 10/06 : les dashboards afficheront des états vides jusqu'à la saisie réelle — comportement vérifié sans erreur, mais les écrans « vides » ne doivent pas être interprétés comme des bugs.
- Si un environnement antérieur au 10/06 réapparaissait, sa base locale pourrait contenir `chef@cuf.cm` migré en `prod` (migration P64) ; le code restauré ne corrige pas ce cas automatiquement — vérifier les rôles en base après tout changement d'environnement.

## 8. Prochaines étapes

1. Saisie des **données réelles** par l'utilisateur (la base est prête).
2. **P5 — Dashboard Chef « aiguilleur »** : cadrage prêt (note P59, plan `documents/plans/P5-dashboard-chef-aiguilleur.md`), en attente du feu vert utilisateur.
3. Activer le vérificateur séparé (maker ≠ checker) sur les prochaines formules critiques.

## 9. Contradiction avec une note précédente ?

**OUI — contradiction explicite et assumée avec P64.** La note P64 actait la suppression du rôle `chef` et la migration `chef@cuf.cm → prod`. P65 annule intégralement cette décision sur instruction utilisateur : la suppression était une sur-interprétation du besoin (l'utilisateur voulait une *distinction* entre deux profils, pas un *remplacement*). P64 reste dans l'historique comme trace de l'itération ; P65 fait foi. Aucune autre note antérieure n'est contredite : P63 (création du rôle prod) reste pleinement valide.

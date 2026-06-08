# Note d'impact mémoire — P64 : Suppression du rôle `chef` — `prod` profil unique de production

**Commit :** `refactor(auth): remove chef role, prod becomes sole production profile` (`70f51e0`)
**Date :** 2026-06-08
**Nature :** Refactoring RBAC — suppression complète d'un rôle, migration des comptes
**Fichiers modifiés :** 22 (routes, templates, utils, init, smoke test)
**Fichiers supprimés :** `app/templates/chef/dashboard.html`
**Migrations DB :** automatique via `_repair_seed_roles()` (idempotent, à chaque démarrage)

---

## 1. Ce qui a été supprimé

Le rôle `chef` (Chef Scierie, « ancien profil ») est entièrement retiré du code. Le
rôle `prod` (Chef de Production), introduit en P63, devient l'unique profil de pilotage
de la production et hérite intégralement du périmètre d'accès de l'ancien `chef`.

### Routes supprimées (`dashboard.py`)

| Route supprimée | URL | Devenir |
|---|---|---|
| `vue_chef()` | `/dashboard/chef` | Supprimée → 404. Le cockpit P0–P2 classique n'existe plus. |
| `vue_chef_v2()` | `/dashboard/chef/v2` | Supprimée → 404. Doublon de `vue_prod()`. |

`vue_prod()` (`/dashboard/prod`) est désormais le seul cockpit de production. Il rend le
template `chef/v2.html` (cockpit V2 : cascade économique, attribution D/P/Q, verdict
global).

### Template supprimé

`chef/dashboard.html` (le cockpit P0–P2, ~1400 lignes) était rendu uniquement par
`vue_chef()`. Devenu orphelin, il a été supprimé via `git rm`. Les partials qu'il
incluait (`_aujourdhui.html`, `_alertes.html`, `_priorites_chef.html`, `_signaux_p2.html`)
sont conservés : certains restent utilisés par d'autres vues.

### Rôle retiré de la registry

- `utils.py` : `'chef'` retiré de `ROLES_VALIDES` (désormais `operateur, prod, pdg, admin`)
  et de `_ACCUEIL_ROLE`. L'`admin` atterrit désormais sur `dashboard.vue_prod`.
- `admin.py` : `'chef'` retiré de `ROLES_DISPONIBLES` et `LIBELLES_ROLE` — non
  sélectionnable dans le formulaire de création d'utilisateur.

---

## 2. Héritage du périmètre d'accès

Toutes les autorisations de l'ancien `chef` ont été transférées à `prod`, par
remplacement systématique dans :

- **Décorateurs `@roles_required`** : `dashboard.py`, `problemes.py` (12 routes),
  `analyse.py`, `recommandations.py`, `admin.py` (paramètres), `saisie.py` (validation
  des fiches, saisie).
- **Contrôles fins `current_user.role in (...)`** : `saisie.py` (droit de valider une
  fiche, visibilité des indicateurs et de l'économie), `services/recommandations.py`
  (métadonnée `roles` des règles de prescription).
- **Templates** : `saisie/historique.html`, `saisie/detail.html`,
  `recommandations/index.html` (libellés et conditions d'affichage).

`prod` conserve ainsi la validation des fiches opérateurs, l'accès aux machines,
production, qualité, pertes, Pareto, Ishikawa, actions, prescriptions, export Excel,
paramètres opérationnels, et la saisie. Il reste exclu de la gestion des utilisateurs
et des prix financiers (admin uniquement, inchangé).

---

## 3. Migration des comptes

Décision utilisateur : **migrer `chef@cuf.cm` vers `prod`** (pas de suppression de compte).

- `_init_donnees_defaut()` : sur une base vierge, `chef@cuf.cm` est créé avec
  `role='prod'` (libellé « Chef de Production »).
- `_repair_seed_roles()` : sur une base existante, **tout** compte encore en `role='chef'`
  est converti en `prod` au prochain démarrage. La boucle est idempotente et couvre
  `chef@cuf.cm` ainsi que tout autre compte chef créé manuellement.

Vérifié à l'exécution : `chef@cuf.cm` se connecte (302), atteint `/dashboard/prod` (200),
et `/dashboard/chef` renvoie 404.

---

## 4. Navigation (`base.html`)

Le menu « Pilotage » réservé à `chef` a été supprimé. Le menu « Production » (introduit
en P63) est désormais conditionné par `('prod', 'admin')` : l'`admin` y accède aussi,
son tableau de bord pointant sur `vue_prod`. La section Configuration (Paramètres) et le
lien « Nouvelle saisie » passent également à `('prod', 'admin')` / `('operateur', 'prod',
'admin')`. Les libellés de rôle et couleurs d'avatar ne référencent plus `chef`.

---

## 5. Lien avec les hypothèses du mémoire

Aucune hypothèse H1–H4 n'est contredite. Les moteurs de calcul (TRS D×P×Q, cascade
économique, Pareto, attribution des pertes) sont **inchangés** — seule la couche
d'accès et de présentation est refactorée. Les indicateurs produits pour `prod` sont
identiques à ce que produisait `chef`.

**Note de cohérence mémoire** : le mémoire et les documents antérieurs parlent parfois du
« profil Chef » ou « Chef de Production » indistinctement. Après P64, la dénomination est
unifiée : un seul profil de pilotage, **Chef de Production** (rôle technique `prod`).
L'audit « Profil Chef de Production » (plan archivé) reste valide — son objet est
exactement ce profil unique, désormais sans ambiguïté de nommage.

---

## 6. Tests de non-régression

- Compilation Python : `exit 0`
- Smoke test : **16/16 verts**, dont une assertion ajoutée : `/dashboard/chef` → 404
- Vérifications manuelles :
  - `chef@cuf.cm` migré → `/dashboard/prod` 200, `/dashboard/chef` 404
  - `admin` redirigé vers `/dashboard/prod` après login
  - `prod@cuf.cm` (P63) toujours opérationnel

---

## 7. Risques résiduels

- **Documentation skill** : `run-cuf-pilotage/SKILL.md` mentionne encore `chef@cuf.cm`
  comme « rôle chef » dans la table des comptes de test. Le compte fonctionne (migré en
  prod) mais le libellé est obsolète. À corriger lors d'une passe documentaire.
- **Données historiques** : aucune table ne stocke le rôle hors de `User.role`, donc
  aucune donnée métier n'est affectée par la suppression.
- **Réversibilité** : la suppression de `chef/dashboard.html` (cockpit P0–P2) est
  récupérable via l'historique git si un besoin de revenir au cockpit classique
  apparaissait. Le commit `70f51e0` isole proprement ce retrait.

---

## 8. Prochaines étapes

Le plan actif reste **P5-A** (diagnostic mixte : Source B + indice de confiance +
cockpit aiguilleur). Il s'applique désormais à un profil unique `prod`, ce qui simplifie
le ciblage : plus de distinction chef/prod à gérer dans les routes et templates de P5-A.

---

## 9. Contradiction avec une note précédente ?

**Contradiction partielle, assumée et résolue.** La note **P63** présentait `prod` et
`chef` comme deux profils **coexistants** (« Les deux rôles coexistent »). P64 supprime
cette coexistence : `chef` disparaît, `prod` devient unique. Ce n'est pas une erreur de
P63 mais une décision produit ultérieure de l'utilisateur (« supprimer le profil chef »).
La logique de `vue_prod` décrite en P63 est inchangée — seule sa concurrente `vue_chef`
est retirée. Les notes P60 et P62 (relatives à `vue_chef_v2`) décrivent une route
désormais supprimée : elles restent valides comme trace historique mais ne décrivent plus
de code actif.

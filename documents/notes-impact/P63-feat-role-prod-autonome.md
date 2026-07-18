# Note d'impact mémoire — P63 : Rôle `prod` autonome — Chef de Production

**Commit :** `feat(auth): add dedicated production chief role` (`4b50bc3`)
**Date :** 2026-06-08
**Nature :** Nouvelle fonctionnalité RBAC — séparation complète du rôle `prod` vs `chef`
**Fichiers modifiés :** `app/__init__.py`, `app/utils.py`, `app/routes/auth.py`,
`app/routes/dashboard.py`, `app/routes/admin.py`, `app/routes/analyse.py`,
`app/routes/recommandations.py`, `app/routes/problemes.py`,
`app/templates/base.html`, `app/templates/admin/users.html`
**Fichiers ajoutés :** aucun
**Migrations DB :** aucune (migration automatique via `_repair_seed_roles()` au démarrage)

---

## 1. Ce qui a été ajouté

### Nouveau rôle `prod`

Un cinquième rôle `prod` (Chef de Production) a été créé, entièrement distinct du
rôle `chef` (Chef Scierie, ancien profil). Les deux rôles coexistent et accèdent à des
tableaux de bord séparés.

| Rôle | Dashboard principal | Périmètre |
|---|---|---|
| `chef` | `/dashboard/chef` | Cockpit scierie classique (P0–P2) |
| `prod` | `/dashboard/prod` | Cockpit V2 (cascade économique, D/P/Q) |

### Route `/dashboard/prod`

Nouvelle route `vue_prod()` dans `dashboard.py` :
- Accessible uniquement aux rôles `prod` et `admin`
- Réutilise le template `chef/v2.html` (cockpit V2) comme base temporaire
- Injecte : TRS moyen, cascade économique (`cascade_economique()`), attribution
  D/P/Q, statut global VERT/ORANGE/ROUGE, priorités chef, machine top, nb problèmes ouverts

### Mise à jour des `@roles_required`

10 routes existantes mises à jour pour accepter `prod` en plus de `chef` et `admin` :
fiches chef, machines, production, qualité, actions, nouvelle action, changer statut,
pertes financières, export Excel, vue_chef_v2.

Analyse Pareto (`analyse.arrets`), prescriptions (`recommandations.index`) et toutes
les 12 routes Ishikawa (`problemes.*`) intègrent également `prod`.

### Séparation des accès

Le rôle `prod` est explicitement exclu de :
- `/admin/utilisateurs` (gestion utilisateurs — admin uniquement)
- `/admin/parametres` prix financiers (`PARAMS_ADMIN_ONLY` — admin uniquement, inchangé)
- `/dashboard/chef` — la route chef bloque un `prod` (403 → 302)
- `saisie.nouveau_poste` — la saisie opérateur reste `operateur/chef/admin`

### Compte de test `prod@cuf.cm`

Le compte est créé dans `_init_donnees_defaut()` avec `role='prod'` (correction de la
création initiale qui utilisait `role='chef'`). La migration automatique dans
`_repair_seed_roles()` corrige toute DB existante au prochain démarrage de l'app :

```python
prod_user = User.query.filter_by(email='prod@cuf.cm').first()
if prod_user and prod_user.role != 'prod':
    prod_user.role = 'prod'
    db.session.flush()
```

### Menu `base.html`

Un bloc de navigation dédié `Production` est affiché si `current_user.role == 'prod'`
(sidebar desktop + offcanvas mobile), avec `/dashboard/prod` comme premier lien. Le
label rôle dans la user card affiche désormais les libellés lisibles (`Chef de
Production`, `Chef Scierie`, `Administrateur`, `PDG`, `Opérateur`) au lieu du
code technique.

---

## 2. Ce qui n'a PAS changé

- Le rôle `chef` et son cockpit `/dashboard/chef` sont intacts — aucune régression.
- Le modèle `User` n'a pas été modifié — le champ `role` (String 20) supporte déjà `prod`.
- Aucune migration Flask-Migrate — la DB évolue via le mécanisme idempotent existant.
- Les calculs TRS, Pareto, cascade économique sont identiques pour `prod` et `chef`.
- Les 16 checks du smoke test passent tous après le commit.

---

## 3. Lien avec les hypothèses du mémoire

**H1** (production réelle < capacité théorique) : non affectée — les calculs TRS
restent identiques pour les deux rôles.

**H2** (causes organisationnelles et techniques identifiables via saisie) : non
affectée — l'accès à l'Ishikawa et au Pareto est préservé pour `prod`.

**H3** (TRS réel < 60 %) : non affectée.

**H4** (outil de pilotage améliore la prise de décision) : **renforcée positivement**.
La création d'un rôle dédié `prod` illustre concrètement que l'outil peut être adapté
à différents profils utilisateurs dans la même structure hiérarchique, ce qui est un
argument de généricité pour OS6 (adaptabilité de l'outil).

Aucune hypothèse n'est contredite.

---

## 4. Argument mémoire (OS6 — adaptabilité)

Le profil `prod` démontre que l'architecture RBAC de wood_pilot permet de créer des
vues métier distinctes sans modifier le modèle de données ni les services de calcul.
Un Chef de Production (supervision de la chaîne complète) et un Chef Scierie (pilotage
poste par poste) peuvent utiliser le même outil avec des interfaces adaptées à leur
niveau de responsabilité. C'est un argument de robustesse architecturale pour la
soutenance.

---

## 5. Tests de non-régression

- Compilation Python : `exit 0` (aucune erreur de syntaxe)
- Smoke test : **16/16 verts**
- Vérification manuelle via curl :
  - `prod@cuf.cm` → login 302, `/dashboard/prod` → 200 ✓
  - `/admin/utilisateurs` avec session `prod` → 302 (bloqué) ✓
  - `/dashboard/chef` avec session `prod` → 302 (bloqué) ✓

---

## 6. Variables d'environnement / configuration

Aucun nouveau `Parametre` ajouté. `ROLES_DISPONIBLES` dans `admin.py` inclut
maintenant `'prod'`, ce qui le rend sélectionnable dans le formulaire de création
d'utilisateur. `LIBELLES_ROLE` est un dict de présentation, sans impact fonctionnel.

---

## 7. Risques résiduels

- Le template `chef/v2.html` est partagé entre `vue_chef_v2` (rôle `chef`) et
  `vue_prod` (rôle `prod`). Si un futur développement diverge les deux vues, il faudra
  dupliquer le template en `prod/dashboard.html`. Le plan P5-A peut être l'occasion
  de cette séparation.
- Le label rôle "prod" dans la user card est traduit côté template — si un nouveau rôle
  est ajouté, penser à mettre à jour le bloc conditionnel dans `base.html`.

---

## 8. Prochaines étapes

Le plan actif est **P5-A** (diagnostic mixte : Source B + indice de confiance +
cockpit aiguilleur). Il est compatible avec l'architecture `prod/chef` : les fonctions
`diagnostic_prioritaire()` et `analyse_recommandations()` seront accessibles aux deux
rôles via les routes existantes.

---

## 9. Contradiction avec une note précédente ?

**Aucune contradiction.** La note P60 décrit la création de `vue_chef_v2` pour le
rôle `chef` — P63 crée `vue_prod` pour le rôle `prod` en réutilisant le même template.
Les deux coexistent. La note P62 (fix variables manquantes) reste valide car les mêmes
variables sont passées correctement dans `vue_prod`.

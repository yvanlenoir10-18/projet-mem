# Note d'impact mémoire — P62 : Fix variables template manquantes dans vue_chef_v2

**Commit :** `fix(P60): compléter vue_chef_v2 — 3 variables template manquantes`
**Date :** 2026-06-08
**Nature :** Correction silencieuse — affichage dégradé sans erreur Flask visible
**Fichiers modifiés :** `app/routes/dashboard.py` (2 appels `render_template` dans `vue_chef_v2`)
**Fichiers ajoutés / supprimés :** aucun.

---

## 1. Ce qui a été corrigé

La route `vue_chef_v2` (commit P60) appelait `render_template('chef/v2.html', ...)` sans
passer trois variables utilisées par le template :

| Variable | Utilisation dans `v2.html` | Effet sans passage |
|---|---|---|
| `equipes_vides` | `{% if equipes_vides %}` — bloc cas vide | Jinja2 évalue `Undefined` comme `False` → le bloc vide ne s'affiche jamais, même sans fiches |
| `nb_postes` | `{{ nb_postes }} poste(s) validés ({{ jours }} j)` | Affichage de la chaîne vide `""` dans le sous-titre du verdict |
| `nb_problemes_ouverts` | `Problèmes ({{ nb_problemes_ouverts }})` dans les liens rapides | Badge affiché vide au lieu du compteur réel |

Les deux appels `render_template` ont été complétés :

- **Cas vide** : `equipes_vides=True`, `nb_postes=0`, `nb_problemes_ouverts=nb_problemes_ouverts`
- **Cas normal** : `equipes_vides=False`, `nb_postes=len(equipes)`, `nb_problemes_ouverts=nb_problemes_ouverts`

---

## 2. Pourquoi ce bug était silencieux

Jinja2 en mode par défaut (`Undefined`) ne lève pas d'erreur sur les variables manquantes :
- `{{ nb_postes }}` → rendu `""` sans exception
- `{% if equipes_vides %}` → évalue à `False` sans exception
- `{{ nb_problemes_ouverts }}` → rendu `""` sans exception

Flask ne loggue rien. Le smoke test vérifie le HTTP 200 mais pas le contenu rendu.
Seule une inspection visuelle ou un test de rendu Playwright aurait détecté le problème.

---

## 3. Ce qui n'a PAS changé

La logique métier de `vue_chef_v2` (TRS, cascade, attribution D/P/Q) est intacte.
Le template `v2.html` n'a pas été modifié. La route `/chef` (fallback) est intacte.
Aucune migration DB.

---

## 4. Lien avec les hypothèses du mémoire

Aucune hypothèse H1–H4 n'est affectée. Ce fix est purement correctif — il rend la Vue 1
conforme à sa spécification P60. L'affichage du badge `Problèmes (N)` dans les liens
rapides était le seul élément fonctionnellement impactant (le chef ne pouvait pas savoir
combien de problèmes Ishikawa étaient ouverts sans cliquer).

---

## 5. Tests de non-régression

Smoke test 16/16 vert après le fix.

---

## 6. Variables d'environnement / configuration

Aucun changement de `Parametre`, de `PARAMS_ADMIN_ONLY`, ni de constantes.

---

## 7. Leçon retenue

Le mode `Undefined` de Jinja2 masque les variables manquantes dans les `render_template`.
Pour tout nouveau template, vérifier systématiquement que chaque `{{ var }}` et
`{% if var %}` a une valeur explicite passée, y compris pour les cas `False` / `0` / `[]`.

---

## 8. Prochaines étapes

Le plan P5-A (diagnostic mixte : Source B + indice de confiance + cockpit aiguilleur)
est le prochain lot. Précondition : `git fetch` + vérifier la branche locale à jour
avant toute modification.

---

## 9. Contradiction avec une note précédente ?

**Aucune contradiction.** Ce fix complète P60 sans en modifier la logique. La note P60
décrit la route comme fonctionnelle — elle l'est maintenant pleinement, avec les trois
variables correctement passées.

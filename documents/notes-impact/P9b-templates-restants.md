# Note d'impact mémoire — P9b : Templates restants Canopée (detail poste, pertes financières, alertes chef)
**Commit :** `301c7a8` — `feat(ui): templates restants Canopée — detail poste, pertes financières, alertes chef`
**Date :** 2026-05-05
**Addendum de :** P9-ui-canopee.md (`be7f166`)
**Fichiers modifiés :** `app/templates/saisie/detail.html` (réécrit, +456 lignes redesignées) · `app/templates/dashboard/pertes.html` (réécrit, +603 lignes redesignées) · `app/templates/chef/_alertes.html` (réécrit, 66 lignes)

---

## 1. Ce qui a été implémenté

P9b complète la refonte Canopée entamée en P9 en redesignant les trois templates qui n'avaient pas été traités lors du premier commit UI. Comme P9, P9b **ne modifie aucune route Flask, aucun calcul métier et aucune logique de base de données** — seule la présentation change.

### `saisie/detail.html` — Page de détail d'une équipe (poste)

Ce template affiche le détail complet d'un poste saisi : informations générales, TRS décomposé, volumes produits par essence, analyse des pertes D/P/Q, et liste des arrêts.

**Décisions de design :**

Le TRS est présenté en **hero section** avec un accent `border-top: 3px solid {{ trs_color }}` coloré dynamiquement selon le niveau de performance. Le mapping entre la chaîne de couleur Bootstrap retournée par la route (`couleur_trs = 'success'|'warning'|'danger'`) et les tokens Canopée est résolu en tête de template via un bloc Jinja `{% set %}` :

```jinja2
{% if couleur_trs == 'success' %}{% set trs_color = 'var(--wp-leaf)' %}
{% elif couleur_trs == 'warning' %}{% set trs_color = 'var(--wp-ochre)' %}
{% else %}{% set trs_color = 'var(--wp-terracotta)' %}{% endif %}
```

Ce pattern évite de modifier la route Flask tout en obtenant la couleur sémantique souhaitée — le template adapte la donnée à son contexte visuel plutôt que l'inverse.

Les **quatre cartes KPI TRS** (Disponibilité, Performance, Qualité, TRS global) utilisent chacune un accent `border-top` coloré : ochre pour D, sky pour P, leaf pour Q, et la couleur dynamique `trs_color` pour le TRS global — même logique que le dashboard Chef, mais à l'échelle d'un seul poste.

La **table des pertes** (section D/P/Q) colore chaque ligne avec le token correspondant en fond semi-transparent (`rgba(..., 0.06)`) et la ligne de total sur fond emerald léger. L'accès au dict `pertes` retourné par `calcule_pertes_equipe()` utilise la notation pointée Jinja2 (`pertes.perte_d`) qui résout automatiquement les clés dict comme les attributs d'objet.

Les **boutons d'action** (Soumettre, Modifier, Verrouiller, Déverrouiller) sont contrôlés par les booléens `peut_soumettre`, `peut_modifier`, `peut_verrouiller`, `peut_deverrouiller` injectés par la route — identique à l'ancien template, dans un bandeau d'en-tête wp-card-header avec justification flex.

### `dashboard/pertes.html` — Tableau de bord Pertes financières

Ce template présente l'analyse mensuelle des pertes de production en FCFA, structurée autour de cinq éléments visuels.

**Sélecteur de période :** le dropdown mois/année est redesigné avec Bootstrap Dropdown mais stylé en Canopée (fond `--wp-cream`, border `--wp-line`, items hover sur `--wp-cream-2`). Il s'agit d'un lien `GET` simple — pas de JavaScript spécifique.

**Quatre KPI cards** : total pertes (terracotta), pertes D organisationnelles (ochre), pertes P opérationnelles (sky), pertes Q matière (leaf) — les couleurs suivent la sémantique D/P/Q établie dans P9 pour l'ensemble de l'interface.

**Donut Chart.js** D/P/Q : couleurs `['#C5973A', '#6FA8B5', '#3F8A5C']` (ochre, sky, leaf) — identiques aux tokens P9 pour cohérence. Le donut est positionné à droite des KPI dans une grille 8/4 Bootstrap.

**Tableau drill-down machine :** chaque ligne machine possède un bouton chevron qui révèle les arrêts sous-jacents. La ligne de détail utilise `style="display:none"` (et non la classe Bootstrap `d-none`) car les styles `.wp-table` redéfinissent la visibilité des lignes de manière incompatible avec `d-none`. La fonction JS `toggleArrets(id)` permute `display:none`/`display:table-row` et applique `transform: rotate(90deg)` au chevron pour signaler l'état ouvert/fermé.

**Pareto Chart.js** : barres terracotta (`#D87149`), courbe cumulée emerald (`#1F5C3D`) — identique à `analyse/arrets.html` (P9) pour une cohérence visuelle entre les deux pages d'analyse.

### `chef/_alertes.html` — Bannières d'alertes du dashboard Chef

Ce partial est inclus via `{% include %}` dans `chef/dashboard.html`. Il affichait deux alertes Bootstrap (`.alert-warning`, `.alert-info`) que P9 avait prévu de redesigner.

**Décision :** les bannières utilisent désormais des `<div>` avec **styles inline** plutôt que des classes Bootstrap `.alert-*`, pour deux raisons :
1. Les tokens Canopée (`--wp-ochre`, `--wp-sky`) ne correspondent pas aux variables Bootstrap utilisées par `.alert-warning`/`.alert-info` — une surcharge CSS aurait été plus fragile.
2. Le composant étant autonome (partial inclus), les styles inline garantissent qu'il s'affiche correctement même si le fichier `style.css` n'est pas chargé ou en cas de conflit de priorité.

L'alerte « saisies manquantes » utilise un fond et une bordure ochre semi-transparents (`rgba(197,151,58,...)`), et l'alerte « brouillons oubliés » utilise un fond et une bordure sky (`rgba(111,168,181,...)`). Les badges de postes et de brouillons sont des `<a>` avec classe `wp-pill wp-pill-warning` / `wp-pill wp-pill-info` — des liens cliquables vers les routes de saisie correspondantes.

---

## 2. Lien avec les objectifs du mémoire

P9b complète OS6 dans sa dimension ergonomique, en assurant que **toutes les pages de l'application** — y compris le détail d'un poste individuel et l'analyse financière mensuelle — sont alignées sur la même direction visuelle. Une incohérence de design entre pages (ancien style sur `detail.html`, nouveau sur `chef/dashboard.html`) aurait nui à la crédibilité de l'outil lors des démonstrations terrain.

La page `dashboard/pertes.html` est particulièrement liée à **OS3** (« estimer le coût financier des pertes enregistrées ») et **OS4** (« identifier et hiérarchiser les causes »). Son design — KPI financiers en tête, donut D/P/Q, drill-down machine, Pareto — traduit visuellement la démarche analytique décrite dans ces objectifs.

La page `saisie/detail.html` est liée à **OS2** (collecte de données) : c'est la page qu'un chef de production consultera pour valider les saisies d'un opérateur avant de les soumettre. Son design — boutons d'action clairs, TRS immédiatement visible en tête, arrêts avec catégories colorées — facilite cette validation.

---

## 3. Données et calculs mobilisés

P9b n'introduit aucun nouveau calcul. Les variables utilisées dans chaque template sont celles déjà documentées dans les notes précédentes :

**`detail.html` :** `poste` (objet `Equipe`), `trs`, `couleur_trs` (string Bootstrap → mappé localement en token Canopée), `pertes` (dict retourné par `calcule_pertes_equipe()`), `productions` (liste d'objets `Production`), `arrets` (liste d'objets `Arret`), `peut_soumettre/modifier/verrouiller/deverrouiller` (booléens de gouvernance P8).

**`pertes.html` :** `total_d`, `total_p`, `total_q`, `total_global` (FCFA), `machines` (liste de tuples machine × perte × nb arrêts), `essences` (dict essence → volume), `par_shift` (dict), `pareto` (liste triée pour Chart.js), `nb_equipes` (dénominateur pour les moyennes), `mois_annee` (période affichée), `mois_list` (dropdown), `chart_labels/durees/cumul` (arrays JSON pour Chart.js).

**`_alertes.html` :** `alertes.saisies_manquantes` (liste de dicts `{date_iso, date_fmt, shift}`), `alertes.brouillons_oublies` (liste de dicts `{id, date_fmt, shift, jours}`).

---

## 4. Hypothèses testées ou confirmées

**P9b ne contredit aucune hypothèse du mémoire.** L'analyse est identique à P9 :

- **H1, H2** : non impactées. Les templates affichent des données calculées par les routes existantes.
- **H3** (TRS réel < 60 %) : le hero de `detail.html` affiche le TRS avec couleur dynamique — si le TRS réel terrain est inférieur à 50 %, la bannière apparaîtra en terracotta (danger), confirmant visuellement H3 sans manipulation des données.
- **H4** (actions correctives sans investissement majeur) : P9b réaffirme que l'amélioration ergonomique est elle-même une action corrective sans investissement matériel.

**Aucune contradiction signalée.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

**Section OS6 — Outil de pilotage :**

La page `detail.html` peut être illustrée dans la section descriptive de l'outil pour montrer le **workflow de validation d'un poste** : l'opérateur saisit → le chef ouvre le détail → vérifie TRS, productions, arrêts → soumet ou renvoie en correction. Ce workflow en trois étapes est rendu visible par les boutons d'action conditionnels.

**Section OS3 — Estimation des pertes financières :**

La page `pertes.html` peut être directement citée comme livrable de l'OS3. Le tableau de bord présente la décomposition D/P/Q en FCFA, le drill-down par machine, et le Pareto des catégories d'arrêt — exactement la structure analytique requise par l'objectif.

**Section Méthodologie — Recueil des alertes :**

Le partial `_alertes.html` illustre le mécanisme de **rappel automatique** intégré à l'outil : un chef qui oublie de saisir un poste voit apparaître une bannière ochre dès sa prochaine connexion. Ce mécanisme est un argument de fiabilité de la collecte de données (OS2).

---

## 6. Limites actuelles

- **Drill-down non paginé :** si une machine cumule plus de 20 arrêts sur un mois, la ligne de détail peut devenir longue. Aucun mécanisme de pagination ou de troncature n'est implémenté — acceptable en contexte CUF où le nombre d'arrêts par machine reste modeste.
- **`_alertes.html` en styles inline :** l'utilisation de styles inline plutôt que des classes CSS dans le partial le rend moins maintenable. Si les tokens de couleur Canopée changent, il faudra mettre à jour `style.css` **et** les valeurs rgba hardcodées dans `_alertes.html`. À documenter comme dette technique légère.
- **Mapping `couleur_trs` en tête de `detail.html` :** la logique de mapping Bootstrap→Canopée est dupliquée dans `detail.html` et `historique.html`. Si une troisième page en a besoin, une macro Jinja centralisée serait préférable — hors périmètre du stage.
- **Pas de test de régression E2E :** les trois templates sont validés par inspection visuelle uniquement. Un test Playwright screenshot comparison aurait détecté d'éventuels problèmes de rendu — hors périmètre.

---

## 7. Vérification de cohérence avec les notes précédentes

**Note P9-ui-canopee.md :** la section 9 mentionnait « Page `saisie/detail_poste.html` : vérifier si elle existe et l'aligner avec Canopée si nécessaire. » P9b ferme ce point : `detail.html` est aligné. **Cohérence confirmée, point en suspens résolu.**

**Note P7-alertes-validations.md :** la note P7 documentait la fonction `_alertes_chef()` et la structure des dicts `saisies_manquantes` et `brouillons_oublies`. P9b utilise exactement ces structures dans `_alertes.html` — les liens `url_for('saisie.detail_poste', poste_id=b.id)` et `url_for('saisie.nouveau_poste')` sont ceux documentés dans P7. **Cohérence confirmée.**

**Note P6-F3-calculateur-gain-fcfa.md :** le calculateur de gain en FCFA (gain potentiel si TRS passe à 70/80/85 %) est visible dans `dashboard/pertes.html` via une section dédiée. Les variables `gain_70`, `gain_80`, `gain_85` sont injectées par la route — identiques à ce que P6-F3 avait documenté. **Cohérence confirmée.**

**Note P8-rbac-gestion-utilisateurs.md :** les boutons `Verrouiller` et `Déverrouiller` dans `detail.html` sont conditionnels sur les booléens de gouvernance P8. Les URLs (`url_for('saisie.verrouiller_equipe', ...)`, `url_for('saisie.deverrouiller_equipe', ...)`) pointent vers les routes protégées par `@roles_required` décrites dans P8. **Cohérence confirmée.**

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien avec P9b |
|---|---|
| Jaouane (2022) — Tableau de bord, Général Emballage, Algérie | La page `pertes.html` adopte la structure KPI-synthèse → graphique → tableau-détail décrite dans Jaouane comme optimal pour un tableau de bord de pilotage industriel : l'indicateur agrégé d'abord, l'analyse ensuite. |
| Laine (2024) — Reporting visuel, Metsä Board, Finlande | La présentation du TRS en hero avec décomposition D/P/Q dans `detail.html` reflète le format de reporting shift-by-shift documenté par Laine dans le contexte des scieries nordiques. |
| Kankkunen & Holopainen (2024) — Daily management, UPM Plywood | Les bannières d'alerte de `_alertes.html` sont la traduction technique du principe de « management visuel quotidien » : le chef voit immédiatement ce qui nécessite son attention (postes manquants, brouillons oubliés) sans chercher dans les menus. |
| Steenkamp et al. (2017) — VMS open-source, Afrique du Sud | Le drill-down machine dans `pertes.html` reproduit le principe de « zoom sémantique » du VMS de Steenkamp : la vue agrégée suffit pour le pilotage quotidien ; la vue détaillée est disponible en un clic pour le diagnostic. |

---

## 9. Prochaines étapes

- **Test complet de l'interface sur Windows :** avec les trois templates désormais alignés, l'interface Canopée est **complète sur toutes les pages de l'application**. Le test Windows peut couvrir l'ensemble des rôles : opérateur (saisie + historique), chef (dashboard + detail + alertes + pertes), PDG (dashboard PDG), admin (gestion utilisateurs + paramètres).
- **Vérifier l'URL `saisie.detail_poste` dans `_alertes.html` :** l'URL `url_for('saisie.detail_poste', poste_id=b.id)` doit correspondre exactement au nom de route dans `saisie.py`. Une erreur de nom de blueprint produirait un `BuildError` Flask à l'exécution — à valider lors du premier lancement.
- **Décider du sort de la barre de recherche :** maintenant que la refonte est complète, trancher définitivement : implémenter la recherche globale (route Flask + requête SQLAlchemy multi-champs) ou masquer le champ dans `base.html`. La deuxième option est préférable dans le contexte du stage.
- **Captures d'écran pour le mémoire :** avec `detail.html` et `pertes.html` disponibles, il est possible de documenter le workflow complet OS3 : saisie → validation → analyse des pertes → chiffrage FCFA. Ces quatre captures forment une séquence narrative pour la section Résultats.
- **Évaluer un addendum de synthèse P9-P9b :** si la section OS6 du mémoire présente la refonte UI comme un seul livrable (ce qui est logique d'un point de vue narratif), les notes P9 et P9b peuvent être consolidées en un seul document de présentation. Les deux notes restent utiles comme journal technique, mais le mémoire peut les citer comme « Phase UI Canopée (commits be7f166 + 301c7a8) ».

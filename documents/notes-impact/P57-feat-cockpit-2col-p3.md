# Note d'impact mémoire — P57 : Cockpit 2 colonnes P3
**Commit :** à venir — `feat(chef): cockpit 2 colonnes + accordéons — restructuration P3`
**Date :** 2026-06-04
**Nature :** Refonte visuelle cockpit Chef — **aucun changement de modèle de données, aucune migration**
**Fichiers modifiés :** `app/templates/chef/dashboard.html` (réécrit) · `app/templates/chef/_aujourdhui.html` (allégé) · `app/templates/chef/_priorites_actions.html` (nouveau)

---

## 1. Ce qui a été implémenté

Restructuration complète du cockpit Chef en 2 colonnes avec accordéons, résolvant le problème d'altitude identifié lors de l'audit P0 (verdict global enfoui à la position 8 d'un scroll de 19 sections).

**Colonne gauche (sticky, ~42 %)** — cockpit décisionnel permanent :
- Verdict global VERT/ORANGE/ROUGE en position 1 (était position 8)
- TRS compact avec Matin/Après-midi inline (remplace le HERO TRS pleine largeur)
- Manque à gagner en FCFA compact avec lien « Détail D/P/Q → » (était position 10)
- Priorités du chef + Actions immédiates (extraites de `_aujourdhui.html` vers nouveau partial `_priorites_actions.html`)
- Alertes saisies + Signaux P2 (inchangés)
- Machine critique + Pareto top-1 (inchangés, compactés)
- Bouton « Fiches à traiter »

La colonne gauche est `position:sticky;top:16px` avec `max-height:calc(100vh - 80px);overflow-y:auto` — elle reste visible pendant que la droite défile.

**Colonne droite (accordéons, ~58 %)** — détails à la demande :
- **Accordéon 1 — Aujourd'hui** (ouvert par défaut) : KPIs objectif/fiches/arrêts/rendement/déclassement + Postes du jour
- **Accordéon 2 — Performance & Analyse** (fermé) : D×P×Q, Manque à gagner détaillé, Scorecard semaine, Graphiques TRS, Tableau essences, Matrice arrêts, Simulateur de gain
- **Accordéon 3 — Boucle d'amélioration** (fermé) : Boucle Lean + Actions Chef **fusionnés** en une seule carte + Recommandations
- **Accordéon 4 — Saisies & Traçabilité** (fermé) : Traçabilité fiches + Anomalies R1-R8

**Fusions réalisées :**
- Boucle Lean (ex-section 6) + Actions Chef (ex-section 7) → carte unique « Cycle d'amélioration continue » : les compteurs dupliqués disparaissent, les 3 boutons (Analyses, Nouvelle action, Suivre) sont regroupés.

**Déplacements :**
- Simulateur de gain → accordéon Performance (outil d'analyse, pas un signal cockpit)
- Traçabilité fiches + Anomalies de saisie → accordéon Saisies (opérationnel, pas cockpit)

**Architecture template :**
- `_priorites_actions.html` (nouveau) : extrait Priorités + Actions immédiates de `_aujourdhui.html`
- `_aujourdhui.html` (allégé) : conserve uniquement KPIs + Postes du jour
- Le graphique TRS est initialisé via `show.bs.collapse` pour éviter que Chart.js tente de rendre un canvas dans un accordéon fermé (canvas non visible → dimensions à 0)

---

## 2. Lien avec les objectifs du mémoire

Contribue directement à **OS6** (outil de pilotage adapté) et au test des 10 secondes.

- La colonne gauche sticky répond à la question « est-ce que l'usine est sous contrôle ? » sans aucun scroll. Verdict + TRS + Manque à gagner + décisions prioritaires sont visibles en permanence.
- Les accordéons réduisent la charge cognitive : un chef qui veut juste vérifier le TRS ne voit pas les 18 autres sections. Il ouvre ce dont il a besoin.
- La structure 2 colonnes est citables dans la section **conception UI** du mémoire comme exemple de hiérarchie décisionnelle appliquée (altitude 1 vs altitude 2-3).

---

## 3. Données et calculs mobilisés

Aucune donnée nouvelle. La restructuration est purement visuelle et organisationnelle — tous les helpers backend (`vue_chef`, `_priorites_chef`, `_projection_production_active`, etc.) sont appelés de façon identique. Seul l'arrangement des `{% include %}` et la structure HTML ont changé.

---

## 4. Hypothèses testées ou confirmées

- **H4** (outil de pilotage adapté) : P3 démontre qu'un outil de pilotage doit hiérarchiser l'information par altitude décisionnelle, pas simplement l'afficher. La structure 2 colonnes est l'implémentation concrète de ce principe.

**Aucune contradiction signalée.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

P3 est citable dans la section **conception et validation de l'outil** (OS6). Il démontre :
- La capacité à itérer sur un prototype fonctionnel sans régression (16/16 smoke tests verts après refonte)
- L'application du principe d'altitude décisionnelle (cockpit en tête, détails à la demande)
- La réduction de la redondance informationnelle (2 cartes Lean/Actions fusionnées)

---

## 6. Limites actuelles

- **Sticky column sur mobile** : sur écran < 992 px (col-lg-5), les deux colonnes s'empilent. La colonne gauche n'est plus sticky — elle précède simplement les accordéons. Comportement acceptable pour l'usage terrain (tablette en paysage OK).
- **Accordéon Performance & Analyse** : contient 6 sous-sections (D×P×Q, Scorecard, Graphiques, Essences, Matrice, Simulateur). Pourrait être découpé davantage en P4 si besoin.
- **Ishikawa et Recommandations** : la logique métier de ces deux modules est à revoir en phase suivante (annoncé lors de la validation P3).

---

## 7. Vérification de cohérence avec les notes précédentes

P3 est additif par rapport à P0, P1 et P2. Aucune modification des calculs TRS, des modèles de données, des routes existantes ni des autres templates.

`_priorites_actions.html` (nouveau) : extrait de `_aujourdhui.html`. Les variables injectées dans `vue_chef()` (`priorites_chef`, `actions_immediates`) restent identiques — seul le fichier template qui les consomme a changé.

`_aujourdhui.html` (allégé) : la signature d'inclusion reste `{% include 'chef/_aujourdhui.html' %}` dans `dashboard.html`. Les variables `kpi_jour`, `postes_du_jour`, `projection_active` sont inchangées.

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

- Hiérarchie décisionnelle et charge cognitive : Miller (1956), loi de Hick-Hyman. La réduction à 4 accordéons vs 19 sections réduit le nombre de choix perceptifs immédiats.
- Design d'interfaces opérationnelles : Nielsen (1994), heuristique n°8 (Esthetic and minimalist design). La colonne gauche applique ce principe — seul l'essentiel est visible par défaut.

---

## 9. Prochaines étapes

- **Validation P3 sur Windows** : `git pull` puis vérifier le layout 2 colonnes sur le profil Chef.
- **P4 — Révision Ishikawa + Recommandations** : revoir la logique métier de ces deux modules (signalé lors de la validation P3).
- **Ajustements visuels éventuels** : après retour terrain, possibilité d'ouvrir par défaut l'accordéon Analyse si le chef utilise principalement cette vue.

# Note d'impact mémoire — P9 : Refonte UI complète — Direction Canopée
**Commit :** `be7f166` — `feat: refonte UI complète — direction Canopée`
**Date :** 2026-05-05
**Fichiers modifiés :** `app/static/css/style.css` (nouveau, ~800 lignes) · `app/templates/base.html` (réécrit) · `app/templates/auth/login.html` · `app/templates/chef/dashboard.html` · `app/templates/pdg/dashboard.html` · `app/templates/saisie/historique.html` · `app/templates/saisie/formulaire.html` · `app/templates/analyse/arrets.html` · `app/templates/admin/users.html` · `app/templates/admin/parametres.html` · `app/templates/errors/404.html` (nouveau) · `app/templates/errors/500.html` (nouveau) · `app/models.py` (propriétés `prenom`, `initiales`) · `app/__init__.py` (handlers erreur)

---

## 1. Ce qui a été implémenté

P9 est une **refonte visuelle complète** de l'interface WoodPilot. Aucune route Flask, aucun calcul métier et aucune logique de base de données n'ont été modifiés. Seule la couche de présentation a changé.

### Système de design « Canopée »

Un fichier CSS unique (`style.css`) définit un système de design cohérent inspiré de la forêt tropicale camerounaise :

| Token | Valeur | Usage |
|---|---|---|
| `--wp-emerald` | `#1F5C3D` | Couleur primaire, sidebar active, boutons principaux |
| `--wp-leaf` | `#3F8A5C` | Succès, indicateurs TRS corrects, volumes conformes |
| `--wp-terracotta` | `#D87149` | Danger, arrêts machine, volumes perdus |
| `--wp-ochre` | `#C5973A` | Avertissement, TRS moyen, bois déclassé |
| `--wp-sky` | `#6FA8B5` | Information, rôle PDG |
| `--wp-cream` | `#FAF6EE` | Fond principal — rappel des planches de bois brut |
| `--wp-ink` | `#1B2620` | Texte principal — encre sur bois |

Tous les tokens Bootstrap 5 (`--bs-primary`, `--bs-success`, etc.) sont **surchargés** par ces valeurs : les composants Bootstrap hérités (boutons, alerts, badges) adoptent automatiquement la palette Canopée sans réécriture.

La typographie unique est **Manrope** (Google Fonts, poids 400 à 800), choisie pour sa lisibilité sur petits écrans et sa rigueur géométrique adaptée aux données chiffrées.

### Structure de navigation

Le layout passe d'une **navbar horizontale sombre** à une **sidebar blanche verticale de 260px** avec topbar sticky de 72px, selon la convention des outils de pilotage industriel modernes (Grafana, Metabase). Sur mobile, la sidebar devient un off-canvas Bootstrap déclenché par un hamburger dans la topbar.

La navigation reste **entièrement conditionnelle par rôle** (héritage de P8) :
- Opérateur : sections Données uniquement
- Chef / Admin : Pilotage + Données + Configuration
- PDG : Direction + Données

### Composants réutilisables

| Composant | Classe CSS | Usage |
|---|---|---|
| Carte KPI | `.wp-kpi` | Indicateurs numériques clés (TRS, volumes, FCFA) |
| Pill de statut | `.wp-pill-{success,danger,warning,neutral,info}` | Statuts arrêts, équipes, rôles utilisateurs |
| Avatar initiales | `.wp-avatar-{emerald,leaf,terra,sky,ochre}` | Représentation utilisateur sans photo |
| Hero section | `.wp-hero` | TRS global en bannière émera lde (dashboard Chef) |
| Table Canopée | `.wp-table` | Tableaux de données uniformisés |
| Carte de contenu | `.wp-card` + `.wp-card-header` | Conteneur de section standardisé |
| Barres CSS | `.wp-bars` | Graphiques simples sans Chart.js |
| Timeline 24h | `.wp-timeline .{run,slow,stop,off}` | État machine heure par heure |

### Détail par template

**`base.html`** : sidebar + topbar universels. `current_user.prenom` (prénom extrait de `nom`) et `current_user.initiales` (deux lettres pour l'avatar) nécessitaient deux nouvelles `@property` sur le modèle `User`, ajoutées sans migration de base de données (propriétés calculées, pas de colonnes DB).

**`auth/login.html`** : carte centrée 460px avec trois blobs de couleur en arrière-plan (emerald, leaf, terracotta). Eye button pour afficher/masquer le mot de passe. Les comptes de démonstration sont affichés dans un footer discret — utile pour les tests terrain.

**`chef/dashboard.html`** : hero TRS à fond emerald avec blob semi-transparent et quatre mini-stats (Disponibilité, Performance, Qualité, Gain potentiel). Calcul du gain JS préservé. Chart.js TRS en couleurs Canopée (#1F5C3D, #D87149, #C5973A).

**`pdg/dashboard.html`** : quatre `.wp-kpi` avec deltas colorés. Pareto top 5 en barres horizontales terracotta. TRS 12 mois `.wp-bars` en CSS pur.

**`saisie/historique.html`** : bande de quatre mini-KPI calculés en Jinja (`postes | selectattr | list | length`). Table `.wp-table` avec pills TRS (vert ≥ 70 %, ochre ≥ 50 %, rouge < 50 %) et pills statut (soumis / brouillon / verrouillé).

**`saisie/formulaire.html`** : trois cartes wp-card (informations, productions, arrêts). Tout le JavaScript de génération dynamique des lignes est **préservé à l'identique** — P9 ne touche pas à la logique métier JS.

**`analyse/arrets.html`** : Pareto Chart.js avec barres terracotta (#D87149) et courbe cumul emerald (#1F5C3D). Tables machine/catégorie avec pills Canopée mappées sur les six catégories d'arrêt (Mécanique → danger, Organisationnelle → warning, Approvisionnement → info, Maintenance planifiée → success, autre → neutral).

**`admin/users.html`** : avatars initiales colorés par rôle (terra=admin, leaf=chef, sky=PDG, emerald=opérateur), pills de rôle colorées selon la même logique. Trois modes dans un seul template (liste / création / modification) — structure inchangée, design Canopée appliqué.

**`errors/404.html` et `errors/500.html`** : templates autonomes (n'héritent **pas** de `base.html`) pour éviter la dépendance à `current_user` au moment de l'erreur. Classes `.wp-error-page` (full-bleed centré) et `.wp-error-code` (chiffre 5,5rem). Handlers enregistrés dans `create_app()`.

---

## 2. Lien avec les objectifs du mémoire

P9 répond directement à **OS6** : « concevoir un outil de pilotage adapté aux besoins des différents responsables de CUF pour assurer un suivi continu des performances de la chaîne 4. »

L'adjectif **adapté** dans OS6 a deux dimensions. La première, fonctionnelle (accès par rôle), a été couverte par P8. La seconde, ergonomique, est couverte par P9 : un PDG sans formation en informatique doit pouvoir lire ses KPI en moins de trois secondes ; un opérateur doit pouvoir saisir un poste sur un écran tactile sans formation préalable.

La direction Canopée traduit trois principes de conception décrits dans la littérature du Thème 6 :
1. **Différenciation visuelle par acteur** — chaque rôle dispose de codes couleur distincts (emerald pour le chef opérationnel, sky pour le PDG), facilitant la reconnaissance immédiate de son espace.
2. **Hiérarchie de l'information** — le hero TRS occupe 30 % de la page chef parce que le TRS est l'indicateur central du mémoire. Les données de détail (essence par essence, arrêt par arrêt) sont accessibles en scroll, pas en premier plan.
3. **Légitimité de l'outil sur le terrain** — un outil visuellement soigné inspire confiance aux utilisateurs et aux décideurs ; c'est un facteur documenté de l'adoption des systèmes de pilotage (Laine, 2024 ; Jaouane, 2022).

---

## 3. Données et calculs mobilisés

P9 n'introduit aucun nouveau calcul. Tous les indicateurs affichés existaient dans les routes Flask depuis P6/P7/P8. P9 ne fait que les présenter différemment.

Le seul ajout technique côté données concerne les propriétés `prenom` et `initiales` sur `User` :

```python
@property
def prenom(self):
    return self.nom.split()[0].title() if self.nom else ''

@property
def initiales(self):
    parts = self.nom.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return self.nom[:2].upper() if self.nom else '?'
```

Ces propriétés sont calculées à partir du champ `nom` existant — aucune migration de base de données n'est nécessaire. Pour les comptes de démonstration (`Agent Saisie`, `Chef Scierie`, `Directeur`), les initiales produites sont respectivement `AS`, `CS`, `D?` (un seul mot) — le fallback `nom[:2]` gère ce cas.

---

## 4. Hypothèses testées ou confirmées

**P9 ne contredit aucune hypothèse du mémoire.**

- **H1** (capacité théorique < 25 m³/poste) : non impactée. P9 affiche les mêmes valeurs calculées, dans un meilleur cadre visuel.
- **H2** (pertes principalement organisationnelles) : non impactée. La page Pareto utilise les mêmes données qu'avant P9.
- **H3** (TRS réel < 60 %) : non impactée. Le hero TRS du dashboard Chef affiche désormais le TRS en 4,5rem — la valeur reste celle calculée par la formule D × P × Q.
- **H4** (actions correctives sans investissement majeur) : **renforcée indirectement**. P9 est lui-même une preuve de H4 : une refonte ergonomique significative (meilleure adoption de l'outil, meilleure lecture des indicateurs) sans modification des équipements physiques ni des algorithmes de calcul.

**Aucune contradiction signalée.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

**Dans la section OS6 — Description de l'outil :**

La direction Canopée peut être présentée comme un choix délibéré de conception inspiré du contexte camerounais : palette forêt-bois (emerald, terracotta, ochre), typographie Manrope lisible sur petits écrans, fond crème évoquant les planches de bois. Ces choix ne sont pas décoratifs — ils ancrent l'outil dans l'identité de CUF et facilitent l'appropriation par des utilisateurs peu habitués aux interfaces numériques.

**Dans la section Résultats — Outil de pilotage :**

Les captures d'écran des dashboards Chef et PDG peuvent illustrer concrètement la différenciation des vues par rôle. Le tableau de bord Chef (hero TRS + scorecard semaine + Pareto arrêts) peut être mis en regard du tableau de bord PDG (KPI financiers + TRS 12 mois) pour démontrer que l'outil répond à des besoins distincts.

**Dans la section Discussion :**

La décision de ne pas développer l'outil « from scratch » (React/PostgreSQL) mais de choisir Flask + Bootstrap + CSS personnalisé est justifiable par les contraintes de maintenance post-stage. Un technicien CUF sans formation en développement peut comprendre et modifier un fichier HTML/CSS ; il ne peut pas maintenir une application React. P9 documente ce compromis.

---

## 6. Limites actuelles

- **Pas de dark mode :** choix délibéré documenté dans le handoff design. Le fond crème (#FAF6EE) est la norme de l'outil ; un dark mode nécessiterait de doubler tous les tokens CSS.
- **Typographie Google Fonts en ligne :** `Manrope` est chargée depuis `fonts.googleapis.com`. Sur un réseau local CUF sans accès Internet, la police ne se chargera pas et le navigateur utilisera `system-ui` comme fallback (déclaré dans le stack). Les espacements peuvent varier légèrement mais la lisibilité reste correcte.
- **Timeline 24h `.wp-timeline` :** le composant CSS est implémenté dans `style.css` mais **aucun template ne l'utilise encore** — les données machine heure par heure ne sont pas collectées dans le modèle actuel (seuls `heure_debut` et `heure_fin` des arrêts existent, pas un état continu toutes les heures). Ce composant est une préparation pour une collecte plus fine si besoin futur.
- **Barre de recherche dans la topbar :** le champ `<input placeholder="Rechercher…">` est présent dans `base.html` mais **non fonctionnel** — aucune route de recherche globale n'existe. Il est affiché uniquement sur desktop (`d-none d-lg-block`) et sera masqué si la fonctionnalité n'est pas développée.
- **Pas de tests visuels automatisés :** la validation de la mise en page repose sur l'inspection manuelle. Un test Playwright de screenshot comparison aurait pu garantir la non-régression — hors périmètre du stage.

---

## 7. Vérification de cohérence avec les notes précédentes

**Note P8-rbac-gestion-utilisateurs.md :** P8 annonçait « Phase 2 (UI/UX) : refonte de l'interface » comme prochaine étape. P9 est exactement cette phase. **Cohérence confirmée.**

**Note 00-cadrage-global-P1-P2-P3.md :** le cadrage documentait trois rôles (Agent administratif, Chef de production, PDG). P9 ajoute un quatrième rôle visible — `admin` — avec son propre code couleur (`wp-avatar-terra`, pill `wp-pill-danger`). Le cadrage ne mentionnait pas explicitement `admin` comme persona distinct. Ce n'est pas une contradiction : `admin` est un super-utilisateur technique, pas un acteur métier du mémoire. La note 00 reste valide.

**Note P6-F1 à P6-F5 et P7 :** tous les calculs et alertes documentés dans ces notes sont **préservés dans les templates** P9. Le calculateur de gain FCFA, le score de régularité CV, la scorecard semaine — tout le JavaScript métier a été conservé à l'identique. **Aucune régression fonctionnelle.**

**Note P5-dashboard-pdg-enrichi.md :** le dashboard PDG conserve `trs_moyen`, `couleur_trs`, `delta_trs`, `production_reelle`, `production_cible`, `perte_fcfa`, `rendement_global`, `rendement_par_essence` — toutes les variables documentées dans P5 sont toujours utilisées dans P9. **Cohérence confirmée.**

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien avec P9 |
|---|---|
| Jaouane (2022) — Tableau de bord, Général Emballage, Algérie | Jaouane documente que la lisibilité visuelle du tableau de bord conditionne son adoption par les responsables. La direction Canopée applique ce principe : hiérarchie de l'information, couleurs sémantiques, typographie lisible. |
| Laine (2024) — Reporting visuel, Metsä Board, Finlande | Laine insiste sur l'importance du reporting visuel dans les scieries nordiques. P9 transpose ce principe à une scierie africaine : le même type d'interface (KPI cards, charts, alertes) mais adapté au contexte CUF (fond crème-bois, couleurs forêt tropicale). |
| Kankkunen & Holopainen (2024) — Daily management, UPM Plywood | Le management quotidien nécessite que l'information soit accessible en quelques secondes. Le hero TRS en 4,5rem sur fond emerald répond à ce principe : le chef de production voit son indicateur clé sans chercher. |
| Mncwango & Mdunge (2025) — DMAIC, OEE bas, Afrique du Sud | L'article souligne que les outils de pilotage OEE doivent être adaptés aux opérateurs de terrain, parfois peu formés. La palette tactile du formulaire de saisie (zones de clic larges, boutons touch 14px, labels clairs) répond à cette exigence. |

---

## 9. Prochaines étapes

- **Test terrain sur Windows (username : BWAME EBENGUE) :** vérifier que l'app démarre correctement depuis PowerShell, que la police Manrope se charge (si connexion Internet disponible), et que les dashboards s'affichent correctement sur la résolution de l'écran du stagiaire.
- **Validation par les personas :** idéalement, montrer les trois vues (opérateur / chef / PDG) à des représentants CUF lors du passage sur site et recueillir des retours. Ajuster les couleurs ou la taille des textes si besoin.
- **Captures d'écran pour le mémoire :** documenter les trois dashboards et la page de login pour les intégrer dans la section OS6. Préférer des captures avec des données réelles (post-terrain) plutôt que les données de démonstration actuelles.
- **Évaluer si `.wp-timeline` est pertinent :** si la collecte terrain permet de reconstituer l'état machine heure par heure (possible si l'opérateur saisit tous les arrêts avec leurs plages horaires), le composant timeline peut être activé sur la page analyse/arrets.
- **Désactiver la barre de recherche ou l'implémenter :** si la recherche globale n'est pas prévue dans le périmètre du stage, masquer définitivement le champ (`d-none`) pour éviter l'effet d'interface trompeuse (fonctionnalité visible mais inopérante).
- **Page `saisie/detail_poste.html` :** cette page est référencée dans `historique.html` (lien vers le détail d'une équipe) et `analyse/arrets.html` (lien sur la date). Elle n'a pas été redesignée dans P9 car elle n'existait pas dans les templates recensés. Vérifier si elle existe et l'aligner avec Canopée si nécessaire.

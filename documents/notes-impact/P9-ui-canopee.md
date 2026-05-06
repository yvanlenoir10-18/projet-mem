# Note d'impact mémoire — P9 : Refonte UI complète — Direction Canoée
**Commit :** `be7f166` — `feat: refonte UI complète — direction Canoée`
**Date :** 2026-05-05
**Fichiers modifiés :** `app/static/css/style.css` (nouveau, ~800 lignes) · `app/templates/base.html` (réécrit) · `app/templates/auth/login.html` · `app/templates/chef/dashboard.html` · `app/templates/pdg/dashboard.html` · `app/templates/saisie/historique.html` · `app/templates/saisie/formulaire.html` · `app/templates/analyse/arrets.html` · `app/templates/admin/users.html` · `app/templates/admin/parametres.html` · `app/templates/errors/404.html` (nouveau) · `app/templates/errors/500.html` (nouveau) · `app/models.py` (propriétés `prenom`, `initiales`) · `app/__init__.py` (handlers erreur)

---

## 1. Ce qui a été implémenté

P9 est une **refonte visuelle complète** de l'interface WoodPilot. Aucune route Flask, aucun calcul métier et aucune logique de base de données n'ont été modifiés. Seule la couche de présentation a changé.

### Système de design « Canoée »

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

Tous les tokens Bootstrap 5 (`--bs-primary`, `--bs-success`, etc.) sont **surchargés** par ces valeurs : les composants Bootstrap hérités (boutons, alerts, badges) adoptent automatiquement la palette Canoée sans réécriture.

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
| Hero section | `.wp-hero` | TRS global en bannière émeraude (dashboard Chef) |
| Table Canoée | `.wp-table` | Tableaux de données uniformisés |
| Carte de contenu | `.wp-card` + `.wp-card-header` | Conteneur de section standardisé |
| Barres CSS | `.wp-bars` | Graphiques simples sans Chart.js |
| Timeline 24h | `.wp-timeline .{run,slow,stop,off}` | État machine heure par heure |

### Détail par template

**`base.html`** : sidebar + topbar universels. `current_user.prenom` et `current_user.initiales` nécessitaient deux nouvelles `@property` sur le modèle `User`, ajoutées sans migration de base de données.

**`auth/login.html`** : carte centrée 460px avec trois blobs de couleur en arrière-plan. Eye button pour afficher/masquer le mot de passe. Comptes de démonstration dans un footer discret.

**`chef/dashboard.html`** : hero TRS à fond emerald avec blob semi-transparent et quatre mini-stats. Calculateur de gain JS préservé. Chart.js TRS en couleurs Canoée.

**`pdg/dashboard.html`** : quatre `.wp-kpi` avec deltas colorés. Pareto top 5 en barres horizontales terracotta. TRS 12 mois en Chart.js.

**`saisie/historique.html`** : bande de quatre mini-KPI calculés en Jinja. Table `.wp-table` avec pills TRS colorées et pills statut.

**`saisie/formulaire.html`** : trois cartes wp-card (informations, productions, arrêts). JavaScript de génération dynamique des lignes **préservé à l'identique**.

**`analyse/arrets.html`** : Pareto Chart.js avec barres terracotta et courbe cumul emerald. Tables avec pills Canoée mappées sur les six catégories d'arrêt.

**`admin/users.html`** : avatars initiales colorés par rôle, pills de rôle colorées. Trois modes dans un seul template.

**`errors/404.html` et `errors/500.html`** : templates autonomes (n'héritent **pas** de `base.html`) pour éviter la dépendance à `current_user` au moment de l'erreur.

---

## 2. Lien avec les objectifs du mémoire

P9 répond directement à **OS6** : « concevoir un outil de pilotage adapté aux besoins des différents responsables de CUF pour assurer un suivi continu des performances de la chaîne 4. »

La direction Canoée traduit trois principes de conception décrits dans la littérature du Thème 6 :
1. **Différenciation visuelle par acteur** — chaque rôle dispose de codes couleur distincts.
2. **Hiérarchie de l'information** — le hero TRS occupe 30 % de la page chef parce que le TRS est l'indicateur central du mémoire.
3. **Légitimité de l'outil sur le terrain** — un outil visuellement soigné inspire confiance (Laine, 2024 ; Jaouane, 2022).

---

## 3. Données et calculs mobilisés

P9 n'introduit aucun nouveau calcul. Le seul ajout technique concerne les propriétés `prenom` et `initiales` sur `User` :

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

Ces propriétés sont calculées à partir du champ `nom` existant — aucune migration de base de données n'est nécessaire.

---

## 4. Hypothèses testées ou confirmées

**P9 ne contredit aucune hypothèse du mémoire.**

- **H4** (actions correctives sans investissement majeur) : **renforcée indirectement**. P9 est lui-même une preuve de H4 : une refonte ergonomique significative sans modification des équipements physiques ni des algorithmes de calcul.

---

## 5. Ce que ce module permet de montrer dans le mémoire

**Dans la section OS6 — Description de l'outil :**
La direction Canoée peut être présentée comme un choix délibéré de conception inspiré du contexte camerounais : palette forêt-bois, typographie Manrope lisible sur petits écrans, fond crème évoquant les planches de bois.

**Dans la section Résultats — Outil de pilotage :**
Les captures d'écran des dashboards Chef et PDG peuvent illustrer la différenciation des vues par rôle.

**Dans la section Discussion :**
La décision de ne pas développer l'outil « from scratch » (React/PostgreSQL) mais de choisir Flask + Bootstrap + CSS personnalisé est justifiable par les contraintes de maintenance post-stage.

---

## 6. Limites actuelles

- **Pas de dark mode** : choix délibéré. Le fond crème (#FAF6EE) est la norme de l'outil.
- **Typographie Google Fonts en ligne** : sur un réseau local CUF sans Internet, le navigateur utilisera `system-ui` comme fallback.
- **Timeline 24h `.wp-timeline`** : composant CSS implémenté mais aucun template ne l'utilise encore.
- **Barre de recherche dans la topbar** : présente dans `base.html` mais non fonctionnelle.
- **Pas de tests visuels automatisés** : validation repose sur l'inspection manuelle.

---

## 7. Vérification de cohérence avec les notes précédentes

**Note P8 :** P8 annonçait « Phase 2 (UI/UX) : refonte de l'interface ». P9 est exactement cette phase. **Cohérence confirmée.**

**Notes P6-F1 à P6-F5 et P7 :** tous les calculs et alertes documentés sont **préservés dans les templates** P9. **Aucune régression fonctionnelle.**

**Note P5 :** le dashboard PDG conserve toutes les variables documentées dans P5. **Cohérence confirmée.**

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien avec P9 |
|---|---|
| Jaouane (2022) | La lisibilité visuelle du tableau de bord conditionne son adoption. |
| Laine (2024) | Reporting visuel dans les scieries nordiques — transposé au contexte CUF. |
| Kankkunen & Holopainen (2024) | L'information doit être accessible en quelques secondes. |
| Mncwango & Mdunge (2025) | Outils OEE adaptés aux opérateurs de terrain peu formés. |

---

## 9. Prochaines étapes

- **Test terrain sur Windows** : vérifier démarrage depuis PowerShell, chargement Manrope, affichage dashboards.
- **Validation par les personas** : montrer les trois vues à des représentants CUF et recueillir des retours.
- **Captures d'écran pour le mémoire** : documenter les trois dashboards et la page de login pour la section OS6.
- **Évaluer si `.wp-timeline` est pertinent** : activer si la collecte terrain permet de reconstituer l'état machine heure par heure.
- **Désactiver la barre de recherche ou l'implémenter** : masquer définitivement si non prévu dans le périmètre du stage.

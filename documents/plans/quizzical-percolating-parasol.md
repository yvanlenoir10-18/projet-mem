# Plan ACTIF — Profil opérateur, Wave 1, F1 : Accueil action-first (Option B)

**Branche :** `claude/install-claude-excel-6MGzv`
**Date :** 2026-05-27
**Approche :** discussion pros/cons avant chaque fonctionnalité, design soigné sur tout le profil opérateur (exigence explicite de l'utilisateur).

---

## Context

L'accueil opérateur (`accueil_operateur.html`) répond déjà à « que dois-je faire ? » via la carte de priorité dynamique. Il manque la deuxième motivation : « est-ce que je progresse ? ». Le bloc stats motivant existe mais il est enterré dans `historique.html` (page peu visitée) et codé en styles inline non réutilisables. F1 Option B remonte la progression sur l'écran le plus consulté et, au passage, transforme ce bloc en composant propre partagé — pour éliminer la duplication et poser une base design réutilisable par tout le profil.

But académique : renforce OS6 (outil de pilotage adapté) et la boucle de rétroaction opérateur (Kankkunen & Holopainen 2024 ; Mncwango & Mdunge 2025).

---

## Décisions de design

1. **Pas de copier-coller des styles inline.** On extrait un composant réutilisable à 3 niveaux :
   - Python : helper `_stats_operateur(user_id)` dans `saisie.py` → dict `{nb_equipes, trs_moyen, meilleur_trs, trs_recent, tendance}`.
   - Template : partial `saisie/_progression.html` inclus par l'accueil ET l'historique.
   - CSS : composant `.wp-progress*` dans `style.css` (remplace les styles inline de l'historique).
2. **Mobile-first** : les métriques passent de 1 ligne (desktop) à grille 2 colonnes sous 480px. Cible terrain = tablette/téléphone wifi.
3. **Cohérence Canopée** : réutilise les variables `--wp-leaf / --wp-ochre / --wp-terracotta / --wp-emerald / --wp-muted` et les seuils TRS existants (≥65 vert, ≥50 ochre, <50 terracotta).

---

## Étapes d'implémentation

### 1. `app/routes/saisie.py`
- Extraire la logique `stats_op` actuelle de `historique()` (lignes ~1384-1410) dans un helper module-level `_stats_operateur(user_id)` qui retourne le dict.
- `historique()` : remplacer le bloc inline par `stats_op = _stats_operateur(current_user.id) if current_user.role == 'operateur' else None`.
- `accueil_operateur()` (lignes 1283-1320) : ajouter `stats_operateur=...` au `render_template`. `fiches_aujourdhui` est déjà calculé et passé — il faut juste l'afficher.

### 2. Nouveau partial `app/templates/saisie/_progression.html`
- Reprend la logique emoji + message contextuel + 4 métriques + badge tendance, mais en classes `.wp-progress*` (zéro style inline).
- Garde-fou : `{% if stats_operateur is not none %}`. Gère l'état `nb_equipes == 0` (message de bienvenue).

### 3. `app/templates/saisie/accueil_operateur.html`
- Header : sous `wp-operator-kicker`, ajouter une ligne « {{ fiches_aujourdhui }} fiche(s) aujourd'hui » (discrète).
- Insérer `{% include 'saisie/_progression.html' %}` entre la carte priorité (ligne ~62) et `wp-operator-grid` (ligne 64), pour le rôle opérateur.

### 4. `app/templates/saisie/historique.html`
- Remplacer le bloc inline (lignes 194-269) par `{% include 'saisie/_progression.html' %}` → consistance visuelle, suppression de la duplication.

### 5. `app/static/css/style.css`
- Ajouter le composant `.wp-progress` (carte, bord gauche `--wp-leaf`), `.wp-progress-head` (emoji + message), `.wp-progress-metrics` (flex/grid responsive), `.wp-progress-metric` (valeur + label), `.wp-progress-trend` (badge ↑/↓). Réutilise `--wp-shadow-sm`, `--wp-line`, rayons 14px cohérents avec `.wp-operator-*`.

---

## Vérification end-to-end

1. Lancer l'app Flask dans `cuf-pilotage/`.
2. Se connecter en opérateur.
3. Accueil : vérifier (a) le compteur « X fiches aujourd'hui » dans le header, (b) le bloc progression entre carte priorité et grille, (c) couleurs TRS + badge tendance corrects.
4. Cas vide (opérateur sans poste soumis) : message de bienvenue 🌱, pas de crash.
5. Historique : même bloc affiché à l'identique (composant partagé).
6. Responsive 375px via Playwright : métriques lisibles en 2 colonnes, rien ne déborde.
7. Aucune régression chef/pdg/admin (bloc réservé à `operateur`).

---
---

# Plan PAUSED (phase chef) — Module Résolution Guidée (Ishikawa 6M + 5 Pourquoi)

> Conservé pour reprise après complétion du profil opérateur.

**Branche :** `claude/install-claude-excel-6MGzv`
**Date :** 2026-05-27
**Inspiration :** ProBeya "Structured Problem Resolution" → transposé bois/scierie

---

## Context

wood_pilot couvre déjà les piliers de mesure ProBeya (TRS D×P×Q, Pareto, criticité machine×catégorie, reco IA grounded). Ce qui manque pour la complétude du mémoire est **l'OS4** : "identifier et hiérarchiser les causes responsables de l'écart". L'Ishikawa 6M et les 5 Pourquoi sont les outils prescrit par le Dr Manga. Ce module les rend guidés, persistants et auditables — ni un tableau blanc mort, ni un PowerPoint. L'hypothèse H2 ("les pertes sont organisationnelles, pas techniques") sera vérifiable empiriquement via le champ `categorie_6m` des causes racines identifiées.

**Périmètre hors scope (validé par l'utilisateur) :** multi-tenant, connecteurs machines (MES), MCP server, signatures réglementaires, PWA offline. Terrain = tablette + wifi, saisie responsive suffit.

---

## Diagnostic — 16 capacités ProBeya vs wood_pilot

| # | Capacité ProBeya | Statut |
|---|---|---|
| 1 | TRS / analyse arrêts | ✅ Présent — D×P×Q, Pareto, criticité machine×catégorie |
| 2 | Dialogues performance (IA) | ✅ Présent — Claude/Groq grounded sur KPIs réels, cache 7j |
| 3 | Fiche suiveuse (dossier lot) | 🟡 Partiel — `fiche_poste.html` + AuditCorrection JSON snapshots |
| 4 | Contrôle qualité (SPC) | 🟡 Partiel — rendement matière, déclassé %, anomalies R3 |
| 5 | GMAO corrective | 🟡 Partiel — arrêts consignés + catégorie "Maintenance planifiée" |
| 6 | Passation de poste | 🟡 Partiel — workflow statuts + dupliquer poste |
| 7 | **Résolution guidée (Ishikawa)** | **❌ Absent — 1er module à implémenter** |
| 8 | SQCDL board quotidien | ❌ Absent — KPIs Q/C/D existent, S et L manquent |
| 9 | Actions + escalade T1→T3 | ❌ Absent — nécessaire pour la pérennité |
| 10 | Matrice compétences opérateurs | ❌ Absent |
| 11 | Marche Gemba / Leader Standard Work | ❌ Absent |
| 12 | SOPs versionnées + Kaizen photo | ❌ Absent |
| 13 | EHS + Andon | ❌ Absent |
| 14 | Flux matière / Kanban bois | ❌ Absent |
| 15 | Formation / onboarding | ❌ Absent |
| 16 | Portail audit / inspecteur | ❌ Absent (hors périmètre mémoire) |

**Score actuel : 2 présents + 4 partiels → Niveau 2 (Structuré) sur l'axe mesure. Niveau 1 (Réactif) sur les axes management visuel et résolution de problèmes.**

---

## Top 5 features à implémenter (roadmap priorisé)

| Priorité | Module | Justification | Lien mémoire |
|---|---|---|---|
| **1** | **Ishikawa + 5 Pourquoi guidés** | Comble OS4 directement ; vérifie H2 empiriquement | OS4, H2 |
| 2 | SQCDL board quotidien | Socle ProBeya ; KPIs Q/C/D déjà calculés (brancher S et L) | OS6 |
| 3 | Actions + escalade T1→T2→T3 | Transversal à tous les modules ; "l'infrastructure survit aux consultants" | OS5, OS6 |
| 4 | Matrice compétences opérateurs | Polyvalence, formation machine ; alimente H2 (causes organisationnelles) | OS4, H2 |
| 5 | EHS + Andon | Pilier S du SQCDL ; presque-accidents, arrêt ligne en 1 tap | OS6 |

---

## Module 1 — Ishikawa 6M + 5 Pourquoi (à implémenter)

### Modèle de données — 3 nouvelles tables

#### `Probleme`
| Colonne | Type | Contrainte | Notes |
|---|---|---|---|
| id | Integer | PK | |
| titre | String(200) | NOT NULL | |
| statut | String(20) | NOT NULL, default='ouvert' | ouvert → en_analyse → cause_identifiee → clos |
| description | Text | nullable | |
| contexte_quoi | Text | nullable | "Quel phénomène ?" |
| contexte_quand | Text | nullable | "Depuis quand / quelle fréquence ?" |
| contexte_ou | Text | nullable | "Sur quelle machine / essence ?" |
| contexte_combien | Text | nullable | "Quel impact quantifié ?" |
| equipe_id | Integer | FK('equipe.id'), nullable | Poste déclencheur |
| pareto_cause | String(200) | nullable | Cause Pareto texte verbatim |
| reco_code | String(50) | nullable | Ex. 'TRS_CRITIQUE' |
| cause_racine_selectionnee_id | Integer | nullable, **PAS de ForeignKey()** (évite FK circulaire SQLite) | Pointe vers IshikawaCause |
| actions_correctives | Text | nullable | Plan d'action libre |
| cree_par_id | Integer | FK('user.id') | |
| cree_le | DateTime | default=utcnow | |
| modifie_le | DateTime | onupdate=utcnow | |

**Transitions de statut :**
- `ouvert → en_analyse` : dès la 1re `IshikawaCause` ajoutée (dans `ajouter_cause()`)
- `en_analyse → cause_identifiee` : quand `sauver_racine()` est appelé
- `cause_identifiee → clos` : par le bouton Clôturer dans le rapport
- `clos → ouvert` : réouverture chef/admin uniquement

#### `IshikawaCause`
| Colonne | Type | Contrainte | Notes |
|---|---|---|---|
| id | Integer | PK | |
| probleme_id | Integer | FK('probleme.id'), NOT NULL | |
| categorie_6m | String(30) | NOT NULL | Machine \| Main d'oeuvre \| Matière \| Méthode \| Milieu \| Mesure |
| description | String(500) | NOT NULL | |
| est_racine | Boolean | default=False | Un seul True par probleme_id (enforced app-level) |
| cree_le | DateTime | default=utcnow | |

#### `PourquoiNiveau`
| Colonne | Type | Contrainte | Notes |
|---|---|---|---|
| id | Integer | PK | |
| cause_id | Integer | FK('ishikawa_cause.id'), NOT NULL | |
| niveau | Integer | NOT NULL | 1 à 5 |
| question | String(600) | NOT NULL | Auto-généré : "Pourquoi [description N-1] ?" |
| reponse | Text | nullable | Vide = non encore répondu |
| cree_le | DateTime | default=utcnow | |

**Règle de chaîne :** Pour ajouter le niveau N, `reponse` du niveau N-1 doit être non vide. La `question` du niveau N = `"Pourquoi " + reponse_N-1.strip() + " ?"`. Enforced dans `sauver_pourquoi()`.

**Décision technique clé :** `cause_racine_selectionnee_id` est déclaré `db.Column(db.Integer, nullable=True)` **sans** `db.ForeignKey()` pour éviter la référence circulaire `Probleme → IshikawaCause → Probleme` qui cause une erreur sur SQLite avec SQLAlchemy. L'intégrité est enforced au niveau applicatif.

---

### Routes — nouveau blueprint `problemes_bp`

**Fichier :** `app/routes/problemes.py` — `url_prefix='/problemes'`

**Constantes dans le fichier :**
```python
CATEGORIES_6M = ['Machine', "Main d'oeuvre", 'Matière', 'Méthode', 'Milieu', 'Mesure']
_LABELS_RECO = {'TRS_CRITIQUE': 'TRS critique', 'ARRETS_NON_DOCUMENTES': 'Arrêts non documentés', ...}
```

| Route | Méthode | Fonction | Rôles | Description |
|---|---|---|---|---|
| `/` | GET | `liste()` | chef, admin | Liste tous les problèmes, filtrable par statut. Passe `stats={ouvert, en_analyse, cause_identifiee, clos}`. |
| `/nouveau` | GET | `nouveau()` | chef, admin | Form étape 1. Pré-remplit depuis `?pareto_cause=`, `?reco_code=`, `?equipe_id=`. |
| `/nouveau` | POST | `nouveau()` | chef, admin | Crée `Probleme`, redirige vers `ishikawa(probleme_id)`. |
| `/<id>/etape/2` | GET | `ishikawa(id)` | chef, admin | Diagramme Ishikawa. Charge `grouped_causes` par 6M. |
| `/<id>/etape/2/cause` | POST | `ajouter_cause(id)` | chef, admin | **AJAX JSON**. Lit `{categorie_6m, description}`. Crée `IshikawaCause`. Si 1re cause → statut `en_analyse`. Retourne `{id, categorie_6m, description}` ou `{erreur}`. |
| `/<id>/cause/<cause_id>` | DELETE | `supprimer_cause(id, cause_id)` | chef, admin | **AJAX JSON**. Supprime cause + PourquoiNiveau cascade. Si cause était racine → clear `cause_racine_selectionnee_id`, statut `en_analyse`. |
| `/<id>/etape/3/<cause_id>` | GET | `pourquoi(id, cause_id)` | chef, admin | Affiche chaîne 5 Pourquoi pour une cause. |
| `/<id>/etape/3/<cause_id>/pourquoi` | POST | `sauver_pourquoi(id, cause_id)` | chef, admin | **AJAX JSON**. Lit `{niveau, reponse}`. Valide niveau N-1 répondu. Upsert `PourquoiNiveau`. Génère `question_suivante`. Retourne `{niveau, question, reponse, question_suivante}`. |
| `/<id>/etape/4` | GET | `selectionner_racine(id)` | chef, admin | Liste toutes les causes avec profondeur 5 Pourquoi. Radio bouton. Textarea actions. |
| `/<id>/etape/4` | POST | `sauver_racine(id)` | chef, admin | Lit `cause_racine_id` + `actions_correctives`. Set `est_racine=True` sur cause choisie (False sur les autres). Set `cause_racine_selectionnee_id` + statut `cause_identifiee`. Redirige vers rapport. |
| `/<id>/rapport` | GET | `rapport(id)` | chef, admin | Rapport A3 imprimable. Eager-load causes + pourquois. |
| `/<id>/clore` | POST | `clore(id)` | chef, admin | `cause_identifiee → clos`. |
| `/<id>/rouvrir` | POST | `rouvrir(id)` | chef, admin | `clos → ouvert`. |
| `/<id>` | GET | `detail(id)` | chef, admin | Smart redirect selon `statut` : ouvert/en_analyse → étape 2 ; cause_identifiee/clos → rapport. |

**CSRF AJAX :** Même pattern que `recommandations/index.html` : `X-CSRFToken: document.querySelector('meta[name="csrf-token"]')?.content` dans les headers `fetch()`. Étendre le handler d'erreur CSRF dans `__init__.py` aux paths `/problemes/`.

---

### Maquettes ASCII — 3 écrans clés (375px mobile)

#### Écran 1 — Étape 2 : Diagramme Ishikawa

```
┌────────────────────────────────────────┐
│ ← Analyse : Blocage grumes  [2 / 4]   │
│ ─────────────────────────────────────  │
│ DIAGRAMME ISHIKAWA (6M)                │
│ Ajoutez les causes observées           │
│ sur chaque branche.                    │
│                                        │
│ ▼ MACHINE  (2 causes)                  │
│ ┌──────────────────────────────────┐   │
│ │ • Courroie usée          [↗] [✕] │   │
│ │ • Vibrations anormales   [↗] [✕] │   │
│ └──────────────────────────────────┘   │
│ [+ Ajouter une cause Machine       ]   │
│                                        │
│ ▼ MAIN D'OEUVRE  (0 causes)            │
│ ┌──────────────────────────────────┐   │
│ │  (aucune cause saisie)           │   │
│ └──────────────────────────────────┘   │
│ [+ Ajouter une cause Main d'oeuvre ]   │
│                                        │
│ ▼ MATIÈRE  (1 cause)                   │
│ ┌──────────────────────────────────┐   │
│ │ • Grumes trop humides    [↗] [✕] │   │
│ └──────────────────────────────────┘   │
│ [+ Ajouter une cause Matière       ]   │
│                                        │
│ [MÉTHODE +] [MILIEU +] [MESURE +]      │
│                                        │
│ ─── FORMULAIRE INLINE (collapse) ───   │
│ Branche : [Machine               ▼]   │
│ Description :                          │
│ [__________________________________ ]  │
│              [Annuler] [Ajouter →  ]   │
│                                        │
│ [← Étape 1]      [→ Étape 3 : 5 Pq]   │
└────────────────────────────────────────┘
```
`[↗]` = lien vers la page 5 Pourquoi de cette cause. Le bouton `[→ Étape 3]` est désactivé si 0 cause totale.

#### Écran 2 — Étape 3 : Chaîne 5 Pourquoi

```
┌────────────────────────────────────────┐
│ ← Ishikawa     5 Pourquoi  [3 / 4]    │
│ ─────────────────────────────────────  │
│ Cause analysée :                       │
│ ┌──────────────────────────────────┐   │
│ │ 🔧 Machine / Courroie usée       │   │
│ └──────────────────────────────────┘   │
│                                        │
│ NIVEAU 1  ✓                            │
│ ┌──────────────────────────────────┐   │
│ │ Q : Pourquoi la courroie est-    │   │
│ │     elle usée ?                  │   │
│ │ R : La maintenance préventive    │   │
│ │     n'est pas planifiée.         │   │
│ └──────────────────────────────────┘   │
│                                        │
│ NIVEAU 2  ← en cours                   │
│ ┌──────────────────────────────────┐   │
│ │ Q : Pourquoi la maintenance      │   │
│ │     préventive n'est pas         │   │
│ │     planifiée ?                  │   │
│ │ R : [Saisir la réponse...    ]   │   │
│ │              [ Enregistrer ↓ ]   │   │
│ └──────────────────────────────────┘   │
│                                        │
│ NIVEAU 3 ░░░ (débloqué après N2)       │
│ NIVEAUX 4, 5 ░░░                       │
│                                        │
│ [← Autres causes]  [→ Sél. racine]     │
└────────────────────────────────────────┘
```

#### Écran 3 — Rapport A3 (imprimable)

```
┌────────────────────────────────────────┐
│ [← Modifier]  RAPPORT A3  [🖨 Imprimer]│
│ ─────────────────────────────────────  │
│ ┌──────────────────────────────────┐   │
│ │ ANALYSE : Blocage grumes         │   │
│ │ CUF Chaîne 4 · Chef Scierie      │   │
│ │ Créé le 27/05/2026               │   │
│ │ Statut : ● CAUSE IDENTIFIÉE      │   │
│ └──────────────────────────────────┘   │
│                                        │
│ 1. CONTEXTE DU PROBLÈME                │
│ Quoi    : Blocage répété des grumes    │
│ Quand   : 3 semaines, poste Matin      │
│ Où      : Bicoupe                      │
│ Combien : ~45 min perdues / poste      │
│                                        │
│ 2. CAUSES IDENTIFIÉES (6M)             │
│ Machine (2) : Courroie usée,           │
│               Vibrations anormales     │
│ Matière (1) : Grumes trop humides      │
│ Méthode, Milieu, Mesure : (vides)      │
│                                        │
│ 3. CAUSE RACINE                        │
│ ★ Machine → Courroie usée              │
│   N1 : Maintenance non planifiée       │
│   N2 : Pas de planning hebdo           │
│   N3 : Pas de responsable désigné      │
│                                        │
│ 4. ACTIONS CORRECTIVES                 │
│ Désigner un référent maintenance.      │
│ Créer un planning hebdo.               │
│                                        │
│ H2 : cause = Méthode/Organisationnelle │
│ → confirme l'hypothèse H2 du mémoire  │
│                                        │
│            [Clôturer ce problème →]   │
└────────────────────────────────────────┘
```

---

### Points d'intégration avec l'existant

| Fichier source | Modification | Changement |
|---|---|---|
| `templates/analyse/arrets.html` | Colonne "Actions" dans le tableau Pareto | Bouton `<a href="{{ url_for('problemes.nouveau', pareto_cause=p.cause) }}">Analyser</a>` par ligne |
| `templates/recommandations/index.html` | Dans chaque carte reco | Bouton "Lancer une analyse" sur `TRS_CRITIQUE`, `ARRETS_NON_DOCUMENTES`, `DECLASS_EXCESSIF` |
| `templates/saisie/detail.html` | Après le bloc anomalies | Bouton "Ouvrir une analyse" si `current_user.role in ('chef','admin')` et `anomalies` |
| `templates/chef/dashboard.html` | KPI row | Widget "Problèmes ouverts" (compte `Probleme.statut in ['ouvert','en_analyse']`) |
| `templates/base.html` | Sidebar nav (desktop + mobile) | Lien "Résolution" (route `problemes.liste`) dans section Pilotage |
| `app/routes/dashboard.py` → `vue_chef()` | Query avant `render_template` | `nb_problemes_ouverts = Probleme.query.filter(Probleme.statut.in_(['ouvert','en_analyse'])).count()` |
| `app/__init__.py` | Import + register_blueprint | `from .routes.problemes import problemes_bp` + `app.register_blueprint(problemes_bp)` |

---

### Valeur académique (OS4 + H2)

**OS4** : Le module livre l'Ishikawa + 5 Pourquoi comme outils guidés, persistants et auditables. Le `Probleme.cause_racine_selectionnee_id` est la "cause racine formellement identifiée" du mémoire. La `pareto_cause` field crée un lien explicite entre le Pareto existant (déjà livrable OS4) et l'Ishikawa (approfondissement OS4).

**H2** : La distribution de `IshikawaCause.categorie_6m WHERE est_racine=True` sur tous les `Probleme` clos est le test empirique de H2. Une requête `GROUP BY categorie_6m` sur cette vue donne le tableau de résultats de H2. Si la majorité des causes racines sont dans "Méthode", "Main d'oeuvre" ou "Milieu" (plutôt que "Machine"), H2 est validée.

---

### Fichiers à créer / modifier

**Nouveaux fichiers :**
```
app/routes/problemes.py          — blueprint + toutes les routes
app/templates/problemes/
  liste.html                     — liste + filtres statut + stats pills
  nouveau.html                   — étape 1 : contexte (QUOI/QUAND/OÙ/COMBIEN)
  ishikawa.html                  — étape 2 : 6 branches accordion + AJAX
  pourquoi.html                  — étape 3 : chaîne 5 niveaux + AJAX
  selectionner_racine.html       — étape 4 : radio cause racine + actions
  rapport.html                   — A3 imprimable (print CSS inline)
```

**Fichiers modifiés :**
```
app/models.py                    — +3 classes : Probleme, IshikawaCause, PourquoiNiveau
app/__init__.py                  — import + register problemes_bp ; CSRF handler étendu
app/routes/dashboard.py          — nb_problemes_ouverts query dans vue_chef()
app/static/css/style.css         — +.wp-pourquoi-card, .wp-6m-branch, .wp-cause-chip, .wp-a3-rapport
templates/base.html              — nav link "Résolution" (chef + admin)
templates/chef/dashboard.html    — KPI widget problèmes ouverts
templates/analyse/arrets.html    — bouton "Analyser" par ligne Pareto
templates/recommandations/index.html — bouton "Lancer une analyse" sur 3 codes
templates/saisie/detail.html     — bouton "Ouvrir une analyse" après anomalies
```

**Non modifiés (aucun changement nécessaire) :**
```
app/routes/analyse.py, saisie.py, recommandations.py — les intégrations sont 100% template-side
app/services/                    — aucun changement
```

---

### Ordre d'implémentation (8 phases)

1. **Models** — 3 classes dans `models.py`. `db.create_all()` crée les tables automatiquement (nouvelles tables, pas d'ALTER TABLE).
2. **Blueprint skeleton** — `problemes.py` avec routes retournant des placeholders. Register dans `__init__.py`. Vérifier le lien nav.
3. **Étape 1 — Nouveau** — Form contexte + pré-remplissage query params. Créer `nouveau.html`.
4. **Étape 2 — Ishikawa AJAX** — `ajouter_cause()` + `supprimer_cause()`. Créer `ishikawa.html` avec accordion Bootstrap + fetch AJAX.
5. **Étape 3 — Pourquoi AJAX** — `sauver_pourquoi()` avec logique de chaîne. Créer `pourquoi.html` avec cartes locked/unlocked.
6. **Étapes 4 + Rapport** — `sauver_racine()` + `rapport()` + `clore()` + `rouvrir()`. Templates restants.
7. **Intégrations** — Modifier les 5 templates existants + `dashboard.py`. Tester les boutons pré-remplissage.
8. **CSS + Print** — Nouveaux composants CSS. Print CSS dans `rapport.html`. Test `window.print()`.

---

## Vérification end-to-end

1. Se connecter en tant que `chef`
2. Aller sur `/analyse/arrets` → cliquer "Analyser" sur la 1re ligne Pareto → vérifier que le formulaire Étape 1 est pré-rempli avec `titre` et `pareto_cause`
3. Remplir le contexte (QUOI/QUAND/OÙ/COMBIEN) → soumettre → arriver sur l'Ishikawa (Étape 2)
4. Ajouter 2 causes sur la branche Machine, 1 sur Matière → vérifier les cartes apparaissent sans rechargement de page
5. Cliquer `[↗]` sur la 1re cause → Étape 3 → saisir 3 niveaux de Pourquoi → vérifier que le niveau 4 se déverrouille
6. Aller sur Étape 4 → sélectionner la cause racine → saisir des actions → soumettre → rapport A3
7. Vérifier le rapport : toutes les sections remplies, `@media print` masque la nav
8. Cliquer Clôturer → vérifier statut `clos` dans la liste
9. Aller sur `/dashboard/chef` → vérifier le widget "Problèmes ouverts" = 0 (clos)
10. Vérifier la cohérence H2 : dans `problemes.liste`, le problème clos montre la catégorie 6M de la cause racine

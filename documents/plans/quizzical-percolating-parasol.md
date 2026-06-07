# P5-A — Diagnostic mixte : Source B + Indice de confiance + Cockpit aiguilleur (PLAN ACTIF)

> Branche `claude/install-claude-excel-6MGzv` · P4 livré et validé le 2026-06-05 (commit `aaf65bf`)
> **Feu vert utilisateur requis avant toute modification de code**
> Décisions QCM verrouillées le 2026-06-07 : Mode Mixte · Prudent (seuil 70) · Carte + page · Formulaire pré-rempli

---

## CONTEXTE

P4 a livré : Source A (7 règles indicateurs réécrites au format 6 sections), suppression couche IA, bilan FCFA, alertes récurrences, prix visibles chef. Ce que P4 **n'a pas livré** (différé explicitement dans `P58-feat-reco-metier-p4.md §6`) :
- **Source B** — bibliothèque de contre-mesures par catégorie d'arrêt Pareto
- **Indice de confiance** — score 0-100 justifiant la prescription
- **Boucle de vérification avant/après** sur indicateur réel
- **Cockpit aiguilleur** — carte de diagnostic avec liens vers les bonnes pages

P5-A livre ces 4 éléments dans un cadre durci : l'app **affiche le raisonnement** qui mène à la prescription, pas seulement la prescription elle-même.

---

## VOCABULAIRE VERROUILLÉ (décision 2026-06-07)

| ❌ Interdit | ✅ À utiliser |
|---|---|
| "cause principale" / "cause vraie" | "hypothèse prioritaire" / "diagnostic probable" |
| "la solution" / "solution optimale" | "prescription proposée" / "contre-mesure recommandée" |
| "preuve" (pour les photos opérateurs) | "élément terrain" / "indice visuel" / "pièce justificative" |
| "l'outil a trouvé" | "l'outil détecte" / "l'outil propose" |
| confiance implicite (score non affiché) | niveau de confiance affiché + signaux explicités |

L'application ne donne pas une recommandation magique. Elle affiche le **raisonnement traçable et défendable** qui y mène.

---

## ALGORITHME EN 4 NIVEAUX (décision 2026-06-07)

```
Niveau 1 — CONTRÔLE         : les données sont-elles fiables ?
Niveau 2 — DÉTECTION        : y a-t-il une anomalie mesurable ?
Niveau 3 — DIAGNOSTIC       : quelle est l'hypothèse de cause ?
Niveau 4 — PRESCRIPTION     : quelle action le chef peut-il prendre maintenant ?
```

Chaque niveau est **séquentiel** : si le Niveau 1 échoue (SAISIES_INCOHERENTES), on ne calcule pas le Niveau 3.

### Niveau 1 — Contrôle de fiabilité

```python
def _controle_fiabilite(contexte):
    """Retourne 'ok' ou un code de problème de données."""
    pct_incoherences = contexte.get('pct_saisies_incoherentes', 0)
    nb_postes = contexte.get('nb_postes', 0)
    seuil = Parametre.get('seuil_saisies_incoherentes', 20.0)
    if nb_postes < 3:
        return 'donnees_insuffisantes'   # pas assez de fiches pour un signal fiable
    if pct_incoherences > seuil:
        return 'saisies_incoherentes'    # les données sont trop bruitées
    return 'ok'
```

Si `controle != 'ok'` → afficher la fiche `SAISIES_INCOHERENTES` uniquement, bloquer les niveaux 2-4.

### Niveau 2 — Détection d'anomalie

Reprend les seuils Source A existants : TRS < seuil critique, déclassement > seuil, manque à gagner > seuil, tendance négative. Si aucun seuil dépassé → afficher « Aucune anomalie détectée — indicateurs dans les normes ».

### Niveau 3 — Diagnostic (hypothèse de cause)

```python
def _diagnostic_hypothese(contexte):
    """
    Retourne l'hypothèse prioritaire avec les signaux qui la justifient.
    Ne prétend PAS trouver la cause vraie.
    """
    signaux = []
    cause_dom = contexte.get('cause_dominante')
    cause_pct  = contexte.get('cause_dominante_pct', 0)
    machine    = contexte.get('machine_critique')
    recurrence = contexte.get('facteur_recurrence', 1.0)
    concentration = contexte.get('machine_concentration_pct', 0)

    if cause_pct >= Parametre.get('seuil_part_cause_dominante', 30.0):
        signaux.append(f"Pareto : '{cause_dom}' représente {cause_pct:.0f}% du temps d'arrêt")
    if recurrence > 1.0:
        signaux.append(f"Récurrence : problème déjà présent sur la période précédente")
    if concentration >= 80:
        signaux.append(f"Concentration machine : {machine} porte {concentration:.0f}% des arrêts")

    if not signaux:
        return None   # pas d'hypothèse défendable

    return {
        'cause':    cause_dom,
        'machine':  machine,
        'signaux':  signaux,
        'nb_signaux': len(signaux),
    }
```

### Niveau 4 — Prescription

Déclenche Source B (bibliothèque contre-mesures) ou Source A selon la nature du signal. Calcule l'indice de confiance. Produit la fiche au format 6 items (voir ci-dessous).

---

## FORMAT DE PRESCRIPTION — 6 ITEMS (décision 2026-06-07)

Remplace l'ancien format 6 sections P4. Chaque fiche est une **hypothèse expliquée**, pas une vérité.

```
Signal détecté :         ← ce que l'outil a mesuré (TRS%, FCFA, heures arrêt, % Pareto)
Données utilisées :      ← quelles fiches, quelle période, quels arrêts justifient l'hypothèse
Diagnostic probable :    ← hypothèse de cause (jamais "cause vraie") + niveau de confiance
Prescription :           ← contre-mesure terrain concrète proposée
Niveau de confiance :    ← N/100 avec détail des signaux qui l'ont composé
Indicateur à suivre :    ← comment vérifier que la prescription a eu un effet (avant/après)
```

### Exemple — fiche Source B Approvisionnement

```
Signal détecté :
  Les arrêts catégorie « Approvisionnement » représentent 38 % du temps
  d'arrêt sur la période (5h10 sur 13h30 d'arrêts totaux).

Données utilisées :
  14 fiches postes · période du 2026-05-27 au 2026-06-03 · 7 arrêts
  catégorie Approvisionnement sur la Scie de tête · même pattern
  détecté sur la période précédente (facteur récurrence : 1.5).

Diagnostic probable :
  Hypothèse prioritaire : le parc bois ne prépare pas les contrats en
  avance suffisante, créant des ruptures entre contrats à la Scie de tête.
  (Ce diagnostic est une hypothèse basée sur les données saisies —
  une investigation terrain est recommandée pour le confirmer.)

Prescription :
  Mettre le parc bois en avance de 3 contrats et créer une zone tampon
  identifiée par contrat. Dès qu'un contrat est terminé, le bois du
  suivant est déjà disponible à la Scie de tête.

Niveau de confiance : 75/100
  · Pareto dominant ≥ 30 % : +30 pts
  · Récurrence confirmée (période précédente) : +20 pts
  · Concentration machine Scie de tête : +20 pts (proxy)
  · Catégorie clairement identifiée : +5 pts

Indicateur à suivre :
  Heures d'arrêt catégorie « Approvisionnement » sur la Scie de tête
  — comparer 7 jours avant / 7 jours après la mise en place.
```

### Exemple — fiche Source A TRS_CRITIQUE

```
Signal détecté :
  TRS moyen 52 % sur la période — en dessous du seuil critique 55 %
  (objectif 60 %). Manque à gagner estimé : 1 200 000 FCFA.

Données utilisées :
  14 fiches postes · TRS calculé poste par poste sur les fiches
  valide_chef + verrouille uniquement · Bicoupe : 8h30 d'arrêts cumulés.

Diagnostic probable :
  Hypothèse prioritaire : la Bicoupe concentre la majorité des arrêts,
  avec un écart poste Matin (58 %) vs Après-midi (44 %) qui suggère
  un problème de passation ou de fatigue en fin de journée.
  (Hypothèse — à confirmer par analyse Ishikawa.)

Prescription :
  Analyser les causes racines des arrêts Bicoupe sur le poste Après-midi
  via un Ishikawa 6M. Commencer par les branches Machine et Méthode.

Niveau de confiance : 62/100
  · TRS sous seuil critique : +30 pts (détection forte)
  · Machine Bicoupe identifiée comme critique : +20 pts
  · Écart Matin/Après-midi ≥ 10 pts : +12 pts

Indicateur à suivre :
  TRS moyen Bicoupe poste Après-midi — comparer semaine avant /
  semaine après l'analyse Ishikawa.
```

---

## INDICE DE CONFIANCE (décision 2026-06-07)

Score 0–100 calculé par `_indice_confiance(contexte)`. Visible dans chaque fiche.

```python
def _indice_confiance(contexte):
    score = 0
    signaux = {}

    # Signal 1 : récurrence (le problème existait déjà la période précédente)
    if contexte.get('facteur_recurrence', 1.0) > 1.0:
        score += 40
        signaux['recurrence'] = "Problème récurrent (période précédente)"

    # Signal 2 : Pareto dominant ≥ seuil
    seuil_pareto = Parametre.get('seuil_part_cause_dominante', 30.0)
    if contexte.get('cause_dominante_pct', 0) >= seuil_pareto:
        score += 30
        signaux['pareto'] = f"Pareto dominant {contexte['cause_dominante_pct']:.0f}% ≥ {seuil_pareto:.0f}%"

    # Signal 3 : concentration machine ≥ 80 %
    if contexte.get('machine_concentration_pct', 0) >= 80:
        score += 20
        signaux['concentration'] = f"Machine {contexte.get('machine_critique')} porte ≥ 80% des arrêts"

    # Signal 4 : catégorie clairement identifiée (pas 'Autre')
    if contexte.get('cause_dominante') not in (None, 'Autre'):
        score += 10
        signaux['categorie'] = f"Catégorie identifiée : {contexte['cause_dominante']}"

    # Déterminer le mode selon la bascule Prudent (seuil 70)
    if score >= 70:
        mode = 'auto'        # Prescription affichée sans réserve particulière
    elif score >= 40:
        mode = 'assiste'     # Prescription proposée avec incitation à vérifier
    else:
        mode = 'faible'      # Données insuffisantes pour une prescription défendable

    return {'score': score, 'mode': mode, 'signaux': signaux}
```

**Affichage selon le mode :**

| Mode | Score | Message affiché | CTA |
|---|---|---|---|
| `auto` | ≥ 70 | Badge vert « Confiance élevée » | [Lancer l'action] |
| `assiste` | 40–69 | Badge orange « À vérifier terrain » + signaux | [Analyser (Ishikawa)] |
| `faible` | < 40 | Badge gris « Données insuffisantes » | [Ajouter des données] |

---

## SOURCE B — BIBLIOTHÈQUE DE CONTRE-MESURES (spec complète dans archive P4 ci-dessous)

Structure : `BIBLIOTHEQUE_CONTRE_MESURES` dict (9 catégories × 5 contre-mesures). Chaque CM porte les métadonnées de scoring. La fonction `_selectionner_contre_mesure(categorie, contexte)` sélectionne la meilleure + 2 alternatives via score multicritère.

**Déclencheur Source B** : catégorie d'arrêt dominante du Pareto ≥ `seuil_part_cause_dominante` (défaut 30 %).

La prescription retournée par Source B est formatée selon les **6 items** ci-dessus (pas l'ancien format 6 sections P4).

---

## COCKPIT AIGUILLEUR — RÈGLES (décision 2026-06-07)

Le cockpit ne **contient pas** de prescriptions. Il **aiguille** vers la bonne page.

### Règles R-DASH

- **R-DASH-1** : chaque signal = une phrase (verbe d'action + lien). Format : « [Signal court] → [Lien page]»
- **R-DASH-2** : pas de contenu dupliqué entre cockpit et pages détail
- **R-DASH-3** : si tous les indicateurs sont dans les normes, la carte est vide (ou absente)
- **R-DASH-4** : un seul niveau de profondeur sur le cockpit (pas d'accordéon imbriqué)

### Carte diagnostic cockpit — `chef/_diagnostic.html`

```
┌─────────────────────────────────────────────────────────────┐
│  DIAGNOSTIC PROBABLE          [Confiance 75/100 — Assisté]  │
├─────────────────────────────────────────────────────────────┤
│  1. Approvisionnement · Scie de tête · 5h10 → [Prescriptions]│
│  2. TRS Après-midi 44 % · Bicoupe → [Analyser (Ishikawa)]   │
│  3. Azobé déclassé 38 % → [Qualité / Matière]               │
└─────────────────────────────────────────────────────────────┘
```

**Maximum 3 priorités**. Chaque ligne = signal court + lien. Aucun texte long.

**Liens par type de signal :**

| Signal | Lien vers |
|---|---|
| TRS, arrêts, Pareto | `/analyse/arrets` |
| Déclassement, essence | `/chef/qualite` |
| Actions en retard | `/dashboard/chef/actions` |
| Prescription Source B prête | `/recommandations/` |
| Ishikawa à créer | route `creer_depuis_diagnostic` |

---

## PRÉCONDITION — REBASE LOCAL (OBLIGATOIRE AVANT TOUT CODE)

Le local est à `31e2167` (pre-P4). Le remote est à `03e2974` (post-P4 + P5 cadrage, 4 commits d'avance).

```bash
git fetch origin claude/install-claude-excel-6MGzv
git rebase origin/claude/install-claude-excel-6MGzv
```

Si conflit → résoudre puis `git rebase --continue`. Aucun code ne doit être écrit avant que cette commande ait réussi.

---

## LOT 1 — SOURCE B + INDICE DE CONFIANCE

**Fichier principal** : `app/services/recommandations.py`

1. Ajouter `BIBLIOTHEQUE_CONTRE_MESURES` (spec complète dans archive P4 ci-dessous, section DESIGN 1).
2. Ajouter `_indice_confiance(contexte)` → `{'score', 'mode', 'signaux'}` (code ci-dessus).
3. Ajouter `_selectionner_contre_mesure(categorie, contexte)` (score multicritère, spec archive P4).
4. Ajouter `_fiche_source_b(contexte, cm, alternatives, indice)` → fiche au format 6 items (PAS l'ancien format 6 sections).
5. Modifier `analyse_recommandations()` : encapsuler dans l'algorithme 4 niveaux (Contrôle → Détection → Diagnostic → Prescription). Si Niveau 3 détecte une catégorie dominante ≥ seuil → émettre aussi une fiche Source B.
6. Ajouter `diagnostic_prioritaire(equipes, contexte_extra)` → dict compact pour la carte cockpit : `{'priorites': [...], 'score_confiance': int, 'mode': str}`. Max 3 items.
7. Enrichir `_contexte_extra()` dans `app/routes/recommandations.py` avec : `facteur_recurrence`, `machine_concentration_pct`.

**Règle de formatage** : dans `_fiche_source_b()` et dans toutes les fiches Source A réécrites, la section "Diagnostic probable" doit contenir la mention `(Hypothèse — à confirmer terrain)` quand le mode est `assiste` ou `faible`.

---

## LOT 2 — COCKPIT AIGUILLEUR + ISHIKAWA PRÉ-REMPLI

**Fichiers** :

1. **`app/templates/chef/_diagnostic.html`** (NOUVEAU partial) : carte cockpit aiguilleur, max 3 lignes, liens R-DASH. Badge confiance en haut à droite.
2. **`app/templates/chef/dashboard.html`** : `{% include 'chef/_diagnostic.html' %}` dans la colonne gauche, après `_alertes.html`.
3. **`app/routes/dashboard.py`** `vue_chef()` : appeler `diagnostic_prioritaire(equipes, contexte)` et injecter `diagnostic_cockpit` dans les deux `render_template`. Importer depuis `recommandations`.
4. **`app/routes/problemes.py`** : ajouter route `creer_depuis_diagnostic` (POST) — idempotente (vérifie si un Problème `reco_code=code` est déjà ouvert), pré-remplit `pareto_cause`, `machine_cible`, `categorie_6m` (via `_CATEGORIE_VERS_6M`). Redirige vers la page d'édition Ishikawa.
5. **`app/templates/recommandations/index.html`** : afficher badge confiance (score + mode) sur chaque fiche Source B · CTA adapté selon mode (`auto` → [Lancer l'action], `assiste` → [Analyser]) · bouton « Voir 2 alternatives » sur fiches Source B.

---

## FICHIERS À MODIFIER

| Fichier | Modification |
|---|---|
| `app/services/recommandations.py` | `BIBLIOTHEQUE_CONTRE_MESURES` · `_indice_confiance()` · `_selectionner_contre_mesure()` · `_fiche_source_b()` · algorithme 4 niveaux dans `analyse_recommandations()` · `diagnostic_prioritaire()` |
| `app/routes/recommandations.py` | Enrichir `_contexte_extra()` avec `facteur_recurrence` + `machine_concentration_pct` |
| `app/routes/dashboard.py` | Injecter `diagnostic_cockpit` dans `vue_chef()` |
| `app/templates/chef/_diagnostic.html` | **NOUVEAU** — carte cockpit aiguilleur |
| `app/templates/chef/dashboard.html` | Include `_diagnostic.html` + import |
| `app/routes/problemes.py` | Route `creer_depuis_diagnostic` (idempotente) |
| `app/templates/recommandations/index.html` | Badge confiance · CTA adapté · bouton alternatives |
| `documents/notes-impact/P5A-feat-diagnostic-mixte.md` | Note d'impact 9 sections avant commit |

Aucune nouvelle table. Pas de Flask-Migrate. `ActionChef.reco_code` et `Probleme.reco_code` existent déjà (livrés P4).

---

## VÉRIFICATION

```bash
# Précondition
git fetch origin claude/install-claude-excel-6MGzv
git rebase origin/claude/install-claude-excel-6MGzv

# Données fraîches
cd cuf-pilotage && python seed_data.py

# Tests de non-régression
bash .claude/skills/run-cuf-pilotage/smoke.sh   # 16/16 doivent rester verts

# Captures
python .claude/skills/run-cuf-pilotage/screenshot.py chef
```

**Contrôles visuels :**
- Carte diagnostic cockpit affiche max 3 priorités avec liens (pas de contenu dupliqué)
- Badge confiance visible sur les fiches Source B : score + mode (auto/assisté/faible)
- Fiches Source B au format 6 items : "Diagnostic probable" contient "(Hypothèse — à confirmer terrain)"
- Mode `assiste` → CTA "Analyser (Ishikawa)" ; mode `auto` → CTA "Lancer l'action"
- Route `creer_depuis_diagnostic` crée un Ishikawa pré-rempli et ne crée pas de doublon si déjà ouvert
- Aucune occurrence de "cause vraie" / "cause principale absolue" dans les textes affichés

---

---

# P4 — Recommandations métier + Actions FCFA + Signaux machines (LIVRÉ 2026-06-05 — archive de référence)

> Commit `aaf65bf` · La spec Source B (`BIBLIOTHEQUE_CONTRE_MESURES`) ci-dessous est la référence pour P5-A Lot 1.
> **NE PAS RÉEXÉCUTER** — P4 est livré. Lire uniquement pour extraire la spec Source B.

---

## CONTEXTE

P3 a livré le cockpit 2 colonnes avec accordéons, verdict global, colonne gauche sticky. P4 est le résultat d'une analyse approfondie des 7 rubriques du profil Chef (Tableau de bord, Fiches Chef, Machines, Qualité, Pertes, Actions, Recommandations), conduite rubrique par rubrique avec l'utilisateur via QCM les 2026-06-04 et 2026-06-05.

### Problèmes identifiés qui justifient P4

1. **Recommandations — texte générique** : les 7 règles génèrent un texte identique quel que soit le TRS réel, la machine critique, la catégorie d'arrêt dominante ou l'essence problématique. Le `contexte` dict est passé aux règles mais jamais utilisé dans le texte des solutions. Résultat : un conseil de manuel, pas une décision terrain.
2. **Couche 2 IA** : `app/services/reco_ai.py` appelle Anthropic/Groq/Tavily — viole la règle verrouillée « 100 % hors ligne ». À supprimer (accord utilisateur obtenu le 2026-06-05 : « Supprimer simplement »).
3. **Lien Reco → action incomplet** : seuls 3 codes sur 7 ont un bouton « Lancer une analyse ». Les 4 autres n'ont aucun chemin vers l'action.
4. **Actions Chef — bilan en arrêts seulement** : `_bilan_efficacite_action_chef()` compare les arrêts avant/après, mais l'utilisateur veut le bilan en **FCFA évité**.
5. **Prix chef invisible** : le chef voit le manque à gagner en FCFA mais ne peut pas consulter les prix par essence (admin-only) pour valider les calculs.
6. **Récurrences machines non remontées** : `_recurrences_machines()` détecte les patterns mais ils ne déclenchent aucune alerte sur le cockpit.

### Ce que l'utilisateur veut (verbatim QCM 2026-06-05)

> « Une bonne recommandation doit dire : quoi faire, pourquoi c'est prioritaire, combien cela coûte actuellement, combien de manque à gagner on peut espérer réduire, et comment vérifier le résultat. »

> « Une recommandation utile ne doit pas être un conseil général. Elle doit être une contre-mesure terrain, déclenchée par un signal mesurable, liée à une cause probable, accompagnée d'un gain attendu et vérifiable après action. »

Format validé — **6 sections obligatoires** par recommandation :
```
1. Signal détecté    — ce que l'outil a vu (TRS%, FCFA, heures arrêts, % Pareto)
2. Lecture terrain   — ce que ça signifie concrètement dans la scierie CUF
3. Ce que ça coûte   — manque à gagner en FCFA sur la période
4. Action concrète   — contre-mesure terrain précise (jamais un conseil général)
5. Gain attendu      — FCFA récupérables si l'action réussit
6. Vérification      — indicateur avant/après pour confirmer l'effet
```

L'utilisateur a aussi demandé que les recommandations forment une **bibliothèque de contre-mesures métier organisée par famille de problème**, et non un simple commentaire d'indicateur. Exemple fourni : arrêts d'approvisionnement à la Scie de tête → « mettre le parc bois en avance de 3 contrats + zone tampon par contrat ».

---

## DESIGN 1 — MOTEUR DE RECOMMANDATIONS MÉTIER (6 sections + bibliothèque)

### Principe

Une recommandation = une contre-mesure terrain déclenchée par un signal mesurable. Le moteur a **deux sources** qui produisent toutes deux des fiches au format 6 sections :

- **Source A — règles indicateur (les 7 existantes, réécrites)** : TRS, déclassement, rendement, objectif, saisies, tendance, arrêts non documentés. Le texte est reconstruit dynamiquement avec les vraies données.
- **Source B — bibliothèque par famille de cause (NOUVEAU)** : le moteur lit la **catégorie d'arrêt dominante** du Pareto et émet une contre-mesure métier ciblée. C'est ce que l'utilisateur a décrit avec l'exemple approvisionnement.

### Source B — Bibliothèque de contre-mesures (ancrée sur `CATEGORIES_ARRET`)

La taxonomie existe déjà : `config.py:40` `CATEGORIES_ARRET` (9 catégories), causes rangées automatiquement par `saisie.py:536` `_categorie_arret_depuis_cause()`. Le Pareto par catégorie est déjà calculé (`dashboard.py:2399`).

**Structure retenue (décision 2026-06-05)** : 5 contre-mesures par catégorie. L'app sélectionne la plus pertinente via un **score multicritère** (pas une simple lambda), avec 2 alternatives accessibles en accordéon.

#### Mécanisme de sélection multicritère

Chaque contre-mesure porte des métadonnées de scoring. La fonction `_selectionner_contre_mesure(categorie, contexte)` note chaque candidat et retourne le meilleur + 2 alternatives :

```python
def _selectionner_contre_mesure(categorie, contexte):
    """Score multicritère : machine (+30), récurrence (+20), durée longue (+15),
    coût élevé (+15), éviter doublon avec action déjà ouverte (-20)."""
    candidates = BIBLIOTHEQUE_CONTRE_MESURES.get(categorie, [])
    if not candidates:
        return None, []

    # Actions déjà ouvertes pour ce code → pénalité doublon
    actions_types_ouverts = {
        a.origine_detail for a in ActionChef.query.filter(
            ActionChef.reco_code.isnot(None),
            ActionChef.statut.in_(['a_faire', 'en_cours'])
        ).all() if a.origine_detail
    }

    def _score(cm):
        s = 0
        if cm.get('prioritaire_si_machine') == contexte.get('machine_critique'):    s += 30
        if cm.get('prioritaire_si_recurrence') and contexte.get('facteur_recurrence', 1.0) > 1.0: s += 20
        if cm.get('prioritaire_si_duree_longue') and contexte.get('machine_arrets_h', 0) >= 4:    s += 15
        if cm.get('prioritaire_si_cout_eleve')  and contexte.get('cause_dominante_fcfa', 0) >= 1_000_000: s += 15
        if cm.get('action_type') in actions_types_ouverts:  s -= 20  # éviter doublon
        return s

    scored = sorted(candidates, key=_score, reverse=True)
    return scored[0], scored[1:3]   # meilleure + 2 alternatives
```

**Champs de métadonnées par contre-mesure** :

| Champ | Rôle |
|---|---|
| `action` | Texte affiché section 4 (contre-mesure principale) |
| `detail` | Explication terrain (affiché en dessous) |
| `type` | `structurelle` / `process` / `quick_win` / `preventive` |
| `prioritaire_si_machine` | Bonus machine (str, optionnel) |
| `prioritaire_si_recurrence` | Bonus si facteur récurrence > 1 (bool) |
| `prioritaire_si_duree_longue` | Bonus si arrêts ≥ 4h sur la période (bool) |
| `prioritaire_si_cout_eleve` | Bonus si FCFA cause ≥ 1 M (bool) |
| `action_type` | Clé unique pour détecter les doublons avec actions ouvertes (str) |
| `taux_reussite` | Tuple (min%, max%) utilisé pour calculer le gain attendu |

```python
# Structure dans recommandations.py
BIBLIOTHEQUE_CONTRE_MESURES = {
    'Approvisionnement': [
        # CM-1 : structurelle, ciblée Scie de tête, très efficace si récurrente
        {'type': 'structurelle', 'prioritaire_si_machine': 'Scie de tête',
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'appro_avance_contrats',
         'taux_reussite': (40, 70),
         'action': "Mettre le parc bois en avance de 3 contrats par rapport à la scierie.",
         'detail': "Dès qu'un contrat est terminé, le bois du suivant est déjà à portée de la Scie de tête. Règle : stock parc ≥ 3 × volume contrat moyen."},
        # CM-2 : structurelle, zone tampon, efficace si coût élevé
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': True, 'action_type': 'appro_zone_tampon',
         'taux_reussite': (35, 65),
         'action': "Créer une zone tampon identifiée et dédiée par contrat à l'entrée du parc.",
         'detail': "Chaque zone tampon porte le numéro de contrat peint au sol. Interdit de mélanger les contrats."},
        # CM-3 : process, ciblée poste Apres-midi (passation)
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'appro_passation_13h',
         'taux_reussite': (30, 55),
         'action': "Déclencher la préparation du prochain contrat avant 13h (passation Matin → Soir).",
         'detail': "Le poste du soir hérite d'un parc préparé. Responsable : chef poste Matin."},
        # CM-4 : quick_win, synchronisation parc-scierie
        {'type': 'quick_win', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'appro_reunion_synchro',
         'taux_reussite': (20, 45),
         'action': "Réunion de synchronisation parc-scierie de 10 min chaque matin avant démarrage.",
         'detail': "Chef parc + Chef scierie confirment stock disponible pour les 2 prochains contrats."},
        # CM-5 : process, évacuation produits finis (fallback)
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'appro_evacuation',
         'taux_reussite': (20, 40),
         'action': "Fluidifier l'évacuation des produits finis pour libérer la voie d'approvisionnement.",
         'detail': "Un couloir obstrué par des planches bloque aussi l'entrée des grumes."},
    ],
    'Panne machine': [
        # CM-1 : preventive, ciblée Bicoupe, levier maximal
        {'type': 'preventive', 'prioritaire_si_machine': 'Bicoupe',
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': True, 'action_type': 'panne_preventif_bicoupe',
         'taux_reussite': (35, 65),
         'action': "Planifier une maintenance préventive Bicoupe chaque lundi 6h–7h.",
         'detail': "La Bicoupe traite 100 % du bois. Un arrêt Bicoupe = arrêt total de la chaîne 4."},
        # CM-2 : preventive, ciblée Scie de tronçonnage
        {'type': 'preventive', 'prioritaire_si_machine': 'Scie de tronçonnage',
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'panne_preventif_tronconnage',
         'taux_reussite': (30, 55),
         'action': "Vérifier serrage des galets et courroies de la Scie de tronçonnage chaque début de poste.",
         'detail': "Les pannes sur la scie de tronçonnage sont souvent dues à des desserrages progressifs non détectés."},
        # CM-3 : structurelle, stock pièces critiques
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': True, 'action_type': 'panne_stock_pieces',
         'taux_reussite': (25, 50),
         'action': "Constituer un stock de pièces critiques sur site (courroies, galets, fusibles, lames de rechange).",
         'detail': "Les délais d'approvisionnement pièces allongent les pannes de 2 h en moyenne. Coût stock < 1 arrêt."},
        # CM-4 : structurelle, fiche de vie machine
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'panne_fiche_vie',
         'taux_reussite': (20, 45),
         'action': "Créer une fiche de vie machine : date panne, cause, durée, pièce changée.",
         'detail': "Sans historique, impossible d'identifier les pannes récurrentes ni d'anticiper les prochaines."},
        # CM-5 : process, formation diagnostic niveau 1
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'panne_formation_diagnostic',
         'taux_reussite': (15, 35),
         'action': "Former un opérateur par poste au diagnostic de premier niveau.",
         'detail': "Un opérateur formé réduit le temps d'attente du mécanicien de 30 à 60 min par incident."},
    ],
    'Mécanique': [
        # CM-1 : preventive, inspection début de poste, efficace si durée longue
        {'type': 'preventive', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': True, 'action_type': 'meca_inspection_debut_poste',
         'taux_reussite': (35, 65),
         'action': "Inspection préventive début de poste : 10 points de contrôle par machine en 5 min.",
         'detail': "Serrage visible, niveau huile, courroie, vibration anormale, démarrage à vide. Cocher sur fiche."},
        # CM-2 : preventive, graissage programmé
        {'type': 'preventive', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'meca_graissage_prog',
         'taux_reussite': (30, 55),
         'action': "Planifier le graissage des machines chaque vendredi fin de poste du soir.",
         'detail': "Le vendredi laisse le week-end pour les ajustements sans impact sur la production courante."},
        # CM-3 : structurelle, tableau de bord maintenance visible
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'meca_tableau_maintenance',
         'taux_reussite': (20, 40),
         'action': "Afficher un tableau de bord de maintenance visible dans l'atelier.",
         'detail': "Dernière révision + prochaine + responsable. La visibilité crée la responsabilisation."},
        # CM-4 : process, réglage tension courroies
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': False, 'action_type': 'meca_tension_courroies',
         'taux_reussite': (25, 45),
         'action': "Revoir les réglages de tension des courroies selon les recommandations constructeur.",
         'detail': "Courroie trop tendue → fatigue roulements. Trop lâche → glisse sous charge."},
        # CM-5 : process, carnet de bord arrêts
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'meca_carnet_bord',
         'taux_reussite': (15, 35),
         'action': "Instaurer un carnet de bord machine rempli à chaque arrêt par le mécanicien.",
         'detail': "Permet de détecter les patterns : même organe, même poste, même essence ?"},
    ],
    'Réglage / outil': [
        # CM-1 : process, standard lames (règle verrouillée CUF)
        {'type': 'process', 'prioritaire_si_machine': 'Bicoupe',
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'reglage_standard_lames',
         'taux_reussite': (50, 80),
         'action': "Appliquer le standard lames : préventif toutes les 2 h + immédiat au changement tendre↔dure.",
         'detail': "Ayous/Iroko = tendres. Azobé/Movingui = dures. Un changement de lame non fait coûte en déclassé."},
        # CM-2 : structurelle, fiche réglage par essence
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': True, 'action_type': 'reglage_fiche_par_essence',
         'taux_reussite': (40, 70),
         'action': "Créer une fiche de réglage par essence affichée au poste (paramètres bicoupe, vitesse, pression).",
         'detail': "L'opérateur n'a pas à mémoriser les réglages. Il lit, il applique, il démarre."},
        # CM-3 : process, séquence démarrage standardisée
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'reglage_sequence_demarrage',
         'taux_reussite': (35, 60),
         'action': "Standardiser la séquence de démarrage : réglage bicoupe → vérification lame → test à vide.",
         'detail': "Démarrer sans séquence = risque de mauvais réglage non détecté avant la première coupe."},
        # CM-4 : process, regroupement par essence
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': False, 'action_type': 'reglage_regroupement_essence',
         'taux_reussite': (30, 55),
         'action': "Regrouper les contrats par essence (toutes les grumes d'une même essence traitées ensemble).",
         'detail': "Moins de changements d'essence = moins de changements de lame = moins de temps perdu."},
        # CM-5 : structurelle, mesure temps réglage
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'reglage_chrono_objectif',
         'taux_reussite': (20, 40),
         'action': "Chronométrer les temps de réglage actuels et fixer un objectif réaliste (objectif cible : < 8 min).",
         'detail': "Sans mesure de référence, impossible de savoir si une amélioration a eu lieu."},
    ],
    'Qualité matière': [
        # CM-1 : preventive, contrôle réception, ciblée si essence problématique connue
        {'type': 'preventive', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': True, 'action_type': 'qualite_controle_reception',
         'taux_reussite': (30, 60),
         'action': "Instaurer un contrôle visuel des grumes à réception : nœuds, fentes, pourri visible.",
         'detail': "Les grumes défectueuses découvertes à la scierie ont déjà mobilisé du temps de transport inutile."},
        # CM-2 : structurelle, tri amont parc
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': True, 'action_type': 'qualite_tri_parc',
         'taux_reussite': (25, 55),
         'action': "Trier les grumes au parc : lot A (conforme), lot B (à déclasser), lot C (à refuser).",
         'detail': "Traiter B et C en fin de poste ou en période creuse évite de polluer le flux principal."},
        # CM-3 : structurelle, pénalité fournisseur
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': True, 'action_type': 'qualite_penalite_fournisseur',
         'taux_reussite': (20, 50),
         'action': "Négocier un droit de retour ou une pénalité avec les fournisseurs de grumes défectueuses.",
         'detail': "Rend le coût de la mauvaise qualité visible côté fournisseur, pas seulement côté scierie."},
        # CM-4 : process, tableau taux déclassement par fournisseur
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'qualite_tableau_fournisseur',
         'taux_reussite': (15, 35),
         'action': "Mesurer le taux de déclassement par fournisseur et afficher le classement chaque semaine.",
         'detail': "La transparence crée une pression naturelle. Le fournisseur en bas du tableau cherche à remonter."},
        # CM-5 : process, formation tri précoce opérateurs
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'qualite_formation_tri',
         'taux_reussite': (15, 30),
         'action': "Former les opérateurs au tri précoce : défauts traitables vs rédhibitoires.",
         'detail': "Un bois nœudeux peut être débité différemment. Un bois pourri ne peut pas être sauvé."},
    ],
    'Organisationnelle': [
        # CM-1 : process, passation Matin↔Soir standardisée
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'org_passation_standardisee',
         'taux_reussite': (40, 70),
         'action': "Standardiser la passation Matin↔Après-midi : fiche signée par les deux chefs de poste.",
         'detail': "5 min max : volumes du matin, problèmes non résolus, état machines, consignes spéciales."},
        # CM-2 : process, 5S fin de poste
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': False, 'action_type': 'org_5s_fin_poste',
         'taux_reussite': (30, 55),
         'action': "Appliquer un 5S de fin de poste : chaque opérateur range son poste avant de partir.",
         'detail': "Un poste rangé = démarrage rapide du poste suivant = moins de temps cherché sur les outils."},
        # CM-3 : process, planning journalier affiché
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'org_planning_affiche',
         'taux_reussite': (25, 45),
         'action': "Afficher le planning du jour (essence, objectif volume, ordre des contrats) au démarrage.",
         'detail': "Les 5 premières minutes d'un poste définissent souvent sa dynamique entière."},
        # CM-4 : process, nettoyages planifiés hors production
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'org_nettoyage_planifie',
         'taux_reussite': (20, 40),
         'action': "Planifier les nettoyages en fin de poste, pas pendant la production.",
         'detail': "Un nettoyage non planifié pendant la production = arrêt non documenté = Pareto faussé."},
        # CM-5 : quick_win, réunion flash 5 min
        {'type': 'quick_win', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'org_reunion_flash',
         'taux_reussite': (15, 35),
         'action': "Instaurer une réunion flash de 5 min en début de poste pour les écarts du poste précédent.",
         'detail': "Transmet les informations critiques sans réunion longue ni email."},
    ],
    'Énergie / réseau': [
        # CM-1 : structurelle, groupe électrogène de secours
        {'type': 'structurelle', 'prioritaire_si_machine': 'Bicoupe',
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': True, 'action_type': 'energie_groupe_secours',
         'taux_reussite': (25, 50),
         'action': "Installer un groupe électrogène de secours dimensionné pour les machines critiques.",
         'detail': "Priorité : Bicoupe + éclairage atelier. Coût groupe < coût d'un arrêt de 2 semaines."},
        # CM-2 : process, déclaration coupures à l'exploitant réseau
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'energie_declaration_exploitant',
         'taux_reussite': (10, 30),
         'action': "Déclarer chaque coupure à l'exploitant réseau avec horodatage et durée exacte.",
         'detail': "Sans historique documenté, aucune pression possible sur le gestionnaire réseau."},
        # CM-3 : preventive, onduleur automates
        {'type': 'preventive', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': False, 'prioritaire_si_duree_longue': True,
         'prioritaire_si_cout_eleve': False, 'action_type': 'energie_onduleur_automates',
         'taux_reussite': (15, 35),
         'action': "Installer un onduleur ou protection surtension sur les automates de commande.",
         'detail': "Les redémarrages après coupure abîment les automates et allongent les arrêts de 20-40 min."},
        # CM-4 : process, tâches non-machines pendant coupures récurrentes
        {'type': 'process', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': False, 'action_type': 'energie_planif_creuses',
         'taux_reussite': (10, 25),
         'action': "Planifier les tâches non-machines (inventaire, maintenance légère) pendant les coupures récurrentes.",
         'detail': "Si les coupures surviennent régulièrement, ne pas subir : planifier autour."},
        # CM-5 : structurelle, contrat délestage prioritaire
        {'type': 'structurelle', 'prioritaire_si_machine': None,
         'prioritaire_si_recurrence': True, 'prioritaire_si_duree_longue': False,
         'prioritaire_si_cout_eleve': True, 'action_type': 'energie_contrat_prioritaire',
         'taux_reussite': (10, 40),
         'action': "Négocier un contrat de délestage prioritaire avec le fournisseur d'énergie.",
         'detail': "Les industries prioritaires sont délestées en dernier. CUF peut en faire partie."},
    ],
}
```

**Affichage** : contre-mesure n°1 en texte principal de la section 4 de la fiche. Un bouton « Voir 2 alternatives » déroule les options n°2 et n°3 sous forme compacte.

Déclencheur Source B inchangé : catégorie d'arrêt n°1 du Pareto ≥ 30 % du temps d'arrêt. Seuil `Parametre.get('seuil_part_cause_dominante', 30.0)`.

### Exemple complet — fiche approvisionnement (cas utilisateur)

```
Signal détecté :
  Les arrêts « Approvisionnement bois » à la Scie de tête représentent
  38 % du temps d'arrêt de la semaine (5h10 cumulées sur 13h30).

Lecture terrain :
  Le parc bois livre les contrats trop tard car le triage est fait au
  dernier moment. La Scie de tête attend les grumes entre deux contrats.

Ce que ça coûte :
  Manque à gagner estimé sur ces arrêts : 1 450 000 FCFA cette semaine.

Action recommandée :
  Mettre le parc bois en avance de 3 contrats par rapport à la scierie
  et créer une zone tampon identifiée pour chaque contrat. Ainsi, dès
  qu'un contrat est fini, le bois du suivant est déjà disponible.

Gain attendu :
  Si les arrêts d'approvisionnement baissent de 50 %, récupération
  estimée à ~725 000 FCFA/semaine.

Vérification :
  Comparer le temps d'arrêt « Approvisionnement » de la Scie de tête
  avant/après sur 7 jours.
```

### Avant / Après — règle indicateur TRS_CRITIQUE (Source A)

```
AVANT (texte statique — identique quelle que soit la réalité)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Cartographier les arrêts machine. Identifier les machines les plus
 impactantes. Mettre en place un relevé structuré des durées et causes."

APRÈS (6 sections, données réelles CUF)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signal détecté : TRS moyen 52 % (seuil critique 50 %, objectif 60 %).
Lecture terrain : la Bicoupe concentre 8h30 d'arrêts ; le poste
  Après-midi affiche 44 % contre 58 % le matin.
Ce que ça coûte : manque à gagner estimé 1 200 000 FCFA cette semaine.
Action : analyser la cause racine des arrêts Bicoupe (Après-midi).
Gain attendu : si TRS remonte à 60 %, ~900 000 FCFA/semaine récupérés.
Vérification : comparer TRS Bicoupe Après-midi avant/après sur 7 jours.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Enrichissement du dict contexte

```python
# Nouvelles clés dans vue_recommandations() / analyse_recommandations()
contexte = {
    # --- Existant ---
    "trs_moyen": 52.3, "manque": 2_450_000, "nb_postes": 14,
    "pct_r2": 18.5, "pct_r3": 12.0,
    # --- Nouveau ---
    "machine_critique": "Bicoupe",           # _machine_prioritaire_recent()
    "machine_arrets_h": 8.5,                 # durée cumulée heures
    "cause_dominante": "Approvisionnement",   # top catégorie Pareto
    "cause_dominante_pct": 38.0,             # sa part du temps d'arrêt
    "cause_dominante_fcfa": 1_450_000,       # son coût estimé
    "essence_declass": "Azobé",              # _qualite_par_essence()
    "declass_pct_essence": 38.2,
    "gain_potentiel_fcfa": 900_000,          # gain si TRS → 60 %
    "trs_objectif": 60.0,                    # Parametre.get('trs_objectif_pct', 60.0)
}
```

Helpers déjà présents à réutiliser : `_machine_prioritaire_recent()` (dashboard.py), Pareto par catégorie (dashboard.py:2399), `_qualite_par_essence()`, `calcule_manque_gagner()` (trs.py), `Parametre.get()`.

### Score de priorité : FCFA × récurrence (décision 2026-06-05)

Remplace la priorité hardcodée et `_priorite_dynamique()`. Chaque recommandation déclenchée reçoit un score calculé :

```python
def _score_recommandation(code: str, manque_fcfa: float, date_fin, jours: int = 30) -> int:
    """Score = FCFA courant × facteur récurrence (nb périodes récentes où la règle a aussi tiré)."""
    # Vérifier si la règle s'est déclenchée dans la période précédente
    date_prec_fin = date_fin - timedelta(days=jours)
    date_prec_debut = date_prec_fin - timedelta(days=jours)
    recos_prec = analyse_recommandations(date_debut=date_prec_debut, date_fin=date_prec_fin)
    codes_prec = {r['code'] for r in recos_prec}
    facteur = 1.5 if code in codes_prec else 1.0   # +50 % si déjà déclenché la période d'avant
    return round(manque_fcfa * facteur)
```

`analyse_recommandations()` retourne la liste triée par `score` décroissant. En cas d'égalité, Source B (cause terrain) passe avant Source A (indicateur). Affichage limité à **5 fiches** maximum (lisibilité terrain).

### Calcul du gain attendu — formule physique (décision 2026-06-05)

Le gain est calculé à partir des paramètres physiques de la chaîne 4, pas en appliquant un % sur le FCFA global. Cela isole la part récupérable imputable à la cause spécifique de la recommandation.

**Source B (cause d'arrêt dominante) :**

```python
def _calculer_gain_attendu_source_b(contexte, taux_reussite_tuple):
    """
    Gain = heures_imputables_cause × taux_reussite × capacite_h × prix_moyen_pondere
    Formule ancrée dans les paramètres physiques de la chaîne 4 (pas un % sur FCFA global).
    """
    taux_min_pct, taux_max_pct = taux_reussite_tuple

    # Proxy heures imputables : inverser le calcul FCFA cause dominante
    prix_moyen = _prix_moyen_pondere(contexte.get('equipes_periode', []))
    capacite_h = Parametre.get('capacite_equipe_h', 1.5625)   # m³/h
    fcfa_cause = contexte.get('cause_dominante_fcfa', 0)

    if fcfa_cause <= 0 or prix_moyen <= 0 or capacite_h <= 0:
        return 0, 0

    # heures perdues imputables à cette cause (récupération inverse du calcul FCFA)
    heures_cause = fcfa_cause / (prix_moyen * capacite_h)

    gain_min = round(heures_cause * taux_min_pct / 100 * capacite_h * prix_moyen)
    gain_max = round(heures_cause * taux_max_pct / 100 * capacite_h * prix_moyen)
    # Équivalent simplifié : gain_min = fcfa_cause × taux_min / 100
    # Mais l'écriture via heures × capacite × prix rend la formule explicitement physique
    return gain_min, gain_max
```

**Taux de réussite par catégorie** (intégrés dans `BIBLIOTHEQUE_CONTRE_MESURES['taux_reussite']` ci-dessus) :

| Catégorie | Taux min | Taux max | Justification |
|---|---|---|---|
| Approvisionnement | 40 % | 70 % | Levier management direct, décision rapide |
| Panne machine | 30 % | 60 % | Dépend de la qualité du préventif effectué |
| Mécanique | 35 % | 65 % | Bonne réponse aux inspections régulières |
| Réglage / outil | 50 % | 80 % | Fort levier : standardisation lames très efficace |
| Qualité matière | 20 % | 50 % | Dépend du fournisseur, hors contrôle direct CUF |
| Organisationnelle | 40 % | 70 % | Levier fort mais exige adhésion des équipes |
| Énergie / réseau | 10 % | 40 % | Facteurs externes, levier limité |

**Source A (règles indicateur) — méthode par type :**

```python
GAIN_METHODE_SOURCE_A = {
    # TRS : gain = (TRS_objectif - TRS_actuel)/100 × heures_totales_postes × capacite × prix × taux
    'TRS_CRITIQUE':         {'taux': (35, 65), 'methode': 'trs_delta'},
    'TRS_MOYEN':            {'taux': (25, 50), 'methode': 'trs_delta'},
    # Déclassé : gain = volume_declass_m3 × (prix_conforme - prix_revente_declass) × taux
    'DECLASS_EXCESSIF':     {'taux': (30, 60), 'methode': 'declass_delta'},
    # Manque : appliquer taux directement sur manque_a_gagner
    'MANQUE_ELEVE':         {'taux': (25, 50), 'methode': 'manque_direct'},
    # Saisies : gain non quantifiable en FCFA direct (problème de données, pas de production)
    'SAISIES_INCOHERENTES': {'taux': None,     'methode': 'non_quantifiable'},
    # Tendance : gain = delta_semaine_fcfa × taux
    'TENDANCE_NEGATIVE':    {'taux': (20, 45), 'methode': 'tendance_delta'},
}
```

**Affichage section 5 :** `"Gain attendu : entre {gain_min} et {gain_max} FCFA/semaine si l'action réussit — estimation basée sur {heures_cause:.1f} h perdues × {capacite_h} m³/h × {prix_moyen} FCFA/m³ × taux de réussite {taux_min}–{taux_max} %."` Présenté comme estimation explicite, hypothèses visibles pour défendabilité académique. Pour `SAISIES_INCOHERENTES`, section 5 affiche : `"Gain non chiffrable directement — ce problème fausse les calculs TRS. Le corriger améliore la fiabilité de tous les indicateurs."`

### Correction seuil hardcodé

`SAISIES_INCOHERENTES` utilise `>20.0` hardcodé. Remplacer par
`Parametre.get('seuil_saisies_incoherentes', 20.0)` — cohérent avec tous les autres seuils.

### Boutons d'action par recommandation (défaut retenu — utilisateur « aucune idée »)

Chaque fiche reçoit le CTA adapté à sa nature plutôt qu'un bouton uniforme :

| Type de reco | CTA principal |
|---|---|
| TRS_CRITIQUE, ARRETS_NON_DOCUMENTES, DECLASS_EXCESSIF, RENDEMENT_FAIBLE, OBJECTIF_NON_ATTEINT, TENDANCE_NEGATIVE | **Créer analyse Ishikawa** (pré-remplit `origine_type='recommandation'`, `reco_code`) |
| Fiches Source B (approvisionnement, etc.) — contre-mesure déjà connue | **Créer une action Chef** (la contre-mesure est identifiée, on la suit) |
| SAISIES_INCOHERENTES — problème de données, pas de production | **Voir les fiches à corriger** (lien vers liste filtrée) |

Si une analyse existe déjà pour un code, afficher « Voir l'analyse #N » : la route `recommandations.index()` injecte `problemes_par_reco = {code: probleme_id}` via `Probleme.query.filter_by(origine_type='recommandation')`.

### Boucle vérification — avant/après sur indicateur réel (décision 2026-06-05)

L'objectif P4 : montrer que l'outil ne se limite pas à proposer des actions — il mesure si l'action a produit un effet. La section 6 compare l'indicateur déclenchant avant et après l'action.

**Chaque règle et contre-mesure définit son `indicateur_verification`** :

| Code / Catégorie | Indicateur mesuré | Sens attendu |
|---|---|---|
| TRS_CRITIQUE, TRS_MOYEN | TRS moyen (%) | ↑ hausse |
| DECLASS_EXCESSIF | % volume déclassé | ↓ baisse |
| ARRETS_NON_DOCUMENTES | % postes avec arrêts non documentés | ↓ baisse |
| SAISIES_INCOHERENTES | % postes avec anomalies R1+R4 | ↓ baisse |
| TENDANCE_NEGATIVE | Manque à gagner (FCFA/semaine) | ↓ baisse |
| Source B (toutes catégories) | Heures d'arrêt de la catégorie dominante | ↓ baisse |

**Calcul avant/après — sans nouvelle table** :

```python
def _calcul_avant_apres_reco(code, action):
    """
    Avant  = indicateur sur les 30 jours AVANT création de l'action.
    Après  = indicateur sur les 7 jours APRÈS la date de clôture.
    Clôture = date du dernier ActionChefEvenement avec nouveau_statut='fait'.
    Pas de nouvelle table : utilise action.cree_le + ActionChefEvenement.
    """
    evt_clos = ActionChefEvenement.query.filter_by(
        action_id=action.id, nouveau_statut='fait'
    ).order_by(ActionChefEvenement.cree_le.desc()).first()

    if not evt_clos:
        return {'statut': 'non_close'}

    date_clos = evt_clos.cree_le.date()
    apres_fin  = date_clos + timedelta(days=7)

    if date.today() < apres_fin:
        jours_restants = (apres_fin - date.today()).days
        return {'statut': 'en_attente', 'jours_restants': jours_restants}

    avant_debut = action.cree_le.date() - timedelta(days=30)
    avant_fin   = action.cree_le.date()
    apres_debut = date_clos

    return _indicateur_avant_apres(code, avant_debut, avant_fin, apres_debut, apres_fin)


def _indicateur_avant_apres(code, avant_debut, avant_fin, apres_debut, apres_fin):
    """Calcule valeur avant et après sur l'indicateur propre à chaque code."""
    INDICATEURS = {
        'TRS_CRITIQUE':         ('trs_moyen',          'hausse'),
        'TRS_MOYEN':            ('trs_moyen',           'hausse'),
        'DECLASS_EXCESSIF':     ('pct_declass',         'baisse'),
        'ARRETS_NON_DOCUMENTES':('pct_r2_anomalies',    'baisse'),
        'SAISIES_INCOHERENTES': ('pct_anomalies_r1r4',  'baisse'),
        'TENDANCE_NEGATIVE':    ('manque_fcfa_semaine',  'baisse'),
    }
    libelle_map = {
        'trs_moyen': 'TRS moyen (%)',
        'pct_declass': '% volume déclassé',
        'pct_r2_anomalies': '% postes arrêts non documentés',
        'pct_anomalies_r1r4': '% postes avec anomalies saisie',
        'manque_fcfa_semaine': 'Manque à gagner FCFA/semaine',
        'heures_arret_categorie': 'Heures arrêt catégorie dominante',
    }

    # Source B : indicateur = heures arrêt de la catégorie (code commence par 'B_')
    if code.startswith('B_'):
        indicateur, sens = 'heures_arret_categorie', 'baisse'
    else:
        indicateur, sens = INDICATEURS.get(code, ('trs_moyen', 'hausse'))

    valeur_avant = _calculer_indicateur(indicateur, avant_debut, avant_fin)
    valeur_apres = _calculer_indicateur(indicateur, apres_debut, apres_fin)

    if valeur_avant is None or valeur_apres is None:
        return {'statut': 'donnees_insuffisantes'}

    delta = valeur_apres - valeur_avant
    delta_pct = round(delta / valeur_avant * 100, 1) if valeur_avant != 0 else 0
    amelioration = (sens == 'hausse' and delta > 0) or (sens == 'baisse' and delta < 0)

    return {
        'statut': 'bilan_disponible',
        'libelle': libelle_map.get(indicateur, indicateur),
        'avant': valeur_avant, 'apres': valeur_apres,
        'delta': delta, 'delta_pct': delta_pct,
        'amelioration': amelioration,
        'verdict': 'Amélioration confirmée ✓' if amelioration else 'Pas d\'amélioration détectée',
    }
```

**Rendu template section 6** selon le `statut` du bilan :
- `non_close` → texte statique de l'indicateur + CTA (créer action / voir action en cours)
- `en_attente` → `"Action clôturée — bilan disponible dans {jours_restants} jours (7 j de recul nécessaires)."`
- `donnees_insuffisantes` → `"Données insuffisantes sur la période de comparaison."`
- `bilan_disponible` → tableau avant/après : indicateur | Avant | Après | Δ | Verdict vert ou rouge

**P4 simple, P5 enrichi** : en P5, cette boucle sera complétée par l'estimation FCFA évités (Design 3 croisé avec le bilan indicateur). En P4, le verdict est qualitatif (amélioration oui/non) + valeurs réelles de l'indicateur.

**Aucune nouvelle table** : repose sur `ActionChef.reco_code` + `ActionChefEvenement` (table existante pour l'audit trail).

---

## DESIGN 2 — SUPPRESSION COUCHE 2 IA (accord utilisateur 2026-06-05)

Fichiers et blocs à supprimer :

1. `app/services/reco_ai.py` — fichier entier.
2. `app/templates/recommandations/index.html` — bloc `wp-reco-ai-zone` (~lignes 141-156) + script AJAX `analyserIA()` (~lignes 164-220).
3. `app/routes/recommandations.py` — route `/ai/<code>` (POST) + import `reco_ai`.

Le bandeau « enrichissement IA » (index.html ligne 53) est remplacé par :
`« Recommandations calculées sur les données réelles des {{ nb_postes }} postes · TRS actuel {{ trs }} % · 100 % hors ligne. »`

---

## DESIGN 3 — BILAN ACTIONS CHEF EN FCFA ÉVITÉ

### Problème actuel

`_bilan_efficacite_action_chef()` (dashboard.py:270) compare uniquement les arrêts avant/après (`nb_arrets`, `duree_moy`, seuil 20 % → « Amélioration visible »).

### Ce que l'utilisateur veut

Bilan en **FCFA évités** (pas seulement en arrêts) + tri de la liste actions par impact FCFA potentiel.

### Enrichissement

```python
# Dans _bilan_efficacite_action_chef(), après duree_moy_avant/après :
capacite_m3_h  = Parametre.get('capacite_equipe_h', 1.5625)
prix_moyen     = _prix_moyen_pondere(equipes_avant)        # prix snapshot
duree_reduite_h = (duree_moy_avant - duree_moy_apres) * nb_arrets_apres / 60
fcfa_evite = round(max(0, duree_reduite_h) * capacite_m3_h * prix_moyen)
bilan["fcfa_evite"] = fcfa_evite
```

Template actions : badge vert « X FCFA évités/semaine (estimation) » si `fcfa_evite > 0`.

### Tri par impact FCFA potentiel

Dans la liste `actions_chef`, trier par durée d'arrêts récents de `action.machine_cible` × capacité × prix. Les actions sur la machine critique remontent en premier.

---

## DESIGN 4 — ALERTE COCKPIT DEPUIS RÉCURRENCES MACHINES

`_recurrences_machines()` (dashboard.py:1622) détecte déjà : machine ≥3 occurrences, cause ≥3 occurrences, combo machine+cause ≥2 occurrences et ≥90 min cumulées.

Injecter le résultat dans `vue_chef()` et l'afficher dans la colonne gauche du cockpit via le partial existant `_signaux_p2.html` :
```
⚠ Récurrence : Bicoupe × « Changement de lame » — 3 fois, 2h15 cumulées
  [Analyser (Ishikawa)] →
```

---

## DESIGN 5 — PRIX VISIBLES PAR LE CHEF (lecture seule)

Dans `app/routes/admin.py`, retirer `prix_ayous`, `prix_iroko`, `prix_azobe`, `prix_movingui` de `PARAMS_ADMIN_ONLY`. Afficher en lecture seule dans un encart de `templates/dashboard/pertes.html` :
« Prix utilisés dans les calculs : Ayous X · Iroko Y · Azobé Z · Movingui W FCFA/m³ — modifiables dans les paramètres admin. »
Afficher la **source effectivement utilisée** par `calcule_manque_gagner()` (prix_snapshot figé vs Parametre vivant) pour cohérence avec les montants.

---

## FICHIERS À MODIFIER

| Fichier | Modification |
|---|---|
| `app/services/recommandations.py` | Réécrire les 7 règles en format 6 sections (Source A) · `BIBLIOTHEQUE_CONTRE_MESURES` (5 CM × 7 catégories avec métadonnées scoring) · `_selectionner_contre_mesure()` (score multicritère : machine +30, récurrence +20, durée +15, coût +15, doublon -20) · `_calculer_gain_attendu_source_b()` (heures_cause × taux × capacite × prix) · `GAIN_METHODE_SOURCE_A` (méthode par règle) · `_score_recommandation()` (FCFA × récurrence) · `_calcul_avant_apres_reco()` + `_indicateur_avant_apres()` (boucle avant/après par indicateur) · corriger seuil `SAISIES_INCOHERENTES` |
| `app/routes/recommandations.py` | Enrichir contexte (machine/cause dominante/FCFA/equipes_periode) · injecter `problemes_par_reco` + `bilans_par_reco` (avant/après indicateur) · supprimer route + import AI |
| `app/templates/recommandations/index.html` | Supprimer Couche 2 · remplacer bandeau IA · CTA adapté par type de reco |
| `app/routes/dashboard.py` | Calculer cause d'arrêt dominante (réutiliser Pareto) · enrichir `_bilan_efficacite_action_chef()` (FCFA) · tri actions par impact · injecter récurrences au cockpit |
| `app/templates/chef/_signaux_p2.html` | Alerte récurrence machine si détectée |
| `app/templates/chef/actions.html` | Badge FCFA évités sur actions bilantées |
| `app/routes/admin.py` | Retirer prix_* de `PARAMS_ADMIN_ONLY` |
| `app/templates/dashboard/pertes.html` | Encart prix lecture seule |
| `app/services/reco_ai.py` | **SUPPRIMER** |
| `documents/notes-impact/P58-feat-reco-metier-p4.md` | Note d'impact 9 sections avant commit |

---

## DIFFÉRÉ P5

- Rubrique 2 Fiches : auto-validation admin après X heures si chef absent ; tri fiches anomalie en tête.
- Rubrique 4 Qualité : flèches tendance par essence + comparaison période sur période.
- Rubrique 5 Pertes : comparaison multi-période + lien « Créer action corrective » depuis une perte.
- Rubrique 3 Machines : bouton Ishikawa depuis fiche récurrence sur la page Machines (pas seulement cockpit).
- Enrichir la bibliothèque Source B avec plusieurs contre-mesures alternatives par catégorie.

---

## VÉRIFICATION

```bash
cd cuf-pilotage && python seed_data.py
bash .claude/skills/run-cuf-pilotage/smoke.sh       # 16/16 doivent rester verts
python .claude/skills/run-cuf-pilotage/screenshot.py chef
# Contrôler :
# · Reco TRS_CRITIQUE affiche les 6 sections avec TRS%, machine, FCFA réels
# · Reco « cause dominante » apparaît si une catégorie ≥ 30 % du temps d'arrêt
# · Aucun bouton « Analyser avec l'IA » nulle part ; bandeau « 100 % hors ligne »
# · CTA adapté : Ishikawa / Action Chef / Corriger fiches selon le type
# · Actions Chef triées par impact FCFA ; badge « FCFA évités » sur action efficace
# · Prix par essence visibles sur /pertes (lecture seule)
# · Alerte récurrence machine dans la colonne gauche du cockpit si détectée
```

---

---

# Audit critique — Profil Chef de Production (wood_pilot / CUF Chaîne 4)

> Produit le 2026-06-02 · Branche `claude/install-claude-excel-6MGzv`
> Contexte : préparation d'une démonstration à un encadreur expert scierie, futur utilisateur potentiel du profil Chef.

---

## 0. PLAN D'EXÉCUTION VALIDÉ (2026-06-03)

**Contexte.** Le profil Chef est analytiquement solide mais échoue au test des 10 secondes et contient un bug d'objectif (147 %) qui ruinerait la crédibilité devant un expert scierie. Le chef ne peut ni vérifier sur quelles fiches reposent ses indicateurs, ni justifier les montants FCFA, ni naviguer facilement d'un chiffre vers son détail. La démo terrain approche. Les 5 corrections ci-dessous (toutes P0) ont été validées par l'utilisateur le 2026-06-03.

### P0-1 — Corriger le bug objectif (147 %)

**Fichier** : `app/routes/dashboard.py`, fonction `_comparaison_equipes_production()` **ligne 1669**.
**Cause exacte** : `objectif = _safe_float_param('objectif_m3', 12.5) * len(items)` — l'objectif d'un shift est multiplié par le nombre de fiches soumises de ce shift, pas par le nombre de jours de la période. À l'inverse, `_resume_production()` (ligne 1590–1657) est **déjà correct** (il agrège `objectif_jour` par jour réel). Le 147 % vient donc de la comparaison par équipe.
**Correction** : remplacer `len(items)` par le nombre de jours distincts de la période (`len({e.date for e in equipes})`). Objectif d'un shift = `12.5 × nb_jours_periode`.
**Vérification** : après correction, l'atteinte affichée doit tomber sous 100 % (cohérent avec TRS ~70 % et H3).

### P0-2 — Traçabilité de la validation (Problème 1 reformulé)

**Fichiers** : `app/routes/dashboard.py` `vue_chef()` (ligne 1988) + `app/templates/chef/dashboard.html` (sous le sélecteur 7j/30j/90j, ligne ~16).
**Backend** : dans `vue_chef()`, compter les fiches de la période par statut. Séparer comptabilisées (`STATUTS_ANALYSES` = valide_chef + verrouille) vs non comptabilisées (`STATUTS_NON_ANALYSES` = brouillon + a_verifier + a_corriger). Constantes déjà dans `models.py:30-31`. Règle R7 : aucune table nouvelle.
**Template** : ligne discrète « X fiches validées comptabilisées · Y non prises en compte (a à vérifier · b à corriger · c brouillon) ». Les compteurs non nuls renvoient vers `dashboard.fiches_chef` filtré par statut (route existante).

### P0-3 — Données récentes + message « Aujourd'hui » vide (Problème 3)

**Fichier 1** : `seed_data.py` lignes 24–29. Remplacer avril 2026 par une fenêtre glissante : `JOUR_FIN = date.today()`, `JOUR_DEBUT = JOUR_FIN - timedelta(days=6)`. Conserver la logique de génération. Relancer `python seed_data.py`.
**Fichier 2** : `app/templates/chef/_aujourdhui.html`. Si pas de fiche du jour, afficher « En attente de la première saisie du jour » + dernière période connue. Sinon, contenu actuel.

### P0-4 — Prix consultables par le chef (Problème 4)

**Fichiers** : template `/pertes` (encart lecture seule).
**Attention à la source** (voir Insight session) : deux jeux de prix coexistent — `prix_snapshot` figé par fiche (seed : Ayous 180k, Iroko 420k, Azobé 280k, Movingui 320k) et les `Parametre` vivants (`__init__.py:93` : Ayous 85k, Iroko 110k, Azobé 120k, Movingui 95k). À l'exécution : afficher la source effectivement utilisée par `calcule_manque_gagner()` dans `trs.py`, pour cohérence avec les montants affichés. Le chef voit, ne modifie pas (modification reste admin-only).

### P0-5 — Vérification des prix vs marché réel (Problème 5)

**Aucun code.** Aligner d'abord les deux jeux de prix (P0-4) puis valider les ordres de grandeur avec l'utilisateur/encadreur. Ajustement via `/admin/parametres`. Argument démo : outil paramétrable.

### Points explicitement reportés

- **Boucle Lean visible** (Pareto → Ishikawa → Action → Bilan) : après validation, sur demande. Mécanique présente, manque la visibilité.
- **Statut global VERT/ORANGE/ROUGE** : P1, juste après les P0.
- **Performance par opérateur** : impossible proprement (`Equipe.operateur_nom` texte libre, sans FK). Reporté P2.
- **Liens machine critique + top-1 Pareto sur cockpit** (Problème 2) : P1 — les liens existent dans `_priorites_chef`, il faut les exposer sur le cockpit.

### Vérification de bout en bout

```bash
cd cuf-pilotage && python seed_data.py        # repeupler sur 7 jours glissants
bash .claude/skills/run-cuf-pilotage/smoke.sh  # 16/16 checks doivent rester verts
python .claude/skills/run-cuf-pilotage/screenshot.py chef
# Contrôler : atteinte objectif < 100 % · ligne traçabilité fiches visible
#   · section « Aujourd'hui » peuplée · prix par essence visibles sur /pertes
```

---

## 0bis. PLAN D'EXÉCUTION P2 — 4 signaux de pilotage (design validé 2026-06-03)

### Contexte

Les P0 (bug objectif, traçabilité, message vide, prix, paramètres) et P1 (cockpit décisionnel : verdict global, signaux critiques, alertes, manque à gagner remonté, boucle Lean) sont livrés et validés sur Windows. P2 ajoute **quatre signaux de pilotage** qui répondent à des angles morts identifiés en section 6 du présent audit. L'utilisateur a validé les 4 décisions de conception le 2026-06-03 : cockpit compact (résumé + clic vers atelier), alerte « soir décroche » à **un seul critère**, et périmètre P2 limité à ces 4 signaux. Aucune nouvelle table, aucun changement de modèle, aucune migration (règle R7). Tout se calcule sur des données déjà présentes.

**Décision de périmètre assumée :** P2 livre les 4 signaux en **ajout additif** sur le cockpit P1 existant, en suivant le principe « résumé sur le cockpit + clic pour creuser » (la carte « Signaux critiques » de P1, `dashboard.html:378`, en est déjà l'amorce). Le **rebuild visuel complet en 2 colonnes** (décision 1, version radicale) est volontairement **différé** : refondre `dashboard.html` d'un bloc romprait le cockpit P1 qui fonctionne et dépasserait l'estimation de ~2 jours. Cette mise en page sera une passe éditoriale P3 séparée. Ce choix est soumis à l'approbation via ExitPlanMode.

### Principe métier verrouillé à respecter

- Les deux postes sont `'Matin'` et `'Apres-midi'` (constante `_SHIFTS_JOUR`, dashboard.py:565). Le « soir 14h–23h » **est** le poste `Apres-midi`. L'alerte cible `Apres-midi`, étiquetée « équipe du soir (Après-midi) ».
- Les KPI ne comptent que les fiches `STATUTS_ANALYSES` (valide_chef + verrouille). Les helpers P2 utilisent le même filtre.
- Le seuil de déclassement réel est `seuil_declass_pct` (défaut **30 %**, pas 15 %). Ne pas inventer de seuil.
- Cadence normale = `capacite_equipe_h` (défaut 1,5625 m³/h, Parametre vivant).

### P2-A — Projection fin de poste enrichie sur le cockpit

**Existant à réutiliser** : `_projection_production_active()` (dashboard.py:1822) renvoie déjà `volume_actuel`, `projection`, `objectif`, `pct`, `couleur`. Affichée sur `/chef/production` (production.html:57) mais **pas** sur le cockpit `/chef`. Le cockpit n'a qu'une sous-ligne allégée (`kpi_jour.objectif.projection`, dashboard.py:790 → _aujourdhui.html:152).

**Modification** :
1. `dashboard.py` — enrichir le dict de `_projection_production_active()` avec `ecart_objectif = round(objectif - projection, 2)` et, si positif, `rattrapage_min = round(ecart_objectif / capacite_h * 60)`. Réutiliser `capacite_equipe_h` via `Parametre.get`.
2. `dashboard.py` `vue_chef()` — appeler `_projection_production_active()` et l'injecter (`projection_active=...`) dans les deux `render_template` (cas vide et cas peuplé).
3. `app/templates/chef/_aujourdhui.html` — remplacer la sous-ligne 152-153 par un encart lisible : « À ce rythme : {volume_actuel} m³ → fin de poste {projection} m³ · objectif {objectif} m³ · il manque {ecart_objectif} m³ (~{rattrapage_min} min à cadence normale) ». Masqué si pas de poste actif.

### P2-B — Alerte « équipe du soir décroche » (un seul critère)

**Nouveau helper** `_alerte_soir_decroche(aujourd_hui, jours=3, seuil_pts=15)` dans dashboard.py :
- Pour chacun des `jours` derniers jours, calculer TRS moyen `Matin` et TRS moyen `Apres-midi` sur les fiches `STATUTS_ANALYSES`.
- Ne considérer que les jours où les **deux** postes existent. Si sur tous ces jours `trs_apresmidi < trs_matin - seuil_pts` (et au moins 3 jours qualifiants) → renvoyer `{trs_soir_moy, trs_matin_moy, ecart, jours_consecutifs}`. Sinon `None`.
- Réutiliser le pattern de moyenne de `trs_moyen_groupe` (vue_chef:2149).

**Injection + rendu** : injecter `alerte_soir` dans `vue_chef`, rendre une carte d'alerte sur le cockpit (nouveau partial `chef/_signaux_p2.html`, inclus après `_alertes.html`).

### P2-C — Alerte déclassement par essence

**Existant à réutiliser** : `_qualite_par_essence(equipes)` (dashboard.py:1883) calcule déjà `declass_pct` par essence + `seuil_declass`.

**Nouveau helper** `_alerte_declassement_essence(equipes)` : appelle `_qualite_par_essence`, filtre les essences où `declass_pct > seuil_declass`, trie par dépassement décroissant, renvoie la liste (vide = pas d'alerte). Rendu dans `chef/_signaux_p2.html` : « {essence} : {declass_pct} % déclassé (seuil {seuil} %) » avec lien vers `/chef/qualite`.

### P2-D — Taux de disponibilité machine sur le cockpit

**Existant à réutiliser** : `_machine_prioritaire_recent(aujourd_hui, jours=7)` (dashboard.py:972) itère déjà les arrêts sur 7 j et somme `duree_min`.

**Modification** : enrichir ce helper pour sommer aussi `arret.duree_impact_min` et compter `nb_postes` (fiches distinctes de la fenêtre). Calculer `disponibilite_pct = round((1 - impact_total / (nb_postes * 480)) * 100, 1)` (480 = `duree_poste`). Ajouter `disponibilite_pct` au dict renvoyé. Afficher dans la carte « Signaux critiques » existante (dashboard.html:387-390) : « {machine} : {disponibilite_pct} % de disponibilité (7 j) ».

### Fichiers touchés

- `cuf-pilotage/app/routes/dashboard.py` — 2 helpers enrichis (`_projection_production_active`, `_machine_prioritaire_recent`), 2 helpers nouveaux (`_alerte_soir_decroche`, `_alerte_declassement_essence`), injections dans `vue_chef`.
- `cuf-pilotage/app/templates/chef/_aujourdhui.html` — projection enrichie.
- `cuf-pilotage/app/templates/chef/_signaux_p2.html` — **nouveau** partial (soir décroche + déclassement essence).
- `cuf-pilotage/app/templates/chef/dashboard.html` — `{% include 'chef/_signaux_p2.html' %}` + disponibilité dans la carte signaux critiques.

**Hors périmètre P2 (différé, conformément à la décision 4)** : table Machine, FK opérateur, prédiction maintenance, mode « Soutenance », rebuild 2 colonnes complet.

### Vérification de bout en bout

```bash
cd cuf-pilotage
bash .claude/skills/run-cuf-pilotage/smoke.sh        # 16/16 doivent rester verts
python .claude/skills/run-cuf-pilotage/screenshot.py chef
# Contrôler sur la capture cockpit chef :
#   · projection fin de poste lisible (si poste actif) avec manque + rattrapage
#   · alerte « soir décroche » présente si l'écart TRS le justifie sur 3 j
#   · alerte déclassement essence si une essence dépasse le seuil
#   · disponibilité machine affichée dans la carte Signaux critiques
```

### Livrable documentaire

Note d'impact 9 sections `documents/notes-impact/P56-feat-signaux-pilotage-p2.md` avant commit. Commit sur `claude/install-claude-excel-6MGzv`, jamais sur main.

---

## 1. Résumé exécutif

Le profil Chef de Production dispose d'un **moteur analytique solide et réel** : TRS D×P×Q calculé sur données terrain, attribution financière des pertes en FCFA, Pareto des arrêts, Ishikawa 6M + 5 Pourquoi complet, recommandations déterministes + IA. Ce n'est ni un tableau de bord vide ni une maquette.

Pourtant, il échoue au test des 10 secondes. Pourquoi ? Parce que **tout est au même niveau d'altitude** dans un scroll continu de 15 sections. Le signal visuellement dominant est une grande carte verte « 70,6 % » qui rassure, pendant que 19,5 M FCFA de manque à gagner et un avertissement sur les arrêts non documentés sont enfouis en-dessous. Il n'existe pas de verdict synthétique « usine sous contrôle : OUI/NON ».

Il y a également **un bug de calcul de l'objectif** qui produira une gêne certaine face à un expert : l'atteinte affichée à 147,5 % sur la page Production est un artefact dû à un objectif qui rétrécit pour coller au nombre de fiches soumises, pas un objectif fixe. Un professionnel du bois qui sait que CUF vise 25 m³/jour lira « 147 % d'atteinte » et perdra confiance dans tous les autres chiffres.

**Verdict** : base prometteuse et sérieuse à restructurer sur l'axe de la hiérarchie décisionnelle — pas une reconstruction.

---

## 2. Diagnostic global sans complaisance

| Critère | État | Commentaire |
|---|---|---|
| Données réelles | ✓ | Tous les calculs sont sur données BD, aucun placeholder |
| Moteur TRS | ✓ | D×P×Q par essence et par équipe, avec impact arrêts exacts |
| Attribution financière | ✓ | Manque à gagner, pertes D/P/Q en FCFA, prix snapshot figé |
| Ishikawa 6M + 5 Pourquoi | ✓ | Implémenté complet (4 étapes, rapport A3) |
| Verdict 10 secondes | ✗ | Absent — pas de statut global "sous contrôle / hors contrôle" |
| Hiérarchie visuelle | ✗ | 15 sections à poids égal, pas de cockpit en tête |
| Objectif affiché | ✗ BUG | 147,5 % = artefact (objectif shrinks avec nb postes soumis) |
| Contexte temporel | ✗ | "Aujourd'hui" à 0 si aucune fiche du jour — aucun message d'état |
| Cohérence mémoire | ✗ partiel | 147,5 % contredit H1/H3 (l'usine sous-performe) |
| Navigation | ✓ | 9 pages cohérentes, liens directs actifs |
| Mobile / terrain | ~ | Conçu desktop, tablette terrain non testée pour le profil chef |

---

## 3. Forces actuelles (à préserver absolument)

1. **Moteur TRS réel** — `services/trs.py` : sweep line sur créneaux, impact arrêts (seul le dépassement maintenance planifiée est imputé). C'est le bon algorithme, pas une approximation.
2. **Attribution D/P/Q en FCFA** — `calcule_pertes_equipe()` + `calcule_manque_gagner()` : chiffrage complet avec prix snapshot figé à la soumission, taux revente déclassé, valeur résiduelle déchets.
3. **Ishikawa guidé** — workflow 4 étapes, solidité de l'analyse tracée (≥3 causes + profondeur ≥3 = "Solide"), lien automatique vers ActionChef.
4. **Priorités décisionnelles** — `_priorites_chef()` : 5 priorités max scorées par urgence, en langage naturel, avec CTA. C'est le bon concept — il faut le monter en tête de page.
5. **Boucle Lean traçable** — Pareto → Ishikawa → ActionChef → bilan efficacité avant/après 7j. C'est un argument de fond pour la démo.
6. **Anti-chevauchement** — contrainte bicoupe (machine unique) enforced client + serveur. Cohérence physique garantie.
7. **Scorecard semaine** — tableau 6j × 2 shifts, color-coded TRS. Outil de supervision concret.

---

## 4. Faiblesses et incohérences

### 4.1 Bug critique — Objectif à 147,5 %

**Fichier** : `dashboard.py:1590–1649`, fonction `_resume_production()`

**Problème** : `objectif = objectif_m3 × len(equipes)` — l'objectif total est calculé comme `12,5 m³ × nombre de postes effectivement soumis`, pas comme `12,5 m³ × nombre de postes attendus sur la période`. Si on a soumis 60 fiches sur 30 jours (objectif 60 × 12,5 = 750 m³) mais que le volume réel conforme est 1 106 m³, on obtient 147 % — qui n'a aucun sens métier car la seed génère des volumes d'entrée 22–36 m³ par poste (physiquement cohérent pour le bois brut) mais l'objectif de 12,5 m³ est une capacité de sortie conforme.

**Impact démo** : un expert scierie qui sait que la bicoupe a une capacité physique de 12,5 m³/poste de sortie conforme verra immédiatement que les 147 % sont impossibles. C'est le risque de crédibilité n°1.

**Hypothèse cause** : dans le ratio, le numérateur est probablement `volume_conforme + volume_declass` (sortie totale) au lieu de `volume_conforme` seul (sortie utilisable), OU la capacité de 12,5 m³ est définie comme une capacité de sortie conforme mais la seed génère des volumes d'entrée bien supérieurs. À vérifier dans `_resume_production()`.

### 4.2 Absence de verdict synthétique

La première question d'un chef en arrivant est « est-ce que l'usine est sous contrôle ? ». Il n'y a pas de réponse en tête de page. Le TRS 70,6 % est visible mais sans interprétation directe (au-dessus/en-dessous de l'objectif ? bonne ou mauvaise semaine ?).

### 4.3 Confusion temporelle

La section « Aujourd'hui » affiche des KPI à 0 si aucune fiche n'est soumise aujourd'hui. La collecte terrain commence demain — dès la première fiche soumise, ce composant sera utile. Mais tant qu'il affiche 0, il envoie un signal négatif lors d'une démo.

### 4.4 Prix réservé à l'admin — chef aveugle sur le chiffrage

Le chef voit le manque à gagner en FCFA mais ne peut pas accéder aux prix par essence (`PARAMS_ADMIN_ONLY` dans `admin.py:32-40`). Il ne peut donc pas valider si le calcul financier est cohérent avec les prix réels du marché. Devant un expert, il sera incapable de justifier les montants.

### 4.5 Pas d'identifiant opérateur

`Equipe.operateur_nom` est un texte libre (STR 100, non unique). Impossible d'agréger les performances par opérateur. Ce n'est pas un bug — c'est une limite de modèle connue, à mentionner comme limitation du mémoire.

### 4.6 Pas de table Machine

Les machines sont des strings figées dans `config.py`. Les analyses de criticité sont valides (durée arrêts par machine × catégorie), mais on ne peut pas afficher « la bicoupe est à 65 % de disponibilité sur la semaine » sans calculer manuellement depuis les arrêts.

---

## 5. Audit détaillé de l'existant

| Élément | Problème métier traité | Décision rendue possible | Valeur opérationnelle | Limite actuelle | Verdict | Action recommandée |
|---|---|---|---|---|---|---|
| Cockpit aujourd'hui (`_aujourdhui.html`) | Que faire maintenant ? | Actions urgentes + fiches à traiter | Élevée | Affiché 0 si pas de fiche du jour | Indispensable | Améliorer : message "En attente de saisie" + contexte période récente |
| Priorités décisionnelles (`_priorites_chef`) | Quelle est la priorité n°1 ? | Choisir où agir en premier | Très élevée | Enterrée dans le scroll, pas en tête de page | Indispensable | Reconstruire : monter en haut, simplifier à 3 priorités max avec verdict global |
| TRS global (grand chiffre) | Performons-nous bien ? | Comparer à l'objectif | Élevée | Pas de comparaison explicite objectif/réel sur le même widget | Indispensable | Améliorer : ajouter flèche direction + "vs objectif 60 %" |
| Manque à gagner FCFA | Combien coûte l'écart ? | Décider si le problème vaut une action | Très élevée | Affiché en 3e position, après le TRS | Indispensable | Améliorer : remonter juste après le verdict global |
| Décomposition D×P×Q | D'où vient la perte ? | Choisir le levier (arrêts vs cadence vs qualité) | Très élevée | Bien placée, mais sans recommandation inline | Indispensable | Conserver + ajouter "Principal levier : [D/P/Q]" |
| Simulateur gain FCFA | Quel gain si j'améliore le TRS ? | Prioriser un investissement | Élevée | Fonctionnel | Utile | Conserver (argument académique OS6) |
| Scorecard semaine | Quelle régularité sur 6 jours ? | Identifier un shift qui décroche | Élevée | Bonne lisibilité | Indispensable | Conserver |
| Pareto arrêts (`/analyse/arrets`) | Quelle cause coûte le plus de temps ? | Décider quelle cause analyser en premier | Très élevée | Page séparée, pas de résumé top-1 sur le dashboard | Indispensable | Améliorer : résumé "Cause n°1 : X — Yh perdues" sur le dashboard + lien |
| Recommandations (`/recommandations/`) | Que recommande l'outil ? | Valider ou réfuter une recommandation IA | Élevée | Page séparée, top 3 en bas de dashboard | Utile | Améliorer : top 1 reco avec CTA |
| Ishikawa + 5 Pourquoi (`/problemes/`) | Quelle est la cause racine ? | Choisir la cause à traiter + plan d'action | Très élevée (OS4/H2) | Accessible mais pas lié depuis le Pareto cockpit | Indispensable | Améliorer : bouton "Analyser" depuis le résumé Pareto |
| Actions Chef (`/dashboard/chef/actions`) | Qu'est-ce qui est en cours / en retard ? | Relancer, clôturer, créer | Élevée | Bilan efficacité machine réel | Indispensable | Conserver |
| Page Production & Objectifs | Atteint-on l'objectif ? | Décider si un rattrapage est nécessaire | Élevée | BUG : 147 % artefact | Indispensable | Reconstruire le calcul |
| Page Qualité / Matière | Quel rendement matière par essence ? | Identifier l'essence qui perd le plus | Élevée | Pas d'alerte inline si déclassé > seuil | Utile | Améliorer : alerte seuil inline |
| Page Machines & Arrêts | Quelle machine cumule le plus d'arrêts ? | Prioriser la maintenance | Élevée | Données réelles, bien structurée | Indispensable | Conserver |
| Page Pertes financières (`/pertes`) | Comment sont réparties les pertes ? | Justifier un investissement maintenance | Très élevée | Accessible, drill-down par machine/essence | Indispensable | Conserver + prix visibles au chef |
| Export Excel | Archiver le rapport mensuel | Partager avec la direction | Utile | Fonctionnel | Secondaire | Conserver |
| Alertes chef (`_alertes.html`) | Saisies manquantes / brouillons | Relancer les opérateurs | Élevée | Template existe mais **non inclus** dans dashboard.html | Utile | Intégrer dans dashboard.html |

---

## 6. Angles morts

| Question chef | Réponse actuelle | Ce qui manque | Donnée nécessaire | Fonctionnalité à créer |
|---|---|---|---|---|
| L'usine est-elle sous contrôle ? | ✗ Absent | Verdict global OUI/NON | TRS du jour vs objectif + anomalies bloquantes | Widget statut global (3 couleurs) en tête du cockpit |
| Quelle est la machine critique en ce moment ? | ~ Partiel (Pareto page séparée) | Résumé "Machine n°1 cumule X h d'arrêts" sur le dashboard | Durée arrêts par machine cette semaine | Résumé machine critique sur le cockpit |
| Quel est l'arrêt le plus coûteux ? | ✗ Absent sur cockpit | L'arrêt qui a coûté le plus en FCFA | Durée × capacité × prix | Ligne "Arrêt le plus coûteux : [cause] [machine] = X FCFA" |
| Quelle est la principale perte de matière ? | ~ Page Qualité séparée | Résumé rendement + essence la plus problématique | Volume déclassé/déchet par essence | Widget rendement matière sur cockpit |
| Quelle est la principale perte de temps ? | ~ Pareto sur page séparée | Cause n°1 Pareto sur cockpit | Durée arrêts par cause | Résumé Pareto top-1 sur cockpit |
| Quelle est la principale perte financière ? | ~ Manque à gagner présent, trop bas | Position plus haute | FCFA calculés | Repositionnement |
| Quel shift a besoin d'accompagnement ? | ~ Comparaison Matin/Soir existe | Pas d'alerte si un shift décroche systématiquement | TRS par shift sur 7j | Alerte "Soir décroche : TRS 48 % vs 65 % Matin" |
| Quels objectifs sont menacés aujourd'hui ? | ~ Partiel si données du jour | Projection "À ce rythme, objectif atteint à X %" | Volume saisi + nb postes restants | Widget projection journalière |

---

## 7. Architecture fonctionnelle cible

### Principe directeur

**Altitude d'abord.** Le cockpit doit être lisible en 10 secondes via 3 zones visuellement distinctes :
- Zone rouge (altitude 1) : verdict + problème n°1 + action n°1
- Zone orange (altitude 2) : causes + tendances + scorecard
- Zone verte (altitude 3) : détails, export, historique

### Module 1 — Cockpit exécutif (altitude 1) — À créer / refactorer

**Objectif** : répondre à « est-ce que l'usine est sous contrôle ? » en un coup d'œil.

Contenu de la bande supérieure fixe :
- Statut global : VERT (TRS ≥ 60 % + pas d'anomalie bloquante) / ORANGE (TRS 50–60 % ou anomalies) / ROUGE (TRS < 50 % ou arrêt non documenté)
- TRS du jour ou de la dernière période + flèche direction vs semaine précédente
- Manque à gagner FCFA de la semaine
- Problème n°1 en une ligne (cause principale Pareto ou anomalie bloquante)
- Action n°1 (première priorité décisionnelle, déjà calculée par `_priorites_chef`)

**Données requises** : toutes existantes.
**Effort** : moyen — refactoring de position, aucun nouveau calcul.

### Module 2 — Postes du jour — Existe, améliorer

Si aucune fiche du jour : message « En attente de la première saisie » + TRS du dernier poste connu.

### Module 3 — Pertes D×P×Q + Manque à gagner — Existe, remonter

Repositionner immédiatement sous le cockpit (actuellement profond dans le scroll).

### Module 4 — Machine critique + Pareto top-1 — À créer en résumé cockpit

Deux lignes sur le cockpit :
- « Machine critique : Bicoupe — 3h30 d'arrêts cette semaine »
- « Cause n°1 Pareto : [cause] — Yh = Z FCFA »

Avec lien vers page Causes d'arrêts + bouton « Analyser (Ishikawa) ».

### Module 5 — Boucle Lean visible — Existe, à rendre visible

Une section « Boucle Lean active » sur le cockpit : nombre de problèmes en cours + nombre d'actions en cours + nombre d'actions efficaces ce mois. Arguments OS4/H2 pour le mémoire.

### Modules 6 et 7 — Scorecard + Recommandations — Conserver tels quels

---

## 8. Parcours utilisateur idéal (chef, 9h00)

1. Ouvre le tableau de bord → voit en 3 secondes : **VERT / ORANGE / ROUGE** + TRS + manque à gagner du jour.
2. Si ROUGE → lit le problème n°1 (une ligne) + l'action n°1 (un bouton).
3. Clique « Voir les causes » → Pareto → voit la cause la plus coûteuse en temps et en FCFA.
4. Clique « Analyser » → ouvre Ishikawa → saisit 2-3 causes → remonte les 5 Pourquoi → identifie cause racine → crée ActionChef.
5. Revient en fin de poste → valide les fiches soumises par les opérateurs.
6. En fin de semaine → exporte le rapport Excel mensuel.

Ce parcours est **techniquement possible aujourd'hui** — il manque uniquement le cockpit de premier regard (étape 1) et le bouton « Analyser » depuis le Pareto du cockpit (étape 3→4).

---

## 9. Conservation / suppression / fusion / reconstruction

| Élément | Action | Justification |
|---|---|---|
| Moteur TRS (`trs.py`) | **Conserver** | Calcul correct, données réelles |
| Attribution financière D/P/Q | **Conserver** | Argument clé démo |
| Ishikawa 6M + 5 Pourquoi | **Conserver** | Complet et fonctionnel |
| Actions Chef + bilan efficacité | **Conserver** | Boucle Lean réelle |
| Scorecard semaine | **Conserver** | Outil de supervision concret |
| Simulateur gain FCFA | **Conserver** | Argument académique OS6 |
| Recommandations déterministes + IA | **Conserver** | Différenciateur fort |
| Cockpit "Aujourd'hui" | **Améliorer** | Ajouter verdict global + message si vide |
| Calcul objectif (`_resume_production`) | **Reconstruire** | Bug métier — objectif doit être fixe (× nb jours, pas × nb fiches) |
| Position Manque à gagner | **Améliorer** | Remonter en altitude 1 |
| Position Priorités décisionnelles | **Améliorer** | Première section visible, pas en scroll |
| Machine critique — résumé cockpit | **Créer** | Angle mort critique |
| Pareto top-1 sur cockpit | **Créer** | Lien cockpit → Pareto → Ishikawa |
| Boucle Lean visible (widget) | **Créer** | Argument démo OS4 |
| Alertes chef (`_alertes.html`) | **Intégrer** | Template exist mais non inclus dans dashboard.html |
| Prix visibles par le chef | **Améliorer** | Actuellement admin-only — chef doit voir les prix pour valider le chiffrage |

---

## 10. Priorisation P0 → P3

### P0 — Démo de demain

| # | Recommandation | Fichier | Effort | Risque si non fait |
|---|---|---|---|---|
| P0-1 | **Corriger le bug objectif** : objectif = `12,5 × 2 × nb_jours_periode` (fixe), pas `12,5 × nb_postes_saisis` | `dashboard.py:1590` `_resume_production()` | 2h | 147 % → perte de crédibilité totale |
| P0-2 | **Seed données récentes** : modifier `seed_data.py` pour générer `aujourd'hui − 7 jours` | `seed_data.py` ligne ~25 | 1h | "Aujourd'hui" reste à 0 pendant la démo |
| P0-3 | **Message cockpit si vide** : `{% if fiches_du_jour %}...{% else %}En attente de saisie{% endif %}` | `templates/chef/_aujourdhui.html` | 30 min | Section vide = prototype non fini |
| P0-4 | **Rendre les prix consultables par le chef** en lecture seule sur `/pertes` | `admin.py` ou template `pertes` | 30 min | Chef ne peut pas justifier les FCFA |
| P0-5 | **Vérifier les prix seed** (Ayous 180k, Iroko 420k, Azobé 280k, Movingui 320k FCFA/m³) vs marché réel CUF | `seed_data.py:119-124` | 15 min vérification | L'encadreur connaît les vrais prix |

### P1 — MVP opérationnel (cette semaine)

| # | Recommandation | Effort |
|---|---|---|
| P1-1 | Widget statut global OUI/NON (3 couleurs) en tête du cockpit | Moyen |
| P1-2 | Résumé machine critique + Pareto top-1 sur cockpit avec bouton « Analyser (Ishikawa) » | Moyen |
| P1-3 | Intégrer `_alertes.html` dans `dashboard.html` | Faible |
| P1-4 | Repositionner Manque à gagner avant le TRS global | Faible |
| P1-5 | Widget boucle Lean (X problèmes actifs, Y actions en cours, Z actions efficaces) | Faible |

### P2 — Version avancée (avant soutenance)

| # | Recommandation | Dépendances |
|---|---|---|
| P2-1 | Alerte "Soir décroche" si TRS shift du soir < TRS shift du matin de X pts sur 7j | Données existantes, règle à créer |
| P2-2 | Alerte déclassement par essence sur page Qualité (seuil paramétrable) | Seuil existant, alerte inline à ajouter |
| P2-3 | Projection journalière « À ce rythme, X % de l'objectif atteint » | Volume saisi + nb postes restants |
| P2-4 | Table Machine (capacité actuelle, taux disponibilité calculé depuis arrêts) | Nouvelle table, migration |
| P2-5 | Identifiant opérateur (FK User optionnel sur Equipe) | Refactor modèle |

### P3 — Vision long terme

| # | Recommandation |
|---|---|
| P3-1 | Prédiction maintenance préventive (arrêts récurrents → alertes prévisionnelles) — nécessite ≥ 3 mois de données |
| P3-2 | SQCDL board quotidien (S et L manquent actuellement) |
| P3-3 | Matrice compétences opérateurs (dépend de P2-5) |
| P3-4 | EHS / Andon (hors périmètre mémoire actuel) |

---

## 11. Plan d'action concret — démo de demain

### Étape 1 — Corriger le bug objectif (P0-1 — 2h)

Dans `_resume_production()` (dashboard.py:1590), remplacer le calcul de `objectif` :

```python
# AVANT (bug — objectif shrinks avec nb postes soumis)
objectif = objectif_m3 * len(equipes)

# APRÈS (correct — objectif fixe basé sur la période)
nb_jours_periode = max(1, (date_fin - date_debut).days + 1)
objectif = objectif_m3 * 2 * nb_jours_periode  # 2 postes/jour × jours × 12,5 m³
```

Le même pattern existe dans `_resume_production_par_equipe()` (lignes ~1660–1680) — appliquer la même correction.

Après correction, l'atteinte sur 30 jours (60 postes × 12,5 m³ = 750 m³ attendus) face à une production conforme ~500–600 m³ donnera 65–80 % — cohérent avec H3 (TRS < 60 %).

### Étape 2 — Seed données récentes (P0-2 — 1h)

Dans `seed_data.py`, remplacer la période de génération :

```python
# AVANT
date_debut = date(2026, 4, 1)
date_fin = date(2026, 4, 30)

# APRÈS (7 jours incluant aujourd'hui)
from datetime import date, timedelta
date_fin = date.today()
date_debut = date_fin - timedelta(days=6)
```

Relancer : `cd cuf-pilotage && python seed_data.py`. Cela peuple la section « Aujourd'hui » du cockpit et la scorecard semaine.

### Étape 3 — Message cockpit si vide (P0-3 — 30 min)

Dans `templates/chef/_aujourdhui.html`, entourer le bloc KPI du jour d'une condition :
```jinja
{% if fiches_du_jour %}
  {# contenu actuel des KPI #}
{% else %}
  <div class="wp-card" style="text-align:center; color: var(--wp-muted); padding: 24px;">
    <i class="bi bi-hourglass-split"></i>
    En attente de la première saisie du jour
    — Dernière période analysée : {{ periode_label }}
  </div>
{% endif %}
```

### Étape 4 — Prix consultables par le chef (P0-4 — 30 min)

Dans le template `/pertes`, ajouter un encart discret avec les prix actuels en lecture seule. Ou, option plus propre : dans `admin.py`, déplacer les clés `prix_*` de `PARAMS_ADMIN_ONLY` vers `PARAMS_CHEF` avec `readonly=True` dans le formulaire.

### Étape 5 — Vérification seed vs marché (P0-5 — 15 min)

Confirmer avec l'encadreur ou via une source fiable que les prix seed (Ayous 180k FCFA/m³, Iroko 420k, Azobé 280k, Movingui 320k) sont dans les bons ordres de grandeur pour la filière bois Cameroun 2026. Ajuster dans `Parametre` via `/admin/parametres` si nécessaire — pas besoin de toucher au code.

### Script de vérification post-corrections

```bash
bash .claude/skills/run-cuf-pilotage/smoke.sh
python .claude/skills/run-cuf-pilotage/screenshot.py chef
# Vérifier 05-chef-dashboard.png :
#   — TRS visible avec flèche direction
#   — Objectif affiché < 100 % (cohérent avec H3)
#   — Section "Aujourd'hui" peuplée
```

---

## 12. Questions à poser à l'encadreur pendant la présentation

1. **« Le point de comptage est avant la bicoupe — est-ce que votre pratique CUF valide que volume_entree correspond bien à ce passage fixe ? »** → Confirme la cohérence avec la règle métier terrain.

2. **« Les capacités par essence (Ayous, Azobé, Iroko, Movingui) sont configurables ici [montrer Paramètres] — correspondent-elles à ce que vous observez sur la chaîne 4 ? »** → Si non, correction en 30 secondes pendant la démo : argument OS6 (outil adaptable).

3. **« La catégorie "Organisationnelle" contribue le plus au Pareto dans nos données de test — est-ce cohérent avec ce que vous observez terrain ? »** → Ouvre la discussion H2 (causes organisationnelles vs techniques).

4. **« Pour la boucle Lean [montrer Pareto → Ishikawa → Action → Bilan] : est-ce que ce workflow correspond à comment vous traitez un problème récurrent aujourd'hui ? »** → Valide l'adéquation terrain de OS4.

5. **« Le manque à gagner estimé à X FCFA par semaine — est-ce un ordre de grandeur que vous reconnaissez, ou est-il sur- ou sous-estimé ? »** → Valide (ou corrige) le chiffrage FCFA.

6. **« Quel est votre outil de suivi au quotidien actuellement (tableau blanc, Excel, rien) ? »** → Donne le contexte de comparaison pour OS6 (avant / après) et renforce l'argument adoption terrain.

---

## 13. Vision produit long terme

Le profil Chef de Production couvre aujourd'hui les niveaux 1 et 2 du modèle de maturité ProBeya :
- **Niveau 1 (Réactif)** : saisie, statuts, validation
- **Niveau 2 (Structuré)** : TRS, Pareto, Ishikawa, pertes FCFA

Pour atteindre le **niveau 3 (Optimisé)**, les étapes sont :
1. Cockpit décisionnel 10 secondes (P0/P1 — en cours)
2. Pilotage par opérateur (P2 — nécessite FK opérateur)
3. Pilotage prédictif par machine (P3 — nécessite historique ≥ 3 mois)

Le **niveau 4 (Excellence)** nécessiterait des capteurs machine (IoT) hors scope du mémoire actuel.

---

## 14. Conclusion

> Le profil Chef de Production actuel est-il déjà un véritable outil de pilotage industriel, une base prometteuse à renforcer, ou un tableau de bord à reconstruire en profondeur ?

**C'est une base sérieuse qui nécessite un travail éditorial ciblé, pas une reconstruction.**

Le moteur analytique est réel, complet et calculé sur données terrain : TRS D×P×Q, attribution financière des pertes en FCFA, Pareto, Ishikawa guidé, boucle Lean avec bilan d'efficacité. Ce n'est pas un tableau de bord générique — c'est un outil construit sur les contraintes spécifiques de la chaîne 4 (bicoupe goulot, 4 essences, anti-chevauchement, prix snapshot figés).

Ce qui manque est un **cockpit de premier regard** : un verdict global, le problème n°1 et l'action n°1 visibles sans scroller. Aujourd'hui, 15 sections à poids égal imposent au chef de construire lui-même la synthèse — c'est l'inverse de ce qu'un outil de pilotage doit faire.

Il y a un bug de calcul de l'objectif (P0-1) qui est le seul élément capable de faire perdre confiance instantanément à un professionnel du secteur bois — et qui contredit directement les hypothèses H1/H3 du mémoire.

Avec les corrections P0 (4–5 heures) et les améliorations P1 (1–2 jours), l'outil sera à la hauteur d'une démonstration professionnelle et d'une utilisation terrain réelle.

---

*Fichiers clés P0 : `dashboard.py:1590` (bug objectif) · `_aujourdhui.html` (message vide) · `admin.py` (prix chef) · `seed_data.py:25` (dates récentes)*
*Smoke test de référence : `bash .claude/skills/run-cuf-pilotage/smoke.sh` — 16/16 checks doivent rester verts après chaque modification.*

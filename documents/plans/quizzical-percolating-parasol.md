# P4 — Refonte Ishikawa + Recommandations (plan actif)

> Branche `claude/install-claude-excel-6MGzv` · P3 livré et validé le 2026-06-04
> Feu vert requis avant toute modification de code

---

## CONTEXTE

P3 a restructuré le cockpit en 2 colonnes avec accordéons. P4 s'attaque au cœur analytique de l'outil : la logique de solidité des analyses Ishikawa et le moteur de recommandations. Les deux ont des faiblesses fondamentales identifiées lors de l'audit P0 :

- **Solidité Ishikawa** : `_solidite_analyse()` récompense la quantité, pas la qualité. Trois causes dans la même famille "Machine" suffisent pour atteindre "Solide". Aucun critère de diversité 6M, aucun critère d'ancrage aux données réelles CUF.
- **Recommandations** : les 7 règles génèrent du texte statique identique quel que soit le TRS réel, la machine critique, l'essence problématique. Le champ `contexte` est passé mais jamais utilisé dans le texte des solutions.
- **Couche 2 IA** : `reco_ai.py` appelle Anthropic/Groq/Tavily — viole la règle verrouillée "100 % hors ligne". À supprimer sur accord explicite.
- **Lien Reco → Analyse** : seuls 3 codes (`TRS_CRITIQUE`, `ARRETS_NON_DOCUMENTES`, `DECLASS_EXCESSIF`) ont un bouton "Lancer une analyse". Les 4 autres recommandations n'ont aucun chemin direct vers Ishikawa.

**Périmètre validé par l'utilisateur** : repenser toute la fonctionnalité — logique Ishikawa, logique Recommandations, lien entre les deux. Enrichir Couche 1, abandonner Couche 2 IA.

---

## DESIGN 1 — SYSTÈME GEMBA-SCORE (nouvelle logique Ishikawa)

### Inspiration monde réel

Le Toyota Production System exige que les "5 Pourquoi" atteignent une **cause systémique** (processus/organisation) et non une cause symptomatique ("erreur humaine"). Six Sigma impose des **quality gates** : une analyse ne peut pas progresser si certains critères bloquants ne sont pas satisfaits. La méthode FTA (Fault Tree Analysis, industrie nucléaire) évalue la **complétude des chaînes causales** : un trou dans la chaîne invalide le raisonnement entier.

### Principe adapté à CUF

Un Ishikawa de qualité n'est pas un inventaire de causes possibles. C'est une **démarche de convergence vers une cause racine systémique actionnable**, ancrée dans les données terrain de la chaîne 4. Le GEMBA-SCORE mesure cette convergence sur 4 axes.

### Schéma GEMBA-SCORE

```
╔══════════════════════════════════════════════════════════════════╗
║           SYSTÈME GEMBA-SCORE — 12 points maximum              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  AXE 1 — SPECTRE 6M                                [0–3 pts]    ║
║  ┌──────────────────────────────────────────────────────────┐   ║
║  │  1 famille 6M explorée  →  0 pt  (analyse en silo)       │   ║
║  │  2 familles             →  1 pt  (angle limité)           │   ║
║  │  3–4 familles           →  2 pts (analyse multi-angle)    │   ║
║  │  5–6 familles           →  3 pts (spectre complet)        │   ║
║  └──────────────────────────────────────────────────────────┘   ║
║  ⚠ BLOQUANT : si Axe 1 = 0 → score plafonné à 5/12 max        ║
║    (mono-catégorie = biais de confirmation, Toyota Principle)    ║
║                                                                  ║
║  AXE 2 — PROFONDEUR CHAÎNE                         [0–4 pts]    ║
║  ┌──────────────────────────────────────────────────────────┐   ║
║  │  Max profondeur = 1  →  0 pt  (niveau symptôme)          │   ║
║  │  Max profondeur = 2  →  1 pt  (cause intermédiaire)      │   ║
║  │  Max profondeur = 3  →  2 pts (cause proximale)          │   ║
║  │  Max profondeur = 4  →  3 pts (approche systémique)      │   ║
║  │  Max profondeur = 5  →  4 pts (cause racine TPS-grade)   │   ║
║  └──────────────────────────────────────────────────────────┘   ║
║  Basé sur max(depth) car une seule chaîne complète vaut         ║
║  plus que cinq chaînes superficielles (Ohno, Toyota)            ║
║                                                                  ║
║  AXE 3 — COMPLÉTUDE CHAÎNE                         [0–2 pts]    ║
║  ┌──────────────────────────────────────────────────────────┐   ║
║  │  ≥ 75% des causes ont ≥ 1 pourquoi renseigné  →  2 pts  │   ║
║  │  ≥ 40%                                         →  1 pt   │   ║
║  │  < 40%                                         →  0 pt   │   ║
║  └──────────────────────────────────────────────────────────┘   ║
║  Une cause sans aucun pourquoi = hypothèse non explorée         ║
║                                                                  ║
║  AXE 4 — ANCRAGE DONNÉES CUF                       [0–3 pts]    ║
║  ┌──────────────────────────────────────────────────────────┐   ║
║  │  Origine Pareto / fiche anomalie     → +1 pt             │   ║
║  │  Machine spécifiée dans le problème  → +1 pt             │   ║
║  │  ≥ 1 cause cite essence/machine CUF → +1 pt             │   ║
║  │  (Ayous, Azobé, Iroko, Movingui, Bicoupe, Scie…)        │   ║
║  └──────────────────────────────────────────────────────────┘   ║
║  Innovation : lie l'analyse au terrain, pas aux généralités     ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  NIVEAUX DE MATURITÉ                                            ║
║  ┌────────┬─────────────┬────────────────────────────────────┐  ║
║  │  0–4   │  Ébauche    │ Insuffisant pour toute décision    │  ║
║  │  5–6   │  Interméd.  │ Structure présente, manque ancrage │  ║
║  │  7–8   │  Structuré  │ Bonne rigueur, exploitable         │  ║
║  │  9–10  │  Solide     │ Analyse fiable, prête pour action  │  ║
║  │ 11–12  │  Expert     │ Niveau TPS — cause systémique CUF  │  ║
║  └────────┴─────────────┴────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════╝
```

### Exemple concret — avant vs après

```
AVANT (scoring actuel — résultat trompeur)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Problème : "Arrêts fréquents bicoupe"
→ Cause 1 (Machine) : "Lame usée"             pourquoi 1 rempli
→ Cause 2 (Machine) : "Vibrations moteur"     pourquoi 1 rempli
→ Cause 3 (Machine) : "Roulement défectueux"  pourquoi 1-2 remplis
Score actuel : "Solide" ✓   (3 causes + max depth 2)
Problème réel : mono-catégorie, profondeur 2, aucune donnée terrain.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APRÈS (GEMBA-SCORE — règle bloquante activée)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Axe 1 Spectre 6M     : 1 famille → 0/3 pts ← BLOQUANT
Score total plafonné : 3/12 → Ébauche
Guidage affiché : "Analyse mono-catégorie. Explorez Main d'œuvre
                   et Méthode pour dépasser ce niveau."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MÊME PROBLÈME analysé avec rigueur (GEMBA-SCORE Expert)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Origine : Pareto (cause = "Arrêts mécaniques Bicoupe")
Machine : Bicoupe
Causes :
  Machine      → "Lame Azobé usée avant 2 h"        P1–P5 remplis
  Méthode      → "Pas de check lame début poste"     P1–P3 remplis
  Main d'œuvre → "Opérateur non formé sur Azobé"    P1–P2 remplis
  Milieu       → "Copeaux non évacués"               P1 rempli
Axe 1 : 4 familles → 2/3
Axe 2 : max depth 5 → 4/4
Axe 3 : 4/4 causes avec P1 renseigné → 2/2
Axe 4 : origine Pareto(+1) + machine(+1) + "Azobé"(+1) → 3/3
Total : 11/12 → Expert
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Affichage dans les templates (objet solidite enrichi)

```python
# Objet renvoyé par l'API solidite (enrichi, rétro-compatible)
{
    "label": "Solide",
    "couleur": "success",
    "detail": "9/12",
    "score": 9,
    "score_max": 12,
    "axes": [
        {"nom": "Spectre 6M",        "pts": 2, "max": 3,
         "commentaire": "3 familles explorées"},
        {"nom": "Profondeur chaîne", "pts": 3, "max": 4,
         "commentaire": "Niveau 4 atteint"},
        {"nom": "Complétude",        "pts": 2, "max": 2,
         "commentaire": "100 % des causes avec P1"},
        {"nom": "Ancrage CUF",       "pts": 2, "max": 3,
         "commentaire": "Origine Pareto + machine OK"}
    ],
    "bloquant": None   # ou {"axe": "Spectre 6M", "message": "..."}
}
```

La fonction `majSolidite()` dans `ishikawa.html` et `pourquoi.html` est enrichie pour afficher 4 mini-barres de progression sous le badge principal — mise à jour en temps réel à chaque sauvegarde de cause/pourquoi.

---

## DESIGN 2 — RECOMMANDATIONS COUCHE 1 ENRICHIE

### Enrichissement du dict contexte

```python
# Nouvelles clés ajoutées dans vue_recommandations() / analyse_recommandations()
contexte = {
    # --- Existant ---
    "trs_moyen": 52.3,
    "manque": 2_450_000,
    "nb_postes": 14,
    "pct_r2": 18.5,
    "pct_r3": 12.0,
    # --- Nouveau ---
    "machine_critique": "Bicoupe",          # top-1 Pareto sur la période
    "machine_arrets_h": 8.5,               # durée cumulée en heures
    "essence_declass": "Azobé",            # essence avec plus haut déclassement
    "declass_pct_essence": 38.2,           # son taux de déclassement %
    "objectif_m3": 25.0,                   # objectif journalier configuré
    "production_reelle_moy": 15.6,         # moyenne réelle sur la période
    "gain_potentiel_fcfa": 1_200_000,      # gain si TRS revient à 60 %
}
```

Ces données sont calculées à partir de helpers déjà présents : `_machine_prioritaire_recent()`, `_qualite_par_essence()`, `Parametre.get()`.

### Avant / Après une solution TRS_CRITIQUE

```
AVANT (statique — identique quelles que soient les données)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Solution 1 :
  titre  : "Cartographier les arrêts machine"
  detail : "Identifier les machines les plus impactantes.
            Mettre en place un relevé structuré des durées et causes."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APRÈS (dynamique — données CUF réelles injectées)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Solution 1 :
  titre  : "Analyser les arrêts Bicoupe (8,5 h cumulées)"
  detail : "La Bicoupe concentre l'essentiel des arrêts sur la période.
            Avec un TRS actuel de 52,3 % (objectif 60 %), chaque heure
            d'arrêt non documenté représente ~288 000 FCFA de manque
            à gagner. Action immédiate : lancer une analyse Ishikawa
            sur la cause racine Bicoupe → gain estimé 1 200 000 FCFA/
            semaine si TRS remonte à 60 %."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Priorité dynamique

```python
# AVANT : priorite = 3 (hardcodé dans _REGLES)

# APRÈS : calculée selon l'écart réel au seuil
def _priorite_dynamique(trs_actuel, seuil_critique, seuil_moyen):
    if trs_actuel is None:
        return 2
    if trs_actuel < seuil_critique:     # ex: 45 < 50
        return 3   # haute
    elif trs_actuel < seuil_moyen:      # ex: 55 < 60
        return 2   # moyenne
    return 1       # basse
```

### Correction seuil hardcodé

`SAISIES_INCOHERENTES` utilise `>20.0` hardcodé. Remplacé par `Parametre.get('seuil_saisies_incoherentes', 20.0)` — cohérent avec tous les autres seuils du moteur.

---

## DESIGN 3 — BOUCLE D'AMÉLIORATION TRACÉE

```
RECOMMANDATIONS                        ISHIKAWA
┌─────────────────────────────┐        ┌─────────────────────────────┐
│ TRS Critique (52.3%)        │        │ "Analyse TRS Critique"      │
│ Bicoupe · 8.5h · 1.2M FCFA │        │                             │
│                             │        │ GEMBA-SCORE : 7/12          │
│ [Créer analyse Ishikawa] ───┼───────►│ ████████░░░░                │
│ (tous les codes, pas 3)     │        │ Axe1:2 Axe2:3 Axe3:1 Axe4:1│
│                             │        │ "Issu de : TRS_CRITIQUE"    │
│ Si analyse existante :      │        │                             │
│ [Voir l'analyse #12]        │        │ [Créer action] ─────────┐   │
└─────────────────────────────┘        └─────────────────────────┼───┘
                                                                  │
                                       ACTION CHEF               │
                                       ┌──────────────────────── ▼───┐
                                       │ "Réduire arrêts Bicoupe"    │
                                       │ Issu de : Analyse #12       │
                                       │ → Reco TRS_CRITIQUE         │
                                       │ Bilan d'efficacité à J+7    │
                                       └─────────────────────────────┘
```

**Implémentation** : le bouton "Créer analyse Ishikawa" pré-remplit `origine_type='recommandation'` et `reco_code=reco.code` — déjà supporté par la route `problemes.nouveau` existante (cf. template index.html lignes 130-136 qui le fait déjà pour 3 codes). P4 étend ce mécanisme à tous les codes.

Pour afficher "Voir l'analyse" si une analyse existe, la route `recommandations.index()` injecte un dict `problemes_par_reco` : `{code: probleme_id}` construit par une requête sur `Probleme.query.filter_by(origine_type='recommandation').all()`.

---

## DESIGN 4 — SUPPRESSION COUCHE 2 IA

Fichiers et blocs à supprimer (sous confirmation utilisateur) :

1. `app/services/reco_ai.py` — fichier entier
2. `app/templates/recommandations/index.html` — bloc `wp-reco-ai-zone` (~lignes 141-156) + script AJAX `analyserIA()` (~lignes 164-220)
3. `app/routes/recommandations.py` — route `/ai/<code>` (POST)
4. Import de `reco_ai` dans les fichiers qui l'utilisent

Le bandeau "enrichissement IA" (index.html ligne 53) est remplacé par : "Recommandations calculées sur les données réelles des {{ nb_postes }} postes · TRS actuel {{ trs }}% · 100 % hors ligne."

---

## FICHIERS À MODIFIER

| Fichier | Modification |
|---|---|
| `app/routes/problemes.py` | Réécrire `_solidite_analyse()` (lignes 98-118) avec GEMBA-SCORE · Ajouter helper `_gemba_axes()` |
| `app/services/recommandations.py` | Enrichir contexte dict · Réécrire 7 solutions dynamiques · Ajouter `_priorite_dynamique()` · Corriger seuil hardcodé |
| `app/routes/recommandations.py` | Injecter nouvelles clés contexte · Injecter `problemes_par_reco` · Supprimer route AI |
| `app/templates/problemes/ishikawa.html` | Enrichir `majSolidite()` — afficher 4 mini-barres GEMBA |
| `app/templates/problemes/pourquoi.html` | Même enrichissement `majSolidite()` |
| `app/templates/recommandations/index.html` | Supprimer Couche 2 · Bouton "Créer analyse" sur tous codes · "Voir l'analyse" si existe |
| `app/templates/problemes/rapport.html` | Afficher "Issu de la recommandation [titre]" si `origine_type == 'recommandation'` |
| `app/services/reco_ai.py` | **SUPPRIMER** (accord utilisateur requis) |
| `documents/notes-impact/P58-feat-ishikawa-reco-p4.md` | Note d'impact 9 sections avant commit |

---

## VÉRIFICATION

```bash
cd cuf-pilotage && python seed_data.py
bash .claude/skills/run-cuf-pilotage/smoke.sh       # 16/16 doivent rester verts
python .claude/skills/run-cuf-pilotage/screenshot.py chef
# Contrôler :
# · GEMBA-SCORE avec 4 mini-barres dans ishikawa + pourquoi templates
# · Score "Ébauche" si analyse mono-catégorie (règle bloquante active)
# · Score "Expert" si 4+ familles × depth 5 × données CUF
# · Recommandations citent TRS%, FCFA, machine et essence réels
# · Bouton "Créer analyse Ishikawa" présent sur TOUS les codes
# · Aucun bouton "Analyser avec l'IA" visible
# · Message "100 % hors ligne" à la place du bandeau IA
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

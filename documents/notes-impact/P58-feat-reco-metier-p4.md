# Note d'impact mémoire — P58 : Prescriptions de pilotage métier P4
**Commit :** `feat(P4): prescriptions de pilotage 6 sections — moteur métier hors ligne`
**Date :** 2026-06-07
**Nature :** Refonte du moteur de recommandations — nouvelles colonnes modèle, suppression couche IA, renommage navigation
**Fichiers modifiés :** `app/services/recommandations.py` (réécrit) · `app/routes/recommandations.py` (réécrit) · `app/templates/recommandations/index.html` (réécrit) · `app/models.py` (4 colonnes) · `app/__init__.py` (migrations) · `app/static/css/style.css` (6 classes) · `app/templates/base.html` (labels) · `app/templates/chef/dashboard.html` · `app/templates/pdg/dashboard.html`
**Fichiers supprimés :** `app/services/reco_ai.py` · `test_ia.py`

---

## 1. Ce qui a été implémenté

### Moteur de prescriptions 6 sections (Source A — règles déterministes)

Le fichier `services/recommandations.py` est entièrement réécrit autour du pattern `_GABARITS` : un dict qui associe chaque code de règle à une fonction `_fiche_*(ctx)` produisant une fiche structurée en 6 sections obligatoires.

**6 sections par prescription :**
1. **Signal détecté** — ce que l'outil a mesuré (TRS%, FCFA, heures d'arrêt, % Pareto)
2. **Lecture terrain** — ce que ce signal signifie concrètement dans la scierie CUF
3. **Ce que ça coûte** — manque à gagner en FCFA sur la période sélectionnée
4. **Action concrète** — contre-mesure terrain précise, jamais un conseil générique
5. **Gain attendu** — FCFA récupérables si l'action réussit (formule physique ou estimation bornée)
6. **Vérification** — indicateur avant/après pour confirmer l'effet de l'action

**7 règles réécrites :**
- `ARRETS_NON_DOCUMENTES` — % postes avec arrêts R2 non documentés ; CTA `corriger_fiches` (avertissements)
- `SAISIES_INCOHERENTES` — % postes avec anomalies R1/R4 bloquantes ; CTA `corriger_fiches` (bloquantes)
- `TRS_CRITIQUE` — TRS < seuil critique ; CTA `creer_ishikawa`
- `TRS_MOYEN` — TRS en zone d'alerte (< objectif, > critique) ; CTA `creer_ishikawa`
- `MANQUE_ELEVE` — manque à gagner hebdomadaire > 500 000 FCFA ; CTA `creer_ishikawa`
- `DECLASS_EXCESSIF` — % volume déclassé > seuil paramétrable ; CTA `creer_ishikawa`
- `TENDANCE_NEGATIVE` — dégradation des performances sur la période ; CTA `creer_ishikawa`

**Deux familles de règles clairement séparées :**
- **Problème de données** (ARRETS_NON_DOCUMENTES, SAISIES_INCOHERENTES) : gain non quantifiable en FCFA direct ; section 3 reformulée pour expliquer pourquoi ces anomalies faussent tous les autres indicateurs ; CTA vers correction des fiches.
- **Perte mesurable** (5 autres règles) : gain calculé à partir du manque à gagner réel et d'un taux de réussite borné (min/max %) ; CTA vers Ishikawa ou Décision directe.

**Contexte enrichi injecté par la route :**
La fonction `_contexte_extra(equipes, manque)` dans `routes/recommandations.py` calcule avant d'appeler le service :
- `machine_critique` + `machine_arrets_h` : machine avec le plus de minutes d'arrêt cumulées
- `cause_dominante` + `cause_dominante_pct` + `cause_dominante_fcfa` : top catégorie du Pareto par catégorie
- `essence_declass` + `declass_pct_essence` : essence avec le ratio déclassé/total le plus élevé

Ces clés permettent à chaque `_fiche_*()` de produire un texte ancré sur les données réelles (« la Bicoupe concentre 8h30 d'arrêts ») plutôt qu'un conseil générique.

**Formule du gain potentiel :**
```
gain_potentiel = manque × (trs_objectif - trs_moyen) / (100 - trs_moyen)
```
Cette formule est physiquement correcte : elle représente la fraction du manque à gagner récupérable si le TRS remonte à l'objectif, en tenant compte du fait que le TRS ne peut jamais dépasser 100 %.

### Suppression de la couche 2 IA

`app/services/reco_ai.py` (290 lignes, appels Anthropic/Groq/Tavily) est supprimé. Ce fichier violait la règle verrouillée « 100 % hors ligne ». La route `/ai/<code>` (POST) et tous les imports associés sont retirés de `routes/recommandations.py`. Le bandeau dans le template est remplacé par « 100 % hors ligne ».

### Traçabilité prescriptions → actions

4 colonnes ajoutées au modèle `ActionChef` :
- `prescription_initiale` (Text) : texte complet de l'action prescrite, figé à la création
- `indicateur_suivi` (String 200) : indicateur de vérification (ex. « TRS moyen (%) »)
- `date_verification_prevue` (Date) : date prévue pour mesurer l'effet
- `reco_code` (String 50) : code de la règle déclencheuse (ex. `TRS_CRITIQUE`)

Migrations automatiques via `_ensure_schema()` dans `__init__.py` — aucune intervention manuelle requise.

### Renommage navigation

Dans `base.html` (les deux blocs de navigation) :
- « Actions Chef » → **« Décisions de pilotage »**
- « Recommandations » → **« Prescriptions de pilotage »**

### CSS — grille 6 sections

6 classes ajoutées dans `style.css` :
- `.wp-fiche-6s` : grille 2 colonnes responsive (1 colonne sous 768px)
- `.wp-fiche-section` : carte individuelle avec fond légèrement grisé
- `.wp-fiche-action` : section 4 mise en évidence (fond ivoire, bordure ochre)
- `.wp-fiche-label` / `.wp-fiche-texte` : typographie section

---

## 2. Lien avec les objectifs du mémoire

P4 contribue directement à **OS4** (analyse des causes et décision d'action) et **OS6** (outil de pilotage adapté).

La prescription en 6 sections n'est pas un commentaire d'indicateur — c'est une **fiche de contre-mesure terrain** au sens Lean/DMAIC : signal mesuré → diagnostic → coût actuel → action → gain attendu → vérification. Cette structure est citable dans le mémoire comme implémentation du cycle PDCA au niveau prescription.

Le renommage « Recommandations » → « Prescriptions de pilotage » est intentionnel et défendable : une prescription implique un signal déclencheur mesurable et une action précise vérifiable, pas un conseil général.

---

## 3. Données et calculs mobilisés

- **Manque à gagner** : `manque_a_gagner_agrege(equipes)` — inchangé
- **Pareto par catégorie** : `pareto_arrets(equipes)` — réutilisé pour identifier `cause_dominante`
- **TRS moyen** : agrégation simple sur `equipe.trs_global`
- **Machine critique** : agrégation de `arret.duree_min` par `arret.machine` — identique à `_machine_prioritaire_recent()` dans dashboard.py
- **Paramètres** : `Parametre.get('trs_objectif_pct', 60.0)`, `Parametre.get('seuil_saisies_incoherentes', 20.0)`, etc. — seuils tous paramétrables

Le seuil `SAISIES_INCOHERENTES` était hardcodé à `> 20.0` dans l'ancienne version. Il utilise maintenant `Parametre.get('seuil_saisies_incoherentes', 20.0)`, cohérent avec tous les autres seuils de l'application.

---

## 4. Hypothèses testées ou confirmées

- **H2** (causes organisationnelles et techniques identifiables par les données) : le fait que le moteur puisse identifier la cause dominante du Pareto et construire une prescription ciblée autour d'elle confirme que les données saisies suffisent à orienter le diagnostic.
- **H4** (outil de pilotage adapté) : les 6 sections répondent aux questions concrètes d'un chef de production (qu'est-ce qui se passe / pourquoi / combien ça coûte / que faire / que vais-je récupérer / comment je vérifie). Le format est plus opérationnel qu'une liste de solutions génériques.

**Vérification de contradiction :** aucune contradiction avec H1–H4. La suppression de la couche IA renforce la cohérence avec la contrainte « 100 % hors ligne » qui est une exigence de terrain CUF (pas de connexion internet fiable à l'atelier).

---

## 5. Ce que ce module permet de montrer dans le mémoire

**Dans la section outil de pilotage (OS6) :**
Le passage de `solutions[]` statiques à `_GABARITS` + `_fiche_*(ctx)` est un exemple concret de **personnalisation dynamique sans IA** : les textes s'adaptent aux données réelles (TRS actuel, machine critique, FCFA) sans dépendance réseau. Cela répond à la critique fréquente des tableaux de bord génériques.

**Dans la section DMAIC — phase Improve (OS4) :**
La structure prescription → Ishikawa → ActionChef forme un pipeline DMAIC complet : la prescription identifie le problème (Measure/Analyze), l'Ishikawa en cherche la cause racine (Analyze), l'ActionChef lance l'amélioration (Improve) et la section Vérification prépare le contrôle (Control).

**Argument académique sur la suppression de l'IA :**
Le choix d'un moteur déterministe plutôt qu'un LLM est défendable sur deux critères : la reproductibilité (même données → même prescription → résultat vérifiable) et l'explicabilité (chaque section référence un indicateur mesurable, pas une inférence opaque).

---

## 6. Limites actuelles

- **Source B (bibliothèque de contre-mesures métier)** : le plan P4 prévoyait une bibliothèque de 5 contre-mesures par catégorie d'arrêt (`BIBLIOTHEQUE_CONTRE_MESURES`), avec sélection multicritère. Cette source n'est pas implémentée en P4 — elle est différée en P5. Les 7 règles Source A couvrent déjà les situations les plus courantes.
- **Boucle avant/après sur indicateur** : `_calcul_avant_apres_reco()` + `_indicateur_avant_apres()` (plan P4 section Vérification) sont différés en P5. La section 6 de chaque fiche affiche un texte statique d'indicateur, pas encore un tableau avant/après calculé dynamiquement.
- **Bilan actions en FCFA évité** : `_bilan_efficacite_action_chef()` compare encore les arrêts (pas les FCFA). Différé P5.
- **`reco_code` GET param dans `nouvelle_action_chef()`** : la route reçoit déjà le paramètre mais ne le sauvegarde pas encore dans `ActionChef.reco_code`. À compléter en P5.
- **Score de priorité FCFA × récurrence** : l'ancien `priorite` hardcodé reste en place. Le scoring dynamique (FCFA × facteur récurrence) est différé P5.

---

## 7. Vérification de cohérence avec les notes précédentes

**Par rapport à P14 (note d'impact recommandations initiales) :** P58 remplace entièrement la logique P14. Les `solutions[]` sont conservées comme champ vide `[]` pour compatibilité, mais ne sont plus utilisées dans le rendu principal.

**Par rapport à P14b (Groq moteur gratuit) :** P58 supprime définitivement ce moteur. La décision est cohérente avec P14b qui notait déjà la fragilité de la dépendance réseau.

**Par rapport à P54/P56/P57 (cockpit P1/P2/P3) :** le widget prescription du cockpit chef/PDG (`reco.solutions[0].titre`) a été mis à jour pour utiliser `reco.fiche.action` en priorité. Aucune régression cockpit.

**Aucune contradiction signalée.** Les modèles, routes et templates non touchés restent inchangés.

---

## 8. Références bibliographiques mobilisées implicitement

- **DMAIC (Motorola / Six Sigma)** : la structure en 6 sections (signal → lecture → coût → action → gain → vérification) est une implémentation directe du cycle Measure-Analyze-Improve-Control au niveau d'une prescription individuelle.
- **Hoshin Kanri / A3 Toyota** : la fiche prescription est comparable au format A3 utilisé dans les usines Toyota — problème / situation actuelle / analyse / plan d'action / résultat attendu. La version à 6 sections est une adaptation allégée.
- **Nielsen (1994), heuristique n°6** (Recognition rather than recall) : afficher le signal déclencheur et le coût dans la même fiche évite au chef de devoir naviguer entre plusieurs pages pour reconstituer le contexte.

---

## 9. Prochaines étapes

- **Validation P4 terrain** : vérifier sur Windows que les prescriptions affichent les vraies données des fiches seedées (TRS réel, FCFA réel, machine critique réelle).
- **P5 — Navigation** : refonte du menu (5 entrées, groupe « Diagnostic »), Ishikawa sorti du menu principal.
- **P5 — Source B** : bibliothèque de contre-mesures métier par catégorie d'arrêt Pareto (BIBLIOTHEQUE_CONTRE_MESURES, plan détaillé dans le plan P4 archivé).
- **P5 — Boucle avant/après** : `_calcul_avant_apres_reco()` + tableau indicateur avant/après dans la section Vérification.
- **P5 — Bilan FCFA évité** : enrichir `_bilan_efficacite_action_chef()` avec le calcul FCFA évités.
- **P5 — Score dynamique** : remplacer le `priorite` hardcodé par le score FCFA × facteur récurrence.

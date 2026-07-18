# Note d'impact — P14 : Moteur de recommandations hybride (Couche 1 + IA)
> Commit : (en attente) — feat(p14): moteur de recommandations hybride deterministe + IA
> Date : 2026-05-13
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Ajout d'un moteur de recommandations prioritaires accessible depuis un lien dédié dans la navigation et visible en synthèse (Top 3) au sommet des tableaux de bord chef et PDG.

Le moteur est articulé en deux couches indépendantes. La Couche 1 applique sept règles déterministes sur les données des trente derniers jours : TRS critique (sous 50 %), TRS moyen (entre 50 et 60 %), manque à gagner élevé (au-delà de 500 000 FCFA), arrêts non documentés récurrents (anomalie R2 sur plus de 30 % des postes), déclassé excessif récurrent (anomalie R3 sur plus de 30 % des postes), saisies incohérentes récurrentes (anomalies R1 ou R4 sur plus de 20 % des postes), et tendance baissière hebdomadaire (manque à gagner en hausse de plus de 10 % entre la semaine courante et la précédente). Chaque règle est associée à trois solutions concrètes rédigées à partir de la littérature scientifique mobilisée dans le mémoire. La priorité de chaque règle (Haute, Moyenne, Basse) est calculée à partir de seuils stockés dans la table Parametre et donc ajustables sans modifier le code.

La Couche 2 enrichit chaque recommandation à la demande. Le bouton « Analyser avec l'IA » déclenche une requête POST vers un endpoint Flask dédié. Cet endpoint appelle l'API Claude (modèle Sonnet) en lui fournissant le contexte CUF (TRS mesuré, manque à gagner, essences, machine goulot) et les résultats d'une recherche web via l'API Tavily sur le problème détecté. Claude génère trois solutions supplémentaires avec justification, exemple d'application dans une usine similaire, et référence bibliographique si disponible. Les résultats sont mis en cache JSON dans `instance/reco_cache.json` pendant sept jours pour éviter les appels API répétés à chaque consultation.

La Couche 2 intègre également un mécanisme de sources externes : l'administrateur peut renseigner dans la table Parametre (clé `reco_sources_externes`) une liste JSON d'URLs — articles scientifiques, rapports FAO, étude de cas — que l'IA charge et intègre à son contexte. Cela permet d'orienter les recommandations vers la bibliographie spécifique du mémoire (Karsenty 2021, Laine 2024, etc.) plutôt que vers des sources génériques.

---

## 2. Fichiers modifiés ou créés

| Fichier | Type | Action |
|---|---|---|
| `cuf-pilotage/app/services/recommandations.py` | Service | **Nouveau** — 7 règles + `analyse_recommandations()` + `top_n_recommandations()` |
| `cuf-pilotage/app/services/reco_ai.py` | Service | **Nouveau** — Claude API + Tavily + cache JSON 7 jours |
| `cuf-pilotage/app/routes/recommandations.py` | Route | **Nouveau** — blueprint `/recommandations/` + `POST /recommandations/ai/<code>` |
| `cuf-pilotage/app/templates/recommandations/index.html` | Template | **Nouveau** — page dédiée (liste + boutons IA + panneaux résultats) |
| `cuf-pilotage/app/__init__.py` | Factory | Import + enregistrement du blueprint + seed 5 nouveaux Parametre |
| `cuf-pilotage/app/routes/dashboard.py` | Route | Import + injection `top_recos` (chef) et `top_recos_pdg` (PDG) |
| `cuf-pilotage/app/templates/chef/dashboard.html` | Template | Section Top 3 recommandations avant le scorecard semaine |
| `cuf-pilotage/app/templates/pdg/dashboard.html` | Template | Section Top 3 recommandations entre la vue exécutive et les KPI |
| `cuf-pilotage/app/templates/base.html` | Template | Lien nav « Recommandations » (desktop + mobile) |
| `cuf-pilotage/app/static/css/style.css` | CSS | 15 nouvelles classes `.wp-reco-*` et `.wp-ai-*` |
| `cuf-pilotage/requirements.txt` | Dépendances | `anthropic>=0.30.0` + `tavily-python>=0.3.0` |
| `cuf-pilotage/start.ps1` | Script | Chargement `.env` + instructions clés API |
| `documents/notes-impact/P14-recommandations.md` | Documentation | Nouveau |

Aucune migration de base de données. Cinq lignes ajoutées à la table Parametre via un seed idempotent. R7 respectée.

---

## 3. Objectif spécifique du mémoire servi

**OS5 — Proposer des actions correctives prioritaires et estimer les gains de production et les bénéfices financiers attendus** : le moteur de recommandations P14 est la concrétisation directe de cet objectif. Sans système de recommandations, les indicateurs mesurés (TRS, manque à gagner, anomalies) restent des constats sans orientation décisionnelle. Avec P14, chaque dérive est accompagnée de trois solutions immédiatement actionnables, fondées sur la littérature scientifique et adaptées au contexte CUF. La Couche 2 étend cela à la littérature industrielle mondiale disponible en ligne.

**OS6 — Concevoir un outil de pilotage adapté aux besoins des différents responsables** : le filtre par rôle (chef = règles opérationnelles, PDG = règles stratégiques) est la signature d'un tableau de bord exécutif efficace selon Kankkunen & Holopainen (2024). Le chef de production voit les règles TRS et anomalies de saisie ; le PDG voit les règles financières (manque à gagner) et de tendance.

---

## 4. Lien avec les hypothèses de recherche

**H4 — Des actions correctives sans investissement majeur permettent d'améliorer le TRS et de réduire les pertes financières** : P14 est l'instrument de validation de H4. Chaque recommandation est conçue pour être actionnée sans investissement matériel. La présence du delta (P13) permet de mesurer l'impact de chaque action dès la semaine suivante. Sans recommandations, H4 reste une hypothèse ; avec P14, elle devient testable sur le terrain.

**H3 — Le TRS réel est inférieur à 60 %** : les règles TRS_CRITIQUE et TRS_MOYEN se déclenchent précisément sous les seuils 50 % et 60 %, confirmant ou infirmant H3 pour chaque période. Si TRS_MOYEN n'est jamais déclenchée et TRS_CRITIQUE l'est systématiquement, H3 est non seulement confirmée mais sa sous-estimation est démontrée.

**H1 et H2 ne sont pas directement concernées** par cette modification.

---

## 5. Technique utilisée et choix architectural

**Couche 1 — règles déterministes** : les sept règles sont définies comme une liste de dicts dans `_REGLES`. La fonction `analyse_recommandations()` calcule les métriques agrégées (TRS moyen, manque à gagner, pourcentage de postes avec anomalie par code), compare chaque valeur au seuil correspondant depuis `Parametre`, et construit la liste des règles actives triées par priorité décroissante. Cette architecture permet d'ajouter une huitième règle en ajoutant un dict à `_REGLES` et un bloc de condition dans `analyse_recommandations()`, sans toucher à la logique existante.

**Couche 2 — enrichissement IA** : la fonction `ai_enrichissement()` dans `reco_ai.py` suit le pipeline suivant : vérification cache → recherche Tavily → chargement sources externes → construction du prompt Claude → appel API → extraction JSON → mise en cache. Chaque étape est isolée dans une fonction privée, ce qui rend le code testable et maintenable. Le modèle utilisé est `claude-sonnet-4-6`, qui offre le meilleur rapport qualité/coût pour ce cas d'usage (génération de texte structuré à partir de sources documentaires).

**Cache JSON** : les résultats IA sont stockés dans `instance/reco_cache.json`, un fichier persistant entre redémarrages, sans nouvelle table DB. Le TTL de 7 jours est un compromis entre fraîcheur (les sources web évoluent) et économie d'appels API (Claude Sonnet coûte environ 0,02 € par appel type). Le bouton « Rafraîchir » permet de forcer un recalcul immédiat avec le paramètre `?force=1`.

**Séparation Couche 1 / Couche 2** : les deux couches sont dans des fichiers séparés (`recommandations.py` et `reco_ai.py`). `recommandations.py` ne dépend pas des API externes — il fonctionne sans connexion internet. `reco_ai.py` dépend d'`anthropic` et de `tavily-python`, mais leur absence est gérée gracieusement : si le module n'est pas installé, la fonction retourne un message d'erreur lisible au lieu de lever une exception.

**Filtre par rôle** : chaque règle porte un champ `roles` (liste de strings). La fonction `top_n_recommandations()` filtre les règles actives par le rôle de l'utilisateur connecté. Le chef de production voit les règles TRS et anomalies opérationnelles ; le PDG voit les règles financières et de tendance. Un administrateur voit toutes les règles actives.

---

## 6. Contrainte respectée

**Règle R7** : aucune modification de schéma de base de données. Cinq lignes sont ajoutées à la table `Parametre` existante via un seed idempotent. Le cache IA est stocké dans un fichier JSON dans `instance/`, pas dans la DB.

**Règle R6** : validation explicite obtenue avant écriture du code. L'utilisateur a confirmé les choix clés (déclenchement par bouton, accès internet disponible, cache JSON persistant, filtrage par rôle, sources externes chargées par l'IA) au cours de quatre rounds de questions.

---

## 7. Limites identifiées

Les recommandations déterministes sont rédigées à partir de la littérature du mémoire et d'une connaissance générale des scieries camerounaises. Elles ne sont pas encore validées par des observations terrain CUF. Le seuil de 30 % pour les anomalies R2/R3 devra être recalibré après les premières semaines de collecte réelle.

L'enrichissement IA (Couche 2) produit des résultats non reproductibles : deux appels consécutifs au même problème génèrent des solutions différentes. Le cache atténue ce comportement (TTL 7 jours), mais le jury de soutenance doit comprendre que les solutions IA sont des suggestions, pas des prescriptions. Pour la soutenance, les recommandations déterministes de la Couche 1 constituent la réponse académique principale à OS5 ; la Couche 2 est présentée comme une extension prototypique.

Les sources externes (`reco_sources_externes`) ne disposent pas encore d'interface graphique de gestion. Elles sont configurées directement dans la table `Parametre`. Une page d'administration dédiée pourrait être ajoutée dans une phase ultérieure.

---

## 8. Commandes Windows pour appliquer

```powershell
git pull origin claude/install-claude-excel-6MGzv
.\start.ps1
```

Pour activer le module IA avant le démarrage, créer un fichier `.env` dans `cuf-pilotage/` :
```
ANTHROPIC_API_KEY=sk-ant-xxxxx
TAVILY_API_KEY=tvly-xxxxx
```

`start.ps1` charge automatiquement ce fichier. Sans ce fichier, l'application fonctionne normalement et affiche un message explicite si l'on tente d'utiliser le bouton « Analyser avec l'IA ».

Pour vérifier le résultat :
- Se connecter avec `chef@cuf.cm` / `cuf2026` → le tableau de bord chef affiche le Top 3 recommandations.
- Se connecter avec `pdg@cuf.cm` / `cuf2026` → la section Recommandations apparaît entre la vue exécutive et les KPI.
- Cliquer sur « Recommandations » dans le menu → page dédiée avec toutes les règles actives.
- Cliquer sur « Analyser avec l'IA » → si ANTHROPIC_API_KEY est configurée, trois solutions IA apparaissent dans un panneau dépliable.

---

## 9. Références bibliographiques mobilisées

- **Kankkunen & Holopainen (2024)** — *Daily management, UPM Plywood* : les recommandations doivent être filtrées par niveau hiérarchique. Le chef de production a besoin de recommandations opérationnelles (réglages, maintenance, formation) ; le PDG a besoin de recommandations stratégiques (priorisation des essences, investissement dans la maintenance préventive). Afficher toutes les règles à tous les niveaux noierait le signal dans le bruit.

- **Laine (2024)** — *Reporting visuel, Metsä Board* : le management visuel terrain (affiche en cabine, rappel au point de décision) est plus efficace que la formation seule. Plusieurs solutions déterministes s'appuient directement sur ce principe (affiche rappel arrêts, fiche réglage par essence en cabine bicoupe).

- **Mncwango & Mdunge (2025)** — *DMAIC pour OEE bas, Afrique du Sud* : la maintenance préventive réduit les pannes imprévues de 40 à 60 %. Cette valeur est citée dans la solution déterministe de la règle TRS_CRITIQUE.

- **Danwé, Bindzi & Meva'a (2012)** — *Scieries camerounaises* : une lame émoussée augmente le taux de déclassé de 15 à 25 %. Cité dans les solutions des règles DECLASS_EXCESSIF et MANQUE_ELEVE.

- **Jaouane (2022)** — *Tableau de bord, Général Emballage, Algérie* : la rapidité de réaction aux dérives est améliorée par la lisibilité immédiate des recommandations associées aux indicateurs. Le Top 3 intégré dans chaque tableau de bord répond à ce principe.

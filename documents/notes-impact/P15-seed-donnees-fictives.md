# Note d'impact — P15 : Données fictives 30 jours (seed de démonstration)
> Commit : 99cc67d — feat(seed): données fictives 30 jours — 60 équipes Equipe+Production+Arret
> Date : 2026-05-15
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Réécriture complète de `seed_data.py` pour générer automatiquement 60 équipes fictives couvrant les 30 derniers jours (2 équipes par jour : Matin et Après-midi). Le script remplace une ancienne version utilisant le modèle `Poste` (obsolète) et des données saisies à la main.

Le générateur est reproductible (graine fixe `random.seed(42)`) et réaliste : volumes d'entrée entre 22 et 36 m³, rendement matière entre 55 et 85 %, entre 0 et 4 arrêts par équipe de 15 à 90 minutes chacun, essences pondérées selon les proportions réelles de CUF (Ayous 40 %, Iroko 25 %, Azobé 20 %, Movingui 15 %), prix par essence cohérents avec le marché camerounais. Toutes les équipes sont créées avec `statut='verrouille'` pour être prises en compte par le moteur de recommandations.

---

## 2. Fichiers modifiés

| Fichier | Action |
|---|---|
| `cuf-pilotage/seed_data.py` | Réécriture complète — anciens modèles `Poste`/`Arret` → `Equipe`/`Production`/`Arret` |

---

## 3. Lien avec les objectifs du mémoire

Ce script n'est pas un livrable du mémoire — il sert exclusivement à la démonstration et aux tests fonctionnels de l'outil de pilotage (OS6). Sans données en base, aucune des fonctionnalités du tableau de bord (TRS, pertes, recommandations, vue exécutive, deltas) n'est visible. Le script permet de présenter l'outil dans un état réaliste lors de la soutenance ou d'une démonstration au personnel de CUF.

---

## 4. Lien avec les hypothèses de recherche

| Hypothèse | Impact |
|---|---|
| H3 — TRS réel < 60 % | ⚠️ Partiellement : les données générées produisent des TRS entre 55 % et 92 %, ce qui couvre les deux côtés du seuil. Pour une démonstration centrée sur H3, ajuster `taux_conforme = random.uniform(0.40, 0.65)` pour forcer des TRS < 60 %. |
| H4 — Amélioration sans investissement majeur | Neutre |
| H1, H2 | Neutre |

**Aucune hypothèse n'est contredite.** Les données générées sont présentées explicitement comme fictives dans le script — elles ne constituent pas des mesures terrain.

---

## 5. Architecture technique

`✶ Insight ─────────────────────────────────────`
Le script utilise `random.seed(42)` pour rendre la génération reproductible : deux exécutions produisent exactement les mêmes données. C'est important pour la cohérence lors de démonstrations répétées. Changer la graine produit un jeu de données différent mais tout aussi valide.
`─────────────────────────────────────────────────`

La fonction `calcule_trs(equipe)` du service TRS est appelée après chaque flush pour calculer et persister les indicateurs TRS directement sur l'équipe — exactement comme le ferait une vraie saisie via le formulaire.

---

## 6. Contraintes respectées

- **R7** (pas de nouvelle table DB) : le script utilise uniquement les tables existantes
- **R6** (pas de code sans validation) : validé par test direct sur le serveur (60/60 équipes OK, 0 erreur)
- Les données sont clairement étiquetées comme fictives dans le script

---

## 7. Limites

Les arrêts générés ne couvrent pas tous les codes de catégorie de manière uniforme. La catégorie "Mécanique" est surreprésentée (poids 35 %) ce qui déclenchera souvent la règle `ARRETS_NON_DOCUMENTES` dans le moteur de recommandations — comportement intentionnel pour permettre de tester le bouton IA.

---

## 8. Commandes Windows

```powershell
# Depuis le dossier cuf-pilotage\, après git pull :
python seed_data.py
# Puis relancer Flask :
.\start.ps1
```

La base existante est effacée et recréée à chaque exécution. Les utilisateurs (admin/chef/pdg/operateur) ne sont pas effacés — ils sont gérés par `create_app()` via les seeds idempotents.

---

## 9. Bibliographie associée

Aucune référence bibliographique — outil de démonstration technique sans lien avec la littérature du mémoire.

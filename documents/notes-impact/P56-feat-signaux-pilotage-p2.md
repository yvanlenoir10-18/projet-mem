# Note d'impact mémoire — P56 : Signaux de pilotage P2
**Commit :** à venir — `feat(chef): 4 signaux de pilotage P2 — projection, soir, déclassement, disponibilité`
**Date :** 2026-06-04
**Nature :** Amélioration UI cockpit Chef — **aucun changement de modèle de données, aucune migration**
**Fichiers modifiés :** `app/routes/dashboard.py` · `app/templates/chef/_aujourdhui.html` · `app/templates/chef/dashboard.html` · `app/templates/chef/_signaux_p2.html` (nouveau)

---

## 1. Ce qui a été implémenté

Quatre signaux de pilotage ajoutés au cockpit Chef, tous construits sur des données existantes (règle R7 : aucune nouvelle table).

**P2-A — Projection fin de poste enrichie**
- `_projection_production_active()` enrichi : calcul de `ecart_objectif` (m³ manquants) et `rattrapage_min` (minutes à cadence normale pour rattraper l'écart). La cadence utilise le paramètre `capacite_equipe_h` (vivant, défaut 1,5625 m³/h).
- Affiché dans `_aujourdhui.html` sous forme d'encart coloré : « À ce rythme → fin poste ~X m³ · il manque Y m³ (~Z min) ». Visible uniquement si un poste est actif (signal temps réel).

**P2-B — Alerte équipe du soir décroche**
- Nouveau helper `_alerte_soir_decroche(aujourd_hui, jours=3, seuil_pts=15)` : un seul critère, TRS Après-midi < TRS Matin − 15 points sur 3 jours qualifiants consécutifs.
- La constante terrain : le poste `Apres-midi` (14h–23h) est le « soir » du vocabulaire CUF. Le helper cible `Apres-midi`, affiché comme « équipe du soir ».
- Rendu dans le nouveau partial `_signaux_p2.html`.

**P2-C — Alerte déclassement par essence**
- Nouveau helper `_alerte_declassement_essence(equipes)` : réutilise `_qualite_par_essence()` existant, filtre les essences dépassant `seuil_declass_pct` (défaut 30 %, paramétrable), trie par dépassement décroissant.
- Rendu dans `_signaux_p2.html` avec lien vers `/chef/qualite`.

**P2-D — Taux de disponibilité machine sur le cockpit**
- `_machine_prioritaire_recent()` enrichi : somme `duree_impact_min` des arrêts, calcule `disponibilite_pct = (1 − impact / (nb_postes × duree_poste)) × 100`. Code couleur : vert ≥ 90 %, ochre ≥ 75 %, terracotta < 75 %.
- Affiché dans la carte « Signaux critiques » existante (dashboard.html) sous le nom de la machine.

**Architecture retenue** : ajout additif sur le cockpit P1. Les alertes P2-B et P2-C sont conditionnelles — le bloc `_signaux_p2.html` n'affiche rien si aucune condition n'est remplie. Le rebuild visuel complet en 2 colonnes est différé en P3 pour ne pas risquer de régressions sur le cockpit P1 validé.

---

## 2. Lien avec les objectifs du mémoire

Contribue directement à **OS6** (outil de pilotage adapté) et **OS1** (mesure TRS / écart objectif).

- La projection fin de poste (P2-A) répond à la question : « À ce rythme, vais-je atteindre l'objectif aujourd'hui ? » — décision d'action immédiate opérationnelle.
- L'alerte soir décroche (P2-B) permet de détecter des écarts de performance inter-équipes, argument terrain pour H2 (causes organisationnelles) et H3 (TRS < 60 %).
- L'alerte déclassement (P2-C) lie la qualité matière aux pertes FCFA, argument pour H1 (pertes économiques quantifiables).
- Le taux de disponibilité machine (P2-D) est un indicateur direct du composant D du TRS — OS1.

---

## 3. Données et calculs mobilisés

- **Projection (P2-A)** : `volume_conforme` des fiches brouillon/à_vérifier du poste actif × `(480 / minutes_écoulées)`. Paramètre `capacite_equipe_h` pour le rattrapage.
- **Soir décroche (P2-B)** : TRS moyen par poste par jour sur `STATUTS_ANALYSES`. Seuil fixe 15 pts, fenêtre 3 jours.
- **Déclassement (P2-C)** : `volume_declass / (volume_conforme + volume_declass)` par essence, seuil `seuil_declass_pct`.
- **Disponibilité (P2-D)** : `1 − Σ(duree_impact_min) / (nb_postes × duree_poste)`.

Aucune donnée métier nouvelle — tout vient des tables `Equipe`, `Production`, `Arret` existantes.

---

## 4. Hypothèses testées ou confirmées

- **H1** (pertes économiques mesurables) : P2-C alerte sur le déclassement matière qui alimente directement `calcule_manque_gagner()`. Cohérence renforcée.
- **H2** (causes organisationnelles) : P2-B peut détecter un problème d'encadrement de l'équipe du soir. Contribution indirecte.
- **H3** (TRS < 60 %) : P2-A et P2-D fournissent des données en temps réel cohérentes avec H3. Pas de contradiction.
- **H4** (outil de pilotage adapté) : P2 est une démonstration directe — les signaux alertent sur des situations réelles et actionnables.

**Aucune contradiction signalée.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

P2 est citable dans la section **conception et validation de l'outil** (OS6). Il démontre :
- La capacité de l'outil à produire des signaux d'alerte contextuels (pas d'alerte permanente, alerte déclenchée par une condition métier réelle).
- La réutilisation de calculs existants (aucune redondance de code) — bonne pratique d'ingénierie logicielle.
- La traçabilité décision → action : l'alerte soir décroche pointe vers le scorecard, l'alerte déclassement pointe vers la page Qualité.

Si le mémoire inclut une démonstration avec un encadreur expert scierie, les 4 signaux P2 peuvent être testés en conditions réelles dès la première semaine de saisie terrain.

---

## 6. Limites actuelles

- **P2-A (projection)** : ne s'affiche que si des fiches sont saisies pendant le poste actif (`STATUT_BROUILLON` ou `STATUT_A_VERIFIER`). Pas de projection si aucune saisie en cours.
- **P2-B (soir décroche)** : nécessite au moins 3 jours avec les deux postes dans `STATUTS_ANALYSES`. Avec des données seed peu nombreuses, l'alerte ne se déclenche peut-être pas.
- **P2-D (disponibilité)** : basé sur `duree_impact_min` qui est calculé par le modèle Arret. Si des arrêts n'ont pas de durée d'impact renseignée, la disponibilité est sur-estimée.
- **Rebuild visuel 2 colonnes** : différé P3. La page reste un scroll continu de 15 sections (amélioré vs P0 par le cockpit P1, mais pas encore restructurée en 2 colonnes).

---

## 7. Vérification de cohérence avec les notes précédentes

P2 est additif par rapport à P0 et P1. Aucune modification des calculs TRS, des modèles de données, des routes existantes ni des templates non-chef.

`_machine_prioritaire_recent()` modifié : la signature est inchangée, le dict renvoyé est augmenté d'un champ `disponibilite_pct`. Tous les templates existants qui l'affichent (`dashboard.html` uniquement) restent compatibles — le champ `disponibilite_pct` est rendu avec `{% if ... is not none %}`.

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

- TRS = D × P × Q : Nakajima (1988), repris par Muchiri & Pintelon (2008). P2-D (disponibilité) est le composant D du TRS.
- Détection d'anomalies par seuil : principe de contrôle statistique de processus (SPC), base des cartes de contrôle (Shewhart). Le seuil de 15 pts sur 3 jours est un critère opérationnel simplifié adapté au contexte CUF.

---

## 9. Prochaines étapes

- **Validation P2 sur Windows** : `git pull` puis vérifier les 4 signaux sur le profil Chef.
- **Ajustement seuil alerte soir** : 15 pts est une valeur de démarrage. À recalibrer après 2–3 semaines de données terrain réelles.
- **P3 — Rebuild visuel 2 colonnes** : refonte éditoriale de `dashboard.html` (bandeau altitude 1 fixe, 2 colonnes, ateliers cliquables). Sur demande, après validation P2 terrain.

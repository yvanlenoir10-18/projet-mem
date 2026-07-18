# Note d'impact mémoire — Import des données terrain réelles (bicoupe, mai–juin 2026)

> Branche `claude/install-claude-excel-6MGzv` · Session 2026-07-10 · Commit `31b04db`
> Source : `documents/collecte/Suivi_bicoupe_CUF_mai-juin-2026.xlsx`
> Outil : `documents/outils/import_donnees_reelles.py` · Aucun code applicatif modifié.

---

## 1. Ce qui a été implémenté

Remplacement des données simulées (seed de démonstration, 60 fiches) par les **relevés
terrain réels** de la bicoupe de la chaîne 4, consignés par le chef dans un classeur Excel
de 10 feuilles. L'import charge **95 quarts** (date + créneau) couvrant du **5 mai au 10 juin
2026** (34 jours), soit 167 lignes de production et 176 arrêts.

Deux livrables versionnés :
- `documents/collecte/Suivi_bicoupe_CUF_mai-juin-2026.xlsx` — données brutes ;
- `documents/outils/import_donnees_reelles.py` — outil d'import **idempotent** (purge +
  recharge), hypothèses documentées en tête de fichier, rejouable via `CUF_XLSX=…`.

Aucune ligne de code applicatif n'a été touchée : seules des données ont été chargées et deux
artefacts (outil + données) ajoutés. La base SQLite étant hors-Git, l'import se rejoue depuis
le fichier Excel versionné après tout nouveau conteneur.

## 2. Lien avec les objectifs du mémoire

- **OS1 (capacité théorique → production réelle → écart + TRS)** : l'import fournit enfin un
  TRS **mesuré sur données réelles** (63,3 % moyen bicoupe) à confronter à la capacité
  théorique (12,5 m³/poste) et à l'objectif affiché (25 m³/jour). L'écart production réelle /
  objectif s'établit à **88,4 % d'atteinte** sur les jours produits.
- **Fil DMAIC — étape Measure** : le passage de la seed aux relevés réels matérialise la phase
  « Mesurer » du DMAIC. Les figures du mémoire (cockpit, Pareto, qualité, direction) ne sont
  plus illustratives mais **fondées sur la mesure terrain**.
- **Hypothèse H3** (TRS réel < 60 %) : directement interpelée — voir §4 et §7.

## 3. Données et calculs mobilisés

Le fichier consigne le **TRS mesuré** mais **pas les volumes en m³** (production en
billons/colis). L'import reconstruit les entrées du modèle app par **inversion des formules
de `app/services/trs.py`**, en s'ancrant sur les colonnes **D/P/Q publiées** (propres, toutes
dans [0 %, 100 %]) plutôt que sur les colonnes brutes (Marche, minutes) qui contiennent des
incohérences de saisie manuelle (Marche > 480 min, retard relève = 979 min, un poste à
l'arrêt total).

| Composante | Formule `trs.py` | Inversion appliquée |
|---|---|---|
| Disponibilité D | `(480 − arrêts) / 480` | arrêts recréés pour sommer à `480 − D×480` |
| Performance P | `volume_sorti / (capacité × h_utiles)` | `volume_sorti = P × capacité × h_utiles` |
| Qualité Q | `volume_conforme / volume_sorti` | `volume_conforme = Q × volume_sorti` |

Le temps d'arrêt total est réparti sur les causes réelles (changement de lame, panne, retard
relève) au prorata des minutes itemisées ; les libellés de panne bicoupe sont enrichis depuis
la feuille 9 (« panne électrique », « problème de griffe »…).

**Contrôle de fidélité** : TRS reconstruit vs TRS du fichier → **écart moyen 0,17 pt**, écart
max 0,8 pt (arrondis). TRS moyen reconstruit = TRS moyen fichier = **63,3 %**.

## 4. Hypothèses testées ou confirmées

Quatre choix de modélisation sont **assumés et visibles** (règle « jamais inventer sans le
signaler ») :

- **H-a. Capacité = 1,5625 m³/h** (paramètre app) — fixe l'échelle absolue des volumes.
- **H-b. Rendement matière par essence** (Ayous 68 % → Azobé 52 %, selon densité), calibré
  autour du benchmark Cameroun 60 %. **Hypothèse de modélisation, non mesurée par CUF**
  (le fichier n'a pas les m³ d'entrée). **Sans effet sur le TRS** — seulement sur rendement
  matière / déchets.
- **H-c. Trois créneaux réels** (Matin / Après-midi / **Nuit**) : les relevés révèlent que la
  chaîne 4 tourne en **3×8**, ce que l'objectif affiché « 25 m³/jour = 2 postes » n'intègre pas.
- **H-d. Essences hors des 4 configurées** (Bilinga, DABEMA, MOABI, FRAKE, SAPELLI, LIMBALI)
  regroupées sous « Autre » (prix = moyenne des 4).

**Confirmation méthodologique** : le moteur TRS de l'app reproduit fidèlement (0,17 pt) le TRS
calculé indépendamment par le chef — validation croisée de `trs.py`.

## 5. Ce que ce module permet de montrer dans le mémoire

- **5 figures régénérées** sur données réelles (profil Chef de Production `prod@cuf.cm` pour
  les figures 15-18 ; direction `pdg@cuf.cm` pour la 19) :
  cockpit (verdict + TRS 63,3 %), production/objectif (88,4 %), Pareto des arrêts,
  qualité/matière par essence, tableau de bord direction.
- **Pareto** : le **changement de lame** domine le temps perdu (**53,4 %**, catégorie
  Réglage/outil), devant la panne machine bicoupe (28,4 %) et le retard de relève (8,3 %).
  Résultat cohérent avec la règle métier verrouillée (lames : préventif toutes les 2 h +
  changement essence tendre↔dure).
- **Manque à gagner estimé ~238,7 M FCFA** (valeur potentielle − réelle valorisée), argument
  économique chiffré pour la direction.
- **Dispersion du TRS** (0 % → 98 % selon les quarts) : l'irrégularité, et non le niveau
  moyen, est le vrai levier de pilotage — angle fort pour la discussion.

## 6. Limites actuelles

- **Volumes m³ reconstruits, non mesurés** : le fichier ne consigne pas les m³. Les volumes
  dérivent des taux P/Q mesurés × capacité paramétrée ; le rendement matière par essence
  (H-b) est une hypothèse de densité, pas une mesure CUF. À présenter comme tel.
- **Attribution des essences approximative** : la feuille 8 (essences par équipe A/B/C) ne se
  raccorde pas parfaitement aux créneaux de la feuille 5 ; l'attribution est pondérée par date.
- **Modèle 2 postes vs réalité 3 postes** : l'objectif de l'app (25 m³/jour = 2 postes) ne
  reflète pas le poste de nuit. L'atteinte 88,4 % compare 3 postes réels à un objectif 2 postes.
- **Période fixe (mai-juin)** : « aujourd'hui » (juillet) est postérieur aux données ; les
  widgets temps réel (cockpit du jour) s'affichent en mode « en attente de saisie ».

## 7. Vérification de cohérence avec les notes précédentes

- **Contradiction signalée avec H3** : l'hypothèse H3 pose « TRS réel < 60 % en l'absence de
  système de mesure ». Or le TRS bicoupe réel moyen mesuré est **63,3 %**, donc **au-dessus**
  du seuil et du benchmark 60 %. Cette contradiction est **explicitement à traiter** dans le
  mémoire, pas à masquer. Nuances défendables : (a) mesure **bicoupe seule**, pas la chaîne
  entière ; (b) période où le chef **tenait déjà un relevé manuel** (donc pas « absence de
  système de mesure ») ; (c) la **dispersion** (0 %→98 %) traduit bien un pilotage non maîtrisé.
  H3 reste pertinente reformulée autour de la **régularité** plutôt que du niveau moyen.
- **Cohérent avec la décision 2026-06-10** (base purgée du fictif, ne pas relancer
  `seed_data.py`) : l'import remplace définitivement la seed par du réel.
- **Cohérent avec la règle métier verrouillée** : ordre machines, 4 essences configurées,
  point de comptage bicoupe, standard lames — tous respectés (extras regroupés en « Autre »).

## 8. Références bibliographiques mobilisées implicitement

- **Nakajima (1988)** — TPM et définition du TRS/OEE en trois facteurs Disponibilité ×
  Performance × Qualité, socle de la reconstruction par inversion.
- **Jonsson & Lesshammar (1999)** — mesure de la performance manufacturière et limites du OEE
  isolé, pertinent pour le passage « mesure du niveau » → « mesure de la dispersion ».
- **Benchmarks filière bois** (rappelés dans CLAUDE.md) : Cameroun 60 % cible, pertes scieries
  30–36 %, Afrique centrale ~35 % — cadres de comparaison du rendement matière 62 %.

## 9. Prochaines étapes

- **Discuter la contradiction H3** dans la rédaction (reformuler autour de la régularité).
- **Saisie complémentaire opérateur** possible en plus de l'import (fiches réelles au fil de
  l'eau via `saisie@cuf.cm`).
- **P5-A — Diagnostic mixte / cockpit aiguilleur** : plan actif
  (`documents/plans/quizzical-percolating-parasol.md`), en attente du feu vert utilisateur ;
  les données réelles fourniront désormais un terrain de test authentique.
- **Aligner l'objectif sur 3 postes** (option) si la direction valide le fonctionnement 3×8,
  pour rendre l'atteinte comparable poste à poste.

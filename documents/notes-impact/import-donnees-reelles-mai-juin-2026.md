# Note d'impact — Import des données terrain réelles (mai–juin 2026)

> Branche `claude/install-claude-excel-6MGzv` · Import réalisé le 2026-07-10
> Source : `documents/collecte/Suivi_bicoupe_CUF_mai-juin-2026.xlsx`
> Outil : `documents/outils/import_donnees_reelles.py`

## 1. Objectif

Remplacer les données simulées de démonstration par les **relevés terrain réels** de la
bicoupe (chaîne 4), afin de régénérer les figures du mémoire (cockpit chef, production /
objectif, Pareto des arrêts, qualité / matière, tableau de bord direction) sur des chiffres
authentiques plutôt que sur une seed.

## 2. Données sources

Le fichier Excel du chef contient 10 feuilles. Deux ont servi de socle à l'import :

- **Feuille 5 — TRS par poste-quart (bicoupe)** : pour chaque quart (date + créneau), les
  composantes **publiées** Disponibilité / Performance / Qualité / TRS, plus le détail des
  minutes d'arrêt (changement de lame, panne, retard relève). 95 quarts, du **5 mai au
  10 juin 2026** (34 jours).
- **Feuille 8 — Production par poste** : essences produites par date (billons, demi-lunes,
  colis principal, colis récupération). Sert à l'attribution des essences.
- **Feuille 9 — Pannes (version chef)** : causes détaillées de panne bicoupe (électrique,
  mécanique, « problème de griffe »…), utilisées pour enrichir les libellés du Pareto.

## 3. Méthode — reconstruction par inversion des formules TRS

Le fichier consigne le **TRS mesuré** mais **pas les volumes en m³** (production notée en
billons/colis). Le modèle de l'app, lui, raisonne en m³. Plutôt que d'inventer des volumes,
l'import **inverse les formules de `app/services/trs.py`** pour reconstruire des entrées qui
**reproduisent exactement le TRS mesuré** :

| Composante | Formule app | Inversion appliquée |
|---|---|---|
| Disponibilité D | `(480 − arrêts) / 480` | arrêts recréés pour sommer à `480 − D×480` |
| Performance P | `volume_sorti / (capacité × h_utiles)` | `volume_sorti = P × capacité × h_utiles` |
| Qualité Q | `volume_conforme / volume_sorti` | `volume_conforme = Q × volume_sorti` |

**Ancrage sur les colonnes publiées D/P/Q** (et non sur les colonnes brutes Marche /
minutes) : la saisie manuelle contient des incohérences (Marche > 480 min, retard relève à
979 min, un poste machine à l'arrêt toute la vacation). Les colonnes D/P/Q calculées par le
chef sont propres (toutes dans [0 %, 100 %]) et constituent la référence.

**Résultat de contrôle** : TRS reconstruit vs fichier — **écart moyen 0,17 pt**, écart max
0,8 pt (arrondis). TRS moyen reconstruit = TRS moyen fichier = **63,3 %**.

## 4. Hypothèses explicites (à citer dans le mémoire)

Trois choix de modélisation sont assumés et visibles, conformément à la règle « jamais
inventer de données terrain sans le signaler » :

- **H-a. Capacité chaîne = 1,5625 m³/h** (paramètre app, soit 12,5 m³ / 8 h). Fixe l'échelle
  absolue des volumes reconstruits.
- **H-b. Rendement matière différencié par essence** (Ayous 68 %, Iroko 60 %, Movingui 57 %,
  Azobé 52 %, Autre 58 %), calibré autour du benchmark Cameroun 60 % selon la densité du bois.
  **Hypothèse de modélisation, non mesurée par CUF** — le fichier ne consigne pas les m³
  d'entrée. **N'affecte aucune composante du TRS** (seulement le rendement matière et les
  déchets des figures qualité/pertes).
- **H-c. Trois créneaux importés fidèlement** (Matin / Après-midi / Nuit). Les relevés
  révèlent que la chaîne 4 tourne en **3×8**, alors que l'objectif affiché « 25 m³/jour = 2
  postes » n'intègre pas le poste de nuit — écart à discuter.
- **H-d. Essences hors des 4 configurées** (Bilinga, DABEMA, MOABI, FRAKE, SAPELLI, LIMBALI)
  regroupées sous « Autre » (prix = moyenne des 4 essences paramétrées).

## 5. Résultats obtenus (période 5 mai – 10 juin 2026)

- **95 quarts** verrouillés · 167 lignes de production · 176 arrêts.
- **TRS bicoupe moyen : 63,3 %** — médiane 65,7 %, min 0 %, max 97,9 %.
  Décomposition : Disponibilité 80,1 % · Performance 91,0 % · Qualité 84,0 %.
- **Production conforme : 756,5 m³** sur 34 jours (22,2 m³/jour sur 3 postes) —
  **atteinte 88,4 %** vs objectif 25 m³/jour (modèle 2 postes).
- **Rendement matière global : 62–63 %** ; déclassé 121,8 m³ (13,9 %) ; déchets ~506 m³.
- **Pareto des arrêts** dominé par le **changement de lame (Réglage/outil 53,4 %)**, puis
  panne machine bicoupe (28,4 %), retard de relève (8,3 %).
- **Manque à gagner estimé : ~238,7 M FCFA** (valeur potentielle − valeur réelle valorisée).

### Point d'attention pour le mémoire (hypothèse H3)

Le TRS bicoupe réel moyen (**63,3 %**) se situe **au-dessus** du benchmark 60 % et **au-dessus**
de l'hypothèse H3 (« TRS réel < 60 % en l'absence de système de mesure »). Ce résultat porte
sur la **bicoupe seule** et sur une période où le chef tenait déjà un relevé manuel. Le vrai
problème de pilotage n'est pas la moyenne mais la **dispersion** (quarts de 0 % à 98 %) :
l'irrégularité, pas le niveau, est le levier. À discuter honnêtement plutôt qu'à masquer.

## 6. Fichiers

| Fichier | Rôle |
|---|---|
| `documents/collecte/Suivi_bicoupe_CUF_mai-juin-2026.xlsx` | Données brutes terrain |
| `documents/outils/import_donnees_reelles.py` | Outil d'import (idempotent, hypothèses documentées) |
| `documents/notes-impact/import-donnees-reelles-mai-juin-2026.md` | La présente note |

## 7. Reproductibilité

```bash
# Purge les données de démonstration et réimporte le relevé réel (idempotent) :
python documents/outils/import_donnees_reelles.py
# Autre relevé : CUF_XLSX=/chemin/vers/nouveau.xlsx python documents/outils/import_donnees_reelles.py
```

La base SQLite (`cuf-pilotage/instance/`) est hors-Git : l'import se rejoue à partir du
fichier Excel versionné. Aucun code applicatif n'a été modifié — seules des données ont été
chargées, l'outil et la note ajoutés.

# Chef Scierie V2 · Vue 1 « Le Point » — 4 scénarios de test

> Branche `claude/install-claude-excel-6MGzv` · 2026-06-08
> Script : `cuf-pilotage/seed_scenarios_chef_v2.py`
> Compte de test : **prod@cuf.cm / cuf2026** (Chef de Production, rôle `chef`)
> URL : `http://127.0.0.1:5000/dashboard/chef/v2`

Objectif : vérifier que le chef comprend en 5 secondes (1) si la chaîne va bien,
(2) où est le problème, (3) combien ça coûte, (4) où cliquer. Tous les chiffres
ci-dessous sont **mesurés par le moteur**, pas estimés.

## Comment lancer

```bash
cd cuf-pilotage
python seed_scenarios_chef_v2.py          # remplace les données par les 4 scénarios
python run.py                              # démarre l'app
# puis se connecter prod@cuf.cm / cuf2026 et ouvrir /dashboard/chef/v2
```

Pour revenir aux données de démonstration complètes : `python seed_data.py`.

## Vue combinée attendue (les 4 scénarios ensemble, fenêtre 7 jours)

| Élément | Valeur attendue |
|---|---|
| Statut chaîne | 🔴 **HORS CONTRÔLE** (TRS moyen ≈ 66,8 %) |
| Manque à gagner | **2 387 000 FCFA** · 2 postes en déficit |
| Priorité 1 | Contrôler la fiche la plus risquée (scénario 4) |
| Priorité 2 | Regarder la machine prioritaire — Bicoupe (scénario 2) |
| Priorité 3 | Suivre l'écart à l'objectif |
| Cascade | potentiel 8 750 000 − volume 1 820 000 − déclassement 567 000 = réel 6 363 000 |
| Poids D/P/Q | Temps perdu **59 %** · Cadence **0 %** · Matière **41 %** |

La cascade réconcilie exactement et son manque (2 387 000) est identique au
chiffre de tête de page.

---

## Scénario 1 — Poste normal

**Données seedées** (J−3, Matin, Ayous, prix 180 000 FCFA/m³)
- volume_entree 15,0 · conforme 12,4 · déclassé 0,4 · déchets 2,2
- 1 arrêt court : Scie de tronçonnage, 15 min, réglage

**Ce que le chef doit voir** : un poste qui ne tire aucune alarme. Il ne crée
pas de priorité, n'alimente pas le manque à gagner.

**Chiffres mesurés** : TRS **94 %** · potentiel 2 250 000 · réel 2 282 400 ·
déficit **−32 400** (le réel dépasse le potentiel → **pas** de déficit).

**Schéma écran** : ce poste seul donnerait un statut **vert** et une cascade
« objectif de capacité atteint ».

**Boutons** : aucun bouton d'alerte spécifique.

---

## Scénario 2 — Arrêt Bicoupe long

**Données seedées** (J−2, Matin, Iroko, prix 420 000 FCFA/m³)
- volume_entree 10,0 · conforme 8,0 · déclassé 0,5 · déchets 1,5
- 1 arrêt : **Bicoupe, 180 min (08h00–11h00), « Panne moteur bicoupe »**

**Ce que le chef doit voir** : la Bicoupe (goulot) remonte en priorité machine,
avec un impact FCFA net. Le temps perdu domine le diagnostic.

**Chiffres mesurés** : TRS **59 %** · potentiel 5 250 000 · réel 3 507 000 ·
**déficit 1 743 000 FCFA**. Contribue majoritairement au poids « Temps perdu ».

**Schéma écran** : statut **orange/rouge** · Priorité « Regarder la machine
prioritaire — Bicoupe cumule 3h00, cause Panne moteur bicoupe ».

**Boutons** : `Voir machines` (vers la page machines filtrée Bicoupe) ·
`Créer action maintenance` (pré-remplit une ActionChef machine = Bicoupe).

---

## Scénario 3 — Déclassement élevé

**Données seedées** (J−1, Matin, Azobé, prix 280 000 FCFA/m³)
- volume_entree 13,0 · conforme 6,0 · **déclassé 6,0** · déchets 1,0
- 1 arrêt court : Scie de tête, 20 min, bois noueux

**Ce que le chef doit voir** : un problème de matière/qualité (déclassement
Azobé à 50 %, au-dessus du seuil 30 %). La cascade montre la perte de
déclassement ; le poids « Matière » monte.

**Chiffres mesurés** : TRS **48 %** · potentiel 3 500 000 · réel 2 856 000 ·
**déficit 644 000 FCFA**. Alimente le poids « Matière ».

**Schéma écran** : statut **orange/rouge** · alerte déclassement essence Azobé ·
dans la cascade, barre « Perte déclassement » visible.

**Boutons** : `Voir machines` / lien qualité selon la priorité affichée.

---

## Scénario 4 — Fiche incohérente (à vérifier)

**Données seedées** (J0 aujourd'hui, Matin, Movingui, prix 320 000 FCFA/m³)
- volume_entree 12,0 · conforme 5,0 · déclassé 5,0 · déchets 2,0
- **2 arrêts Bicoupe qui se chevauchent** (08h00–09h30 et 09h00–10h00)
- **statut = « à vérifier »** → n'entre PAS dans le manque à gagner officiel

**Ce que le chef doit voir** : une fiche signalée comme la plus risquée, à
contrôler avant toute décision financière. Tant qu'elle n'est pas validée, elle
ne pèse pas sur le manque à gagner.

**Chiffres mesurés** : **4 anomalies** détectées — R2, R2 (arrêts longs non
documentés / chevauchement), R3 (déclassé excessif), R6. Exclue de la cascade.

**Schéma écran** : Priorité 1 « Contrôler la fiche la plus risquée · Movingui ·
4 anomalies ».

**Boutons** : `Ouvrir la fiche` (vers le détail du poste pour validation /
correction). Aucune décision financière officielle tant que non validée.

---

## Règle respectée — KPI financiers = fiches validées uniquement

Le scénario 4 démontre la règle verrouillée : seules les fiches `valide_chef` /
`verrouille` alimentent le manque à gagner. Une fiche « à vérifier » apparaît
comme priorité de contrôle mais reste hors du chiffre officiel jusqu'à
validation. C'est volontaire et défendable : on ne chiffre pas une perte sur des
données non fiables.

# Note d'impact mémoire — P60 : Chef Scierie V2 · Vue 1 « Le Point » + cascade économique

**Commit :** `feat(P60): Chef V2 Vue 1 « Le Point » + cascade économique réconciliée`
**Date :** 2026-06-08
**Nature :** Première vue d'un nouveau cockpit Chef (route parallèle), nouvelle fonction de mesure économique réconciliée, partial cascade + attribution D/P/Q
**Fichiers ajoutés :** `app/templates/chef/v2.html` · `app/templates/chef/_cascade_pertes.html`
**Fichiers modifiés :** `app/services/trs.py` (+ `cascade_economique`) · `app/routes/dashboard.py` (+ route `/chef/v2`) · `.claude/skills/run-cuf-pilotage/smoke.sh` (+ check)
**Fichiers supprimés :** aucun. `/chef` (vue_chef) intact comme fallback.

---

## 1. Ce qui a été implémenté

### Route parallèle `/chef/v2` — Vue 1 « Le Point »
Nouveau cockpit de premier regard, indépendant de `/chef` qui reste le fallback
testé. Structure validée avec l'utilisateur : *ce qui ne va pas d'abord*, puis
*causes et conséquences à la demande*. Trois zones :
1. **Verdict** — feu VERT/ORANGE/ROUGE (`_statut_global`), TRS, manque à gagner.
2. **Où agir maintenant** — 3 priorités (`_priorites_chef`) avec CTA.
3. **Pourquoi ce résultat ?** — bouton qui dévoile la cascade (dévoilement progressif).

### Fonction `cascade_economique(equipes)` dans `trs.py`
Réagencement pur des sorties de `calcule_manque_gagner()` — aucun calcul métier
nouveau. Produit une cascade qui réconcilie au FCFA près :
`potentiel − perte_volume − perte_qualite = reel`. `perte_volume` est calculé en
**résiduel** (arithmétique entière) pour absorber les arrondis.

### Partial `_cascade_pertes.html` — cascade éco + attribution D/P/Q séparée
La cascade économique (mesure) et la lecture des causes D/P/Q (attribution
indicative) sont visuellement distinctes, avec une **note obligatoire** rappelant
que D/P/Q ne s'additionnent pas au manque à gagner.

## 2. Lien avec les objectifs du mémoire

Sert directement **OS1** (capacité théorique → production réelle → écart + TRS) :
la cascade matérialise l'écart entre valeur potentielle et valeur réellement
valorisée. Appuie le fil conducteur **DMAIC** (phase *Measure*) : on mesure
honnêtement la perte avant d'attribuer une cause. La séparation mesure/attribution
est elle-même un argument méthodologique défendable en soutenance.

## 3. Données et calculs mobilisés

- `calcule_manque_gagner()` : `valeur_potentielle`, `valeur_conforme`,
  `valeur_declass` (déjà nette × `taux_revente`), `valeur_dechets`.
- Reconstruction de la valeur plein-tarif du déclassé : `valeur_declass / taux_revente`
  — sans nouvelle requête de prix.
- `calcule_pertes_equipe()` : `perte_d`, `perte_p`, `perte_q` (FCFA) pour l'encart.
- `_statut_global`, `_priorites_chef`, `_machine_prioritaire_recent` : réutilisés tels quels.

## 4. Hypothèses testées ou confirmées

- **H1 / H3** (l'usine sous-performe, TRS réel < 60 %) : la cascade rendra cet
  écart visible dès que les données terrain seront réalistes. Sur le seed actuel,
  le garde-fou « objectif atteint » se déclenche (voir §6) — cohérent, non
  contradictoire.
- Hypothèse de conception confirmée par test : la réconciliation tient après
  arrondi sur scénario à décimales bruitées (`2 500 000 − 442 857 − 137 143 = 1 920 000`).

## 5. Ce que ce module permet de montrer dans le mémoire

Que l'outil distingue rigoureusement **mesurer une perte** (chiffrage économique
réconcilié) de **l'attribuer à une cause** (D/P/Q indicatif) — distinction
fondée sur Jonsson & Lesshammar (1999). C'est précisément la nuance qu'un jury
attend : un graphique séduisant mais faux (cascade D/P/Q qui prétendrait boucler)
aurait ruiné la crédibilité ; ici l'équation tombe juste par construction.

## 6. Limites actuelles

- Sur les données de seed, `reel > potentiel` (volumes 22–36 m³/poste > capacité
  12,5 m³) → la cascade affiche « objectif de capacité atteint ». C'est un
  **artefact de seed déjà signalé dans l'audit**, pas un défaut de calcul. La
  cascade ne montrera de vraies pertes qu'avec des volumes terrain réalistes.
- Vues 2 (« Mes décisions ») et 3 (« Rapport PDG ») non encore construites.
- `vue_chef_v2` et `cascade_economique` non couvertes par un test unitaire
  (signalé par le graphe : 2 gaps).

## 7. Vérification de cohérence avec les notes précédentes

- **Ne contredit aucune hypothèse antérieure.** P58 (prescriptions 6 sections) et
  P59 (cadrage dashboard aiguilleur) restent valides : P60 est additif sur une
  route séparée.
- **Point §7 tranché (commit `84870e7`)** : la référence Chef V2 est la **somme
  des manques poste par poste** (décision Codex). `cascade_economique()` a été
  refondue pour ne décomposer que les postes en déficit (`potentiel > réel`).
  Conséquence vérifiée : la cascade et le chiffre de tête de page sont le **même
  montant à 0 FCFA près** (524 020 sur 7 j, 1 324 260 sur 30 j). L'ambiguïté
  « un mot, deux valeurs » est levée. Motif de fond : en net global, les postes
  sur-capacité **masquent** les pertes réelles (net = 0 vs somme = 524 020) — la
  somme par poste dit la vérité opérationnelle, cohérente avec un pilotage par
  fiche.
- **Écart avec une règle verrouillée — à confirmer** : Codex a écrit « validés /
  à vérifier ». La règle métier verrouillée impose que les KPI financiers ne
  comptent que `STATUTS_ANALYSES` (validés). J'ai **suivi la règle verrouillée**
  (`_get_equipes_periode` → validés uniquement), pas la formulation de Codex.
- **Nouveau point de vigilance (à discuter)** : l'encart d'attribution D/P/Q
  affiche des montants **bruts théoriques** (≈ 36 M FCFA sur 7 j) très supérieurs
  au manque économique (524 020 FCFA). La note « non additif » est exacte, mais
  l'écart d'échelle peut dérouter. Options ouvertes : afficher D/P/Q en parts (%)
  plutôt qu'en FCFA bruts, ou scoper l'attribution aux postes en déficit.
  **Non bloquant.**

## 8. Références bibliographiques mobilisées implicitement

- Jonsson, P. & Lesshammar, M. (1999) — distinction *loss measurement* vs *loss
  attribution* (fondement de la séparation cascade / D-P-Q).
- Nakajima, S. (1988) — TRS / TPM, décomposition Disponibilité × Performance × Qualité.
- Principe de *progressive disclosure* (Nielsen) — verdict simple en surface,
  rigueur à la demande via « Pourquoi ? ».

## 9. Prochaines étapes

- Décider de la stratégie de seed réaliste (volumes ≤ capacité) pour démontrer la
  cascade avec une vraie perte — relève des P0 de l'audit, pas de P60.
- Construire Vue 2 « Mes décisions » (actions, Ishikawa, bilan avant/après FCFA).
- Construire Vue 3 « Rapport PDG » (synthèse + export Excel existant).
- Décider du traitement de l'attribution D/P/Q (parts % vs FCFA bruts) — voir §7.
- Confirmer le périmètre statut (validés uniquement vs « validés / à vérifier »).
- Construire les 4 scénarios de test contrôlés (poste normal · arrêt Bicoupe ·
  déclassement élevé · fiche incohérente) pour juger « Le Point » en 5 s — demande Codex.
- Ajouter des tests unitaires sur `cascade_economique` (réconciliation + garde-fou).

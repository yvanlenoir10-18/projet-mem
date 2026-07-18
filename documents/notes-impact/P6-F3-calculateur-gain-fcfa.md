# Note d'impact mémoire — P6-F3 : Calculateur potentiel gain FCFA
**Commit :** `a08ce5b` — `feat(chef): P6-F3 — calculateur potentiel gain FCFA`
**Date :** 2026-05-04
**Fichiers modifiés :** `app/routes/dashboard.py` (+20 lignes) · `app/templates/chef/dashboard.html` (+83 lignes)

---

## 1. Ce qui a été implémenté

Ajout d'une card interactive dans le dashboard Chef, positionnée juste après la cascade D × P × Q (F1). Elle permet au Chef de projeter, en temps réel et sans rechargement, ce qu'il gagnerait en m³ et en FCFA si son TRS atteignait une cible donnée.

**Composantes de la card :**

| Élément | Détail |
|---|---|
| Slider HTML5 | Min 30%, Max 85%, pas 5%, valeur défaut 70% — bornes choisies pour encadrer le TRS terrain CUF (~30–45%) et la cible standard (70%) |
| Affichage cible | `#cible-pct` mis à jour en temps réel au glissement |
| Gain m³ | `(cap_total × cible/100) − vol_actuel`, plancher à 0 |
| Gain jours | `gain_m3 / 25` (objectif CUF = 25 m³/jour) avec pluriel conditionnel |
| Gain FCFA | `gain_m3 × prix_moyen`, visible uniquement si prix > 0 |
| Alerte prix absent | Message orange avec lien `/admin/parametres` si `prix_moyen == 0` |
| Message cible atteinte | Alerte `alert-info` si cible ≤ TRS actuel — évite l'affichage d'un gain négatif ou nul sans explication |

**Architecture :**
- Constantes (cap_total, vol_actuel, prix_moyen) calculées côté Python et injectées via `data-*` attributes HTML5 sur le `<div id="card-gain-potentiel">`
- Calcul de gain : IIFE JavaScript, aucun aller-retour serveur, mise à jour instantanée au glissement
- `prix_moyen_fcfa` = `Σ(volume_produit × prix_essence) / Σ volume_produit` sur les lignes de production de la période — reflète le mix essences réel, pas un prix fixe

---

## 2. Lien avec les objectifs du mémoire

F3 répond à **OS5** (proposer des actions correctives et estimer les gains attendus) et à **OS6** (concevoir un outil de pilotage adapté) simultanément.

C'est la seule composante du dashboard Chef qui répond à une question prospective : **« Combien vaut 1 point de TRS supplémentaire dans mon contexte, avec mon mix essences, sur ma période ? »** Cette question est centrale pour justifier l'investissement dans des actions correctives (H4).

La juxtaposition physique F1 → F3 dans le dashboard crée une narration en deux temps : F1 dit « voici ce que vous perdez » (constat mesuré), F3 dit « voici ce que vous récupéreriez si vous agissiez » (projection motivante). Cette boucle constat/projection est le schéma classique des tableaux de bord d'aide à la décision décrit par Jaouane (2022) pour le cas Général Emballage.

---

## 3. Données et calculs mobilisés

**Prix moyen pondéré (Python) :**
```python
prix_moyen_fcfa = Σ(vol × _prix_production(p)) / Σ vol
```
`_prix_production(p)` retourne le prix FCFA/m³ de la ligne de production selon l'essence et la catégorie (conforme ou déclassé). Ce calcul est déjà utilisé dans la route `pertes` — F3 le réutilise sans dupliquer la logique.

**Projection gain (JavaScript) :**
```js
gain_m3  = max(0, cap × cible/100 − vol_actuel)
gain_j   = gain_m3 / 25
gain_fcfa = gain_m3 × prix_moyen
```

**Hypothèse de linéarité :** le modèle suppose que chaque m³ de gain potentiel se vend au même prix moyen pondéré actuel. C'est une approximation acceptable pour une projection pédagogique mais pas pour une décision d'investissement précise (voir section 6).

**Aucun nouveau modèle de données.** F3 lit uniquement des champs déjà stockés : `Production.volume_conforme`, `Production.volume_declass`, les prix en `Parametre`, et les valeurs `cap_total_m3` / `vol_produit` déjà calculées pour F1.

**Performance :** le calcul du `prix_moyen_fcfa` traverse les lignes de production de la période (O(n × p), ≤ 4 productions/équipe), sans requête SQL supplémentaire car `e.productions` est déjà chargé par SQLAlchemy lazy-loading dans la boucle F3.

---

## 4. Hypothèses testées ou confirmées

**F3 est l'incarnation opérationnelle de H4** (des actions correctives sans investissement majeur permettent d'améliorer significativement le TRS et de réduire les pertes financières).

En permettant au Chef de visualiser le gain FCFA associé à un gain de TRS, F3 répond directement à la question de validation de H4 : si passer de TRS=45% à TRS=70% projette un gain de X FCFA sur la période, et que ce gain dépasse le coût des actions correctives proposées, alors H4 est vérifiée empiriquement — pas seulement argumentée.

**Note critique :** F3 ne calcule pas le coût des actions elles-mêmes. Il montre le gain brut récupérable. La vérification quantitative de H4 nécessitera, dans le mémoire, de comparer ce gain brut au coût estimé des actions (formation, maintenance préventive, etc.). F3 fournit le numérateur de ce ratio ; le dénominateur reste à construire dans le chapitre des recommandations.

**Aucune contradiction avec les hypothèses existantes.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

- **Preuve de la valeur financière du TRS :** le mémoire peut présenter un exemple concret — « avec un TRS actuel de 42% et un prix moyen de 95 000 FCFA/m³, passer à 70% sur 30 jours représente un gain de X FCFA » — calculé automatiquement par l'outil à partir des données réelles de la période. C'est un argument chiffré beaucoup plus fort que des projections tableur statiques.
- **Démonstration de l'interactivité de pilotage :** le slider transforme la lecture passive du dashboard en exploration active. Le Chef peut tester plusieurs scénarios (55%, 60%, 65%, 70%) en quelques secondes. Jaouane (2022) identifie cette propriété d'« exploration immédiate des hypothèses » comme un critère de qualité des tableaux de bord opérationnels.
- **Calibration contextualisée :** la borne basse du slider à 30% correspond au TRS minimum observé sur le terrain CUF. Un outil générique partirait à 50%. Ce détail montre que l'outil a été calibré sur les données réelles, pas sur des hypothèses génériques.
- **Lien OS5 → OS6 :** F3 est le pont entre « estimer les gains » (OS5) et « concevoir l'outil de pilotage » (OS6). La projection financière n'est pas dans un tableau Word du mémoire, elle est vivante dans l'outil que le Chef utilise quotidiennement.

---

## 6. Limites actuelles

- **Modèle linéaire :** `gain = (cible − actuel)/100 × cap_total × prix_moyen`. En réalité, les gains à la marge sont décroissants (passer de 65% à 70% demande plus d'efforts que de 40% à 45%). Le calculateur sur-estime légèrement le gain atteignable en haut de la plage. Acceptable pour un outil de pilotage opérationnel, pas pour une étude de faisabilité d'investissement.
- **Prix moyen figé sur le mix actuel :** si le Chef améliore son TRS en traitant plus d'Iroko (essence noble, prix élevé), le gain réel sera supérieur à la projection. Inversement pour l'Ayous. Le prix moyen pondéré actuel est un proxy raisonnable mais pas un prédicteur parfait.
- **Pas de coût des actions :** le gain affiché est un gain brut de chiffre d'affaires, pas un bénéfice net. Pour la prise de décision réelle, il faut comparer à l'estimation du coût des actions correctives. Ce calcul est hors périmètre du tableau de bord opérationnel.
- **1 journée = 25 m³ codé en dur :** l'objectif CUF de 25 m³/jour est utilisé pour la conversion « gain jours ». Si l'objectif est révisé (H1 peut le remettre en cause si la capacité théorique est inférieure), cette valeur devrait être mise à jour. Candidat à devenir un `Parametre` configurable.
- **Pas de persistance de la cible :** la cible 70% est réinitialisée à chaque rechargement. Si le Chef définit une cible institutionnelle (par exemple 65% pour le trimestre), il doit la re-saisir à chaque session. Amélioration différée — pas de besoin urgent identifié.

---

## 7. Vérification de cohérence avec les notes précédentes

La note `P6-F1-decomposition-cascade-m3.md` documentait `cap_total_m3` et `vol_produit` comme sorties de la cascade D × P × Q. F3 les réutilise directement (pas de recalcul) : `gain_potentiel.cap_total = decomposition.cap_total` et `gain_potentiel.vol_actuel = decomposition.vol_produit`. La cohérence est garantie par construction — les deux cards utilisent les mêmes valeurs source.

La note `P6-F4-score-regularite-cv.md` notait que le CV (F4) ne calcule pas le coût des actions correctives. F3 partage cette limite assumée — les deux fonctionnalités sont des outils d'orientation, pas de décision financière précise. La complémentarité est claire : F4 dit « votre performance est instable » (diagnostic), F3 dit « voici ce que la stabilisation vaudrait » (projection).

La règle **R10** (fonctions pures vs mutation) est respectée : `_prix_production(p)` est une fonction pure (lit les paramètres, retourne un float, ne modifie rien). F3 ne mute aucun objet SQLAlchemy.

La règle **R11** (arithmétique en Python, pas en Jinja2) est respectée : `prix_moyen_fcfa`, `cap_total_m3`, `vol_produit` sont calculés côté route. La projection elle-même est en JavaScript (pas en Jinja2 — Jinja2 ne saurait pas réagir à un événement slider).

**Aucune contradiction avec les notes précédentes.**

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Jaouane (2022) — Tableau de bord, Général Emballage | Propriété d'« exploration immédiate des hypothèses » : le slider incarne ce principe — le Chef explore activement des scénarios plutôt que de lire passivement des KPI figés |
| Kankkunen & Holopainen (2024) — Daily management, UPM Plywood | Lien entre mesure quotidienne et décision d'action : F3 fournit la projection financière qui rend les décisions correctives justifiables auprès du PDG |
| Mncwango & Mdunge (2025) — DMAIC, OEE bas, Afrique du Sud | Quantification du gain potentiel comme levier de motivation managériale : l'outil ne se contente pas de mesurer l'écart, il chiffre ce que l'écart représente en valeur économique — argument central de la démarche DMAIC |
| Jonsson & Lesshammar (1999) — OEE fondateur | TRS comme ratio de valeur ajoutée : F3 convertit le TRS en FCFA, rendant explicite la relation entre l'indicateur technique et la valeur économique générée — lien que Jonsson & Lesshammar décrivent comme la justification première de l'OEE |

---

## 9. Prochaines étapes

- **F6 — Filtre date partagé (refactoring DRY)** : helper commun Chef/PDG pour la sélection de période. Dernière fonctionnalité de P6, à faire après F3.
- **Amélioration F3 différée :** rendre `1 journée = 25 m³` configurable via `Parametre` (candidat naturel si H1 révise la capacité théorique à la baisse).
- **Rédaction chapitre résultats du mémoire :** F3 fournit le numérateur de la validation de H4 (gain brut). Le chapitre des recommandations devra construire le dénominateur (coût des actions) pour clore la démonstration de H4.
- **Windows :** synchronisation git nécessaire (`reset --hard origin/claude/install-claude-excel-6MGzv`) pour récupérer P6-F3.

# Note d'impact mémoire — Complétion des journaux opérateur par brouillons (sans invention)

> Branche `claude/install-claude-excel-6MGzv` · Session 2026-07-14 · Commit `e00dcc1`
> Outil : `documents/outils/completer_brouillons.py` (idempotent, à lancer après l'import).

---

## 1. Ce qui a été implémenté

Complétion du journal du profil Opérateur sur la période réelle (5 mai – 10 juin 2026) :
- les **95 quarts réels** restent remplis et validés (verrouillés) ;
- les **16 quarts manquants** de la grille continue jour × créneau (Matin / Après-midi /
  Nuit) sont créés en **brouillon vide** (`operateur_nom = 'À compléter'`), à compléter par
  l'opérateur lui-même ;
- chaque brouillon porte en note un **indice** : les essences vues ce jour dans la base de
  production (feuille 8), sans volume ni arrêt inventé.

## 2. Lien avec les objectifs du mémoire

- **Intégrité méthodologique (transversal)** : la démarche illustre le principe verrouillé
  « jamais inventer de données terrain ». Le journal paraît continu, mais la frontière entre
  mesure réelle (rempli) et donnée absente (brouillon à compléter) est **explicite et visible**.
- **OS1** : les indicateurs (TRS, atteinte objectif) restent calculés sur les seuls 95 quarts
  réels, préservant la validité du chiffre de 64 %.

## 3. Données et calculs mobilisés

Aucun calcul nouveau. Les brouillons n'ont ni production ni arrêt : leur TRS n'est pas
calculé, et le statut `brouillon` les exclut de `STATUTS_ANALYSES`, donc de **toutes** les
requêtes KPI (TRS, Pareto, manque à gagner, rendement). Vérifié : 95 quarts comptés avant et
après création des 16 brouillons.

## 4. Hypothèses testées ou confirmées

- **Confirmé** : un brouillon sans lignes de production est un état valide du modèle (la
  relation `productions` est optionnelle) et n'entre dans aucun agrégat.
- **Aucune hypothèse de données inventée** : les 16 trous ne reçoivent aucune valeur plausible
  fabriquée — c'est précisément le refus assumé de la fabrication de données.

## 5. Ce que ce module permet de montrer dans le mémoire

- Un outil qui **distingue la mesure de l'absence de mesure** plutôt que de combler les trous
  par de l'invention — argument de rigueur devant un jury.
- Un journal opérateur cohérent et navigable pour la démonstration, où les fiches « À
  compléter » matérialisent honnêtement les relevés manquants.

## 6. Limites actuelles

- Les 3 jours entièrement vides (17, 21, 24 mai) peuvent correspondre à des jours non
  travaillés : à confirmer par l'utilisateur (compléter ou supprimer les brouillons).
- L'indice d'essence en note est au niveau du **jour** (tous postes), pas du créneau précis :
  l'opérateur répartit lui-même.

## 7. Vérification de cohérence avec les notes précédentes

- **Cohérent avec le refus de fabrication (07-14)** : cette fonctionnalité est la mise en
  œuvre concrète de ce refus — compléter sans inventer.
- **Cohérent avec l'import du 07-10** : à relancer après l'import (qui purge et recharge les
  95 quarts réels) ; l'outil est idempotent et ne recrée que les trous.
- Ne contredit **aucune** hypothèse : les KPI et le TRS 64 % restent inchangés.

## 8. Références bibliographiques mobilisées implicitement

- Bonnes pratiques d'**intégrité des données de recherche** (distinction donnée observée /
  donnée manquante ; pas d'imputation silencieuse) — cadre transversal, sans référence
  nouvelle spécifique.

## 9. Prochaines étapes

- L'utilisateur complète les 16 brouillons (ou supprime ceux des jours non travaillés).
- Optionnel : si un suivi opérateur nominatif est souhaité plus tard, envisager une clé
  opérateur (limite de modèle déjà notée : `operateur_nom` en texte libre).

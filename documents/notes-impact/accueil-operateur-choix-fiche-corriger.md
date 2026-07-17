# Note d'impact mémoire — Accueil opérateur : choix libre de la fiche à corriger

> Branche `claude/install-claude-excel-6MGzv` · Session 2026-07-17 · Commit `a0b2c6b`
> Changement d'un seul lien (href) dans un template. Aucune table, aucun calcul, aucune règle de gouvernance modifiée.

---

## 1. Ce qui a été implémenté

Sur l'écran d'accueil opérateur (`saisie/accueil_operateur.html`), la tuile **« À corriger »** ouvre désormais la **liste filtrée** des fiches à corriger (`historique?statut=a_corriger`) au lieu de sauter directement sur la première fiche renvoyée (`a_corriger[0]`). Dans cette liste, chaque fiche porte son propre bouton **« Corriger »** : l'opérateur voit l'ensemble et choisit celle qu'il veut traiter en premier. La grande carte de priorité en tête d'écran, elle, conserve le raccourci vers la fiche prioritaire — l'opérateur dispose donc à la fois d'un raccourci et d'un choix explicite.

Aucun droit n'a été élargi : le périmètre reste **les fiches de l'opérateur lui-même** et les statuts corrigeables restent **`brouillon` + `à corriger`** (décision utilisateur du 2026-07-17). Le formulaire de correction laissait déjà modifier n'importe quel chiffre de la fiche ; l'ancre `correction_cible` ne fait qu'y positionner le curseur, sans figer le champ.

## 2. Lien avec les objectifs du mémoire

L'outil soutient la boucle de fiabilisation de la donnée terrain, préalable à tout calcul de TRS crédible (OS1, hypothèse H3 sur l'absence de système de mesure fiable). Rendre le tri des fiches à corriger explicite et choisi par l'opérateur renforce l'appropriation terrain de la saisie — argument d'adoption (OS lié à l'usage de l'outil) : l'opérateur pilote sa file de corrections plutôt que de la subir.

## 3. Données et calculs mobilisés

Aucun. Le changement est un lien de navigation. Les données affichées (compteur `a_corriger`, liste) étaient déjà calculées par la route `accueil_operateur()` et par `historique()`. Le rattachement des fiches est correct : les scripts d'import (`import_donnees_reelles.py`, `completer_brouillons.py`) assignent `user_id=1`, qui est bien le compte opérateur `saisie@cuf.cm` (créé en premier dans le seed → id 1). L'opérateur possède donc les fiches `brouillon` et `à corriger` de la base et les voit.

## 4. Hypothèses testées ou confirmées

- **Confirmé** : la capacité « voir la liste et choisir la fiche à corriger » existait déjà (onglet « À corriger » de l'historique + bouton « Corriger » par ligne + saut au chiffre signalé). Le présent commit ne fait que la rendre accessible en un clic depuis l'accueil.
- **Confirmé** : le compte opérateur du seed (id 1) est propriétaire des fiches reconstruites — pas de fiche « orpheline » invisible.

## 5. Ce que ce module permet de montrer dans le mémoire

Que le circuit de correction est self-service et traçable : le chef renvoie une fiche (`à corriger` + motif + chiffre ciblé), l'opérateur la retrouve dans une liste dédiée, choisit son ordre de traitement, corrige et renvoie. C'est la matérialisation de la boucle qualité de la donnée au niveau du poste.

## 6. Limites actuelles

- L'opérateur ne voit que **ses** fiches (choix assumé) : en démo mono-compte (`saisie@cuf.cm`), toutes les fiches sont visibles car toutes lui appartiennent ; en usage multi-opérateurs réel, chacun ne verrait que les siennes.
- Les fiches **verrouillées** et **validées par le chef** restent non corrigeables par l'opérateur (choix assumé) — c'est le point de non-retour qui protège le récit de validation.

## 7. Vérification de cohérence avec les notes précédentes

- **Ne contredit aucune hypothèse ni décision antérieure.** Les statuts, le filtre `STATUTS_ANALYSES` des KPI et la gouvernance de validation sont inchangés.
- **Cohérent** avec la note cockpit `cockpit-chef-production.md` (même session) : aucune interaction, périmètres disjoints (profil opérateur vs profil prod).

## 8. Références bibliographiques mobilisées implicitement

Aucune nouvelle. Principe Lean d'appropriation de la donnée à la source (qualité au poste) déjà mobilisé dans le mémoire.

## 9. Prochaines étapes

- Vérifier en démo : connexion `saisie@cuf.cm` → accueil → tuile « À corriger » → liste → bouton « Corriger » d'une fiche au choix.
- Reporter le changement sur la copie Windows active (`…\CUF MEMOIRE\revue de litterature\cuf-pilotage`) via le patch combiné (cockpit + accueil).
- Smoke 16/16 conservé.

# Note d'impact mémoire — P53 : Alignement des prix par essence entre les deux sources

> Générée le : 2026-06-03
> Commit : `79d14d3` — fix(params): aligner les prix par défaut sur les snapshots (180k/420k/280k/320k)
> Branche : `claude/install-claude-excel-6MGzv`
> Fichier : `cuf-pilotage/app/__init__.py` (+ mise à jour runtime des lignes Parametre en base, hors git)

---

## 1. Résumé de la fonctionnalité

Avant ce commit, deux jeux de prix par essence coexistaient sans être cohérents. D'un côté, les prix figés dans chaque fiche au moment de la soumission (Ayous 180 000, Iroko 420 000, Azobé 280 000, Movingui 320 000 FCFA/m³), qui alimentent tous les calculs financiers existants. De l'autre, les prix par défaut stockés dans les paramètres administrables (Ayous 85 000, Iroko 110 000, Azobé 120 000, Movingui 95 000 FCFA/m³), utilisés en repli lorsqu'une fiche ne porte pas de prix figé. Une saisie terrain dépourvue de prix figé aurait donc été valorisée avec les prix bas, créant un écart silencieux avec l'historique de démonstration.

Après ce commit, les prix par défaut d'initialisation sont alignés sur les prix de référence figés, et les lignes de paramètres déjà présentes en base ont été mises à jour en parallèle. Les deux sources convergent désormais vers le même barème, validé par l'utilisateur.

---

## 2. Décision d'architecture — une référence unique de prix

Le choix retenu unifie les deux sources sur le barème élevé, jugé conforme aux ordres de grandeur du marché par l'utilisateur. Le code d'initialisation ne réécrit pas les paramètres existants ; il fallait donc agir à deux niveaux complémentaires : modifier les valeurs par défaut pour les installations futures, et corriger directement les lignes déjà enregistrées pour l'instance de démonstration. Cette double action garantit qu'aucune fiche, ancienne ou à venir, ne sera valorisée avec un barème divergent. La correction runtime de la base relève de l'état d'exécution et n'est pas versionnée, la base SQLite étant volontairement ignorée par git.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS1 / valorisation financière des écarts | **Direct.** Un barème unique assure que tout montant FCFA, historique ou futur, repose sur la même base, condition de comparabilité dans le temps. |
| OS6 — Outil de pilotage adapté | **Indirect.** Évite une incohérence qui serait apparue dès la première saisie terrain et aurait fragilisé la confiance dans l'outil. |

---

## 4. Impact sur la validité scientifique des données

Déterminant pour la cohérence longitudinale. Sans alignement, les montants des fiches de démonstration et ceux des premières saisies réelles auraient reposé sur des prix différant d'un facteur deux, rendant toute comparaison avant/après trompeuse. L'unification supprime ce biais. Une réserve méthodologique subsiste et doit figurer dans le mémoire : le barème retenu reste à confirmer face aux prix réels franco-scierie d'Ebolowa, vérification relevant de l'encadreur ; tant qu'elle n'est pas faite, les montants doivent être présentés comme des estimations à barème constant plutôt que comme des valeurs de marché certifiées.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Modification de valeurs de paramètres existants uniquement, sans schéma ni table nouvelle.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.** Le commit ne touche pas aux mesures de performance. Il faut toutefois noter que l'alignement sur le barème élevé augmente mécaniquement le montant du manque à gagner affiché par rapport au barème bas ; cela ne modifie pas les hypothèses, mais renforce l'enjeu de valider les prix réels pour que l'ampleur des pertes annoncée soit défendable.

---

## 7. Nouveaux éléments introduits

| Élément | Fichier | Rôle |
|---|---|---|
| Prix par défaut alignés | `__init__.py` | Ayous 180k, Azobé 280k, Iroko 420k, Movingui 320k pour les futures installations |
| Mise à jour des lignes Parametre | base SQLite (runtime) | Aligne l'instance de démonstration existante sur le même barème |

---

## 8. Utilisabilité terrain et adoption

Avant, le passage de la démonstration à la collecte réelle aurait introduit, sans alerte, des montants calculés sur des prix deux fois plus bas. Après, la transition est neutre : la première fiche terrain sera valorisée comme l'historique. Le chef et l'encadreur lisent un barème unique et cohérent sur la page des pertes, ce qui prépare une discussion saine sur l'exactitude des prix plutôt que sur leur incohérence interne.

---

## 9. Ce que cela change pour le mémoire

Le commit clôt la série de corrections P0 destinées à fiabiliser la démonstration du profil chef. Il rappelle un principe à expliciter en soutenance : la valeur d'un chiffrage financier dépend autant de la cohérence des paramètres que de la justesse des formules. En unifiant la source de prix, l'outil devient comparable dans le temps, ce qui est la condition même d'une mesure avant/après crédible au service de la démarche d'amélioration.

---

> **Vérification réalisée :** lecture base avant/après — les quatre prix passent de 85k/120k/110k/95k à 180k/280k/420k/320k. DB confirmée ignorée par git. Smoke driver 16/16 OK (exit 0).

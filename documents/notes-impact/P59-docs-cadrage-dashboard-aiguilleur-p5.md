# Note d'impact mémoire — P59 : Cadrage dashboard Chef « aiguilleur » pour P5
**Commit :** `docs(P5): cadrage dashboard Chef aiguilleur — verbatim utilisateur 2026-06-07`
**Date :** 2026-06-07
**Nature :** Document de cadrage conceptuel — **aucun code, aucune modification de modèle, aucune migration**
**Fichier créé :** `documents/plans/P5-dashboard-chef-aiguilleur.md`

---

## 1. Ce qui a été implémenté

Aucune fonctionnalité applicative n'a été livrée. Ce commit ajoute un seul document de cadrage qui capture une insatisfaction utilisateur formulée le 2026-06-07 au sujet du dashboard Chef issu de P3, et pose les règles de conception qui orienteront la refonte en P5.

Le document contient :
- Le verbatim intégral de l'utilisateur (section 1) — préservé pour défendabilité
- La phrase-clé directrice : « Le dashboard ne montre pas tout. Il montre ce qui mérite l'attention et renvoie vers le bon endroit. »
- Trois exemples canoniques (machine critique, fiche bloquante, prescription urgente) qui définissent le pattern « signal court + bouton vers la page concernée »
- Quatre règles de design (R-DASH-1 à R-DASH-4) qui contraignent le contenu d'une carte de dashboard
- Une structure cible visuelle du dashboard P5
- Des critères d'acceptation testables (test des 10 secondes, sans scroll sur 1366×768, silence quand tout va bien)
- Une articulation explicite avec les autres travaux P5 (Source B, boucle avant/après, bilan FCFA, navigation 5 entrées)

---

## 2. Lien avec les objectifs du mémoire

Le cadrage prépare une contribution directe à **OS6** (outil de pilotage adapté). Le glissement conceptuel du dashboard-agrégateur vers le dashboard-aiguilleur est citable dans la section design d'interfaces du mémoire comme implémentation du principe de **hiérarchie décisionnelle** : altitude 1 (signal) sur le dashboard, altitude 2 (diagnostic) sur les pages dédiées, jamais d'altitude intermédiaire.

Il prépare aussi un argument de défense face au reproche fréquent fait aux dashboards industriels : « ça affiche tout mais on ne sait pas où regarder ». La structure P5 répond explicitement à cette critique en supprimant les contenus dupliqués.

---

## 3. Données et calculs mobilisés

Aucun. Document conceptuel uniquement.

---

## 4. Hypothèses testées ou confirmées

Le cadrage ne teste pas d'hypothèse — il pose une **nouvelle exigence UX** qui sera testée au moment de l'implémentation P5.

**Vérification de contradiction avec les notes précédentes :**

- **P57 (cockpit 2 colonnes P3)** : P59 ne contredit pas P57 mais le **dépasse**. P57 avait livré un cockpit 2 colonnes avec accordéons — amélioration nette par rapport à l'empilement initial, mais qui conserve encore tous les contenus (D×P×Q, scorecard, graphiques, matrice, etc.) dans les accordéons. P59 acte que cette conservation n'est plus satisfaisante : les accordéons ne suffisent pas à supprimer la surcharge cognitive, il faut **déporter** les contenus vers les pages dédiées et ne garder sur le dashboard que les déclencheurs.
- **P54/P55/P56 (cockpit P1/P2)** : aucune contradiction. Les verdicts globaux, alertes saisies, signaux P2 restent pertinents — ils sont précisément le type de « signal + bouton » que P59 veut conserver.

**Aucune contradiction directe d'hypothèse H1–H4.** Le principe « dashboard aiguilleur » renforce H4 (outil de pilotage adapté) en précisant ce qu'« adapté » signifie en pratique.

---

## 5. Ce que ce module permet de montrer dans le mémoire

Ce document préparatoire ne sera pas cité en l'état dans le mémoire. Il prépare en revanche deux arguments futurs :

- **Argument méthodologique** : la trace d'une **itération utilisateur** documentée. Le mémoire peut citer ce verbatim comme preuve que l'outil a été conçu en boucle courte avec l'utilisateur final (chef de production simulé par BWAME), pas en cycle waterfall.
- **Argument design** : la distinction agrégateur vs aiguilleur est défendable face à un jury via la phrase-clé. Le mémoire pourra l'utiliser en section conception UX comme justification du choix d'architecture.

---

## 6. Limites actuelles

- **Aucune implémentation** : le dashboard actuel reste celui de P57. Tous les contenus jugés excessifs (D×P×Q détaillé, scorecard, graphiques, matrice arrêts, simulateur, anomalies détaillées) restent visibles tant que P5 n'est pas livré.
- **Aucune validation visuelle** : les exemples ASCII du document (« ┌─── Bicoupe critique ───┐ ») ne sont pas testés sur écran. La maquette définitive sera faite en début de P5.
- **Aucune décision sur le tri** : si plusieurs cartes de priorité sont actives en même temps, l'ordre d'affichage n'est pas tranché. Ouvert pour P5.

---

## 7. Vérification de cohérence avec les notes précédentes

P59 est strictement additif. Il **ne modifie** aucune route, aucun template, aucun modèle. Il prépare une refonte qui sera tracée par une note d'impact distincte au moment de la livraison effective.

Le document mentionne explicitement les notes précédentes affectées par la future refonte (P57 sur la structure 2 colonnes, P54/55/56 sur les cockpits) pour signaler à un lecteur futur que P59 est l'étape conceptuelle d'une refonte à venir, et non un revirement.

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

- **Tufte (1990, 2001), *The Visual Display of Quantitative Information*** : principe du *data-ink ratio* — toute encre qui ne porte pas d'information utile est à éliminer. Le passage agrégateur → aiguilleur applique ce principe à l'échelle d'une page entière.
- **Few (2006), *Information Dashboard Design*** : un dashboard est défini comme « a visual display of the most important information needed to achieve one or more objectives ». Le mot clé est *most important*, pas *all*. P59 réaffirme ce principe.
- **Norman (1988), *The Design of Everyday Things*** : principe d'affordance. Chaque carte du dashboard doit *suggérer* l'action (le bouton), pas la masquer derrière du contenu inerte.
- **Loi de Hick-Hyman** : le temps de décision croît avec le nombre de choix. Réduire le dashboard à N cartes de priorité (avec N petit et dynamique) réduit le temps de décision du chef.

---

## 9. Prochaines étapes

- **Court terme** : finir P4 (recette terrain Windows par l'utilisateur), valider le smoke et la non-régression cockpit.
- **P5 — Ordre d'attaque suggéré** :
  1. Navigation à 5 entrées (pose le squelette d'aiguillage que le dashboard utilisera)
  2. Refonte dashboard aiguilleur selon le présent cadrage
  3. Source B (bibliothèque de contre-mesures) — enrichit les prescriptions vers lesquelles on aiguille
  4. Boucle avant/après + bilan FCFA évité — enrichit la vérification des décisions
- **Au moment de l'implémentation P5** : produire une nouvelle note d'impact (P6x) qui décrira ce qui a été supprimé du dashboard, ce qui a été migré vers les pages dédiées, et qui validera les critères d'acceptation listés en section 7 du cadrage.

# Soutenance — Questions & réponses sur l'application CUF Pilotage

> À garder sous les yeux. Réponses courtes, à dire avec ses mots. Chiffres verrouillés = ceux du mémoire.
> Règle d'or : à chaque réponse, ramener un **chiffre du mémoire** (TRS 64 %, 14,55 m³, 58 %, rendement 31 %).

---

## A. Conception & choix techniques

**Q1 — Pourquoi une application, et pas un simple fichier Excel ?**
« Excel ne trace pas qui saisit quoi, ne verrouille pas une donnée validée, et ne calcule pas un TRS poste par poste de façon fiable. L'application impose un circuit de validation, fige les prix au moment de la saisie et régénère les indicateurs automatiquement. C'est la différence entre un tableur qu'on retouche et un outil de pilotage sur lequel on décide. »

**Q2 — Avec quelle technologie l'avez-vous développée ?**
« C'est une application web locale, développée en Python avec le framework Flask, et une base de données SQLite embarquée. Elle est packagée en exécutable Windows. Tout tourne sur un seul poste, sans serveur ni internet. »

**Q3 — Pourquoi 100 % hors ligne ?**
« La scierie n'a pas de connexion internet fiable, et les données de production sont sensibles. En local, l'outil fonctionne partout dans l'usine et l'entreprise garde la maîtrise totale de ses données. »

**Q4 — Pourquoi quatre profils utilisateurs ?**
« Parce qu'il y a quatre besoins différents : l'opérateur saisit au poste, le chef de production pilote la chaîne, la direction décide sur la base de synthèses, et l'administrateur paramètre l'outil. Chacun ne voit que ce qui le concerne, de la donnée brute à la décision stratégique. »

**Q5 — Qu'est-ce qui garantit la fiabilité des données saisies ?**
« Un circuit de statuts : brouillon, à vérifier, validé par le chef, puis verrouillé. Seules les fiches validées comptent dans les indicateurs, et une fiche verrouillée ne bouge plus. Les prix sont figés au moment de la saisie, donc le manque à gagner calculé ne change pas rétroactivement. »

---

## B. Démarche / méthodologie

**Q6 — Quelle démarche avez-vous suivie pour concevoir l'outil ?**
« La même que dans mon mémoire : la démarche DMAIC — Définir, Mesurer, Analyser, Améliorer, Contrôler. L'application déroule ces cinq étapes : la saisie définit le problème, le TRS le mesure, le Pareto et l'Ishikawa l'analysent, les contre-mesures l'améliorent, et le verrouillage plus le suivi avant/après le contrôlent. »

**Q7 — En quoi l'application dépasse-t-elle un tableau de bord classique ?**
« Un tableau de bord affiche des chiffres. Le mien déroule une boucle d'amélioration continue complète : il ne dit pas seulement "le TRS est bas", il localise la machine et la cause, chiffre la perte en francs, propose une action et vérifie ensuite si elle a produit un effet. »

**Q8 — Comment avez-vous validé que l'outil est correct ?**
« En le calant sur les données réelles de mon mémoire. Les indicateurs de l'application reproduisent au chiffre près ceux du document : TRS 64 %, production 14,55 m³ par poste, rendement matière 31 %. Si l'outil et le mémoire disent la même chose, c'est que le calcul est juste. »

---

## C. Les indicateurs

**Q9 — Comment le TRS est-il calculé ?**
« TRS égale Disponibilité multipliée par Performance multipliée par Qualité. Dans mon cas : Disponibilité 79,9 %, Performance 92,5 %, Qualité 84,9 %, ce qui donne un TRS de 64 %. La Disponibilité vient des arrêts, la Performance du volume produit rapporté à la capacité, la Qualité de la part conforme. »

**Q10 — Votre TRS de 64 % dépasse votre hypothèse H3 (TRS < 60 %). Contradiction ?**
« H3 porte sur l'absence de système de mesure, pas sur un seuil précis. Le vrai problème n'est pas le niveau moyen mais la dispersion : mes postes vont de 8 % à 98 %. C'est cette irrégularité qui prouve le défaut de pilotage, et c'est exactement ce que l'outil corrige. 64 % reste par ailleurs sous la cible camerounaise de 60 %… pardon, au-dessus de 60 % mais loin d'une scierie optimisée. »
> ⚠️ Précision honnête : 64 % > 60 %. Dis plutôt : « le niveau moyen masque une forte irrégularité — c'est elle le vrai signal, et c'est ce que l'outil rend visible ».

**Q11 — D'où vient le rendement matière de 31 % ?**
« C'est le rapport entre le volume conforme sorti et le volume de bois entré, essence par essence. Le Bilinga, un bois dur, est le plus bas à 23,3 % ; l'Ayous, plus tendre, monte à 33,8 %. La dureté du bois pénalise le rendement. »

**Q12 — Comment l'application chiffre-t-elle le manque à gagner ?**
« Elle convertit les pertes de temps et de matière en francs, à partir du prix de chaque essence. Cela rend visible le coût de la non-performance et fait de la chaîne 4 un sujet de direction, plus seulement d'atelier. »

---

## D. Les données

**Q13 — Sont-ce de vraies données ?**
« Les indicateurs reproduisent les relevés terrain de mon mémoire : temps de marche, cadences chronométrées, et volumes débités issus des extractions Cuflink. L'application est paramétrable : prix, capacités et objectifs se changent en quelques secondes. »

**Q14 — D'où viennent les volumes en mètres cubes ?**
« Du point de comptage fixe situé avant la bicoupe, là où passe 100 % du bois. C'est le repère physique réel de la chaîne 4, la bicoupe étant la machine goulot. »

**Q15 — Pourquoi le Bilinga et pas l'Azobé ?**
« Le Bilinga est l'essence dure majoritaire de la période étudiée, contrats à l'appui. C'est elle qui illustre le mieux la contrainte matière, avec un rendement bas à 23,3 %. »

---

## E. Limites & critiques (à assumer)

**Q16 — Votre objectif de 25 m³ par poste, est-il fondé ?**
« Non, et c'est justement un de mes constats. C'est l'objectif affiché par la direction, mais il n'a pas de fondement technique démontré. L'outil le prend comme référence tout en montrant qu'il n'est atteint qu'à 58 %. »

**Q17 — Pourquoi trois postes dans l'application alors qu'on parle de deux ?**
« La chaîne tourne réellement en trois-huit sur les relevés. L'objectif officiel de 25 m³, lui, est calé sur un quart de huit heures. L'outil affiche la réalité des relevés sans contredire la référence. »

**Q18 — Le manque à gagner de l'app ne colle pas exactement à celui du mémoire.**
« Le mémoire chiffre en prix export FOB, l'application est paramétrée en prix marché local. Les deux sont du même ordre de grandeur — plusieurs centaines de millions par an — et on passe de l'un à l'autre en changeant les prix dans les paramètres. »

**Q19 — Quelles sont les limites de l'outil aujourd'hui ?**
« Il n'individualise pas encore la performance par opérateur, et il repose sur la qualité de la saisie humaine. Ce sont des évolutions identifiées, pas des impasses : le modèle de données les permet. »

---

## F. Apport & valeur

**Q20 — Qu'apporte concrètement l'application à CUF ?**
« Avant, la compilation de la performance était inexistante. Maintenant elle est automatique et immédiate : le chef voit son TRS, la cause d'arrêt dominante et le coût des pertes en un coup d'œil. L'outil transforme un savoir dispersé en décisions traçables. »

**Q21 — L'outil est-il réutilisable ailleurs ?**
« Oui. Toute la logique — TRS, Pareto, pertes en francs — est paramétrable. En changeant les essences, les capacités et les prix, il s'adapte à une autre chaîne ou à une autre scierie. »

**Q22 — Quelle est la cause d'arrêt la plus coûteuse ?**
« Le changement de lame domine le Pareto. C'est cohérent avec la règle de maintenance : lame changée toutes les deux heures en préventif, et immédiatement à chaque changement d'essence tendre vers dure. C'est le premier levier d'action. »

---

### Réflexe pour toute question à laquelle tu ne sais pas répondre
« C'est un point que l'outil permet justement d'objectiver ; dans l'état actuel de mes données, voici ce que je peux affirmer… » — puis ramène un chiffre que tu connais (TRS 64 %, 14,55 m³, rendement 31 %). Ne jamais inventer un chiffre.

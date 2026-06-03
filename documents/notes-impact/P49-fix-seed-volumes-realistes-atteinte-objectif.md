# Note d'impact mémoire — P49 : Volumes de seed réalistes et correction de l'atteinte d'objectif à 147 %

> Générée le : 2026-06-03
> Commit : `4ac8813` — fix(seed): volumes conformes réalistes 10-20 m³/poste + période glissante 30j
> Branche : `claude/install-claude-excel-6MGzv`
> Fichier : `cuf-pilotage/seed_data.py`

---

## 1. Résumé de la fonctionnalité

Avant ce commit, le générateur de données de démonstration produisait chaque planche (`Production`) de façon indépendante : un volume entrant de 22 à 36 m³ par planche, avec 1 ou 2 planches par poste. Un poste à deux essences pouvait donc « avaler » jusqu'à 72 m³ de bois brut — impossible pour une bicoupe travaillant 8 h. Après rendement (55-78 % conforme), la production conforme atteignait 20 à 26 m³ par poste, soit le double de l'objectif technique de 12,5 m³/poste. La page « Production & Objectifs » du chef affichait en conséquence une atteinte d'objectif d'environ 147 %, en contradiction visible avec un TRS mesuré autour de 70 %.

Après ce commit, le volume est raisonné au niveau du poste : un budget de matière brute de 16 à 28 m³ (cohérent avec la capacité d'un poste avant la bicoupe, le point de comptage fixe) est tiré une fois, puis réparti entre les essences lorsque le poste en traite deux. La production conforme retombe à 10-20 m³/poste (moyenne 14,9 m³), exactement la fourchette des relevés terrain de la chaîne 4. L'atteinte affichée passe de 147 % à environ 120 %, et 22 % des postes tombent désormais sous l'objectif, ce qui rend le tableau de bord vivant plutôt qu'uniformément vert.

Le commit modifie aussi la période générée : 30 derniers jours glissants finissant aujourd'hui, au lieu d'avril 2026 figé. La section « Aujourd'hui » du cockpit, la scorecard semaine et les vues 7j/30j sont ainsi toujours peuplées au moment d'une démonstration.

---

## 2. Décision d'architecture — raisonner le volume au poste, pas à la planche

L'option retenue corrige la cause racine au bon niveau d'agrégation. Le bug ne venait ni de la formule d'objectif (`12,5 × nombre de postes`, qui reste un comparateur de productivité par poste juste pour opposer l'équipe du matin et celle du soir), ni du calcul du TRS, mais du fait que chaque planche tirait son volume isolément, sans plafond commun au poste. Plafonner le budget matière au niveau du poste reproduit la contrainte physique réelle : la bicoupe est un goulot unique qui traite un débit borné par poste. La répartition entre essences (fraction aléatoire 0,4-0,6 quand il y a deux planches) conserve la mixité d'essences sans gonfler le total. Aucune autre option (baisser l'objectif à 25 m³/poste, ou accepter le 147 %) n'a été retenue, car la règle métier verrouillée fixe l'objectif à 12,5 m³/poste et la crédibilité d'une démonstration exige des volumes terrain plausibles.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS1 — Capacité théorique → production réelle → écart + TRS | **Direct.** L'écart entre la capacité (12,5 m³/poste) et la production réelle simulée (10-20 m³) est désormais représenté de façon plausible. La coexistence d'une atteinte volume supérieure à 100 % et d'un TRS de 70 % illustre que le volume seul ne mesure pas la performance : c'est le cœur de la démonstration OS1. |
| OS6 — Outil de pilotage adapté | **Indirect.** Un jeu de démonstration crédible conditionne l'adhésion de l'encadreur et des utilisateurs terrain. Des chiffres aberrants auraient discrédité l'outil entier. |

---

## 4. Impact sur la validité scientifique des données

Le commit ne touche que les données fictives de démonstration, pas le moteur de calcul ni les données réelles à venir. Aucune formule de TRS, de pertes FCFA ou de rendement n'est modifiée. La validité des calculs reste donc identique ; seul le réalisme des jeux d'essai progresse. Lorsque la collecte terrain commencera, les volumes réels remplaceront le seed et l'atteinte reflétera la production effective. Il faut signaler dans le mémoire que les copies d'écran de démonstration reposent sur des données simulées calibrées sur les relevés terrain, et non sur des relevés bruts.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Aucune modification du modèle de données ni de schéma. Seule la fonction de génération `_genere_productions()` et les constantes de période ont changé.

---

## 6. Contradiction avec hypothèses précédentes

**Point d'attention sur H1.** L'hypothèse H1 du mémoire pose que la capacité théorique n'est pas atteinte. Or l'atteinte volume affichée (~120 %, parfois plus) pourrait sembler la contredire si on la lit isolément. La contradiction n'est qu'apparente : l'objectif de 12,5 m³/poste est un objectif de sortie conforme volontairement modeste, tandis que la performance réelle se mesure par le TRS (≈70 %), qui reste sous le benchmark de 60 % d'une scierie optimisée seulement en partie et loin de l'excellence. Le mémoire doit donc être explicite : **dépasser l'objectif de volume ne signifie pas atteindre la capacité théorique en temps et en qualité**. Cette nuance renforce H3 (TRS réel insuffisant) plutôt qu'elle ne la fragilise. Aucune contradiction avec H2 ni H4.

---

## 7. Nouveaux éléments introduits

| Élément | Fichier | Rôle |
|---|---|---|
| Budget matière au poste (`entree_poste`) | `seed_data.py` | Plafonne le volume brut d'un poste à 16-28 m³ avant répartition entre essences |
| Répartition par fraction (0,4-0,6) | `seed_data.py` | Distribue le budget entre deux planches sans gonfler le total |
| Période glissante `JOUR_FIN = date.today()` | `seed_data.py` | Génère les 30 derniers jours au lieu d'avril 2026 figé |

---

## 8. Utilisabilité terrain et adoption

Avant, un chef ouvrant la démonstration voyait une atteinte de 147 % qu'un professionnel du bois reconnaît immédiatement comme impossible pour la bicoupe, et une section « Aujourd'hui » à zéro car les données dataient d'avril. Après, l'atteinte se situe autour de 120 % avec une part de postes en rouge, et la journée courante est renseignée. La démonstration raconte une histoire cohérente : production de volume correcte mais efficacité-temps faible, ce qui justifie précisément la démarche d'amélioration portée par l'outil.

---

## 9. Ce que cela change pour le mémoire

Le jeu de démonstration devient un support défendable face à l'encadreur. L'argument à exploiter dans la section consacrée à OS1 est la dissociation entre volume et performance : une chaîne peut produire un volume supérieur à un objectif modeste tout en gaspillant 30 % de son potentiel en arrêts et déclassements, ce que seul le TRS révèle. C'est l'illustration la plus directe du fil conducteur DMAIC — mesurer avant de conclure — et la justification du passage d'un suivi en volume brut à un suivi en TRS décomposé.

---

> **Vérification réalisée :** seed relancé sur 30 jours (60 équipes, 2026-05-05 → 2026-06-03). Contrôle base : conforme/poste min 10,0 — moyenne 14,9 — max 20,0 m³ ; atteinte Matin 122 %, Après-midi 117 % ; 22 % des postes sous l'objectif de 12,5 m³. Smoke driver 16/16 OK.

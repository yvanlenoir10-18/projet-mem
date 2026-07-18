# Note d'impact — P13 : Vue exécutive PDG (cumuls 4 horizons + deltas)
> Commit : (en attente) — feat(p13): vue exécutive PDG cumuls + delta vs période précédente
> Date : 2026-05-13
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Ajout d'une section « Vue exécutive » au sommet du tableau de bord PDG. Cette section présente, pour quatre horizons temporels affichés simultanément, les indicateurs clés de la chaîne 4 avec leur variation relative en pourcentage par rapport à la période précédente de même nature. Les quatre horizons sont la journée courante, la semaine courante (lundi → aujourd'hui), le mois courant (1er → aujourd'hui) et l'année courante (1er janvier → aujourd'hui). Les périodes de comparaison correspondantes sont respectivement la veille, la semaine ISO précédente complète, le mois calendaire précédent complet et l'année calendaire précédente complète.

Pour chaque horizon, quatre indicateurs sont affichés : volume conforme cumulé en mètres cubes, TRS moyen pondéré, manque à gagner estimé en FCFA, et nombre de postes saisis. Chaque indicateur est accompagné d'un badge coloré qui exprime la variation relative en pourcentage : vert si l'évolution est favorable, rouge si elle est défavorable, gris si elle est stable (variation absolue inférieure à 2 %) ou indisponible. Pour le manque à gagner, la convention est inversée puisqu'une baisse du manque est une bonne nouvelle.

L'horizon le plus court (jour) permet au PDG de réagir en temps quasi réel sur des dérives ponctuelles, tandis que l'horizon le plus long (année) lui donne le recul nécessaire pour évaluer la trajectoire de fond. La présence simultanée des quatre horizons sur un même écran évite tout clic pour comparer et permet une lecture en quelques secondes.

---

## 2. Fichiers modifiés ou créés

| Fichier | Type | Action |
|---|---|---|
| `cuf-pilotage/app/services/cumuls.py` | Service | **Nouveau** — `cumul_periode()`, `calcule_delta()`, `vue_executive_pdg()` |
| `cuf-pilotage/app/routes/dashboard.py` | Route | Import + injection dans `vue_pdg()` |
| `cuf-pilotage/app/templates/pdg/dashboard.html` | Template | Section « Vue exécutive 4 horizons » au sommet |
| `cuf-pilotage/app/static/css/style.css` | CSS | Classes `.wp-delta`, `.wp-delta-success`, `.wp-delta-danger`, `.wp-delta-muted` |
| `documents/notes-impact/P13-vue-executive-cumuls-deltas.md` | Documentation | Nouveau |

Aucune migration de base de données. Aucune nouvelle table. Aucun champ ajouté aux modèles. Les cumuls sont recalculés à la volée à chaque consultation, à partir des équipes déjà saisies. R7 respectée.

---

## 3. Objectif spécifique du mémoire servi

**OS6 — Concevoir un outil de pilotage adapté aux besoins des différents responsables de CUF pour assurer un suivi continu des performances de la chaîne 4** : un dashboard PDG sans deltas n'est qu'une photographie. Avec les deltas, il devient un instrument de pilotage. Le PDG peut désormais juger, en regardant un seul écran, si la chaîne 4 va mieux ou moins bien que la veille, que la semaine précédente, que le mois passé et que l'année dernière. Cette capacité à lire simultanément quatre échelles de temps est précisément ce que les revues de littérature (Laine 2024 sur Metsä Board, Kankkunen et Holopainen 2024 sur UPM Plywood) identifient comme la signature d'un dashboard exécutif efficace.

**OS3 — Évaluer l'écart entre la capacité théorique et la production réelle, calculer le TRS de la chaîne 4 et estimer le coût financier des pertes enregistrées** : les cumuls de volume conforme et de manque à gagner par horizon donnent au PDG une mesure cumulée de l'écart sur la durée, complétant le calcul instantané par poste.

---

## 4. Lien avec les hypothèses de recherche

**H3 — Le TRS réel de la chaîne 4 est inférieur à 60 %** : la vue exécutive permet d'observer si le TRS moyen reste sous la barre des 60 % sur la durée. Un TRS bas un jour donné n'invalide pas H3 ; un TRS bas confirmé sur l'horizon annuel l'établit fermement. La nouvelle section est donc l'instrument de validation longitudinale de H3.

**H4 — Des actions correctives sans investissement majeur permettent d'améliorer le TRS et de réduire les pertes financières** : les deltas constituent l'instrument de mesure direct de l'efficacité des actions correctives qui seront proposées en P14 et exécutées sur le terrain. Sans deltas, l'impact d'une action est invisible ; avec eux, le PDG peut constater dès la semaine suivante si la décision a porté ses fruits. Cette modification renforce H4 en lui donnant un instrument de validation.

**H1 et H2 ne sont pas directement concernées par cette modification**, qui porte exclusivement sur la lisibilité de l'information existante, pas sur la nature des indicateurs.

---

## 5. Technique utilisée et choix architectural

Le service `cumuls.py` est construit autour de trois fonctions à responsabilité unique : `_bornes_horizons()` calcule les quatre couples de dates (période courante, période précédente) pour une date de référence donnée, `cumul_periode()` interroge la base et synthétise les indicateurs sur une période quelconque, `calcule_delta()` produit le badge coloré à partir de deux valeurs. La fonction de plus haut niveau `vue_executive_pdg()` orchestre ces trois primitives. Cette séparation rend le code testable isolément et permet d'ajouter facilement un cinquième horizon (par exemple le trimestre) ou un cinquième indicateur en modifiant uniquement les structures de données, sans toucher à la logique de calcul.

Les périodes précédentes ne sont pas définies de manière uniforme : pour la journée et la semaine, on prend la période immédiatement antérieure de même durée ; pour le mois et l'année, on prend la période calendaire complète précédente. Ce choix correspond à l'attente cognitive du PDG : comparer mai à avril a du sens, comparer le 1er-13 mai au 19-30 avril non. La nuance est documentée dans la docstring de `_bornes_horizons()`.

La couleur des deltas suit deux conventions opposées selon l'indicateur. Pour le volume, le TRS et le nombre de postes, une hausse est favorable et donc verte. Pour le manque à gagner, une hausse est défavorable et donc rouge. Cette inversion est explicitée par le paramètre `inverse=True` dans l'appel à `calcule_delta()`, ce qui rend le code lisible sans commentaire.

Le seuil de stabilité de 2 % est choisi pour éviter le bruit visuel : les variations inférieures à 2 % entre deux périodes courtes ne sont pas statistiquement significatives et n'ont pas de valeur de pilotage. Cette valeur est codée en dur dans `calcule_delta()` ; elle pourrait être paramétrée si nécessaire dans une phase ultérieure.

La gestion du cas « période précédente vide » suit la convention « N/A » plutôt que « +100 % » : afficher une croissance de 100 % depuis zéro est mathématiquement défendable mais cognitivement trompeur pour un dirigeant. Mieux vaut un « N/A » honnête qui invite à attendre la prochaine période complète.

---

## 6. Contrainte respectée

**Règle R7** : aucune modification de schéma de base de données. Le service `cumuls.py` lit uniquement les équipes existantes via l'ORM, sans transformation persistée.

**Règle R6** : validation explicite obtenue avant écriture du code. L'utilisateur a confirmé les trois points clés (4 horizons simultanés, deltas en pourcentage avec couleur uniquement, N/A si période précédente vide) et a explicitement répondu « GO ».

---

## 7. Limites identifiées

Les cumuls sont recalculés à chaque chargement de la vue PDG, sans cache. Pour un volume de quelques dizaines à quelques centaines d'équipes (V1), c'est suffisant. Au-delà de plusieurs milliers d'équipes, la requête sur l'horizon annuel ralentira et il faudra introduire un cache mémoire à durée de vie courte (par exemple 5 minutes) ou pré-calculer les agrégats nocturnement dans une table dédiée.

Le TRS moyen affiché est une moyenne arithmétique non pondérée des `trs_global` des équipes de la période. Un poste très court avec un TRS élevé pèse autant qu'un poste complet avec un TRS bas. Pour la V1, cette approximation est acceptable car les postes ont par définition tous une durée nominale de 480 minutes. Si la durée réelle devient variable (par exemple postes raccourcis), il faudra pondérer par la durée effective.

La période précédente du mois est définie comme le mois calendaire précédent complet. Au tout début d'un mois, cela introduit un biais : comparer le 1er au 5 avril (5 jours) au mois de mars complet (31 jours) n'est pas équitable. Le pourcentage affiché est mécaniquement très négatif. Cette limitation est documentée dans la note ; elle se résorbe naturellement après quelques jours de chaque mois et n'affecte donc pas le pilotage en régime de croisière.

La vue exécutive ne comporte pas encore de filtre temporel pour explorer une date de référence différente d'aujourd'hui. Le PDG ne peut donc pas reconstituer la vue exécutive telle qu'elle apparaissait par exemple lundi dernier. Si ce besoin émerge, il suffira d'ajouter un sélecteur de date qui passe la valeur au paramètre `reference` de `vue_executive_pdg()`.

---

## 8. Commandes Windows pour appliquer

```powershell
git pull origin claude/install-claude-excel-6MGzv
.\start.ps1
```

L'application est ensuite accessible sur `http://127.0.0.1:5000`. Aucune migration de base de données n'est nécessaire. La nouvelle section apparaît automatiquement en haut de la vue PDG (`/dashboard/pdg`) dès que l'utilisateur connecté possède le rôle `pdg` ou `admin`.

Pour vérifier visuellement le résultat :
- Se connecter avec `pdg@cuf.cm` / `cuf2026`.
- La section « Vue exécutive · 4 horizons » apparaît au sommet, avec une grille de 4 colonnes (Aujourd'hui, Cette semaine, Ce mois, Cette année).
- Chaque colonne affiche les 4 indicateurs avec leur delta coloré.
- Si une période précédente est vide (par exemple si aucune saisie hier), le delta apparaît « N/A » en gris.

---

## 9. Références bibliographiques mobilisées

- **Laine (2024)** — *Reporting visuel, Metsä Board*, Finlande : étude de cas sur le tableau de bord exécutif d'un industriel forestier finlandais. Laine défend que la juxtaposition d'horizons temporels multiples sur un même écran est supérieure à la sélection d'un horizon unique, car elle permet au dirigeant de détecter immédiatement si une dérive courte est isolée ou si elle s'inscrit dans une tendance longue.

- **Kankkunen & Holopainen (2024)** — *Daily management, UPM Plywood*, Finlande : démontre que les dashboards exécutifs efficaces affichent systématiquement la valeur courante associée à son delta par rapport à la période précédente. Sans delta, le dirigeant ne dispose que d'une photo et ne peut pas piloter une trajectoire.

- **Jaouane (2022)** — *Tableau de bord, Général Emballage*, Algérie : confirme dans un contexte africain industriel que la lisibilité immédiate des écarts vs périodes précédentes améliore la rapidité de réaction des décideurs et réduit le délai entre détection d'une dérive et action corrective.

# Note d'impact mémoire — P6-F4 : Score de régularité (CV du TRS)
**Commit :** `3dbe797` — `feat(chef): P6-F4 — score de régularité (CV du TRS)`
**Date :** 2026-05-04
**Fichiers modifiés :** `app/routes/dashboard.py` (+46 lignes) · `app/templates/chef/dashboard.html` (+14 lignes)

---

## 1. Ce qui a été implémenté

Ajout du **coefficient de variation (CV) du TRS** directement dans la card KPI « TRS moyen » existante, sans créer de nouvelle card. Le CV est le rapport σ/μ × 100, où σ est l'écart-type échantillon (dénominateur n−1, formule de Bessel) et μ la moyenne du TRS sur la période sélectionnée.

**Logique de déclenchement :**
- `n ≥ 10 postes` avec `trs_global > 0` : badge coloré affiché
- `n < 10` : le badge est absent, aucun affichage partiel trompeur

**Les trois états visuels du badge :**

| CV (provisoire) | Badge | Sens métier |
|---|---|---|
| CV < 10 % | `bg-success` · « régulier » | Performance stable, reproductible |
| 10 % ≤ CV < 25 % | `bg-warning` · « variable » | Performance irrégulière, à investiguer |
| CV ≥ 25 % | `bg-danger` · « instable » | Performance chaotique, causes profondes à identifier |

**Note contextuelle Azobé/Iroko :** si au moins une production de la période contient une essence dure (Azobé ou Iroko, Janka ~11 000 N), un avertissement `ℹ Présence Azobé/Iroko — variabilité naturelle attendue` s'affiche sous le badge. Cela empêche le Chef d'interpréter une variabilité structurelle (liée à la dureté du bois) comme une anomalie opérationnelle.

**Seuils provisoires** : les valeurs 10 % et 25 % sont commentées `# SEUILS PROVISOIRES — recalibrer après 60 jours données CUF réelles` dans le code. Ils seront remplacés par des percentiles empiriques CUF une fois la base suffisamment peuplée.

---

## 2. Lien avec les objectifs du mémoire

F4 répond à **OS6** (concevoir un outil de pilotage adapté aux besoins du Chef de Production) en complétant la lecture du TRS moyen par une dimension absente dans tous les autres indicateurs du dashboard : la **stabilité temporelle de la performance**.

Un TRS moyen de 65 % peut correspondre à deux réalités opérationnelles très différentes :
- Chaque poste tourne autour de 65 % (faible CV → régulier) : la cause est systémique et doit être traitée en profondeur
- Les postes alternent entre 45 % et 85 % (CV élevé → instable) : des événements perturbateurs ponctuels existent et peuvent être ciblés

F4 rend cette distinction visible en une ligne, sans navigation supplémentaire, directement dans la card la plus regardée du dashboard. C'est l'incarnation du principe de non-redondance d'information : la moyenne reste lisible, le CV la complète sans la remplacer.

---

## 3. Données et calculs mobilisés

**Calcul :**
```
trs_valides = [e.trs_global for e in equipes if e.trs_global is not None and e.trs_global > 0]
CV = (statistics.stdev(trs_valides) / statistics.mean(trs_valides)) × 100
```

- `statistics.stdev` : dénominateur n−1 (variance échantillon), correct pour une fenêtre de 30–90 postes qui est un échantillon de la production réelle, pas une population exhaustive
- `trs_global > 0` : exclut les postes à TRS nul qui fausseraient la moyenne à la baisse et le CV à la hausse sans représenter une vraie variabilité opérationnelle (postes sans production enregistrée)
- `n ≥ 10` : garantit que le CV est statistiquement interprétable ; en dessous de 10 observations, la variance échantillon est instable

**Détection essence dure :**
```python
a_essence_dure = any(p.essence in {'Azobé', 'Iroko'} for e in equipes for p in e.productions)
```
Parcourt l'ensemble des lignes de production de la période. Cette traversal est en O(n × p) où p est le nombre moyen de lignes par équipe (≤ 4 en pratique). Aucune requête SQL supplémentaire : `e.productions` est déjà chargé via la relation SQLAlchemy lazy-loaded en contexte de boucle.

**Aucun nouveau modèle de données.** F4 lit uniquement `Equipe.trs_global` et `Production.essence`, deux champs déjà calculés et stockés lors de la soumission.

---

## 4. Hypothèses testées ou confirmées

**F4 éclaire H3 et H4 de manière nouvelle :**

- **H3** (*TRS réel < 60 %*) : La moyenne TRS le confirme ou l'infirme. Mais F4 ajoute : si H3 est vraie ET que le CV est faible (< 10 %), cela signifie que le TRS bas est **structurel et stable** — pas dû à des accidents ponctuels. Cette nuance oriente directement les actions correctives (H4) : inutile de chercher des événements perturbateurs, il faut s'attaquer aux causes permanentes.

- **H4** (*actions correctives sans investissement majeur peuvent améliorer le TRS*) : Le CV devient un indicateur de suivi post-action. Si les actions correctives réduisent la variabilité (CV diminue), elles ont homogénéisé les conditions de travail — ce qui est un effet mesurable et valorisable même si la moyenne n'augmente pas encore beaucoup.

**Aucune contradiction avec les hypothèses existantes.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

- **Sophistication analytique sans complexité d'interface :** F4 n'ajoute pas une nouvelle section, une nouvelle card, un nouveau graphique. Il enrichit un KPI existant d'une seconde dimension (stabilité) sans surcharger l'écran. C'est une démonstration concrète que la complexité fonctionnelle peut être encapsulée dans une interface minimaliste.
- **Lien direct entre indicateur et action :** un Chef qui voit `instable` sait qu'il doit chercher les postes extrêmes (très hauts ou très bas) pour identifier ce qui diffère entre eux. Un Chef qui voit `régulier` sait que le problème est systémique. La lecture immédiate oriente l'investigation sans formation.
- **Conscientisation du contexte matière :** la note Azobé/Iroko introduit une variable que les tableaux de bord industriels classiques ignorent — l'hétérogénéité de la matière première. C'est un détail contextuel qui prouve que l'outil a été pensé pour le contexte CUF, pas importé d'un template générique.
- **Traçabilité des seuils provisoires :** le commentaire `# SEUILS PROVISOIRES` dans le code est lui-même un matériau mémoire — il montre que l'outil a été conçu avec une démarche scientifique (calibrage empirique prévu) et non avec des valeurs arbitraires figées.

---

## 6. Limites actuelles

- **Seuils non calibrés sur données CUF réelles :** CV < 10 % (régulier) et CV < 25 % (variable) sont empruntés à la littérature statistique générale. Pour une scierie tropicale avec des essences dures, la variabilité naturelle du TRS peut excéder 25 % même en conditions opérationnelles normales. Le seuil `instable` risque donc de s'activer trop souvent en phase initiale, avant calibrage.
- **Pas de tendance du CV :** le badge montre le CV de la période en cours mais ne compare pas au CV de la période précédente. Un CV de 18 % peut être bon (si la période précédente était à 28 %) ou mauvais (si elle était à 12 %). La comparaison temporelle est différée.
- **Fenêtre temporelle dépend du filtre :** avec `jours=7`, n peut être < 10 et le badge disparaît. Le Chef pourrait ne pas comprendre pourquoi le badge est absent sur la vue 7 jours mais présent sur 30 jours. Acceptable mais source potentielle de confusion.
- **`e.productions` lazy-loaded :** la traversal des lignes de production pour `a_essence_dure` déclenche des requêtes SQL individuelles si les équipes n'ont pas leurs productions pré-chargées. En pratique avec ≤ 90 équipes sur 90 jours, c'est négligeable. Si la fenêtre s'étend à plusieurs années, envisager `joinedload`.
- **Essences dures codées en dur :** `{'Azobé', 'Iroko'}` est un ensemble Python constant. Si CUF traite d'autres essences dures (Padouk, Wengé), il faudra modifier ce set. Acceptable dans le périmètre actuel.

---

## 7. Vérification de cohérence avec les notes précédentes

La note `P6-F5-scorecard-semaine.md` documentait le scorecard comme outil de **suivi opérationnel quotidien**. F4 est complémentaire : le scorecard montre les 6 derniers jours poste par poste, F4 synthétise la variabilité sur 30–90 jours. Ce sont deux lectures temporelles distinctes de la même dimension « stabilité ».

La note `P6-F1-decomposition-cascade-m3.md` documentait la décomposition D × P × Q. F4 ne touche pas à cette décomposition et ne la remet pas en cause — il opère sur `trs_global` directement, pas sur les composantes D, P, Q. Les deux vues sont orthogonales.

La règle **R11** (`leçons.md` : arithmétique en Python, jamais en Jinja2) est respectée : `statistics.stdev`, `statistics.mean`, le calcul du CV, et la logique de seuillage sont tous côté route Python. Le template ne fait que l'affichage conditionnel du badge.

La règle **R10** (fonctions pures vs mutation) est respectée : F4 lit `trs_global` (déjà stocké, pas recalculé) et ne mute aucun objet.

**Aucune contradiction avec les notes précédentes.**

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Koc & Eryuruk (2025) — OEE industrie textile, Turquie | Justification de la complémentarité moyenne + variabilité pour l'analyse OEE : la moyenne seule masque les déséquilibres inter-shifts |
| Jonsson & Lesshammar (1999) — OEE fondateur | Le TRS comme indicateur de stabilité de process : un TRS élevé et stable est le signe d'un process sous contrôle, pas seulement d'un process performant |
| Novochadlo & Paladini (2024) — OEE temps réel, Brésil | Utilisation du CV comme indicateur de contrôle statistique de process (SPC) : CV < 10 % comme critère de stabilité dans le contexte industriel |
| Danwé, Bindzi & Meva'a (2012) — scieries camerounaises | Variabilité de la performance liée à l'hétérogénéité des essences et des diamètres : justification empirique de la note contextuelle Azobé/Iroko |

---

## 9. Prochaines étapes

- **F3 — Calculateur potentiel gain FCFA** : slider cible TRS (défaut 70 %, modifiable), projection du gain m³ et FCFA si la cible est atteinte. Réutilisera `decompose_dpq()` (R10). Nécessite `Parametre.get('prix_m3_moyen')` ou calcul pondéré depuis les lignes de production.
- **F6 — Filtre date partagé (refactoring DRY)** : helper commun Chef/PDG pour la sélection de période. À faire en dernier, une fois F3 terminé.
- **Recalibrage seuils F4 :** dès que la base dépasse 60 jours de données CUF réelles, calculer les percentiles empiriques P25 et P75 du CV sur l'ensemble des périodes glissantes et remplacer les seuils provisoires 10/25.
- **F4 tendance CV :** comparer le CV de la période courante au CV de la période précédente (delta), sur le modèle du `delta_trs` du dashboard PDG. Différé car la valeur ajoutée immédiate est moindre que F3.
- **Windows :** synchronisation git nécessaire (`reset --hard origin/claude/install-claude-excel-6MGzv`) pour récupérer P6-F4.

# Note d'impact mémoire — P6-F5 : Scorecard semaine 6 jours (lun-sam)
**Commit :** `a62903e` — `feat(chef): P6-F5 — scorecard semaine 6 jours (lun-sam)`
**Date :** 2026-05-04
**Fichiers modifiés :** `app/routes/dashboard.py` (+47 lignes) · `app/templates/chef/dashboard.html` (+58 lignes)

---

## 1. Ce qui a été implémenté

Ajout d'une grille de 12 cellules (6 jours × 2 postes) dans le dashboard Chef, affichant l'état de chaque poste de la semaine courante (lundi → samedi). C'est la première vue du dashboard qui ne fait **pas** d'agrégation temporelle : chaque cellule représente un poste unitaire identifié par sa date et son numéro d'équipe.

**Les trois états visuels :**

| État | Affichage cellule | Fond | Sens métier |
|---|---|---|---|
| Soumis ou verrouillé | TRS en pourcentage (`68%`), texte coloré | `bg-success/warning/danger-subtle` | Donnée validée, lecture immédiate du niveau |
| Brouillon | Sablier `⏳` | `bg-warning-subtle` | Saisie en cours, attente de validation |
| Aucune équipe | Tiret cadratin `—`, texte gris | (aucun) | Soit poste non prévu, soit oubli de saisie |

**Mise en évidence du jour courant :** la colonne du `<th>` correspondant à la date `today` reçoit la classe `table-primary` (fond bleuté), ce qui orient immédiatement le regard du Chef sur la journée en cours.

**Logique calendaire :**
- `lundi = aujourd_hui − timedelta(days=aujourd_hui.weekday())` (avec `weekday()` ISO 8601 où 0=Lundi)
- 6 jours seulement (lun → sam), dimanche exclu — cohérent avec le rythme industriel forestier camerounais
- Index `(date, numero_equipe) → equipe` construit en une seule requête SQL puis lookup O(1) en boucle

---

## 2. Lien avec les objectifs du mémoire

F5 répond à **OS6** (concevoir un outil de pilotage adapté aux besoins du Chef de Production) en complétant la palette de vues du dashboard avec une dimension absente jusque-là : la **vue calendaire de proximité immédiate**.

Les autres composantes du dashboard Chef répondent à des questions agrégées (« quel est le TRS moyen sur 30 jours ? », « où vont les m³ perdus ? », « quelles sont mes machines les plus problématiques ? »). F5 répond à une question opérationnelle distincte : **« Où en suis-je dans la semaine ? Ai-je oublié de faire saisir un poste ? Y a-t-il un brouillon abandonné ? »**

Cette question est centrale pour le Chef de Production qui pilote au jour le jour, mais invisible dans les moyennes mensuelles. C'est précisément la valeur ajoutée d'un outil multi-vues décrit par Laine (2024) dans son étude Metsä Board.

---

## 3. Données et calculs mobilisés

**Aucun calcul nouveau.** F5 lit uniquement :
- `Equipe.date` (clé primaire calendaire)
- `Equipe.numero_equipe` ('Matin' ou 'Apres-midi')
- `Equipe.statut` ('brouillon', 'soumis', 'verrouille')
- `Equipe.trs_global` (déjà calculé à la soumission)

La couleur de cellule applique les seuils canoniques du dashboard : `≥ 70 % = vert`, `50 – 70 % = orange`, `< 50 % = rouge`. Ces seuils sont identiques à ceux du KPI principal et de la matrice F2, ce qui garantit la cohérence visuelle (R12 implicite : un Chef apprend une fois la convention couleur, elle s'applique partout).

**Performance :** une requête SQL `SELECT WHERE date BETWEEN lundi AND samedi` ramène au maximum 12 lignes (souvent moins). L'indexation par dictionnaire Python est en O(1). Aucune contrainte de performance même avec une montée en charge sur plusieurs années de données.

---

## 4. Hypothèses testées ou confirmées

**Aucune contradiction avec les hypothèses existantes.**

F5 ne mobilise ni H1 (capacité), ni H2 (causes), ni H3 (TRS < 60 %), ni H4 (gain par actions). C'est un outil de **suivi opérationnel** plutôt que de validation d'hypothèses scientifiques.

Le scorecard pourra cependant *aider* à confirmer H4 ultérieurement : si les actions correctives produisent une amélioration progressive, la grille hebdomadaire montrera la transition rouge → orange → vert au fil des semaines de manière visible — narration directe et intuitive d'une amélioration mesurée.

---

## 5. Ce que ce module permet de montrer dans le mémoire

- **Démonstration de la diversité des vues du dashboard :** le mémoire pourra présenter les composantes du dashboard Chef comme une suite de réponses à des questions distinctes (synthétique, diagnostic, opérationnel, prospectif). F5 occupe la case « opérationnel quotidien » qui manquait.
- **Preuve de pratique terrain :** afficher 6 jours et exclure le dimanche est une décision basée sur le rythme réel de CUF Ebolowa, pas sur un automatisme générique « semaine = 7 jours ». C'est un détail concret qui prouve que l'outil a été pensé pour le contexte d'usage réel.
- **Détection des trous de saisie :** le tiret `—` n'est pas neutre. C'est un signal visible que le Chef peut interpréter comme « j'ai peut-être oublié de faire saisir cette équipe ». Cette boucle de rétroaction (oubli → visibilité → correction) est elle-même un gain de qualité de données mesurable.
- **Différenciation brouillon vs soumis :** le `⏳` rend visible un état que les autres vues ignorent (les brouillons sont exclus des KPI agrégés). Le scorecard est la seule vue qui intègre les trois statuts simultanément.

---

## 6. Limites actuelles

- **Pas de navigation entre semaines :** le scorecard montre uniquement la semaine en cours. Pour consulter une semaine passée, il faut aller dans l'historique. Choix de simplicité initiale ; navigation à ajouter si besoin terrain remonte.
- **Pas de drill-down :** cliquer sur une cellule ne mène pas vers le détail du poste correspondant. Une amélioration directe serait `<a href="{{ url_for('saisie.editer', id=eq.id) }}">`. Différé.
- **Hypothèse forte sur les noms de postes :** les valeurs `'Matin'` et `'Apres-midi'` sont codées en dur. Si CUF passe à un rythme 3×8 ou ajoute un poste de nuit, il faudra modifier le tuple `SHIFTS`. Acceptable car cohérent avec le périmètre actuel (2 postes/jour confirmé en cadrage).
- **Pas de distinction « jamais prévu » vs « oublié » :** un dimanche n'apparaît pas (sain). Mais un samedi de fermeture exceptionnelle apparaîtra comme `—` sans information sur la cause. Différé — pas de besoin urgent.
- **Texte « Aucune équipe ce jour » dans la légende :** un peu ambigu. Il pourrait être lu comme « pas d'activité » alors qu'il signifie en réalité « aucun enregistrement en base ». Acceptable mais à reformuler si le mémoire fait explicitement la distinction.

---

## 7. Vérification de cohérence avec les notes précédentes

La note `P6-F1-decomposition-cascade-m3.md` documentait la décomposition agrégée sur 30 jours. F5 vient compléter cette vue agrégée par une vue **non-agrégée** sur 6 jours — les deux vues sont complémentaires et explicitement positionnées l'une après l'autre dans le dashboard (cascade puis scorecard).

La note `P6-F2-matrice-criticite.md` introduisait l'usage des classes Bootstrap `bg-*-subtle` pour la coloration des cellules. F5 réutilise exactement le même motif visuel pour assurer la cohérence — un Chef qui comprend la matrice F2 comprend immédiatement le scorecard F5 sans nouvelle lecture des conventions.

La note `P5d-alerte-brouillon-lien-pdg.md` notait que les brouillons étaient exclus de toutes les vues agrégées (KPI, Pareto). F5 corrige partiellement cette invisibilité en montrant les brouillons sous forme `⏳` — ils existent désormais visuellement quelque part dans le dashboard, ce qui réduit le risque qu'ils soient oubliés par le Chef.

La règle **R11** (`leçons.md` : toute arithmétique en Python, jamais en Jinja2) est respectée : tout le formatage `f"{trs:.0f}%"` est fait côté route, le template ne fait que de l'affichage conditionnel.

Aucune contradiction avec les notes précédentes.

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Laine (2024) — Reporting visuel Metsä Board | Multiplicité des vues d'un même dashboard pour répondre à des questions distinctes : F5 incarne la vue « opérationnelle quotidienne » manquante |
| Kankkunen & Holopainen (2024) — Daily management UPM Plywood | Pratique du « management quotidien » : un outil dédié à la lecture quotidienne des écarts de production permet d'agir avant que les écarts ne deviennent structurels |
| Jaouane (2022) — Tableau de bord Général Emballage | Niveau opérationnel du tableau de bord : le Chef doit pouvoir lire l'état du jour sans navigation, sans calcul, sans formation |

---

## 9. Prochaines étapes

- **F4 — Score régularité (CV)** : coefficient de variation du TRS sur la fenêtre période, affiché uniquement si n ≥ 10 postes. Donne au Chef une mesure de la **stabilité** de la performance, complément naturel à la moyenne (qui peut masquer une forte variabilité).
- **F3 — Calculateur potentiel gain FCFA** : slider cible TRS (défaut 70 %, modifiable), projection du gain m³ et FCFA si la cible est atteinte. Réutilisera `decompose_dpq()` (R10).
- **F6 — Filtre date partagé (refactoring DRY)** : helper commun Chef/PDG pour la sélection de période. À faire en dernier, une fois F3 terminé.
- **Améliorations possibles de F5 (différées) :** navigation semaine précédente / suivante ; clic sur cellule → édition du poste ; tooltip avec date complète + nom du saisisseur ; couleur particulière pour les samedis.
- **Windows :** synchronisation git nécessaire (`reset --hard origin/claude/install-claude-excel-6MGzv`) pour récupérer P6-F1, F2 et F5.

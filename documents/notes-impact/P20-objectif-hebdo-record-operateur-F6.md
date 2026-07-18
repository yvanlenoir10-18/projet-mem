# Note d'impact mémoire — P20 : Objectif hebdomadaire de régularité + record personnel (F6/F6b)

> Générée le : 2026-05-27
> Commit : `6a8d9f0` — feat(operateur): objectif hebdomadaire de régularité + record personnel (F6/F6b)
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `__init__.py`, `saisie.py`, `_progression.html`, `style.css`

---

## 1. Résumé de la fonctionnalité

Deux leviers de motivation greffés sur le composant de progression partagé introduit au P17 (F1), livrés ensemble car ils partagent le même helper (`_stats_operateur`) et le même partial (`_progression.html`).

**F6 — Objectif hebdomadaire de régularité.** Une barre de progression « X / Y postes saisis cette semaine » s'affiche dans le bloc de progression (accueil + historique). Elle mesure la **régularité de collecte** (nombre de postes effectivement soumis depuis le lundi), pas la performance. L'objectif est configurable en base (`objectif_postes_semaine`, défaut 5). Trois états : aucun poste, objectif partiel (« encore N postes »), objectif atteint (barre verte + message positif).

**F6b — Record personnel.** Un bandeau « Nouveau record personnel : XX% ! » apparaît lorsque le dernier poste soumis par l'opérateur établit strictement son meilleur TRS de tous les temps (à partir de 2 postes). Le bandeau est calculé à la volée, sans état persistant : il disparaît dès qu'un poste ultérieur au TRS inférieur est soumis.

---

## 2. Décision d'architecture — extension du composant existant, pas de duplication

Les deux features étendent les trois mêmes niveaux que F1 :

| Niveau | Élément | Ajout F6/F6b |
|---|---|---|
| Python | `_stats_operateur(user_id)` | +6 clés : `postes_semaine`, `objectif_hebdo`, `objectif_pct`, `objectif_atteint`, `record_battu`, `record_trs`. |
| Template | `_progression.html` | Bandeau record (après l'en-tête), barre hebdomadaire (après les métriques). |
| CSS | `.wp-progress-record`, `.wp-progress-week*` | Bandeau doré, barre de progression mobile-first. |

Comme le composant est partagé entre l'accueil et l'historique, les deux nouveautés apparaissent automatiquement aux deux endroits, sans copier-coller. C'est le dividende de la factorisation décidée à F1.

**Décision sur le record sans état persistant :** plutôt que de créer une table « records » (qui violerait R7), le record est dérivé des données existantes. La condition est : le poste le plus récent (par date puis création) porte le TRS maximal, et ce maximal est strictement supérieur à tous les autres. Cela évite toute écriture et reste exact.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS2 — Mesurer la production réelle via collecte terrain | **Direct (F6).** L'objectif hebdomadaire encourage explicitement la régularité de saisie. Plus de postes collectés = meilleure couverture = données plus représentatives. |
| OS6 — Concevoir un outil de pilotage adapté | **Direct.** La boucle de rétroaction (record, objectif) fait de l'accueil opérateur un poste de pilotage personnel motivant, conforme au volet « vue opérateur » du tableau de bord différencié. |

---

## 4. Impact sur la validité scientifique des données — point central

**L'objectif porte sur la régularité, jamais sur la performance.** C'est la décision de conception la plus importante de F6.

Un objectif chiffré sur le TRS (« atteignez 65 % cette semaine ») aurait créé une incitation directe à gonfler les volumes pour atteindre la cible — exactement le biais que l'hypothèse H3 (TRS réel < 60 %) doit éviter. En faisant porter l'objectif sur le **nombre de postes saisis**, F6 récompense l'acte de collecte, pas son résultat. Un opérateur dont tous les postes affichent un TRS de 30 % atteindra son objectif hebdomadaire aussi bien qu'un autre à 80 %, du moment qu'il saisit régulièrement. La donnée mesurée reste donc non biaisée.

**Le record (F6b) célèbre un fait passé, sans pression prospective.** Le bandeau ne dit pas « battez votre record » avant la saisie ; il constate « vous avez battu votre record » après coup, sur la base d'un TRS déjà calculé à partir de volumes déjà saisis. Il n'intervient à aucun moment dans le processus de mesure. De plus, le record reste une métrique strictement personnelle (jamais un classement entre opérateurs), conformément à la posture anti-classement actée au P17.

Aucun chiffre n'est inventé : `postes_semaine`, `record_trs` et l'objectif proviennent tous de la base (`Equipe` filtré par statut soumis, `Parametre`).

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. F6/F6b n'ajoutent aucune table ni migration. La seule structure persistée est une ligne `Parametre` (`objectif_postes_semaine`). Le compteur hebdomadaire et le record sont calculés à la volée depuis `Equipe`.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.**

- **H1** (capacité théorique < 25 m³) : non concernée.
- **H2** (pertes organisationnelles) : non concernée directement ; soutenue indirectement par une meilleure couverture de collecte.
- **H3** (TRS réel < 60 %) : **activement protégée.** L'objectif hebdomadaire ne porte volontairement pas sur le TRS (voir section 4). Le record n'agit qu'après la mesure. Aucune incitation à gonfler les volumes n'est introduite.
- **H4** (actions sans investissement majeur) : **cohérente et renforcée.** F6/F6b sont des améliorations ergonomiques à coût nul (ni équipement, ni table), exactement le type d'action peu coûteuse que H4 postule comme efficace pour l'adoption.

**Point d'attention — valeur de l'objectif :** la cible de 5 postes/semaine est provisoire et configurable. Elle devra être calibrée selon le rythme réel de saisie observé sur le terrain (un opérateur saisit-il un ou deux postes par jour ?). Une cible irréaliste démotiverait ; ce paramètre est donc à ajuster après les premières semaines de collecte.

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| Clé `objectif_postes_semaine` | `__init__.py` (seed idempotent) | Cible hebdomadaire de régularité, administrable en base (défaut 5). |
| +6 champs dans `_stats_operateur` | `saisie.py` | `postes_semaine` (lundi→aujourd'hui), `objectif_hebdo`, `objectif_pct` (borné à 100), `objectif_atteint`, `record_battu`, `record_trs`. |
| Bandeau `.wp-progress-record` | `_progression.html` / `style.css` | Célébration dorée du record, affichée si `record_battu`. |
| Barre `.wp-progress-week*` | `_progression.html` / `style.css` | Progression hebdomadaire, passe au vert (`is-done`) à l'objectif atteint. |

---

## 8. Utilisabilité terrain et adoption

1. **Objectif lisible** — « 3 / 5 postes » + barre visuelle : compréhension immédiate de l'avancement, sans calcul mental.
2. **Cadrage positif** — un état vide affiche « une fiche par jour suffit à nourrir l'analyse » plutôt qu'un reproche ; l'objectif atteint félicite.
3. **Récompense émotionnelle** — le bandeau record est un signal de fierté ponctuel, reconnu comme moteur d'engagement durable dans les boucles de rétroaction terrain.
4. **Cohérence visuelle** — réutilise les variables Canopée (`--wp-leaf`, `--wp-emerald`, `--wp-ochre`) et le composant responsive existant ; aucune rupture de style.

Ancrage littérature : Kankkunen & Holopainen (2024) — le tableau de bord quotidien doit donner un sentiment de progression ; Mncwango & Mdunge (2025) — les boucles de rétroaction rapides augmentent l'engagement des opérateurs.

---

## 9. Ce que cela change pour le mémoire

| Section du mémoire | Mise à jour requise |
|---|---|
| OS2 — Adoption de l'outil de collecte | Citer l'objectif hebdomadaire de régularité comme mécanisme d'incitation à la saisie continue, distinct de toute incitation à la performance. |
| OS6 — Vue opérateur | Compléter la description du poste de pilotage personnel : action immédiate (F1), progression (F1), objectif de régularité (F6), record personnel (F6b). |
| Méthodologie — fiabilité des données | Documenter explicitement le choix d'un objectif de régularité (et non de TRS) comme garde-fou méthodologique contre le biais de gonflement des volumes. |
| Conclusion / discussion | Présenter la séparation « récompenser la collecte, jamais la performance mesurée » comme une décision de conception fondée, cohérente avec la posture anti-classement. |
| Limite à signaler | La cible de 5 postes/semaine est provisoire ; à calibrer sur le rythme réel observé. |

---

> **Vérification réalisée :** redémarrage de l'app (paramètre `objectif_postes_semaine=5` confirmé en base). Helper `_stats_operateur` testé directement : les 6 nouveaux champs se calculent (postes_semaine, objectif, record). Rendu vérifié sur `/saisie/accueil` en rôle opérateur (compte de test basculé puis **restauré en admin**) : barre « 0 / 5 postes », largeur 0 %, message semaine vide corrects. États « objectif atteint » et « record battu » vérifiés par rendu du composant en isolation avec dict synthétique (bandeau record + « 92% », classe `is-done`, message de félicitation, pluralisation « encore 3 postes », largeur 40 %) — tous conformes. Vérification navigateur impossible (Chromium non lançable dans cet environnement).

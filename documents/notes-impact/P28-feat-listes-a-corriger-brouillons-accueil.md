# Note d'impact mémoire — P28 : Listes complètes À corriger et Brouillons sur l'accueil opérateur

> Générée le : 2026-05-29
> Commit : `798d8b9` — feat(saisie): listes complètes À corriger et Brouillons sur l'accueil opérateur
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `accueil_operateur.html`, `style.css`

---

## 1. Résumé de la fonctionnalité

Avant ce commit, les tuiles "À corriger" et "Brouillons" sur l'accueil opérateur naviguaient directement vers la **première** fiche de la liste (`modifier_equipe(liste[0].id)`). Si un opérateur avait 7 brouillons, il ne pouvait accéder qu'au plus récent depuis l'accueil — les 6 autres restaient invisibles sans aller dans l'historique.

**Après ce commit :**
- La tuile "À corriger" pointe vers `#a-corriger` (ancre HTML)
- La tuile "Brouillons" pointe vers `#brouillons` (ancre HTML)
- Deux sections conditionnelles s'affichent entre la grille de tuiles et "Dernières fiches" :
  - **"À corriger (N)"** avec bord gauche terracotta — liste toutes les fiches `a_corriger` avec le message chef tronqué, chaque ligne cliquable vers `modifier_equipe` avec ancre `#correction_cible` si définie
  - **"Brouillons (N)"** — liste tous les brouillons, chaque ligne cliquable vers `modifier_equipe`
- Les sections sont **conditionnelles** : si la liste est vide, la section n'est pas rendue (zéro bruit visuel)

Aucune nouvelle route, aucun nouveau template. Changement purement template + CSS minimal.

---

## 2. Décision d'architecture — sections ancrées vs pages dédiées

**Option retenue : sections inline avec ancres HTML** (Option B).
La page accueil opérateur est conçue "action-first" : tout ce dont l'opérateur a besoin est sur un seul écran. Ajouter des pages dédiées (`/saisie/brouillons`, `/saisie/a-corriger`) aurait créé deux nouvelles routes + deux nouveaux templates pour un gain nul sur mobile — la navigation supplémentaire est une friction. Le fragment `#anchor` est un mécanisme HTML natif, sans JavaScript, compatible avec tous les navigateurs et les tablettes terrain.

`scroll-margin-top: 16px` sur `.wp-operator-panel` garantit que le scroll-to-anchor ne cache pas le haut de la section derrière la navbar mobile.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS2 — Collecte terrain | **Direct.** Un opérateur avec plusieurs brouillons ou fiches à corriger peut maintenant les retrouver toutes sans navigation supplémentaire. Réduction du risque d'oubli = données plus complètes. |
| OS6 — Outil de pilotage adapté | **Direct.** Le flux de correction (chef renvoie → opérateur corrige) est maintenant entièrement visible depuis l'accueil, sans passer par l'historique. |

---

## 4. Impact sur la validité scientifique des données

Indirect mais réel : une fiche en `brouillon` qui reste oubliée ne contribue pas aux calculs TRS (les brouillons ne sont pas inclus dans les agrégats). En rendant tous les brouillons visibles depuis l'accueil, on réduit le risque de "données orphelines" non soumises.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Aucune modification du modèle de données.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.**

---

## 7. Nouveaux éléments introduits

| Élément | Fichier | Rôle |
|---|---|---|
| Section `#a-corriger` | `accueil_operateur.html` | Liste complète des fiches à_corriger, conditionnelle, avec message chef |
| Section `#brouillons` | `accueil_operateur.html` | Liste complète des brouillons, conditionnelle |
| `.wp-operator-panel-alert` | `style.css` | Bord gauche terracotta + titre rouge pour la section À corriger |
| `scroll-margin-top: 16px` | `style.css` | Évite que l'ancre soit masquée par la navbar au scroll |

---

## 8. Utilisabilité terrain et adoption

- **Avant :** opérateur avec 7 brouillons → peut uniquement accéder au 1er depuis l'accueil. Pour les autres : historique → chercher manuellement.
- **Après :** accueil → scroll vers "Brouillons (7)" → clic sur n'importe quelle fiche. Même logique pour "À corriger (N)".
- **Cas zéro :** si aucun brouillon ni aucune fiche à corriger, les sections n'apparaissent pas → l'accueil reste propre.

---

## 9. Ce que cela change pour le mémoire

Renforce OS6 : l'accueil opérateur est maintenant un vrai tableau de bord de tâches, pas juste une page de navigation. Argument à citer dans la section "adéquation de l'outil aux besoins terrain" : l'opérateur n'a pas à mémoriser l'état de ses fiches — l'interface le lui rappelle et lui donne accès directement.

---

> **Vérification réalisée :** Screenshot Playwright de l'accueil avec 9 brouillons — section "BROUILLONS (9)" visible sous la grille, chaque ligne cliquable. Tuile "À corriger" affiche "✓ Tout est à jour" (section masquée correctement). Smoke driver 16/16 OK.

# Note d'impact mémoire — P24 : Bugfix guillemets typographiques (saisie opérateur bloquée)

> Générée le : 2026-05-27
> Commit : `5593680` — fix(saisie): remplace les guillemets typographiques qui cassaient tout le JS
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `formulaire.html`

---

## 1. Résumé de la fonctionnalité

Correction d'un bug critique qui rendait **toute saisie impossible** côté opérateur. Le code JavaScript de F4 (poka-yoke volume) contenait des guillemets typographiques courbes (`‘` `’`, U+2018/U+2019) au lieu d'apostrophes droites ASCII dans la fonction `majProduction()`. JavaScript ne reconnaît pas les guillemets courbes comme délimiteurs de chaîne : il en résultait une `SyntaxError` fatale qui désactivait **l'intégralité** du bloc `<script>` inline du formulaire.

Conséquence : aucune fonction du formulaire ne s'exécutait — ni l'ajout de ligne de production (`ajouterProduction`), ni les calculs de volume, ni les mises à jour d'état, ni la logique de soumission. L'opérateur voyait un formulaire figé et ne pouvait rien saisir.

---

## 2. Décision d'architecture — un seul script inline = un seul point de défaillance

Le formulaire de saisie centralise toute sa logique dans un unique bloc `<script>` inline (≈33 000 caractères). Cette concentration est efficace pour la cohésion, mais elle a un revers : une seule `SyntaxError` n'importe où dans le bloc fait échouer le parsing complet, donc toutes les fonctions disparaissent d'un coup.

**Leçon retenue :** une validation syntaxique automatique (`node --check`) du script rendu doit faire partie de la vérification de toute modification touchant ce fichier. C'est désormais le protocole de test appliqué.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS2 — Mesurer la production réelle via collecte terrain | **Direct (déblocage).** Sans saisie possible, aucune donnée terrain ne peut être collectée. Ce fix restaure le canal de collecte, condition nécessaire à OS2. |
| OS6 — Outil de pilotage adapté | **Direct.** Le formulaire est le point d'entrée unique des données ; sa panne paralyse tout l'outil en aval. |

---

## 4. Impact sur la validité scientifique des données

Aucun impact sur la logique de calcul. Le bug était purement syntaxique (caractères de délimitation invalides), sans modification de la formule TRS, des règles de validation métier, ou de la sémantique du poka-yoke F4. Une fois la syntaxe corrigée, le comportement F4 (alerte orange/rouge non-bloquante) fonctionne tel que conçu.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Aucune modification du modèle de données.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.** Bugfix de correction syntaxique sans effet sur les hypothèses de recherche.

---

## 7. Nouvelles fonctions clés introduites

Aucune nouvelle fonction. Correction de 6 occurrences de guillemets courbes (`‘ ’`) en apostrophes droites (`'`) / guillemets doubles (`"`) dans `majProduction()` :
- `let message = '';`
- `message = "L'heure de fin doit être après l'heure de début.";`
- `message = 'Conforme + déclassé dépasse le volume entrée.';`
- `let rangeMessage = '';`
- `alerte.classList.toggle('is-warning', ...)`
- `carte.classList.toggle('has-warning', ...)`

---

## 8. Utilisabilité terrain et adoption

- **Avant le fix :** formulaire de saisie totalement inerte. L'opérateur ne pouvait ajouter aucune ligne, ni soumettre. Blocage complet du flux de collecte.
- **Après le fix :** formulaire pleinement fonctionnel — ajout de lignes, calculs en direct, alertes poka-yoke F4, soumission en brouillon, tout opère normalement.

---

## 9. Ce que cela change pour le mémoire

Aucun impact sur le contenu rédactionnel. Ce fix garantit que le prototype de collecte est opérationnel pour les démonstrations et la collecte terrain — prérequis indispensable à la production des données d'OS2 et d'OS3.

---

> **Vérification réalisée :** Extraction du `<script>` inline du formulaire rendu (connecté en opérateur) et validation par `node --check` → `SYNTAX OK` après correction (contre `SyntaxError: Invalid or unexpected token` avant). Soumission backend d'une saisie complète confirmée fonctionnelle (HTTP 302 → historique). Le bug était strictement côté client : le backend acceptait déjà les soumissions correctement formées.

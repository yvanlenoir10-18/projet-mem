# Note d'impact mémoire — P55 : Installation code-review-graph (infrastructure outillage)
**Commit :** `ad9be80` — `chore(tooling): code-review-graph v2.3.5 — graphe de dépendances pour Claude Code`
**Date :** 2026-06-03
**Nature :** Infrastructure outillage — **aucune modification du code applicatif wood_pilot**
**Fichiers modifiés :** `.mcp.json` · `.gitignore` · `CLAUDE.md` · `.claude/settings.json` · 4 fichiers skills générés

---

## 1. Ce qui a été implémenté

Installation et configuration de `code-review-graph` v2.3.5, un outil d'analyse statique qui construit un graphe de dépendances du code source. L'outil est configuré pour usage exclusif par Claude Code (côté cloud Linux) et **ne modifie rien dans l'application wood_pilot ni dans la base de données**.

**Composants installés :**

- **Serveur MCP** (`code-review-graph mcp --auto-watch`) enregistré dans `.mcp.json`. À chaque session Claude Code, ce serveur expose des outils de navigation par graphe : `semantic_search_nodes`, `get_impact_radius`, `query_graph`, `detect_changes`, `get_review_context`.

- **Hook `Edit/Write/Bash`** dans `.claude/settings.json` : après chaque modification de fichier, le graphe est mis à jour incrémentalement (`code-review-graph update --skip-flows`). Le graphe reste donc toujours synchronisé avec le code réel.

- **Hook `SessionStart`** : affiche le statut du graphe au démarrage de session.

- **4 skills générés** dans `.claude/skills/` : `review-changes`, `explore-codebase`, `debug-issue`, `refactor-safely`. Ces skills structurent des workflows de navigation utilisant le graphe.

- **Graphe initial construit** : 41 fichiers parsés, 379 nœuds (fonctions, classes, routes), 4 534 arêtes (appels, imports, dépendances).

**Graphe local** stocké dans `.code-review-graph/graph.db` (exclu du dépôt via `.gitignore`).

---

## 2. Lien avec les objectifs du mémoire

Ce commit n'est pas un livrable du mémoire. Il améliore la **fiabilité du processus de développement** sans modifier ce qui est démontré ou analysé dans le mémoire.

Bénéfice indirect sur OS6 (outil de pilotage adapté) : les prochaines modifications du code seront précédées d'une analyse d'impact automatique (fonctions affectées, templates liés, dépendances en cascade). Cela réduit le risque de régressions non détectées, ce qui contribue à la qualité et à la cohérence de l'outil final.

---

## 3. Données et calculs mobilisés

Aucune donnée métier mobilisée. L'outil analyse le code source statiquement (Tree-sitter) et ne lit ni la base de données ni les fichiers de configuration de wood_pilot à l'exécution.

Statistiques du graphe initial :
- **41 fichiers** : routes Flask, modèles SQLAlchemy, services, templates Jinja2, utilitaires
- **379 nœuds** : fonctions, classes, méthodes indexées avec leur position dans le code
- **4 534 arêtes** : relations d'appel, d'import, de dépendance entre ces nœuds

---

## 4. Hypothèses testées ou confirmées

**Aucune hypothèse du mémoire n'est impactée.** Ce commit ne touche pas aux calculs TRS, aux données terrain, ni aux algorithmes métier. Les hypothèses H1–H4 restent inchangées.

**Aucune contradiction signalée.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

Ce commit n'est pas citable directement dans le mémoire. Il appartient au journal de développement (notes d'impact) comme trace de la rigueur méthodologique : l'outillage mis en place pour éviter les régressions lors du développement itératif est lui-même documenté.

Si le mémoire inclut une section sur la méthode de développement (OS6 — conception de l'outil), ce type de décision (graphe de dépendances pour maîtriser les impacts) peut être mentionné comme pratique d'ingénierie logicielle appliquée.

---

## 6. Limites actuelles

- **MCP actif uniquement à partir de la prochaine session** : le serveur MCP se charge au démarrage de Claude Code. La session actuelle n'a pas encore accès aux outils graphe via MCP — ils seront disponibles dès la prochaine session.

- **Graphe côté cloud uniquement** : l'installation est sur la machine Linux de Claude Code, pas sur le Windows de l'utilisateur. Le graphe n'est pas utilisable localement par l'utilisateur.

- **Jinja2 partiellement parsé** : Tree-sitter supporte les templates HTML embarqués, mais la logique Jinja2 (filtres, macros, blocs `{% %}`) est traitée comme du texte opaque. Les dépendances template → route sont dans le graphe via les routes Flask, pas via les `url_for()` dans les templates.

- **Pas de couverture des tests** : le projet n'a pas de suite de tests Python formelle. Le champ `tests_for` du graphe sera vide pour la plupart des nœuds.

---

## 7. Vérification de cohérence avec les notes précédentes

Ce commit est orthogonal à toutes les notes précédentes P1–P54. Il ne modifie aucun fichier applicatif et ne remet en question aucune décision de conception documentée.

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

Aucune référence bibliographique du mémoire n'est mobilisée par ce commit d'infrastructure.

---

## 9. Prochaines étapes

- **Redémarrer la session Claude Code** pour que le serveur MCP `code-review-graph` soit actif et que les outils graphe (`semantic_search_nodes`, `get_impact_radius`, etc.) soient disponibles.
- **Appliquer la règle permanente** : avant toute modification touchant les routes Flask, les modèles, les services métier (TRS, pertes FCFA, Ishikawa, Actions Chef), consulter le graphe pour identifier les dépendances avant de coder.
- **Validation P1 sur Windows** : l'étape immédiate reste la vérification des 5 éléments P1 (bandeau VERT/ORANGE/ROUGE, signaux critiques, alertes, FCFA remonté, Boucle Lean) sur la machine Windows après `git pull`.

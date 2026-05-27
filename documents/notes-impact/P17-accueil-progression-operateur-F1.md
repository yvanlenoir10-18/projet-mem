# Note d'impact mémoire — P17 : Accueil action-first + bloc progression opérateur (F1)

> Générée le : 2026-05-27
> Commit : `ef942f5` — feat(operateur): accueil action-first avec bloc progression partagé (F1)
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `saisie.py`, `_progression.html` (nouveau), `accueil_operateur.html`, `historique.html`, `style.css`

---

## 1. Résumé de la fonctionnalité

Première fonctionnalité de la refonte du profil opérateur inspirée de ProBeya (vague 1). Elle remonte la **progression personnelle** de l'opérateur (TRS moyen, meilleur TRS, tendance 7 jours, nombre de postes saisis) sur l'**accueil** — l'écran le plus consulté — en complément de la carte de priorité déjà présente. Jusqu'ici, ces statistiques motivantes (introduites au P16, Bug 5) n'existaient que sur la page Historique, peu visitée, et étaient codées en styles inline non réutilisables.

L'accueil répond désormais à deux questions complémentaires, l'une sous l'autre :
1. **« Que dois-je faire maintenant ? »** — carte de priorité (corrections, brouillon, nouvelle fiche)
2. **« Est-ce que je progresse ? »** — bloc de progression personnelle

S'ajoutent : un compteur de fiches du jour dans l'en-tête, des badges de notification sur les tuiles (corrections / brouillons / en attente) et des états « tout est à jour » pour les tuiles vides.

---

## 2. Décision d'architecture — composant partagé, pas de copier-coller

Le bloc statistiques a été transformé en **composant réutilisable à trois niveaux** pour supprimer la duplication entre l'accueil et l'historique :

| Niveau | Élément | Rôle |
|---|---|---|
| Python | `_stats_operateur(user_id)` dans `saisie.py` | Calcule le dict de stats. Appelé par `accueil_operateur()` ET `historique()`. |
| Template | `saisie/_progression.html` (nouveau) | Rend le bloc. Inclus par les deux pages via `{% include %}`. |
| CSS | classes `.wp-progress*` dans `style.css` | Style du composant. Remplace les styles inline de l'historique. |

Cette factorisation est une dette technique remboursée : le P16 avait laissé le bloc en HTML inline dans `historique.html`. Le code de calcul (auparavant dupliqué dans `historique()`) est maintenant en un seul endroit.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact de F1 |
|---|---|
| OS6 — Concevoir un outil de pilotage adapté | **Direct.** L'accueil opérateur devient un véritable poste de pilotage personnel : priorité d'action + progression, lisibles sans défilement. C'est l'incarnation côté opérateur du tableau de bord différencié par profil exigé par OS6. |
| OS2 — Mesurer la production réelle via collecte terrain | **Indirect.** La boucle de rétroaction immédiate (voir son TRS progresser) est un levier d'adoption de l'outil de collecte. Sans adoption, pas de données — donc pas de mesure fiable. |

---

## 4. Impact sur la validité scientifique des données

**Aucun.** F1 ne touche ni au calcul du TRS, ni aux écritures en base, ni aux règles de validation de saisie. C'est une fonctionnalité d'affichage et de motivation. Les valeurs affichées (`trs_moyen`, `meilleur_trs`, `trs_recent`, `tendance`) sont des agrégats en lecture seule calculés à la volée depuis `Equipe.query` filtré par `user_id`, en ne retenant que les postes effectivement soumis et porteurs d'un TRS (`statut in ('soumis', 'verrouille', 'valide_chef')`).

Le calcul de tendance compare la moyenne TRS des 7 derniers jours à celle des 7 jours précédents ; si l'une des deux périodes est vide, la tendance est `flat` sans erreur. Aucun chiffre n'est inventé : tout provient de la base.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. F1 n'introduit aucune table ni migration. Les statistiques restent calculées à la volée. La seule structure ajoutée est un fichier template (`_progression.html`) et des classes CSS.

À noter : le commit a été **rebasé** sur deux commits remote arrivés en parallèle (`feat: add guided problem resolution` — le module Ishikawa, et `feat: add chef machines downtime view`). Ces commits remote, eux, ajoutent des tables (Probleme, IshikawaCause, PourquoiNiveau) ; ils feront l'objet de leurs propres notes d'impact côté profil chef. Le rebase a fusionné `style.css` sans conflit (CSS F1 et CSS Ishikawa dans des régions distinctes du fichier).

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.**

- **H1** (capacité théorique < 25 m³) : non concernée — F1 est une fonctionnalité d'interface.
- **H2** (pertes organisationnelles) : non concernée directement. F1 soutient toutefois indirectement la démonstration de H2, car une meilleure adoption de l'outil produit davantage de données terrain exploitables.
- **H3** (TRS réel < 60 %) : non concernée. Le bloc affiche le TRS tel que calculé, sans le modifier. Le point de coupure du P16 (données fiables après le 2026-05-27) reste valide.
- **H4** (actions sans investissement majeur) : **cohérente et renforcée.** La boucle de rétroaction est une action d'amélioration à coût nul (ni équipement, ni nouvelle table) — exactement le type d'action peu coûteuse que H4 postule comme efficace.

**Point d'attention — anti-classement :** Le bloc affiche uniquement la progression personnelle de l'opérateur (son propre record, sa propre tendance), jamais un classement entre opérateurs. Ce choix est délibéré et s'appuie sur la littérature : les classements publics entre pairs dégradent l'engagement à long terme dans les contextes de saisie terrain. Cette posture devra être mentionnée si le mémoire discute la conception de la boucle de motivation.

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| `_stats_operateur(user_id)` | `saisie.py` | Helper partagé : dict `{nb_equipes, trs_moyen, meilleur_trs, trs_recent, tendance}`. Source unique de vérité des stats opérateur. |
| `_progression.html` | `templates/saisie/` | Partial du composant de progression (emoji contextuel, message, métriques, badge tendance). |
| `.wp-progress*` | `style.css` | Composant CSS mobile-first : grille de métriques en `auto-fit` (1 ligne desktop, 2 colonnes sous 480px). |
| `.wp-tile-badge`, `.wp-tile-ok-text` | `style.css` | Badges de notification et états « tout est à jour » sur les tuiles de l'accueil. |

---

## 8. Utilisabilité terrain et adoption

F1 répond directement aux contraintes terrain de la scierie CUF (saisie sur tablette/téléphone, opérateurs semi-qualifiés). Les choix de conception orientés intuition utilisateur :

1. **Lecture en moins de 3 secondes** — la priorité d'action et la progression sont toutes deux « above the fold ».
2. **Badges de notification rouges** — pattern de reconnaissance immédiate (issu des smartphones) signalant une fiche à corriger sans avoir à lire.
3. **États positifs** — une tuile vide affiche « Tout est à jour » plutôt qu'un « 0 » muet, évitant l'anxiété.
4. **Composant responsive auto-fit** — les métriques se réorganisent proprement de 2 à 4 colonnes selon le nombre de données disponibles et la largeur d'écran.

Ancrage littérature : Kankkunen & Holopainen (2024) — le tableau de bord quotidien doit donner un sentiment de progression ; Mncwango & Mdunge (2025) — les boucles de rétroaction rapides augmentent l'engagement des opérateurs.

---

## 9. Ce que cela change pour le mémoire

| Section du mémoire | Mise à jour requise |
|---|---|
| OS6 — Vue opérateur | Décrire l'accueil opérateur comme un poste de pilotage personnel à deux niveaux (action immédiate + progression). C'est la réponse concrète au volet « vue opérateur » du tableau de bord différencié. |
| Chapitre méthodologie — adoption de l'outil | Citer la boucle de rétroaction personnelle (sans classement entre pairs) comme mécanisme d'appropriation, cohérent avec H4. |
| Conclusion / discussion | Le choix anti-classement (progression personnelle uniquement) peut être présenté comme une décision de conception fondée sur la littérature, et non un défaut. |
| Limite à signaler | La progression n'a de sens qu'après plusieurs postes saisis ; pour un opérateur débutant, le bloc affiche un message de bienvenue neutre (état `nb_equipes == 0`). |

---

> **Vérification réalisée :** rendu HTML contrôlé via session authentifiée (login + CSRF) sur `/saisie/accueil` et `/saisie/historique` en rôle opérateur — composant `wp-progress` rendu à l'identique sur les deux pages, 3 à 4 métriques selon les données, aucune erreur de template. Capture d'écran visuelle impossible dans cet environnement (Chromium non installable, dépôt apt bloqué) ; la vérification s'est donc faite au niveau du HTML servi. Rôle de test restauré après contrôle.

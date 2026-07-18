# Note d'impact mémoire — P5d : Alerte brouillon — lien Voir → lecture seule PDG
**Commit :** `6440a89` — `feat(pdg): alerte brouillon — lien Voir → lecture seule pour le PDG`
**Date :** 2026-05-03
**Fichiers modifiés :** `app/templates/pdg/dashboard.html` (3 lignes)

---

## 1. Ce qui a été implémenté

Ajout d'un lien "Voir →" dans l'alerte brouillon pour le rôle PDG, en lecture seule.

| Rôle | Comportement avant | Comportement après |
|---|---|---|
| **Chef / Admin** | "Voir et soumettre →" → historique avec boutons Soumettre/Supprimer | Inchangé |
| **PDG** | Alerte visible, aucun lien, aucune action possible | "Voir →" → historique en lecture seule (aucun bouton d'action car brouillons créés par admin/chef) |

La lecture seule du PDG est garantie par le template existant `saisie/historique.html` : les boutons Soumettre et Supprimer n'apparaissent que pour `p.user_id == current_user.id`. Le PDG qui ne crée pas de postes ne verra jamais ces boutons sur les brouillons des autres.

---

## 2. Lien avec les objectifs du mémoire

Cette modification affine la décision de conception documentée dans P5 (section 5 et 7) : la différenciation role-aware PDG/Chef. P5 prévoyait déjà que "le PDG voit l'alerte mais pas l'action". P5d complète ce principe en donnant au PDG une visibilité réelle sur les brouillons (qui sont-ils ? quelle date ?) sans lui donner de pouvoir d'action.

Cette nuance est cohérente avec Jaouane (2022) qui distingue les niveaux stratégique (PDG : surveillance) et opérationnel (Chef : action). Le PDG surveille, le Chef agit.

---

## 3. Données et calculs mobilisés

Aucun nouveau calcul. L'accès au lien `url_for('saisie.historique')` est identique pour les deux rôles — seul le libellé du lien change.

---

## 4. Hypothèses testées ou confirmées

**Aucune contradiction avec les hypothèses existantes.**

La différenciation PDG/Chef renforcée ici est cohérente avec la contrainte terrain identifiée dans le cadrage (section 3 de `contexte_memoire_CUF.md`) : "le PDG de CUF n'a pas de formation forestière et ne doit pas être exposé aux actions opérationnelles".

---

## 5. Ce que ce module permet de montrer dans le mémoire

- La vue exécutive PDG est maintenant complète sur la gestion des alertes : le PDG est informé (alerte jaune visible), peut investiguer (lien Voir), mais ne peut pas interférer avec les flux opérationnels (Soumettre/Supprimer réservés au propriétaire du poste).
- Cela illustre concrètement la conception multi-niveaux décrite dans la section méthodologique, avec une preuve technique : le contrôle d'accès est basé sur `p.user_id == current_user.id` (propriété), pas seulement sur le rôle — ce qui est une décision de design plus robuste qu'un simple `if role == 'chef'`.

---

## 6. Limites actuelles

- L'historique affiche tous les postes (soumis et brouillons confondus) sans filtrage. Pour le PDG, une vue filtrée "seulement les brouillons" serait plus pertinente. Différé à P6 ou au-delà selon la priorité.
- Le bouton "Saisir un poste" en haut de la page historique reste visible pour le PDG — il peut techniquement créer un poste. Ce cas n'a pas été bloqué à ce stade (hors périmètre P5).

---

## 7. Vérification de cohérence avec les notes précédentes

La note `P5-dashboard-pdg-enrichi.md` (section 5) indiquait : "La différenciation role-aware (PDG / Chef / Admin) est une décision de conception documentée." P5d renforce et précise cette décision en accordant au PDG une fenêtre d'observation sur les brouillons, cohérente avec le principe de séparation des responsabilités.

Aucune contradiction avec les notes précédentes.

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Jaouane (2022) | Distinction niveau stratégique (PDG : surveillance) vs opérationnel (Chef : action) — directement illustrée par le lien "Voir →" vs "Voir et soumettre →" |

---

## 9. Prochaines étapes

- **Windows :** l'utilisateur doit faire `git fetch + git reset --hard` pour récupérer tous les commits P5b/P5c/P5d.
- **P6 Dashboard Chef :** vue opérationnelle enrichie — drill-down machine, comparaison Matin/Après-midi, statistiques d'effectif.
- **Filtrage historique pour PDG :** différé — afficher uniquement les brouillons du mois en cours serait plus utile que la liste complète.

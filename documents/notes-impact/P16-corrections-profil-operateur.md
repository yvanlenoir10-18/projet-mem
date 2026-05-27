# Note d'impact mémoire — P16 : Corrections profil opérateur (6 bugs)

> Générée le : 2026-05-27
> Commit : `f29c4a8` — fix(operateur): 6 corrections profil opérateur — validation, UX, mobile
> Fichiers modifiés : `saisie.py`, `formulaire.html`, `historique.html`, `detail.html`

---

## 1. Résumé de la fonctionnalité

Correction de 6 problèmes identifiés sur le profil opérateur (agent de saisie terrain), suite à une analyse approfondie de l'interface de collecte. Ces corrections touchent à la fois la qualité des données collectées, l'ergonomie mobile et la motivation de l'opérateur à remplir les formulaires.

---

## 2. Bugs corrigés et impact sur les données

| Bug | Problème initial | Correction apportée |
|---|---|---|
| Bug 1 — Heure arrêt inversée | `calcule_duree()` faisait `max(0, ...)` — une heure fin < debut donnait 0 min sans erreur, gonflant le TRS artificiellement | La route rejette avec message d'erreur + données préservées |
| Bug 2 — Essence non obligatoire | Le select était pré-sélectionné sur la première essence, lignes silencieusement ignorées si vide | Select démarre sur "— Choisir —", erreur bloquante si volumes sans essence |
| Bug 3 — Virgule rejetée | `float("12,5")` levait une ValueError en français, le formulaire se réinitialisait à blanc | `_parse_float()` convertit `,` → `.` ; données re-affichées après erreur |
| Bug 4 — Validation trop tardive | `_verifier_coherence()` ne tournait qu'au submit; erreurs découvertes trop tard | Validation inline JS temps réel pendant la saisie ; blocage au submit |
| Bug 5 — Pas de rétroaction | L'opérateur ne voyait son TRS qu'une fois dans un flash message | Bloc stats personnel sur l'historique + encouragement contextualisé sur detail |
| Bug 6 — Formulaire inutilisable sur mobile | `col-md-2` = 6 champs côte à côte stackés verticalement sur phone | Layout 2 colonnes sur mobile (`col-6 col-md-2`), boutons min-height 44px |

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact de P16 |
|---|---|
| OS2 — Mesurer la production réelle via un système de collecte terrain | **Direct et critique.** Bug 1 faussait le TRS en stockant 0 min pour des arrêts mal saisis. Bug 2 perdait silencieusement des lignes de production sans essence. Bug 3 bloquait les saisies de terrain avec la virgule française. Ces 3 corrections renforcent la fiabilité des données brutes. |
| OS3 — Calculer le TRS et estimer le coût des pertes | **Indirect mais important.** La correction du Bug 1 supprime une source de biais systématique sur le TRS : un arrêt de 2h saisi à l'envers (debut=10h, fin=08h) donnait 0 min d'arrêt au lieu de 120 min, ce qui pouvait gonfler la Disponibilité de 15-20 points. |
| OS6 — Concevoir un outil de pilotage adapté aux responsables de CUF | **Direct.** Le Bug 6 (mobile) était un blocage majeur pour l'utilisation terrain. Le Bug 5 (feedback motivant) s'appuie directement sur la littérature retenue (Mncwango & Mdunge 2025 — boucles de rétroaction et engagement opérateur). |

---

## 4. Impact sur la validité scientifique des données

### Problème critique résolu (Bug 1)

Le Bug 1 était le plus grave du point de vue scientifique. En l'absence de correction, un arrêt mal saisi (heure_fin < heure_debut) était stocké avec `duree_min = 0`, ce qui :

- **Gonflait la Disponibilité** : si l'équipe avait réellement 2h d'arrêt mais l'heure était inversée, la Disponibilité passait de `(480−120)/480 = 75%` à `480/480 = 100%`
- **Gonflait le TRS** : un TRS réel de 52,5 % pouvait être calculé à 70 % sur le même poste
- **Biaissait H3** : l'hypothèse H3 (TRS réel < 60 %) risquait de ne pas être validée sur données biaisées, alors qu'elle l'est en réalité

Ce bug aurait pu compromettre la démonstration centrale du mémoire. Il est maintenant bloqué côté serveur ET côté client (JS en temps réel).

---

## 5. Nouvelles fonctions clés introduites

| Fonction | Fichier | Rôle |
|---|---|---|
| `_parse_float(val)` | `saisie.py` | Convertit `"12,5"` et `"12.5"` en float |
| `_form_data_brut()` | `saisie.py` | Extrait les données brutes du POST pour re-affichage |
| `_render_form(equipe, productions_data, arrets_data)` | `saisie.py` | Accepte maintenant des données pré-remplies indépendamment d'un equipe DB |
| `validerProd(index)` | `formulaire.html` | Validation inline JS : conforme + déclassé ≤ entree |
| `validerArret(index)` | `formulaire.html` | Validation inline JS : fin > debut |
| `_pf(val)` | `formulaire.html` | `parseFloat` côté JS avec support virgule |
| stats_operateur dict | `saisie.py/historique()` | TRS moyen, meilleur TRS, tendance 7j — calculé depuis Equipe existant |

---

## 6. Règle R7 — Aucune nouvelle table DB

Les statistiques opérateur (Bug 5) sont calculées à la volée depuis `Equipe.query` filtré par `user_id`. Aucune nouvelle table ni migration. La règle R7 est respectée.

Le calcul de tendance sur 7 jours compare `trs_recent` (moyenne des équipes des 7 derniers jours) à `trs_prec` (7 jours précédents). Si l'une des deux périodes est vide, `tendance = 'flat'` sans erreur.

---

## 7. Contradiction avec hypothèses précédentes

**Aucune contradiction avec les hypothèses de recherche H1–H4.**

**Point d'attention — données existantes potentiellement biaisées :**

Les équipes déjà enregistrées en base avant le commit `f29c4a8` peuvent contenir des arrêts avec `duree_min = 0` issus d'heures inversées. Ces données historiques ne sont pas recalculées automatiquement. Pour le mémoire, il est recommandé :

1. De noter que les données antérieures au 2026-05-27 peuvent comporter ce biais
2. D'utiliser principalement les données collectées après cette date pour les calculs TRS

Les données du seed (`seed_data.py`, 60 équipes avril 2026) sont générées algorithmiquement avec des heures cohérentes — elles ne sont pas affectées.

---

## 8. Utilisabilité terrain et adoption

Le Bug 6 (mobile) est le plus important pour l'adoption terrain à la scierie CUF. Les opérateurs saisissent sur téléphone, pas sur desktop. Un formulaire avec 6 champs côte à côte inopérables sur mobile était un blocage absolu à l'utilisation réelle.

Le Bug 5 (feedback motivant) s'ancre dans la littérature retenue :

- **Mncwango & Mdunge (2025)** — "Les boucles de rétroaction rapides augmentent l'engagement des opérateurs et la qualité des données de terrain"
- **Kankkunen & Holopainen (2024) — Daily management, UPM Plywood** — le tableau de bord quotidien doit donner un sentiment de progression

Le bloc de stats personnelles (TRS moyen, meilleur TRS, tendance) visible dès l'historique crée cette boucle de rétroaction sans alourdir la base de données.

---

## 9. Ce que cela change pour le mémoire

| Section du mémoire | Mise à jour requise |
|---|---|
| OS6 — Outil de pilotage | Mentionner explicitement la validation temps réel et l'ergonomie mobile comme éléments de conception répondant aux contraintes terrain CUF (saisie sur téléphone, opérateurs semi-qualifiés) |
| Chapitre méthodologie — collecte terrain | Souligner que le système valide les incohérences de saisie en temps réel (fin > début, essence obligatoire) — gage de fiabilité des données collectées |
| Résultats TRS (OS3) | Préciser que les données analysées sont celles postérieures à `2026-05-27`, période à partir de laquelle Bug 1 est corrigé et les TRS sont fiables |
| Conclusion | La boucle de rétroaction opérateur (Bug 5) peut être citée comme mécanisme d'appropriation de l'outil — cohérent avec H4 (actions sans investissement majeur) |

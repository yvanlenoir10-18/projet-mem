# Note d'impact mémoire — P25 : Anti-chevauchement horaire + correction poka-yoke F4

> Générée le : 2026-05-28
> Commit : `938a888` — feat(saisie): anti-chevauchement horaire + poka-yoke F4 corrigé
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `saisie.py`, `formulaire.html`, `style.css`

---

## 1. Résumé de la fonctionnalité

Deux corrections métier liées à la contrainte physique de la chaîne 4 (une seule machine : la bicoupe).

**Anti-chevauchement (blocage de saisie incohérente) :**
Il est physiquement impossible que deux essences soient traitées simultanément sur la chaîne 4. Un créneau `Ayous 06:00–11:00` + `Azobé 08:00–14:00` est une saisie impossible. L'application bloque désormais cette incohérence à deux niveaux :
- **Côté serveur** : `_chevauchement_productions()` dans `saisie.py` détecte le conflit avant tout flush DB et retourne un flash `danger` précis (nomme les deux essences et leurs créneaux).
- **Côté client** : `rafraichirEtatProductions()` dans `formulaire.html` détecte le conflit en temps réel à chaque frappe (no-submit + bannière terracotta + alerte par carte).
- Les bornes jointives (fin d'une = début d'une autre, ex : 06:00–11:00 + 11:00–14:00) sont **autorisées**, car elles représentent deux créneaux consécutifs — physiquement valides.

**Correction poka-yoke F4 :**
Le poka-yoke F4 (alerte volume anormalement élevé) comparait le `volume_entree` à la capacité théorique. C'était incorrect : la capacité théorique de la bicoupe est une capacité de **sortie** (bois conforme + déclassé), pas d'entrée. La comparaison est désormais : `conforme + déclassé` vs `capacité_créneau`. L'alerte orange/rouge est donc déclenchée sur la vraie mesure métier.

---

## 2. Décision d'architecture — double garde (client + serveur)

**Pourquoi les deux niveaux ?**
- La garde client est immédiate et pédagogique : l'opérateur voit l'alerte au fur et à mesure qu'il saisit, sans attendre la soumission.
- La garde serveur est la vérité de confiance : elle protège contre les clients JavaScript désactivés ou les soumissions directes (API, curl). Aucune donnée incohérente ne peut entrer en DB.

**Algorithme sweep line (O(n log n)) :**
Les intervalles sont triés par début, puis un seul "couvreur courant" est maintenu. Le test de conflit est `it.debut < couvrant.fin` (strict) : cette inégalité stricte exclut naturellement les bornes jointives (`debut == fin`) sans cas spécial. C'est la même logique côté Python (`saisie.py`) et côté JavaScript (`formulaire.html`).

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS2 — Mesurer la production réelle via collecte terrain | **Direct.** Les données collectées ont maintenant une cohérence physique garantie : aucune saisie impossible (deux essences simultanées) ne peut entrer en base. La fiabilité du dataset OS2 est renforcée. |
| OS3 — Calculer le TRS | **Indirect.** La correction du poka-yoke F4 assure que les alertes de qualité (Q dans TRS = D×P×Q) sont déclenchées sur la bonne métrique (output, pas input). |
| OS6 — Outil de pilotage adapté | **Direct.** L'outil détecte et signale une incohérence terrain avant qu'elle ne pollue les données — attribut de qualité fondamental d'un outil de pilotage. |

---

## 4. Impact sur la validité scientifique des données

La correction du poka-yoke F4 a un impact direct sur la validité du calcul de qualité (Q) du TRS. Avant la correction, l'alerte se déclenchait sur le volume d'entrée (matière brute), qui n'est pas borné par la capacité machine. Après la correction, elle se déclenche sur `conforme + déclassé` (production nette), qui est la grandeur physiquement contrainte par la vitesse de la bicoupe. Résultat : les alertes orange/rouge correspondent désormais aux cas où l'opérateur a déclaré produire plus que ce que la machine peut physiquement sortir sur le créneau — ce qui est le seul signal de fiabilité pertinent pour OS3.

L'anti-chevauchement garantit qu'aucune ligne de la base `ProductionLigne` ne peut représenter une impossibilité physique. Sans cela, un calcul agrégé (ex. volume total sur poste) pourrait compter deux fois du bois qui n'existe pas.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Aucune nouvelle table. La logique de validation est entièrement applicative (`saisie.py`) et client (`formulaire.html`). Le schéma DB est inchangé.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.**

Une nuance à documenter pour H3 : si le poka-yoke F4 avait produit des alertes sur du volume d'entrée (avant correction), cela n'avait aucun effet sur les données enregistrées — le poka-yoke est non-bloquant (alerte orange/rouge, pas un refus de soumission). Les données TRS stockées ne sont donc pas affectées rétroactivement. La correction ne crée pas de rupture de série pour H3.

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| `_minutes_horaire(valeur)` | `saisie.py` | Convertit `HH:MM` en minutes entières depuis minuit. Retourne `None` si invalide — évite les exceptions silencieuses dans la comparaison. |
| `_chevauchement_productions(essences, prod_debuts, prod_fins)` | `saisie.py` | Sweep line O(n log n). Retourne `None` (pas de conflit) ou un message flash en français décrivant précisément le conflit. Tolère les bornes jointives. |
| `intervallesProduction()` | `formulaire.html` | Collecte tous les intervalles valides depuis les cartes DOM actives (essence + heure début + heure fin). |
| `rafraichirEtatProductions()` | `formulaire.html` | Sweep line JS : met à jour l'alerte par carte, la bannière globale, retourne `true` si conflit. Appelée à chaque `majProduction()` et au `submit`. |
| `.wp-overlap-alert` | `style.css` | Bannière rouge terracotta avec icône Bootstrap, ombre portée, display:flex — cohérente avec `.wp-operator-*`. |

---

## 8. Utilisabilité terrain et adoption

- **Comportement avant :** un opérateur pouvait saisir Ayous 06:00–11:00 et Azobé 08:00–14:00 sur la même fiche. La donnée entrait en DB sans avertissement, polluant les calculs agrégés.
- **Comportement après :**
  - Dès que l'opérateur saisit le deuxième créneau qui chevauche le premier, une alerte rouge apparaît immédiatement sur la carte concernée et une bannière terracotta s'affiche en haut du formulaire.
  - Si l'opérateur ignore les alertes et clique "Soumettre", le formulaire bloque (JavaScript) et fait défiler jusqu'à la bannière.
  - Si JavaScript est désactivé, le serveur refuse la soumission avec un flash d'erreur explicite.
  - Les bornes jointives (enchaînement logique de créneaux) sont autorisées et ne déclenchent aucune alerte.

---

## 9. Ce que cela change pour le mémoire

**OS2 et OS3 :** Le dataset de production est maintenant garanti cohérent physiquement. Les lignes enregistrées dans `ProductionLigne` respectent la contrainte machine-unique de la chaîne 4. Cela renforce la crédibilité des données terrain présentées dans le mémoire.

**OS6 :** L'outil dispose d'une validation métier spécifique au contexte CUF (machine unique, séquentialité obligatoire des essences) — ce niveau de contextualisation est un argument pour OS6 ("outil adapté aux besoins de CUF"), à citer dans la section résultats.

**Poka-yoke F4 :** La correction aligne l'indicateur d'alerte sur la définition métier de la capacité théorique (issue des calculs OS1). C'est une cohérence formelle entre OS1 (capacité théorique = débit de sortie bicoupe) et OS3 (TRS qualité = sorties conformes / sorties théoriques possibles). Citer dans la section "adéquation de l'outil aux hypothèses de recherche".

---

> **Vérification réalisée :** Tests curl directs sur `/saisie/nouveau` :
> - Chevauchement (Ayous 06:00–11:00 + Azobé 08:00–14:00) → HTTP 200 + flash "Chevauchement horaire : « Ayous » (06:00–11:00) et « Azobe » (08:00–14:00) se recouvrent. La chaîne ne traite qu'une essence à la fois." ✓
> - Jointif (Ayous 06:00–11:00 + Azobé 11:00–14:00) → HTTP 302 success ✓
> - `node --check` sur le script inline du formulaire rendu → SYNTAX OK ✓

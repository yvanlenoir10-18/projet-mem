# Note d'impact mémoire — P52 : Prix de valorisation visibles par le chef (page Pertes)

> Générée le : 2026-06-03
> Commit : `c3b79be` — feat(chef): prix de valorisation visibles en lecture seule sur /pertes
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `cuf-pilotage/app/routes/dashboard.py`, `cuf-pilotage/app/templates/dashboard/pertes.html`

---

## 1. Résumé de la fonctionnalité

Avant ce commit, la page des pertes financières affichait un manque à gagner et des pertes D/P/Q en FCFA, mais le chef ne pouvait consulter aucun des prix par essence qui servent à ces calculs : ces paramètres étaient réservés à l'administrateur. Devant un encadreur demandant « d'où viennent ces montants ? », le chef était démuni.

Après ce commit, un encart en lecture seule apparaît sur la page des pertes, juste sous les montants principaux. Il liste, pour chaque essence présente dans la période, le prix de valorisation effectivement utilisé en FCFA par mètre cube, avec la mention explicite que ces prix sont figés à la soumission des fiches et modifiables uniquement par l'administrateur. Le chef peut ainsi justifier chaque montant sans obtenir de droit d'écriture sur les paramètres.

---

## 2. Décision d'architecture — afficher le prix réellement utilisé, pas le prix théorique

Le point délicat tenait à la coexistence de deux sources de prix dans l'application : le prix figé par fiche au moment de la soumission (`prix_snapshot`) et les prix vivants stockés dans les paramètres administrables. La fonction `_prix_production()` privilégie le snapshot avant de retomber sur le paramètre. Les montants de la page reposent donc sur les snapshots. Afficher les prix administrables aurait introduit une incohérence : le chef aurait lu des prix sans rapport avec les montants calculés. L'encart calcule par conséquent la moyenne pondérée par volume des prix snapshot réellement employés sur la période, garantissant que prix affiché et montant FCFA proviennent de la même base. Seules les essences effectivement présentes dans la période sont listées, ce qui évite d'exposer des prix sans objet.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS1 / valorisation financière des écarts | **Direct.** Le chiffrage du manque à gagner devient justifiable jusqu'au prix unitaire, condition de sa défense scientifique. |
| OS6 — Outil de pilotage adapté | **Direct.** Le chef gagne en autonomie : il comprend et explique les montants au lieu de les subir comme une boîte noire. |

---

## 4. Impact sur la validité scientifique des données

Positif sans modifier aucun calcul. La fonctionnalité ne change pas une formule ni un montant ; elle rend visible le paramètre de valorisation qui les sous-tend. Pour le mémoire, c'est un gage de transparence méthodologique : la valorisation FCFA repose sur des prix explicitement consultables et datés du moment de la saisie, ce qui protège contre l'objection d'une estimation arbitraire. La note souligne toutefois que les prix snapshot doivent eux-mêmes correspondre aux prix de marché réels pour que les montants soient pertinents, ce qui relève d'une vérification distincte avec l'encadreur.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Le prix effectif est calculé à la volée par agrégation des snapshots déjà stockés sur les productions. Aucune table ni colonne nouvelle.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.** La fonctionnalité est consultative. Elle renforce la crédibilité de la valorisation financière mobilisée pour quantifier les écarts, sans toucher aux mesures de performance servant à tester les hypothèses.

---

## 7. Nouveaux éléments introduits

| Élément | Fichier | Rôle |
|---|---|---|
| `prix_essences_acc` + agrégation pondérée | `dashboard.py` (`pertes`) | Cumule prix snapshot × volume par essence sur la période |
| Variable `prix_essences` | `dashboard.py` | Liste des prix effectifs transmise au template |
| Encart « Prix de valorisation utilisés » | `pertes.html` | Affichage lecture seule, mention « modifiables par l'administrateur » |

---

## 8. Utilisabilité terrain et adoption

Avant, le chef ne pouvait pas répondre à une question pourtant centrale d'un expert : sur quels prix repose le manque à gagner. Après, il pointe l'encart et lit, par exemple, « Iroko : 420 000 FCFA/m³ ». L'échange devient possible : si l'encadreur estime ce prix trop haut ou trop bas, la discussion s'ouvre et l'administrateur ajuste. Cette transparence, sans ouvrir de droit de modification au chef, respecte la séparation des rôles tout en rendant l'outil défendable.

---

## 9. Ce que cela change pour le mémoire

La fonctionnalité illustre la traçabilité de la valorisation financière, complément naturel de la traçabilité de la mesure introduite par ailleurs. Elle nourrit l'argument selon lequel l'outil ne se contente pas d'afficher des FCFA, mais permet d'en exposer la construction. Elle ouvre aussi une question de méthode à traiter dans le mémoire : la fiabilité des prix de référence, qui conditionne la pertinence de tout chiffrage de pertes, et qui justifie de documenter la source des prix retenus.

---

> **Vérification réalisée :** connexion chef + page /pertes (HTTP 200). Encart présent affichant Ayous 180 000, Azobé 280 000, Iroko 420 000 FCFA/m³ — valeurs identiques aux snapshots utilisés dans les montants. Smoke driver 16/16 OK.

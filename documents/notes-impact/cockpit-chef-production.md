# Note d'impact mémoire — Le profil Chef de Production ouvre le cockpit décisionnel

> Branche `claude/install-claude-excel-6MGzv` · Session 2026-07-17 · Commit `28a5749`
> Changement de routage/RBAC (6 lignes, 4 fichiers). Aucune nouvelle fonctionnalité, aucune table, aucun calcul modifié.

---

## 1. Ce qui a été implémenté

Le profil **Chef de Production** (`prod`, compte `prod@cuf.cm`) ouvre désormais le **cockpit décisionnel complet** (`vue_chef`, template `chef/dashboard.html`) au lieu de la vue allégée « Le Point » (`vue_prod`). Concrètement, le rôle `prod` obtient le verdict global (SOUS/HORS CONTRÔLE), le TRS décomposé D×P×Q, le manque à gagner en FCFA, la projection de fin de poste, les signaux critiques, les alertes et les priorités décisionnelles — exactement le rendu servi au chef et à l'administrateur.

Quatre points de câblage ont été alignés : la table d'accueil par rôle (`utils.py:_ACCUEIL_ROLE`), la redirection effective après connexion (`auth.py:_redirect_par_role`), l'autorisation d'accès à la route `/dashboard/chef` (`dashboard.py:vue_chef`, décorateur `roles_required` enrichi de `'prod'`), et le lien « Tableau de bord » du menu latéral prod (`base.html`, versions bureau et tiroir mobile). Les neuf sous-pages du chef (Fiches, Machines, Production, Qualité, Pertes, Causes d'arrêts, Résolution, Décisions, Prescriptions) autorisaient déjà le rôle `prod` et figuraient déjà dans son menu ; seule la page d'atterrissage restait branchée sur la vue minimale.

## 2. Lien avec les objectifs du mémoire

Le Chef de Production est l'acteur central de **OS1** (capacité théorique → production réelle → écart + TRS) et du fil conducteur **DMAIC** : c'est lui qui lit le TRS, identifie le goulot (bicoupe) et décide des contre-mesures. Lui donner le cockpit complet dès la connexion matérialise la promesse du mémoire selon laquelle la compilation, auparavant inexistante, devient automatique et immédiatement lisible au niveau du pilote de la chaîne 4. Le parcours de démonstration (annexe outil) gagne en cohérence : le profil dont le titre est « Chef de Production » présente enfin l'instrument de pilotage attendu, et non un tableau de bord réduit.

## 3. Données et calculs mobilisés

Aucun. Le changement est purement un routage RBAC : la même route `vue_chef` sert le même template avec les mêmes agrégats. Il a été vérifié que `vue_chef` ne contient aucun branchement sur `current_user.role` (ses deux appels `render_template` — cas données vides et cas peuplé — sont identiques quel que soit le rôle) et que `chef/dashboard.html` ne masque aucun bloc par rôle. Le profil `prod` reçoit donc un rendu **octet pour octet identique** à celui du chef : les chiffres du mémoire (TRS 64 %, production 14,55 m³/poste, rendement 31 %) ne sont ni recalculés ni altérés.

## 4. Hypothèses testées ou confirmées

- **Confirmé** : le rendu du cockpit est indépendant du rôle appelant (preuve : `grep current_user.role` vide dans `vue_chef` et dans `chef/dashboard.html` ; page prod servie à 14,3 Ko contre 7,5 Ko pour la vue minimale, soit le template riche).
- **Confirmé** : la redirection de connexion passe bien par `auth.py:_redirect_par_role` et non par `utils.py:redirect_accueil` — les deux tables devaient être alignées, sans quoi le rôle `prod` restait redirigé vers `/dashboard/prod` (constat fait lors du premier test, corrigé ensuite).

## 5. Ce que ce module permet de montrer dans le mémoire

Que l'outil attribue à chaque acteur la vue correspondant à sa responsabilité réelle : le Chef de Production dispose d'un cockpit de premier regard (test des 10 secondes) qui répond à « l'usine est-elle sous contrôle ? » sans reconstruire lui-même la synthèse. C'est l'argument d'ergonomie décisionnelle porté par l'audit du profil chef (sections 1 et 7 du plan d'audit) : altitude d'abord, verdict avant détail.

## 6. Limites actuelles

- **Fenêtre de dates par défaut (30 j).** Le cockpit affiche par défaut les 30 derniers jours. Les données reconstruites du mémoire couvrant le **28 avril → 23 juin 2026**, un accès le 17 juillet ne capte que la queue de la période et fait chuter le TRS affiché (~8 %). Pour la démonstration, **basculer sur « 90 j »** restitue le TRS ≈ 64 % attendu. Ce n'est pas un défaut du présent changement mais un effet de calendrier à connaître.
- **La route `vue_prod` (« Le Point ») existe toujours** mais n'a plus de lien dans le menu prod. Elle reste accessible par URL directe ; elle pourra être retirée ou reconvertie ultérieurement.
- **Report assumé** : la comparaison fine des fonctionnalités entre l'ancien profil `chef` (« Chef Scierie ») et `prod` (« Chef de Production »), en vue d'en fusionner ou d'en porter certaines, reste à faire (différée explicitement par l'utilisateur : « c'est ce qu'on va faire après »).

## 7. Vérification de cohérence avec les notes précédentes

- **Cohérent** avec la note `calibration-production-14-55.md` : aucun paramètre ni volume touché, les valeurs alignées (objectif 25, production 14,55, rendement 31 %) sont préservées.
- **Ne contredit aucune hypothèse antérieure.** Le changement est un routage d'affichage ; H1–H4 et les décisions verrouillées (objectif 25 m³/poste, bicoupe goulot, 4 essences dont Bilinga) sont inchangées.
- **Point de vigilance documentaire** : la fiche `documents/fiche-soutenance-demo.md` (étape 1) décrit encore « `prod@cuf.cm` → Tableau de bord *Le Point* (figure 9) ». Avec ce changement, `prod` ouvre le cockpit riche, plus « Le Point ». La fiche devra être ajustée si la démonstration s'appuie sur le compte `prod` — à valider avec l'utilisateur avant de réécrire un renvoi de figure calé sur le mémoire.

## 8. Références bibliographiques mobilisées implicitement

Aucune nouvelle. Le principe de hiérarchie visuelle décisionnelle (cockpit 10 secondes, verdict global) s'appuie sur le cadre Lean/TRS déjà mobilisé dans le mémoire (décomposition TRS = Disponibilité × Performance × Qualité ; benchmarks scierie 60 %).

## 9. Prochaines étapes

- Décider du sort de `documents/fiche-soutenance-demo.md` (mettre à jour l'étape 1 pour refléter le cockpit prod, ou conserver « Le Point » via URL directe pendant la démo).
- Le cas échéant, retirer ou reconvertir la route `vue_prod` devenue orpheline dans le menu.
- Session suivante : audit `chef` vs `prod` pour porter/fusionner les fonctionnalités pertinentes (tâche différée par l'utilisateur).
- Rappel démo : ouvrir le cockpit prod sur **« 90 j »** pour afficher le TRS ≈ 64 % du mémoire.

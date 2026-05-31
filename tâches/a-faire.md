# CUF Pilotage — Plan vivant des tâches

> Projet : Application Flask de pilotage Chaîne 4, Scierie CUF Ebolowa
> Mis à jour : 2026-04-30 (P3 complété)

---

## ✅ PHASE 1 — Saisie des équipes (COMPLÉTÉ)

- [x] Modèle Equipe + Production + Arret
- [x] Formulaire de saisie multi-essence
- [x] Calcul TRS automatique (Disponibilité × Performance × Qualité)
- [x] Historique des équipes
- [x] Détail d'une équipe (KPIs + arrêts + pertes)
- [x] Export Excel (3 feuilles : Résumé | Équipes | Arrêts)
- [x] **P1 Amendment** — Refonte modèle matière :
  - [x] volume_conforme (planches conformes, prix plein)
  - [x] volume_declass (bois déclassé, vente locale ×0.30)
  - [x] volume_dechets (calculé = entree − conforme − declass)
  - [x] Perte Q décomposée : perte_q_declass + perte_q_dechets
  - [x] Formulaire avec calcul live JS des déchets

---

## ✅ PHASE 2 — Analyse des pertes (COMPLÉTÉ)

- [x] Supprimer Pareto du dashboard Chef
- [x] Route `/dashboard/pertes` avec filtre mensuel calendaire
- [x] Template `pertes.html` — KPIs D/P/Q + drill-down par machine + Pareto
- [x] Perte P ventilée par shift (Matin / Après-midi)

---

## ✅ PHASE 3 — Workflow brouillon → soumis → verrouillé (COMPLÉTÉ)

Commit : `5baf68b`

- [x] Statut par défaut `brouillon` + champs `soumis_le` / `modifie_par` / `modifie_le`
- [x] `prix_snapshot` figé à la soumission (premier freeze uniquement)
- [x] Helpers `_peut_modifier()` / `_peut_soumettre()` — contrôle d'accès centralisé
- [x] Routes soumettre / modifier / verrouiller / déverrouiller avec abort(403)
- [x] Dashboard + export Excel filtrés sur `_STATUTS_ANALYSES` (jamais les brouillons)
- [x] `formulaire.html` — mode dual création/modification avec pré-remplissage JS
- [x] `historique.html` — badge brouillon + boutons Soumettre/Supprimer contextuels
- [x] `detail.html` — badge statut + soumis_le + trace modifie_par + boutons d'action

---

## ⏳ PHASES SUIVANTES (backlog)

- [ ] **Phase 4** — Export Excel enrichi
- [ ] **Phase 5** — Dashboard PDG (vue exécutive)
- [ ] **Phase 6** — Dashboard Chef (vue opérationnelle)
- [ ] **Phase 7** — Validation & alertes

---

## 🔧 BUGS RÉSOLUS

| Bug | Cause | Fix |
|-----|-------|-----|
| Internal Server Error | Ancien cuf.db avec schema incompatible (arret.poste_id) | Supprimer cuf.db avant restart |
| Flask reload infini Windows | Watchdog détecte les fichiers Windows Store Python | `use_reloader=False` dans run.py |
| 500 générique sans message | `except (ValueError, KeyError)` trop étroit | `except Exception as e` avec flash |

---

## ⏳ CORRECTION EN COURS — TRS par essence temporalise

Objectif : rendre le TRS par essence cohérent quand plusieurs essences sont sciées dans un même poste.

- [x] Identifier le biais actuel : chaque essence hérite du TRS global du poste.
- [x] Ajouter les heures de traitement début/fin sur chaque ligne de production.
- [x] Calculer le TRS par essence avec les arrêts qui chevauchent réellement la fenêtre de l'essence.
- [x] Mettre à jour la saisie, le détail et le dashboard Chef.
- [x] Vérifier la compatibilité avec les anciennes données et le lancement local.

Revue finale :
- Compilation Python OK.
- Rendu `/login`, `/dashboard/chef` et `/saisie/nouveau` OK sur SQLite mémoire.
- Test métier OK : un arrêt 10h-11h est imputé à Azobé 9h-14h, pas à Ayous 6h-9h.

---

## ⏳ P2 — Socle opérateur et pertes financières nettes

Objectif : rendre wood_pilot défendable comme outil de pilotage et d'aide à la décision, en commençant par la saisie opérateur.

Décisions métier validées :
- [x] Objectif m³/poste = norme interne.
- [x] Prix par essence = prix de vente réel.
- [x] Bois déclassé = revendable à 70 % du prix normal.
- [x] Déchets = valeur nulle en V1.
- [x] Capacités par essence préparées dans Paramètres, même si elles restent identiques au départ.
- [x] Arrêts planifiés = perte seulement sur dépassement de la durée prévue.
- [x] Opérateur = saisie et historique opérationnel sans chiffres économiques.

Étapes :
- [x] Ajouter l'identité de l'opérateur terrain sur les fiches de saisie.
- [x] Masquer les indicateurs économiques aux opérateurs.
- [x] Aligner les calculs financiers sur CA potentiel − CA réel valorisé.
- [x] Passer le taux de revente du déclassé à 70 % et garder les déchets à 0 FCFA.
- [x] Préparer les capacités par essence dans Paramètres.
- [x] Vérifier les parcours `/saisie/nouveau`, `/saisie/historique`, `/saisie/poste/<id>`, `/dashboard/pertes`.

Revue finale :
- Compilation Python OK.
- Test métier OK : maintenance planifiée 50 min avec 30 min prévues = 20 min d'impact TRS.
- Test rôle OK : opérateur sans manque à gagner ni prix/m³, chef avec indicateurs économiques.
- Rendu OK : `/dashboard/chef`, `/dashboard/pertes`, `/admin/parametres`, `/dashboard/pdg`, `/dashboard/export/excel`, `/saisie/feuille-releve`.

---

## ⏳ P2.1 — Profil opérateur, étape 1 : accueil terrain

Objectif : donner à l'opérateur un point d'entrée simple, orienté collecte terrain.

- [x] Créer une route `/saisie/accueil`.
- [x] Afficher les actions utiles : nouvelle fiche, continuer brouillon, feuille terrain, historique.
- [x] Afficher les compteurs opérationnels sans indicateurs économiques.
- [x] Rediriger le rôle opérateur vers cet accueil après connexion.
- [x] Vérifier le rendu et les parcours opérateur.

Revue finale :
- Compilation Python OK.
- Connexion opérateur redirige vers `/saisie/accueil`.
- Rendu OK : `/saisie/accueil`, `/saisie/historique`, `/saisie/nouveau`, `/saisie/feuille-releve`.
- Contrôle rôle OK : l'accueil opérateur n'affiche ni manque à gagner ni prix/m³.

---

## ⏳ P2.1 — Profil opérateur, étape 2 : fiches à corriger

Objectif : permettre au chef production/admin de renvoyer une fiche soumise vers l'opérateur avec un motif de correction.

- [x] Ajouter les champs de retour correction sur `Equipe`.
- [x] Ajouter le statut `a_corriger`.
- [x] Autoriser l'opérateur à modifier et resoumettre uniquement ses fiches `brouillon` ou `a_corriger`.
- [x] Ajouter une action chef/admin "Renvoyer à corriger".
- [x] Afficher les fiches à corriger dans l'accueil, l'historique et le détail.
- [x] Vérifier le parcours complet : opérateur soumet → chef renvoie → opérateur corrige → opérateur resoumet.

Revue finale :
- Compilation Python OK.
- Test workflow OK : chef renvoie une fiche soumise en `a_corriger`, motif enregistré.
- Test opérateur OK : accueil + historique affichent `À corriger`, détail affiche le motif sans données économiques.
- Test resoumission OK : l'opérateur peut resoumettre sa fiche corrigée, qui repasse en `soumis`.
- Test chef OK : une fiche soumise affiche l'action "Renvoyer à corriger".

---

## ⏳ P2.1 — Profil opérateur, étape 3 : journal d'audit des corrections

Objectif : historiser les corrections pour savoir qui a demandé quoi, qui a modifié quoi, et quand.

- [x] Ajouter un modèle dédié au journal d'audit.
- [x] Enregistrer les événements : renvoi à corriger, modification, resoumission.
- [x] Conserver un résumé Avant/Après des champs importants de la fiche.
- [x] Afficher l'audit uniquement aux rôles chef/admin.
- [x] Vérifier le parcours complet avec preuves.

Revue finale :
- Compilation Python OK.
- Test audit OK : événements `renvoi_correction`, `modification`, `resoumission` créés dans l'ordre.
- Test traçabilité OK : auteur, rôle, ancien statut, nouveau statut, motif et valeurs Avant/Après enregistrés.
- Test accès OK : opérateur voit le motif courant, chef/admin voient le journal d'audit.

Correction UX :
- [x] Le message du chef est visible dans l'accueil opérateur, l'historique, le détail et le formulaire de correction.

---

## ⏳ P2.1 — Profil opérateur, étape 4 : contrôles horaires intelligents

Objectif : détecter les incohérences horaires qui fragilisent les calculs et la lecture métier.

- [x] Ajouter les règles d'alerte sur arrêts invalides, durées nulles et chevauchements par machine.
- [x] Ajouter les règles d'alerte sur créneaux d'essence incomplets, invalides ou chevauchés.
- [x] Vérifier l'affichage dans le détail et l'historique.
- [x] Fournir des exemples de saisie pour tester chaque règle dans l'app.

Revue finale :
- Compilation Python OK.
- Test R5 OK : arrêt à durée nulle détecté.
- Test R6 OK : deux arrêts sur la même machine avec chevauchement détectés.
- Test R7 OK : créneau d'essence incomplet détecté.
- Test R8 OK : deux essences qui se chevauchent détectées sans bloquer la soumission.
- Rendu OK : détail affiche les messages, historique affiche le drapeau d'anomalies.

---

## ⏳ P2.1 — Profil opérateur, étape 5 : saisie guidée des arrêts

Objectif : réduire les erreurs de saisie des arrêts en guidant l'opérateur avec des choix simples.

- [x] Ajouter la confirmation explicite `Aucun arrêt pendant le poste`.
- [x] Ajouter une nomenclature simple de causes d'arrêt prédéfinies.
- [x] Auto-remplir la catégorie à partir de la cause choisie.
- [x] Afficher une aide courte pour expliquer chaque cause.
- [x] Adapter les contrôles qualité et les écrans de détail.
- [x] Fournir des cas d'utilisation testables après mise à jour.

Revue finale :
- Compilation Python OK.
- Test `Aucun arrêt` OK : les lignes d'arrêt parasites sont ignorées et la fiche affiche la confirmation.
- Test `Changement de lame` OK : cause enregistrée, catégorie `Réglage / outil`, commentaire conservé.
- Test `Maintenance prévue` OK : 50 min réelles, 30 min prévues, 20 min impactent le TRS.
- Rendu OK : formulaire de saisie et dashboard chef.

Correction UX :
- [x] Les causes d'arrêt sont visibles sous forme de boutons rapides avant les champs.
- [x] Le bug JavaScript après suppression du dernier arrêt est corrigé.
- [x] Test rendu OK : le formulaire affiche `Utilisation rapide`, `Changement de lame`, `Manque de bois`.
- [x] `Autre` affiche un champ pour écrire la cause manuellement.
- [x] `Changement de lame` affiche un champ pour préciser la lame ou le motif.
- [x] Les champs horaires de production et d'arrêt sont agrandis pour mieux lire l'heure.

---

## ⏳ P2.1 — Profil opérateur, étape 6 : vérification avant soumission

Objectif : faire relire une fiche à l'opérateur avant l'envoi final, avec résumé métier et alertes sans chiffres économiques.

- [x] Ajouter une route `/saisie/equipe/<id>/verification`.
- [x] Afficher le résumé de la fiche : date, poste, opérateur, essences, volumes, arrêts.
- [x] Afficher les erreurs bloquantes avant soumission.
- [x] Afficher les alertes horaires non bloquantes sur les brouillons.
- [x] Afficher le message du chef pour les fiches `a_corriger`.
- [x] Remplacer les soumissions directes depuis détail/historique par un passage par la vérification.
- [x] Vérifier que l'opérateur ne voit ni TRS, ni FCFA, ni prix sur cet écran.

Revue finale :
- Compilation Python OK.
- Test rendu OK : fiche correcte → page `Fiche prête à soumettre`.
- Test blocage OK : conforme + déclassé > entrée → soumission bloquée.
- Test alerte OK : deux arrêts qui se chevauchent sur la même machine affichent `R6` et restent soumettables.
- Test correction OK : une fiche `a_corriger` affiche le message du chef avant resoumission.
- Test workflow OK : détail et historique pointent vers la vérification, puis la soumission finale fige les prix.

---

## ⏳ P2.1 — Profil opérateur, étape 7 : fiches terrain imprimables et téléchargeables

Objectif : permettre le travail papier/offline et l'archivage terrain sans bloquer la production.

- [x] Améliorer la fiche terrain vierge avec action d'impression et téléchargement.
- [x] Ajouter une fiche remplie par poste `/saisie/poste/<id>/fiche`.
- [x] Ajouter le téléchargement HTML autonome des fiches vierges et remplies.
- [x] Ajouter les boutons depuis l'accueil opérateur, le détail et l'historique.
- [x] Garantir que la fiche opérateur ne contient ni TRS, ni FCFA, ni prix.
- [x] Vérifier les droits : un opérateur ne peut pas ouvrir la fiche d'un autre opérateur.

Revue finale :
- Compilation Python OK.
- Test fiche vierge OK : impression + téléchargement disponibles.
- Test fiche remplie OK : essences, volumes, arrêts, notes et signatures affichés.
- Test téléchargement OK : `Content-Disposition: attachment` sur fiche vierge et fiche remplie.
- Test accès OK : opérateur propriétaire autorisé, autre opérateur refusé, chef autorisé.
- Test confidentialité OK : aucun `FCFA` ni `TRS` dans la fiche imprimable opérateur.

Correction :
- [x] Supprimer les options de téléchargement HTML, car elles ne produisaient pas un vrai PDF.
- [x] Garder uniquement `Imprimer / enregistrer en PDF` pour les fiches générées par l'application.

---

## ⏳ P2.1 — Profil opérateur, étapes 8 et 9 : workflow papier → numérique + pièce jointe

Objectif : tracer clairement les fiches ressaisies depuis papier et conserver la preuve terrain signée.

- [x] Ajouter le mode de saisie : directe dans l'application ou ressaisie depuis fiche papier.
- [x] Ajouter l'information `fiche papier signée disponible`.
- [x] Ajouter une pièce jointe PDF/photo pour la fiche terrain signée.
- [x] Stocker les pièces jointes dans `instance/fiches_papier`.
- [x] Protéger l'accès : opérateur propriétaire seulement, chef/admin autorisés.
- [x] Afficher l'origine de la saisie dans le formulaire, le détail, la vérification et la fiche imprimable.
- [x] Refuser les extensions non prévues.

Revue finale :
- Compilation Python OK.
- Test création OK : fiche `papier`, case signée, PDF joint et stocké.
- Test détail/vérification OK : origine papier + nom du fichier affichés.
- Test fiche imprimable OK : origine papier et pièce jointe indiquées, sans `TRS` ni `FCFA`.
- Test accès OK : opérateur propriétaire autorisé, autre opérateur refusé, chef autorisé.
- Test sécurité OK : fichier `.exe` refusé avec message clair.

---

## ⏳ P2.1 — Profil opérateur, étapes 10 et 11 : statuts précis + validation chef

Objectif : séparer clairement les fiches encore terrain des fiches réellement exploitables dans les tableaux de bord.

- [x] Ajouter le statut `a_verifier` pour les fiches envoyées au chef mais pas encore validées.
- [x] Ajouter le statut `valide_chef` pour les fiches validées et exploitables dans les analyses.
- [x] Conserver `verrouille` pour les fiches définitives.
- [x] Garder l'ancien statut `soumis` comme compatibilité historique.
- [x] Faire passer la soumission opérateur de `brouillon/a_corriger` vers `a_verifier`.
- [x] Ajouter l'action chef/admin `Valider chef`.
- [x] Exclure les fiches `brouillon`, `a_verifier` et `a_corriger` des calculs de tableaux de bord.
- [x] Afficher les fiches `a_verifier` comme alertes chef à traiter.
- [x] Permettre au chef de renvoyer une fiche `a_verifier` ou `valide_chef` à corriger avec message visible par l'opérateur.
- [x] Mettre à jour les badges, libellés, exports et tableaux de bord.

Revue finale :
- Compilation Python OK.
- Test workflow OK : `brouillon` → `a_verifier` → `a_corriger` → `a_verifier` → `valide_chef` → `verrouille`.
- Test dashboard chef OK : les fiches `a_verifier` apparaissent dans les alertes de validation.
- Test calculs OK : une fiche `a_verifier` n'est pas comptée dans les indicateurs, une fiche `valide_chef` l'est.
- Test audit OK : l'action `validation_chef` est enregistrée dans le journal.
- Test opérateur OK : le message de correction du chef reste visible avant resoumission.

---

## ⏳ P2.1 — Profil opérateur, étape 12 : accueil plus pratique et cliquable

Objectif : simplifier l'accueil opérateur pour que chaque bloc visible mène directement à une action utile.

- [x] Remplacer les KPI passifs par des cartes d'action cliquables.
- [x] Mettre en avant l'action prioritaire : corriger, continuer un brouillon ou créer une fiche.
- [x] Garder un accès rapide à la fiche papier vierge.
- [x] Rendre les fiches récentes cliquables selon leur statut.
- [x] Réduire les textes et supprimer les blocs non nécessaires à l'action immédiate.
- [x] Vérifier le rendu opérateur sans chiffres économiques.

Revue finale :
- Compilation Python OK.
- Test rendu OK : `/saisie/accueil` affiche l'action prioritaire, les cartes cliquables et les dernières fiches.
- Test action OK : `À corriger` et `Brouillons` ouvrent directement la fiche à traiter.
- Test confidentialité OK : aucun `FCFA`, `TRS`, `prix/m³` ni manque à gagner sur l'accueil opérateur.
- Contrôle interface OK : suppression des KPI passifs et du bloc de rappels non actionnable.

---

## ⏳ P2.1 — Profil opérateur, étape 13 : saisie production par essence plus agréable

Objectif : rendre les passages d'essence faciles à créer, lire et compléter sur tablette/ordinateur.

- [x] Transformer chaque ligne de production en carte lisible.
- [x] Ajouter des boutons rapides pour créer un passage par essence.
- [x] Ajouter les boutons `Début maintenant` et `Fin maintenant`.
- [x] Afficher la durée calculée du passage.
- [x] Afficher automatiquement les déchets estimés et alerter si les volumes sortis dépassent l'entrée.
- [x] Garder la possibilité de saisir plusieurs passages de la même essence.
- [x] Vérifier que la sauvegarde et la modification conservent les données existantes.

Revue finale :
- Compilation Python OK.
- Test rendu OK : le formulaire affiche les cartes de passage, boutons essence, durée et déchets estimés.
- Test confidentialité OK : aucun `FCFA`, `TRS`, `prix/m³` ni manque à gagner dans le formulaire opérateur.
- Test sauvegarde OK : `Ayous 06:00-09:00`, `Azobé 09:00-14:00`, `Ayous 14:00-15:00` sont conservés comme trois passages distincts.
- Contrôle diff OK : pas d'erreur `diff --check`, uniquement les avertissements Windows LF/CRLF.

---

## ⏳ P2.1 — Profil opérateur, étape 13B : confidentialité et filtres des fiches

Objectif : garantir que l'opérateur ne voit que ses propres fiches, tout en donnant au chef/admin une vue globale filtrable.

- [x] Confirmer le cloisonnement opérateur sur historique, détail, fiche imprimable et pièce jointe.
- [x] Ajouter les filtres d'historique : jour, statut, essence, poste, mode de saisie.
- [x] Ajouter le filtre opérateur pour chef/admin.
- [x] Garder l'interface opérateur simple et sans indicateurs économiques.
- [x] Vérifier par test qu'un opérateur ne peut pas voir les fiches d'un autre.

Revue finale :
- Compilation Python OK.
- Test accès OK : un opérateur ne voit que ses fiches dans l'historique.
- Test sécurité OK : un opérateur reçoit `403` s'il tente d'ouvrir la fiche d'un autre opérateur.
- Test chef OK : le chef voit toutes les fiches.
- Test filtres OK : opérateur, jour, statut, essence et mode de saisie filtrent correctement.

---

## ⏳ P2.1 — Profil opérateur, étape 14 : assistant de calcul des volumes

Objectif : permettre à l'opérateur de calculer un volume à partir du nombre de pièces et des dimensions, sans calcul manuel.

- [x] Ajouter un assistant repliable dans chaque passage d'essence.
- [x] Calculer `nombre × longueur × largeur × épaisseur`.
- [x] Gérer les unités simples : longueur en mètres, largeur/épaisseur en centimètres.
- [x] Permettre d'appliquer le résultat à `entrée`, `conforme` ou `déclassé`.
- [x] Proposer `remplacer` ou `ajouter` au champ cible.
- [x] Vérifier que le formulaire reste utilisable en saisie directe m³.

Revue finale :
- Compilation Python OK.
- Test rendu OK : le formulaire affiche `Calcul pièces`, pièces, longueur, largeur, épaisseur, résultat, `Remplacer` et `Ajouter`.
- Test confidentialité OK : aucun `FCFA`, `TRS`, `prix/m³` ni manque à gagner dans le formulaire opérateur.
- Test sauvegarde OK : les valeurs calculées et copiées dans les champs m³ existants sont bien enregistrées.
- Contrôle diff OK : pas d'erreur `diff --check`, uniquement les avertissements Windows LF/CRLF.

---

## ⏳ P2.1 — Profil opérateur, étape 15 : commentaires opérateur transmis au chef

Objectif : faire remonter les observations terrain utiles au chef production, sans surcharger la saisie opérateur.

- [x] Renommer la zone générale en `Commentaires pour le chef`.
- [x] Afficher les commentaires généraux et les commentaires d'arrêts sur la vérification avant envoi.
- [x] Afficher un bloc `Commentaires opérateur` dans le détail d'une fiche.
- [x] Ajouter un filtre historique `Avec commentaires`.
- [x] Signaler les fiches commentées dans l'historique avec un extrait lisible.
- [x] Vérifier le parcours opérateur → chef avec une fiche commentée.

Revue finale :
- Compilation Python OK.
- Test workflow OK : l'opérateur crée une fiche avec commentaire général + commentaire d'arrêt.
- Test vérification OK : l'écran avant envoi affiche `Commentaires transmis au chef` sans `FCFA`.
- Test chef OK : le filtre historique `Avec commentaires` retrouve la fiche et le détail affiche `Commentaires opérateur`.

Note pour le futur profil chef production :
- [ ] Exploiter les commentaires opérateur comme matière de décision : filtre prioritaire, lecture dans les fiches à valider, repérage des arrêts longs sans explication, synthèse par machine/cause.

---

## ⏳ P2.1 — Profil opérateur, étape 16 : saisie des arrêts plus rapide

Objectif : rendre la saisie des arrêts plus lisible et plus rapide, surtout sur tablette, sans ajouter de charge mentale.

- [x] Transformer chaque arrêt en carte lisible.
- [x] Ajouter les boutons `Début maintenant` et `Fin maintenant`.
- [x] Afficher la durée réelle de l'arrêt en direct.
- [x] Signaler immédiatement une heure de fin avant l'heure de début.
- [x] Rappeler de commenter les arrêts longs.
- [x] Vérifier que la sauvegarde des arrêts reste compatible avec l'existant.

Revue finale :
- Compilation Python OK.
- Test rendu OK : le formulaire affiche les cartes d'arrêt, les actions d'heure rapide et les alertes d'arrêt long.
- Test sauvegarde OK : un arrêt Bicoupe 07:00 → 08:10 est enregistré à 70 min avec son commentaire terrain.
- Test confidentialité OK : le formulaire et le détail opérateur restent sans `FCFA`.

---

## ⏳ P2.1 — Profil opérateur, étape 17 : sauvegarder puis vérifier directement

Objectif : réduire les clics après la saisie en envoyant l'opérateur directement vers l'écran de vérification quand la fiche est prête.

- [x] Ajouter un bouton `Enregistrer et vérifier`.
- [x] Conserver le bouton de sauvegarde simple pour les brouillons incomplets.
- [x] Rediriger une nouvelle fiche vers `/verification` si l'opérateur choisit ce parcours.
- [x] Rediriger une fiche corrigée vers `/verification` après modification.
- [x] Vérifier que l'envoi au chef reste séparé de la sauvegarde.
- [x] Vérifier la confidentialité opérateur.

Revue finale :
- Compilation Python OK.
- Test création OK : `Enregistrer brouillon` redirige vers l'historique.
- Test création OK : `Enregistrer et vérifier` redirige vers l'écran de vérification.
- Test statut OK : la fiche reste en `brouillon` tant que l'opérateur n'a pas cliqué sur `Envoyer au chef`.
- Test modification OK : une fiche modifiée avec `Enregistrer et vérifier` revient à la vérification.
- Test confidentialité OK : le formulaire et la vérification opérateur restent sans `FCFA`.

---

## ⏳ P2.1 — Profil opérateur, étape 18 : reprendre la structure d'une fiche

Objectif : réduire la ressaisie lorsque deux postes ont la même structure de production, sans copier les données terrain variables.

- [x] Ajouter une action `Reprendre structure`.
- [x] Créer une nouvelle fiche en `brouillon`.
- [x] Copier seulement l'effectif, le poste, les essences et les créneaux.
- [x] Ne pas copier volumes, arrêts, commentaires, pièce jointe ou statut.
- [x] Protéger l'accès : opérateur propriétaire, chef/admin autorisés.
- [x] Vérifier que la fiche copiée reste modifiable avant envoi.

Revue finale :
- Compilation Python OK.
- Test duplication OK : deux passages Ayous/Azobé sont repris avec horaires, mais volumes remis à 0.
- Test sécurité OK : un autre opérateur ne peut pas dupliquer une fiche qui ne lui appartient pas.
- Test confidentialité OK : détail et formulaire opérateur restent sans `FCFA`.

---

## ⏳ P2.1 — Profil opérateur, étape 19 : brouillons incomplets mieux guidés

Objectif : dire clairement à l'opérateur ce qui bloque ou fragilise l'envoi d'une fiche au chef.

- [x] Détecter les volumes entrée manquants par essence.
- [x] Détecter les créneaux d'essence incomplets.
- [x] Conserver les incohérences métier bloquantes existantes.
- [x] Afficher les points bloquants dans `À compléter avant envoi`.
- [x] Afficher les points non bloquants dans `Points à relire`.
- [x] Bloquer aussi la soumission directe si un point bloquant existe.

Revue finale :
- Compilation Python OK.
- Test OK : une fiche Ayous avec volume entrée 0 affiche `Volume entrée manquant pour Ayous`.
- Test OK : l'envoi direct d'une fiche incomplète revient vers l'écran de vérification.
- Test confidentialité OK : aucun `FCFA` dans la vérification opérateur.

---

## ⏳ P2.1 — Profil opérateur, étape 20 : résumé opérateur avant envoi

Objectif : montrer simplement ce qui a été saisi, ce qui reste à relire, et ce qui part au chef.

- [x] Ajouter un bloc `Résumé opérateur` sur l'écran de vérification.
- [x] Afficher `Ce que j'ai saisi`.
- [x] Afficher `À relire`.
- [x] Afficher `Ce qui part au chef`.
- [x] Garder une vue sans TRS, sans prix et sans chiffres économiques.

Revue finale :
- Compilation Python OK.
- Test OK : une fiche complète affiche le résumé, les données transmises au chef et les commentaires.
- Test confidentialité OK : aucun `FCFA` dans le résumé opérateur.

---

## ⏳ P2.1 — Étape 22 : préparer la validation chef

Objectif : préparer le futur profil chef production en rendant les fiches à valider plus exploitables.

- [x] Enrichir les fiches `à vérifier chef` avec le nombre de commentaires.
- [x] Enrichir les fiches `à vérifier chef` avec le nombre d'anomalies.
- [x] Afficher un extrait de commentaire opérateur dans l'alerte chef.
- [x] Prioriser visuellement les fiches avec commentaires/anomalies.
- [x] Ne pas encore refondre tout le profil chef production.

Revue finale :
- Compilation Python OK.
- Test OK : une fiche envoyée au chef avec commentaires apparaît dans le dashboard chef.
- Test OK : une fiche avec anomalie horaire affiche un badge d'alerte côté chef.

---

## ✅ P2.2 — Corrections immédiates du profil opérateur

Objectif : corriger les fragilités critiques détectées dans l'audit du profil opérateur, sans surcharger l'interface.

- [x] Séparer clairement le responsable terrain de la personne qui remplit la fiche.
- [x] Bloquer côté serveur les volumes, effectifs et durées négatifs.
- [x] Rendre la preuve papier obligatoire avant envoi quand la fiche est une ressaisie papier.
- [x] Verrouiller la catégorie d'arrêt : elle est déduite de la cause, pas choisie librement.
- [x] Remplacer les libellés opérateur ambigus `À vérifier chef` par `Chez le chef`.
- [x] Vérifier le workflow création → vérification → envoi avec ces nouvelles règles.

Revue finale :
- Compilation Python OK.
- Test création OK : volume négatif refusé et aucune fiche parasite créée.
- Test papier OK : une ressaisie papier sans pièce jointe/signature reste bloquée avant l'envoi au chef.
- Test arrêt OK : une catégorie falsifiée côté formulaire est ignorée et recalculée depuis la cause.
- Test statut OK : une fiche envoyée affiche `Chez le chef`.
- Test traçabilité OK : `Responsable terrain` et `Fiche remplie par` sont conservés et affichés.

---

## ✅ P2.3 — Corrections opérateur ciblées : CSRF, upload, guidage

Objectif : corriger uniquement les oublis 1, 2, 3 et 4 du profil opérateur.

- [x] Activer CSRF globalement et ajouter les tokens aux formulaires/POST AJAX.
- [x] Renforcer la sécurité des pièces jointes papier par vérification de signature fichier.
- [x] Ajouter une cible de correction pour guider l'opérateur vers le bloc/champ concerné.
- [x] Vérifier le rendu serveur du formulaire opérateur et l'affichage du guidage.
- [x] Vérifier les parcours POST critiques avec CSRF et les refus sans CSRF.

Revue finale :
- Compilation Python OK.
- Import application OK : `APP_IMPORT_OK`.
- Test CSRF OK : POST sans jeton refusé sans création de fiche.
- Test upload OK : faux PDF refusé par signature binaire.
- Test correction ciblée OK : `bloc-arrets` stocké et lien `#bloc-arrets` visible côté opérateur.
- Test lancement réel OK : serveur Flask temporaire, `/login` 200, connexion opérateur, `/saisie/nouveau` 200.
- Correction anti-crash OK : les templates vérifient que `csrf_token` existe avant de l'appeler, utile si un ancien serveur recharge les templates sans redémarrage Python.

---

## ⏳ P2.4 — Profil opérateur terrain plus simple

Objectif : rendre le profil opérateur plus sûr, plus guidé et plus facile à utiliser en atelier.

- [x] Étape 1 — Alerte forte après duplication : forcer la vérification de la date et rappeler que les volumes/arrêts ne sont pas copiés.
- [x] Étape 2 — Aide conforme / déclassé / déchets directement dans la saisie production.
- [x] Étape 3 — Sécuriser le bouton `Aucun arrêt` pour éviter l'effacement accidentel.
- [x] Étape 4 — Saisie guidée en étapes sans casser le formulaire existant.
- [x] Étape 5 — Checklist de vérification plus visuelle.
- [x] Étape 6 — Historique opérateur simplifié.

Revue étape 1 :
- Alerte flash renforcée après `Reprendre structure`.
- Redirection vers le formulaire avec le marqueur `reprise=1`.
- Bandeau visible en haut du formulaire pour rappeler de vérifier la date/poste.
- Rappel clair : essences et créneaux repris, volumes, arrêts, commentaires et pièce jointe non copiés.
- Test OK : la duplication crée une nouvelle fiche brouillon avec volumes à 0 et affiche l'alerte de reprise.

Correction UX chef :
- [x] Clarifier `Zone à corriger` côté chef : ce choix indique la zone à ouvrir pour l'opérateur, il ne corrige pas la fiche directement.
- [x] Ajouter un aperçu de la zone choisie.
- [x] Ajouter un lien `Voir cette zone dans le formulaire` pour prévisualiser l'ancre.
- [x] Confirmer après envoi quelle zone a été indiquée à l'opérateur.
- Test OK : chef choisit `Arrêts machine`, renvoie la fiche, `correction_cible = bloc-arrets`, puis l'opérateur voit le lien `#bloc-arrets`.

Correction UX détail fiche :
- [x] Masquer le `Journal d'audit des corrections` de l'écran normal de détail.
- [x] Conserver les traces en base pour audit futur, sans les afficher au chef dans son flux de travail.
- Test OK : une fiche avec `soumission_initiale` en base n'affiche plus `Journal d'audit`, `soumission_initiale` ni `Voir les valeurs tracées`.

Revue finale P2.4 :
- Aide production ajoutée : conforme, déclassé, déchets expliqués dans le bloc production.
- `Aucun arrêt` sécurisé : confirmation forte si des arrêts existent déjà.
- Formulaire guidé en 5 étapes : en-tête, production, arrêts, commentaires/papier, vérification.
- Vérification enrichie par une checklist visuelle : vert complet, orange à relire, rouge bloquant.
- Historique opérateur simplifié : filtres directs, cartes par fiche, action principale visible selon le statut.
- Test OK : rendu formulaire, vérification, historique, filtre `Validées`, lien de correction ciblée.

Correction UX chef :
- [x] Simplifier le renvoi à corriger : remplacer la liste technique par des boutons `Production`, `Arrêts`, `Papier`, `Commentaire`, `En-tête`.
- [x] Ajouter des messages rapides pour éviter au chef de tout retaper.
- [x] Garder le stockage `correction_cible` pour envoyer l'opérateur vers le bon bloc.
- Test OK : bouton `Arrêts` équivaut à `bloc-arrets` et la fiche passe bien en `a_corriger`.

Recette finale opérateur :
- [x] Parcours complet OK : création fiche → vérification → envoi chef → retour correction → correction opérateur → resoumission → validation chef.
- [x] Confidentialité OK : les vues opérateur testées ne montrent pas `FCFA`, `prix/m³` ou manque à gagner.
- [x] Workflow correction OK : le chef choisit une zone simple, l'opérateur revient directement au bon bloc.
- [x] CSRF OK : login, création, vérification et envoi fonctionnent avec jeton CSRF actif.
- [x] Rendu serveur OK : formulaire, historique, détail, vérification et accueil opérateur.

---

## ⏳ P3.1 — Profil Chef Scierie : accueil Aujourd'hui

Objectif : donner au chef scierie une première vue courte, actionnable et orientée décision immédiate.

- [x] Créer une zone `Aujourd'hui` en haut du dashboard Chef.
- [x] Afficher les actions immédiates : fiches à contrôler, corrections en attente, postes non saisis, brouillons anciens.
- [x] Ajouter 5 KPI du jour : objectif, fiches à traiter, arrêts, rendement matière, déclassement.
- [x] Afficher les postes du jour Matin / Après-midi avec statut et accès direct.
- [x] Vérifier le rendu `/dashboard/chef` et le lancement Flask avant clôture.

---

## ⏳ P3.2 — Profil Chef Scierie : validation fiche assistée

Objectif : aider le chef à valider vite, sans laisser passer les incohérences fortes.

- [x] Ajouter une synthèse `Validation chef` sur la page détail fiche.
- [x] Distinguer les anomalies bloquantes et les avertissements métier.
- [x] Bloquer côté serveur la validation si une anomalie rouge est présente.
- [x] Demander une confirmation et un motif si le chef valide malgré avertissements orange.
- [x] Mettre en évidence les arrêts longs dans la table des arrêts.
- [x] Vérifier le rendu détail fiche et les parcours validation bloquée / validation avec avertissement.

---

## ⏳ P3.3 — Profil Chef Scierie : page Fiches chef

Objectif : donner au chef une liste de contrôle dédiée aux fiches, au lieu de l'obliger à passer par l'historique opérateur.

- [x] Créer la route `/dashboard/chef/fiches`.
- [x] Ajouter les filtres : statut, période, équipe, utilisateur, anomalies, recherche rapide.
- [x] Afficher une liste actionnable : fiche, date, équipe, opérateur, essences, volume, TRS, arrêts, anomalies, statut, action.
- [x] Relier le dashboard Chef et la navigation à cette nouvelle page.
- [x] Vérifier le rendu et les filtres avant commit.

---

## ⏳ P3.4 — Profil Chef Scierie : Machines & Arrêts

Objectif : donner au chef une vue de diagnostic pour comprendre quelles machines et quelles causes bloquent réellement la production.

- [x] Créer la route `/dashboard/chef/machines`.
- [x] Ajouter une lecture officielle et une lecture temps réel.
- [x] Classer les machines par durée d'arrêt, fréquence, cause dominante et statut.
- [x] Afficher les arrêts longs et les récurrences simples.
- [x] Relier le dashboard Chef et la navigation à cette page.
- [x] Vérifier le rendu, les filtres et le lancement Flask avant commit.

---

## ⏳ P3.5 — Profil Chef Scierie : Résolution guidée Ishikawa + 5 Pourquoi

Objectif : transformer les symptômes terrain en causes racines défendables pour le pilotage et le mémoire OS4/H2.

- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter les modèles `Probleme`, `IshikawaCause`, `PourquoiNiveau`.
- [x] Créer le blueprint `/problemes` avec workflow : liste, nouveau, Ishikawa, 5 Pourquoi, cause racine, rapport A3.
- [x] Créer les templates de résolution guidée et le CSS associé.
- [x] Ajouter la navigation `Résolution`.
- [x] Intégrer les liens depuis Machines & Arrêts, Pareto, Recommandations, détail fiche et dashboard chef.
- [x] Vérifier les accès rôles, le workflow complet, l'anti-doublon, le CSRF AJAX et l'impression A3.
- [x] Commit et push GitHub.

---

## ⏳ P3.6 — Profil Chef Scierie : Production & Objectifs

Objectif : permettre au chef de voir si la scierie atteint l'objectif, où se situent les écarts et quels postes/essences doivent être analysés.

- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter la route `/dashboard/chef/production`.
- [x] Calculer objectif vs réalisé, écarts par jour, comparaison Matin/Après-midi, production par essence et postes sous objectif.
- [x] Créer l'écran chef avec filtres `officiel` / `temps réel`.
- [x] Relier la navigation et le bloc `Aujourd'hui`.
- [x] Vérifier le rendu, les filtres et les liens vers fiches/Résolution.
- [x] Commit et push GitHub.

---

## ⏳ P3.7 — Profil Chef Scierie : Qualité / Matière

Objectif : montrer où part la matière et identifier les essences/fiches qui créent le plus de déclassement ou de déchets.

- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter la route `/dashboard/chef/qualite`.
- [x] Calculer rendement matière, déclassé, déchets, répartition par essence et comparaison Matin/Après-midi.
- [x] Créer l'écran chef avec filtres `officiel` / `temps réel`.
- [x] Relier la navigation, `Aujourd'hui`, les fiches et le module Résolution.
- [x] Vérifier le rendu, les filtres et les accès rôles.
- [x] Commit et push GitHub.

---

## ⏳ P3.8 — Profil Chef Scierie : Plan d'action léger

Objectif : transformer un problème vu par le chef en décision suivie avec responsable, délai, statut et alerte de retard.

- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter le modèle `ActionChef`.
- [x] Créer les routes `/dashboard/chef/actions`, `/dashboard/chef/actions/nouvelle` et changement rapide de statut.
- [x] Créer les écrans liste actions et création action.
- [x] Ajouter la navigation `Actions Chef`.
- [x] Relier les actions depuis Machines & Arrêts, Production, Qualité, Résolution et détail fiche.
- [x] Afficher les actions en retard dans les actions immédiates du chef.
- [x] Vérifier création, retard, statuts, accès PDG interdit et classement sans action avec motif.
- [x] Commit et push GitHub.

---

## ⏳ P3.9 — Profil Chef Scierie : recette complète

Objectif : vérifier que le profil Chef fonctionne comme une console de pilotage opérationnel après l'ajout des modules Fiches, Machines, Production, Qualité, Résolution et Actions.

- [x] Synchroniser la branche avec les changements de Claude Code.
- [x] Vérifier la compilation Python.
- [x] Vérifier le JavaScript du formulaire de saisie.
- [x] Vérifier les accès : chef/admin autorisés, PDG/opérateur redirigés.
- [x] Tester les pages Chef principales.
- [x] Tester les liens internes des pages Chef.
- [x] Tester une action en retard affichée dans le dashboard.
- [x] Tester le changement de statut d'une action.
- [x] Tester `Classé sans action` refusé sans motif puis accepté avec motif.
- [x] Nettoyer les données temporaires de test.
- [x] Commit et push GitHub.

---

## ⏳ P3.10 — Profil Chef Scierie : priorités de décision

Objectif : transformer les signaux déjà calculés en une courte liste de priorités actionnables pour aider le chef à décider quoi regarder maintenant.

- [x] Synchroniser la branche avec les changements de Claude Code.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter un service léger de priorisation dans le dashboard Chef.
- [x] Remonter les priorités principales : actions en retard, fiches à vérifier, problèmes ouverts, machine prioritaire, production sous objectif, déclassement élevé.
- [x] Afficher un bloc compact `Priorités du chef` sur `/dashboard/chef`.
- [x] Vérifier compilation, rendu dashboard et accès rôles.
- [x] Commit et push GitHub.

---

## ⏳ P3.11 — Profil Chef Scierie : actions directes sur priorités

Objectif : permettre au chef de passer plus vite du signal à l'action depuis le bloc `Priorités du chef`.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter une action secondaire optionnelle aux priorités décisionnelles.
- [x] Préremplir `Action Chef` ou `Résolution` selon le type de priorité.
- [x] Afficher deux boutons quand une priorité a une action directe.
- [x] Vérifier compilation, rendu dashboard et accès rôles.
- [x] Commit et push GitHub.

---

## ⏳ P3.12 — Profil Chef Scierie : formulaire Action guidé

Objectif : rendre la création d'une action plus compréhensible quand elle vient d'une priorité, d'une machine, d'une fiche ou d'une analyse.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter un bloc d'origine visible en haut du formulaire.
- [x] Ajouter une aide courte selon le type d'action.
- [x] Clarifier les champs décision, responsable, délai et description.
- [x] Vérifier compilation, rendu formulaire et accès rôles.
- [x] Commit et push GitHub.

---

## ⏳ P3.13 — Profil Chef Scierie : anti-doublon actions/priorités

Objectif : éviter que le chef crée plusieurs actions ou analyses ouvertes pour le même signal.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Détecter les actions ouvertes similaires pour les priorités machine et objectif.
- [x] Détecter les analyses ouvertes similaires pour le déclassement.
- [x] Afficher `Suivre action existante` ou `Suivre analyse ouverte` au lieu de recréer un doublon.
- [x] Vérifier compilation, rendu dashboard et scénario anti-doublon.
- [x] Commit et push GitHub.

---

## ⏳ P3.14 — Profil Chef Scierie : suivi temporel des actions

Objectif : aider le chef à distinguer les actions en retard, à traiter aujourd'hui, à suivre bientôt et sans délai.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter les statistiques `aujourd_hui`, `bientot`, `sans_delai`.
- [x] Ajouter les filtres correspondants dans `/dashboard/chef/actions`.
- [x] Ajouter des cartes de suivi temporel dans l'écran Actions Chef.
- [x] Vérifier compilation, rendu et filtres.
- [x] Commit et push GitHub.

---

## ⏳ P3.15 — Profil Chef Scierie : signal temporel par action

Objectif : rendre chaque action plus lisible dans la liste en indiquant immédiatement si elle est en retard, à traiter aujourd'hui, à venir, sans délai ou terminée.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Calculer un signal temporel par action.
- [x] Afficher ce signal dans chaque carte action.
- [x] Vérifier compilation, rendu et filtres existants.
- [x] Commit et push GitHub.

---

## ⏳ P3.16 — Profil Chef Scierie : actions rapides sur les actions Chef

Objectif : réduire les clics pour changer le statut d'une action courante.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter des boutons rapides `Démarrer` et `Marquer fait`.
- [x] Garder le changement avancé par liste déroulante.
- [x] Vérifier compilation, rendu et changements de statut.
- [x] Commit et push GitHub.

---

## ⏳ P3.17 — Profil Chef Scierie : actions urgentes sur l'accueil Chef

Objectif : faire apparaître les actions en retard ou proches de l'échéance dès l'ouverture du dashboard Chef.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Calculer les 3 actions les plus urgentes.
- [x] Afficher responsable, délai, statut et lien direct sur l'accueil Chef.
- [x] Vérifier compilation et rendu dashboard.
- [x] Commit et push GitHub.

---

## ⏳ P3.18 — Profil Chef Scierie : traitement direct des actions urgentes

Objectif : permettre au chef de démarrer ou terminer une action urgente directement depuis l'accueil.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter `Démarrer` et `Marquer fait` dans les actions urgentes du dashboard.
- [x] Garder le lien vers la page de suivi complet.
- [x] Vérifier compilation, rendu et changement de statut avec CSRF.
- [x] Commit et push GitHub.

---

## ⏳ P3.19 — Profil Chef Scierie : pilotage des actions par responsable

Objectif : aider le chef à voir rapidement qui porte les actions ouvertes et qui a des retards.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Calculer une synthèse des actions ouvertes par responsable.
- [x] Ajouter un bloc `Par responsable` dans Actions Chef.
- [x] Ajouter un filtre rapide par responsable.
- [x] Vérifier compilation, rendu et filtrage.
- [x] Commit et push GitHub.

---

## ⏳ P3.20 — Profil Chef Scierie : suggestions de responsables dynamiques

Objectif : faciliter la création d'action sans imposer encore une gestion complexe des profils responsables.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Détecter que le formulaire avait déjà une base de suggestions.
- [x] Ajouter les responsables déjà utilisés aux suggestions.
- [x] Garder les responsables terrain par défaut.
- [x] Vérifier compilation, rendu et création d'action.
- [x] Commit et push GitHub.

---

## ⏳ P3.21 — Profil Chef Scierie : délais rapides dans les actions

Objectif : accélérer la création d'une action avec des choix de délai simples.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Analyser le champ délai actuel.
- [x] Ajouter les boutons `Aujourd'hui`, `Demain`, `Dans 3 jours`, `Dans 7 jours`, `Sans délai`.
- [x] Vérifier compilation, rendu et création d'action.
- [x] Commit et push GitHub.

---

## ⏳ P3.22 — Profil Chef Scierie : confirmation avant clôture rapide

Objectif : éviter qu'une action disparaisse du suivi après un clic involontaire sur `Fait`.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Repérer les boutons rapides `Fait` sur le dashboard et la liste Actions Chef.
- [x] Ajouter une confirmation légère avant clôture.
- [x] Vérifier compilation, rendu et changement de statut avec CSRF.
- [x] Commit et push GitHub.

---

## ⏳ P3.23 — Profil Chef Scierie : résultat obligatoire à la clôture

Objectif : conserver la preuve terrain d'une action réellement terminée.

- [x] Synchroniser la branche avec GitHub.
- [x] Vérifier le mécanisme de migration SQLite légère.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Ajouter `note_resultat` au modèle et aux bases existantes.
- [x] Exiger une note courte quand une action passe à `Fait`.
- [x] Adapter les clôtures rapides et avancées.
- [x] Vérifier migration, rendu, validation serveur et CSRF.
- [x] Commit et push GitHub.

---

## ⏳ P3.24 — Profil Chef Scierie : historique métier des actions

Objectif : reconstituer simplement qui a créé, démarré, clôturé ou rouvert une action.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Analyser les modèles et routes Actions Chef.
- [x] Ajouter une table légère d'événements métier.
- [x] Tracer la création et les changements de statut.
- [x] Afficher une timeline repliable dans Actions Chef.
- [x] Vérifier création, transitions, affichage et compilation.
- [x] Commit et push GitHub.

---

## ⏳ P3.25 — Profil Chef Scierie : pilotage des actions par machine

Objectif : aider le chef à retrouver rapidement les décisions ouvertes liées à une machine précise.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Analyser les filtres existants de la page Actions Chef.
- [x] Calculer une synthèse des actions ouvertes par machine.
- [x] Ajouter un bloc `Par machine` cliquable dans Actions Chef.
- [x] Ajouter un filtre exact par machine.
- [x] Vérifier compilation, rendu et filtrage.
- [x] Commit et push GitHub.

---

## ⏳ P3.26 — Profil Chef Scierie : bilan d'efficacité des actions machine

Objectif : aider le chef à vérifier si une action terminée a réellement réduit les arrêts de la machine concernée.

- [x] Synchroniser la branche avec GitHub et relire les règles du projet.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Analyser les données disponibles pour mesurer l'efficacité.
- [x] Comparer une fenêtre courte d'arrêts validés avant et après la clôture.
- [x] Afficher un bilan léger dans les actions terminées liées à une machine.
- [x] Vérifier calcul, rendu et compilation.
- [x] Commit et push GitHub.

---

## ⏳ P3.27 — Profil Chef Scierie : rappel des actions inefficaces

Objectif : empêcher qu'une action machine marquée `Fait` disparaisse du pilotage alors que les arrêts continuent.

- [x] Synchroniser la branche avec GitHub.
- [x] Créer une branche de sauvegarde avant modification.
- [x] Analyser le dashboard Chef et les bilans P3.26.
- [x] Détecter les actions terminées récentes dont le bilan est `À revoir`.
- [x] Afficher un rappel ciblé sur l'accueil Chef avec accès direct au suivi.
- [x] Vérifier calcul, rendu dashboard et compilation.
- [x] Commit et push GitHub.

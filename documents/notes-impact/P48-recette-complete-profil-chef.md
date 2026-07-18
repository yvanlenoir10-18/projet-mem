# P3.31 - Recette complete du profil Chef Scierie

Date : 31/05/2026

## Objectif

Verifier que le profil Chef Scierie est fiable avant d'ajouter de nouvelles fonctionnalites.
La recette couvre la chaine complete :

`collecter -> controler -> diagnostiquer -> analyser -> decider -> suivre -> mesurer l'effet`

## Resultat global

Statut : **valide**

Aucun bug applicatif visible n'a ete detecte pendant la recette. Les donnees temporaires creees
pour les tests ont ete supprimees apres chaque scenario.

## 1. Acces et permissions

Verifications :

- chef et admin : acces aux ecrans de pilotage ;
- operateur : acces aux ecrans terrain, refus sur les ecrans Chef ;
- PDG : refus sur le pilotage Chef, acces aux recommandations partagees ;
- utilisateur non connecte : redirection vers la connexion.

## 2. Fiche terrain vers validation Chef

Scenario teste :

1. L'operateur cree un brouillon Ayous.
2. Il relit la checklist puis envoie la fiche.
3. Le dashboard Chef remonte la fiche a controler.
4. Le chef renvoie : `Verifier le volume conforme Ayous avec le releve du cubeur.`
5. L'operateur voit le message et clique directement vers la zone Production.
6. Il corrige le volume, renvoie la fiche, puis le chef valide.

Resultat :

- transitions correctes : `brouillon -> a_verifier -> a_corriger -> a_verifier -> valide_chef` ;
- message Chef visible cote operateur ;
- lien direct vers la zone a corriger ;
- audit present : soumission initiale, renvoi, modification, resoumission, validation Chef.

## 3. Diagnostic Machines, Production et Qualite

Scenario teste :

- poste temporaire Ayous avec un arret `Blocage grumes recette` de 90 minutes sur `Bicoupe P331`.

Resultat :

- Machines & Arrets : machine, duree, cause, bouton Analyser et bouton Action visibles ;
- Production & Objectifs : ecart journalier et comparaison Matin / Apres-midi visibles ;
- Qualite / Matiere : conforme, declasse, dechets et analyse par essence visibles ;
- Pareto : la cause terrain peut ouvrir une analyse.

## 4. Resolution guidee Ishikawa 6M + 5 Pourquoi

Scenario teste :

1. Ouvrir une analyse depuis le diagnostic machine.
2. Ajouter des causes Machine, Matiere, Methode et Mesure.
3. Repondre a trois niveaux de Pourquoi pour la cause Methode.
4. Supprimer une cause de test et verifier la suppression de ses Pourquoi.
5. Choisir `Routine de controle avant poste absente` comme cause racine.
6. Generer le rapport A3, cloturer puis rouvrir le probleme.

Resultat :

- pre-remplissage depuis la machine fonctionnel ;
- niveau `Analyse solide` atteint avec trois causes et trois Pourquoi ;
- suppression en cascade correcte ;
- rapport A3 imprimable complet ;
- interpretation H2 visible ;
- cloture et reouverture fonctionnelles.

## 5. Cycle Actions Chef

Scenario teste :

1. Creer une action maintenance depuis une machine.
2. Donner une echeance deja depassee.
3. Verifier la remontee du retard dans la liste et sur l'accueil Chef.
4. Passer l'action en cours.
5. Essayer de cloturer sans resultat : refus attendu.
6. Cloturer avec le resultat terrain.
7. Comparer les arrets avant / apres.

Resultat :

- pre-remplissage machine fonctionnel ;
- retard visible et priorise ;
- cloture impossible sans resultat ;
- historique des transitions lisible ;
- bilan initial `A observer` si le recul est insuffisant ;
- bilan `A revoir` si les arrets augmentent apres l'action ;
- propositions de relance : nouvelle action ou analyse causale ;
- filtres machine + efficacite fonctionnels.

## 6. Verification navigateur

Les ecrans suivants ont ete ouverts dans le navigateur local sans `BuildError`,
`UndefinedError` ni erreur interne :

- `/dashboard/chef`
- `/dashboard/chef/fiches`
- `/dashboard/chef/machines`
- `/dashboard/chef/production`
- `/dashboard/chef/qualite`
- `/problemes/`
- `/dashboard/chef/actions`
- `/analyse/arrets`
- `/recommandations/`

## 7. Verification multi-profils

Accueils verifies :

- operateur : `/saisie/accueil`
- chef : `/dashboard/chef`
- admin : `/dashboard/chef`
- PDG : `/dashboard/pdg`
- fiche terrain imprimable : `/saisie/feuille-releve`

## Exemples de recette manuelle a rejouer

### Exemple A - Corriger une fiche

Creer une fiche operateur Ayous, l'envoyer, puis la renvoyer depuis le Chef avec le message :

`Verifier le volume conforme Ayous avec le releve du cubeur.`

Attendu : l'operateur voit le message et ouvre directement la zone Production.

### Exemple B - Comprendre un arret recurrent

Saisir plusieurs arrets Bicoupe avec la cause `Changement de lame`.

Attendu : Machines & Arrets classe Bicoupe en priorite et propose `Analyser` ou `Action`.

### Exemple C - Suivre une decision

Creer une action `Controler la courroie Bicoupe`, responsable `Maintenance`, avec une date limite.

Attendu : l'action remonte si elle est en retard ; sa cloture exige un resultat ; son effet est ensuite
compare aux arrets avant / apres.

## Commandes de verification executees

```powershell
.\venv\Scripts\python.exe -m compileall app
git diff --check
powershell -ExecutionPolicy Bypass -File .\scripts\redemarrer_wood_pilot.ps1
```

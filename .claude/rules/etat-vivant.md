# Règle — ETAT.md, état vivant entre sessions

## Lecture (début de session)

Lire **`ETAT.md`** (racine du dépôt) avant tout travail. Il contient :
- l'état courant du projet et la prochaine étape ;
- les décisions verrouillées récentes (complément de CLAUDE.md) ;
- les leçons apprises (pièges déjà rencontrés — ne pas les répéter) ;
- la définition objective de « livré ».

## Définition de « livré » (rappel)

Une feature n'est livrée que si : compilation OK + `smoke.sh` 20/20 (le total ne baisse jamais) + screenshots si UI + note d'impact + commit/push sur la branche de travail + ETAT.md mis à jour. Jamais « ça a l'air bon ».

## Mise à jour (fin de session)

Mettre à jour ETAT.md à la fin de chaque session de travail : « Dernière session », « En cours », nouvelles décisions verrouillées, leçons apprises (append-only), section soutenance si une feature a été livrée.

**Une décision structurante non écrite dans ETAT.md est considérée comme perdue à la prochaine compaction de conversation.**

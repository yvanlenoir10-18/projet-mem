# Script vidéo — Démonstration CUF Pilotage (2 minutes)

> Vidéo d'explication de l'application, par profil et en général. Durée cible : **2 min 00**.
> Format : capture d'écran de l'app (navigateur) + voix off lisant la colonne « Narration ».
> Rythme : ~2,5 mots/seconde. Répète le parcours de clics une fois AVANT d'enregistrer.

---

## Avant d'enregistrer

1. Lance l'app (`python run.py`) et ouvre `http://127.0.0.1:5000` en **plein écran** du navigateur.
2. Prépare 5 onglets déjà connectés, ou reste sur un onglet et change de profil au fil du script.
3. Ferme les notifications/extensions du navigateur (barre propre).
4. Enregistre en **une seule prise** en lisant la narration à voix posée.

---

## Découpage minuté

| Temps | À l'écran (action) | Narration (voix off) |
|---|---|---|
| **0:00 – 0:12**<br>*Intro* | Page de connexion, puis logo/accueil. | « Voici l'application de pilotage de la production de la chaîne 4 de la scierie CUF. Elle fonctionne **cent pour cent hors ligne**, en local, et sert cinq profils d'un même outil. » |
| **0:12 – 0:38**<br>*Opérateur* | Connexion `edgar@cuf.cm` → accueil opérateur → ouvrir « Nouvelle fiche », montrer essences + arrêts. | « L'**opérateur** saisit au poste, sur le terrain. Il déclare les essences produites, les volumes, et les arrêts machine. L'interface est large et tactile. Si deux essences se chevauchent sur la bicoupe, l'application **refuse la saisie** : une seule pièce passe à la fois. » |
| **0:38 – 1:20**<br>*Chef (cœur)* | Connexion `chef@cuf.cm` → cockpit (verdict, TRS, manque à gagner) → page Fiches (tuiles de statut) → ouvrir une fiche **bloquée** → montrer Pareto/Ishikawa rapidement. | « Le **chef** contrôle et décide. Son cockpit répond en dix secondes : l'usine est-elle sous contrôle, quel est le **TRS**, combien coûte l'écart en FCFA. Il voit toutes les fiches par statut : à corriger, à vérifier, validées, verrouillées — et celles **bloquées** par une anomalie, qu'il ne peut pas valider tant qu'elles ne sont pas corrigées. Il analyse la cause la plus coûteuse avec le **Pareto** et l'**Ishikawa**, puis lance une action. » |
| **1:20 – 1:42**<br>*PDG* | Connexion `pdg@cuf.cm` → dashboard → bloc « Décision financière » (leviers D/P/Q). | « Le **directeur** a une vue financière de décision. La perte est décomposée en trois leviers chiffrés : les **arrêts**, la **cadence**, la **qualité**. Le levier le plus coûteux indique où un investissement rapporte le plus. » |
| **1:42 – 1:55**<br>*Admin* | Connexion `admin@cuf.cm` → Paramètres → modifier un prix → retour Pertes (montant changé). | « L'**administrateur** gère les comptes et les prix. Il modifie un prix, et tous les calculs financiers se recalculent aussitôt : l'outil est **paramétrable**, il s'adapte au marché. » |
| **1:55 – 2:00**<br>*Clôture* | Vue d'ensemble / cockpit chef. | « Du terrain à la direction, une seule application matérialise la boucle d'amélioration continue **DMAIC** de la chaîne 4. » |

---

## Texte de narration en continu (à lire, ~290 mots)

> Voici l'application de pilotage de la production de la chaîne 4 de la scierie CUF. Elle fonctionne cent pour cent hors ligne, en local, et sert cinq profils d'un même outil.
>
> L'opérateur saisit au poste, sur le terrain. Il déclare les essences produites, les volumes, et les arrêts machine. L'interface est large et tactile. Si deux essences se chevauchent sur la bicoupe, l'application refuse la saisie : une seule pièce passe à la fois.
>
> Le chef contrôle et décide. Son cockpit répond en dix secondes : l'usine est-elle sous contrôle, quel est le TRS, combien coûte l'écart en francs. Il voit toutes les fiches par statut : à corriger, à vérifier, validées, verrouillées, et celles bloquées par une anomalie, qu'il ne peut pas valider tant qu'elles ne sont pas corrigées. Il analyse la cause la plus coûteuse avec le Pareto et l'Ishikawa, puis lance une action corrective.
>
> Le directeur a une vue financière de décision. La perte est décomposée en trois leviers chiffrés : les arrêts, la cadence, la qualité. Le levier le plus coûteux indique où un investissement rapporte le plus.
>
> L'administrateur gère les comptes et les prix. Il modifie un prix, et tous les calculs financiers se recalculent aussitôt : l'outil est paramétrable, il s'adapte au marché.
>
> Du terrain à la direction, une seule application matérialise la boucle d'amélioration continue DMAIC de la chaîne 4.

---

## Comment enregistrer (Windows, gratuit)

**Option 1 — Xbox Game Bar (intégré à Windows) :**
1. Ouvre le navigateur avec l'app.
2. Appuie sur **`Win + G`** → clique sur l'icône **Capturer** → bouton **Enregistrer** (ou `Win + Alt + R`).
3. Fais ta démo en lisant la narration.
4. `Win + Alt + R` pour arrêter. La vidéo est dans `Vidéos\Captures`.

**Option 2 — PowerPoint (si installé) :**
Insertion → **Enregistrement d'écran** → sélectionne la zone → Enregistrer. Tu peux ensuite exporter en MP4 (Fichier → Exporter → Créer une vidéo).

**Option 3 — Outils gratuits dédiés :** OBS Studio ou ShareX (plus de contrôle, capture audio + écran).

**Conseils :**
- Branche un micro-casque pour une voix claire.
- Fais **une répétition à blanc** (parcours de clics) avant la vraie prise.
- Vise 1 min 50 – 2 min : il vaut mieux finir un peu avant que dépasser.
- Si tu dépasses, coupe la partie Admin (1:42–1:55) : c'est la moins essentielle.

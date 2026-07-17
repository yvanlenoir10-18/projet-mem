# Fiche de soutenance — Démo CUF Pilotage

> À garder sous les yeux pendant la présentation. Comptes : mot de passe `cuf2026`.
> Lancement : `cd cuf-pilotage ; python run.py` → http://127.0.0.1:5000

---

## Règle d'or

Menez la démo avec **4 écrans = vos figures 9 à 12**, dans cet ordre. Annoncez un chiffre par écran, celui qui est dans le mémoire. **N'ouvrez pas** « Production & Objectifs » (il agrège 3 postes/jour → affiche 70 % ; l'atteinte *par poste* est bien 58 %).

---

## Parcours démo (5 minutes)

**0. Connexion** — montrez d'abord `admin@cuf.cm` → **Utilisateurs** : « L'outil a **4 profils**, de la saisie à la direction. » (= §3.1.4.2)

**1. `prod@cuf.cm` → Tableau de bord « Le Point »** *(figure 9)*
- Phrase : « Le chef voit en direct son **TRS**, l'écart à l'objectif et les arrêts du moment. La compilation, avant inexistante, est automatique. »
- Chiffre à dire : **TRS 64 %** (l'accueil opérateur l'affiche à 64,0 % ; le cockpit à 63,3 % — même moyenne, à un poste nul près).

**2. → Causes d'arrêts (Pareto)** *(figure 10)*
- Phrase : « Le Pareto se régénère à chaque poste. La cause n°1 est le **changement de lame** — c'est là qu'on agit en premier. »
- Chiffre : changement de lame = cause dominante (mémoire : **69 % des arrêts**).

**3. → Qualité / Matière** *(figure 11)*
- Phrase : « Rendement matière **31 %**, essence par essence. Le **Bilinga**, bois dur, est le plus bas à **23,3 %** — la dureté pénalise le rendement. »
- Chiffres : global **31 %**, Bilinga **23,3 %**, Ayous 33,8 %.

**4. `pdg@cuf.cm` → Tableau de bord Direction** *(figure 12)*
- Phrase : « La direction a la synthèse : TRS global, atteinte des objectifs, pertes financières. La performance de la chaîne 4 devient un sujet de direction, plus d'atelier. »

**5. (optionnel, effet fort)** `saisie@cuf.cm` → **Nouvelle saisie** : remplissez une fiche **en direct** → montre le cœur de l'outil et peuple le cockpit à l'instant.

---

## Chiffres-clés à connaître par cœur (app = mémoire)

| Production 14,55 m³/poste · atteinte 58 % · objectif 25 · TRS 64 % (Dispo 79,9 · Perf 92,5 · Qual 84,9) · rendement 31 % · 95 postes · 4 essences (Ayous, **Bilinga**, Iroko, Movingui) |
|---|

---

## Questions pièges → réponses prêtes

**« Le TRS de 64 % est au-dessus de votre hypothèse H3 (< 60 %) ? »**
→ « H3 porte sur l'**absence de système de mesure**. Le vrai problème n'est pas le niveau moyen mais la **dispersion** : mes postes vont de 8 % à 98 %. C'est l'irrégularité qui prouve le défaut de pilotage, et c'est justement ce que l'outil corrige. Nuance confirmée par la littérature : 64 % dépasse les 61 % de Rusman et se situe dans la fourchette 40-60 % de Koç. »

**« Pourquoi 3 postes dans l'app alors qu'on parle de 2 ? »**
→ « La chaîne tourne réellement en 3×8 (matin, après-midi, nuit) ; les relevés le montrent. L'objectif officiel de 25 m³/poste, lui, est calé sur un quart de 8 h. »

**« Le manque à gagner de l'app (≈ 424 M) ne colle pas avec vos 357 M ? »**
→ « Le mémoire chiffre en **prix export FOB** (407-446 k/m³). L'app est paramétrée en **prix marché local** ; elle est **paramétrable** — on change les prix en 10 secondes dans l'admin. Les deux sont du même ordre : plusieurs centaines de millions par an. »

**« D'où viennent les volumes en m³ dans l'app ? »**
→ « Des relevés terrain : temps de marche et cadences chronométrées. Le débité en m³ vient des extractions Cuflink (que je vous montre en annexe, format image). »

**« Pourquoi Bilinga et pas Azobé ? »**
→ « Bilinga est l'essence dure majoritaire de la période (contrats à l'appui) ; c'est elle qui illustre la contrainte matière — capacité 21 m³, rendement 23,3 %. »

**« Est-ce des vraies données ? »**
→ « Oui : 95 postes réels, 5 semaines de relevés. Les indicateurs de l'app correspondent au chiffre près à ceux du mémoire. »

---

## Avant de commencer (checklist 2 min)

- [ ] `python run.py` lancé, page de login OK.
- [ ] Test connexion `prod@cuf.cm` / `cuf2026`.
- [ ] Écrans 1→4 s'ouvrent sans erreur.
- [ ] PDF contrat ouvert dans un onglet (pièce justificative si on demande la source).
- [ ] Cette fiche ouverte sur le téléphone.

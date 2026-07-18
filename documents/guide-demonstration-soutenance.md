# Guide de démonstration — Application CUF Pilotage (soutenance)

> Objectif : montrer **toutes** les fonctionnalités de l'application devant le jury, dans un ordre fluide, sans écran vide. Chaque section indique : l'écran, le chemin, ce qu'on montre, ce qu'on dit, et les termes techniques expliqués.

---

## 0. Avant de commencer (2 min de préparation)

1. Ouvre PowerShell **dans le dossier de l'app** et lance :
   ```powershell
   Set-Location "C:\Users\BWAME EBENGUE\Desktop\CUF MEMOIRE\revue de litterature\cuf-pilotage"; python run.py
   ```
2. Laisse cette fenêtre **ouverte** (elle fait tourner le serveur). Tu dois voir `Running on http://127.0.0.1:5000`.
3. Dans le navigateur, va sur **http://127.0.0.1:5000** (ou l'adresse `192.168.x.x:5000` si tu montres depuis un autre appareil du réseau).

**Comptes de démonstration** (mot de passe unique : `cuf2026`)

| Profil | Email | Ce qu'il représente |
|---|---|---|
| Opérateur | `edgar@cuf.cm` (aussi `messi`, `gerve`, `saisie`) | Saisie au poste, sur le terrain |
| Chef scierie | `chef@cuf.cm` | Contrôle, analyse, décision |
| Chef de production | `prod@cuf.cm` | Même cockpit que le chef (vision production) |
| Directeur (PDG) | `pdg@cuf.cm` | Vue exécutive de direction |
| Administrateur | `admin@cuf.cm` | Paramètres, prix, comptes utilisateurs |

> **Argument d'ouverture** : « L'application est **100 % hors ligne**, stockage local en base SQLite, pensée pour un poste Windows en scierie sans connexion fiable. Cinq profils, un seul outil. »

---

## 1. Connexion et gestion des rôles (1 min)

- **Écran** : page de connexion (`/login`).
- **On montre** : on saisit `edgar@cuf.cm` / `cuf2026`, on est redirigé automatiquement vers l'accueil **opérateur**. On se déconnecte, on se reconnecte en `chef@cuf.cm` → on arrive sur le **cockpit chef**.
- **Ce qu'on dit** : « Chaque profil a ses droits (RBAC) et sa page d'accueil. Un opérateur ne voit pas les mêmes écrans qu'un chef. »
- **Terme expliqué — RBAC** (*Role-Based Access Control*) : contrôle d'accès selon le rôle. Le serveur vérifie le rôle à chaque page ; une page interdite renvoie une erreur d'accès.

---

## 2. Profil OPÉRATEUR — la saisie terrain (5 min)

Connecté en `edgar@cuf.cm`.

### 2.1 Accueil opérateur — `/saisie/accueil`
- **On montre** : les grandes tuiles tactiles (nouvelle fiche, fiches à corriger, historique).
- **Ce qu'on dit** : « Interface large et tactile, pensée pour une saisie rapide au poste, entre deux passages de grumes. »

### 2.2 Nouvelle fiche — `/saisie/nouveau`
- **On montre** : on renseigne un poste (date, Matin/Après-midi, effectif), une ou deux **essences** avec créneaux horaires et volumes (entrée / conforme / déclassé), et un **arrêt** (cause + durée + machine).
- **Démonstration clé — anti-chevauchement** : on met volontairement deux essences sur des créneaux qui se recouvrent → l'app **refuse** et affiche un message. On corrige → la fiche passe.
- **Ce qu'on dit** : « La bicoupe est une machine unique : deux essences ne peuvent pas y passer en même temps. L'app garantit la cohérence physique de la saisie. »
- **Termes expliqués** :
  - **Volume conforme** : bois débité utilisable (vendable). **Déclassé** : bois de moindre qualité, revendu moins cher.
  - **Essences** : les 4 essences de la chaîne 4 — Ayous, Bilinga, Iroko, Movingui.

### 2.3 Historique et cycle de vie — `/saisie/historique`
- **On montre** : la liste des fiches de l'opérateur avec leur **statut**. On filtre par statut.
- **Ce qu'on dit** : « Une fiche suit un cycle : **Brouillon → À vérifier → (À corriger) → Validée → Verrouillée**. »
- **On montre** : une fiche **À corriger** (le chef a demandé une correction avec un motif) → l'opérateur l'ouvre, corrige le volume, re-soumet.

### 2.4 Fiche papier / feuille de relevé — `/saisie/feuille-releve`
- **On montre** : la version imprimable de la fiche (pour le relevé manuel au poste).
- **Ce qu'on dit** : « Transition douce : le terrain garde une trace papier, l'app numérise. »

---

## 3. Profil CHEF SCIERIE — le cœur analytique (10-12 min)

Connecté en `chef@cuf.cm`. C'est le profil le plus riche : prends ton temps ici.

### 3.1 Cockpit — `/dashboard/chef`
- **On montre, de haut en bas** :
  - **Verdict global** (VERT / ORANGE / ROUGE) : « l'usine est-elle sous contrôle ? » en un coup d'œil.
  - **TRS** du jour/période avec flèche de tendance.
  - **Manque à gagner en FCFA** : ce que l'écart de performance coûte.
  - **Priorités décisionnelles** : les 3 actions les plus urgentes, en langage clair.
  - **Signaux** : machine critique, disponibilité, alerte « équipe du soir décroche », déclassement par essence.
  - **Projection fin de poste** (si un poste est en cours).
  - **Boucle Lean** : nombre de problèmes ouverts / actions en cours / actions efficaces.
- **Terme expliqué — TRS** (*Taux de Rendement Synthétique*, en anglais OEE) : mesure de l'efficacité réelle d'une machine. **TRS = Disponibilité × Performance × Qualité**.
  - *Disponibilité* : la machine tournait-elle (peu d'arrêts) ?
  - *Performance* : tournait-elle à la bonne cadence ?
  - *Qualité* : le bois produit était-il conforme ?
- **Ce qu'on dit** : « Le cockpit répond en 10 secondes : où est le problème, combien il coûte, quoi faire d'abord. »

### 3.2 Fiches à contrôler — `/dashboard/chef/fiches`
- **On montre** : les tuiles du haut affichent le **vrai** nombre de chaque statut (Chez le chef · À corriger · Brouillons · Validées). On clique chaque tuile → la liste se filtre.
- **Démonstration du workflow** : on ouvre une fiche **À vérifier**, on la **valide** (elle passe en *valide_chef*) ; sur une autre, on **demande une correction** avec un motif (elle repart chez l'opérateur).
- **Ce qu'on dit** : « Le chef voit tout le cycle de vie et arbitre : valider, corriger, verrouiller. »
- **Terme expliqué — anomalie bloquante** : une incohérence de saisie (ex. chevauchement horaire) empêche la validation tant qu'elle n'est pas corrigée ; un simple *avertissement*, lui, laisse valider.

### 3.3 Machines & arrêts — `/dashboard/chef/machines`
- **On montre** : le **Pareto des arrêts** (quelles causes coûtent le plus de temps), les **récurrences** (même machine + même cause qui reviennent).
- **Terme expliqué — Pareto** : loi du 80/20. On classe les causes d'arrêt par temps perdu décroissant ; on agit d'abord sur les premières.

### 3.4 Production & objectifs — `/dashboard/chef/production`
- **On montre** : l'atteinte de l'objectif, la comparaison Matin vs Après-midi, la projection.
- **Ce qu'on dit** : « L'objectif affiché de CUF est 25 m³/poste ; la production réelle tourne autour de 14,5 m³. L'app rend cet écart visible et chiffré. »

### 3.5 Qualité / matière — `/dashboard/chef/qualite`
- **On montre** : le rendement matière par essence, l'alerte si le déclassement dépasse le seuil.
- **Terme expliqué — rendement matière** : part du bois d'entrée qui ressort en produit conforme. Le reste est déclassé ou perdu en sciure/chutes.

### 3.6 Pertes financières — `/dashboard/pertes`  *(c'est l'écran qu'on vient de réparer)*
- **On montre** : la répartition des pertes en **FCFA** selon les trois leviers **D / P / Q**, le détail par machine et par essence, et l'**encart prix** par essence.
- **Ce qu'on dit** : « Chaque perte de temps ou de qualité est traduite en argent, avec les prix FOB export réels. Le chef peut donc justifier une décision d'investissement. »
- **Terme expliqué — FOB** (*Free On Board*) : prix du bois rendu au port, hors transport maritime — le prix de référence à l'export.

### 3.7 Actions chef — `/dashboard/chef/actions`
- **On montre** : la liste des actions correctives, leur statut, le **bilan en FCFA évités** sur les actions clôturées. On **crée une action** rapidement.
- **Ce qu'on dit** : « L'app ne s'arrête pas au diagnostic : elle suit l'action et mesure si elle a produit un effet. »

### 3.8 Recommandations — `/recommandations/`
- **On montre** : des fiches de recommandation générées sur les **vraies** données, au format structuré (signal détecté, données utilisées, diagnostic probable, prescription, **niveau de confiance**, indicateur à suivre).
- **Ce qu'on dit** : « L'app affiche le **raisonnement** qui mène à la recommandation, pas seulement la recommandation. Elle propose une hypothèse défendable, jamais une vérité magique — et **100 % hors ligne**, sans IA externe. »

### 3.9 Problèmes / Ishikawa — `/problemes/`
- **On montre** : la création d'une analyse de cause racine — diagramme **Ishikawa 6M** puis **5 Pourquoi**, jusqu'au rapport **A3**, puis clôture.
- **Termes expliqués** :
  - **Ishikawa (arête de poisson)** : méthode qui range les causes possibles en 6 familles (les **6M** : Main-d'œuvre, Matériel, Méthode, Milieu, Matière, Mesure).
  - **5 Pourquoi** : on demande « pourquoi ? » cinq fois de suite pour remonter de l'effet visible à la cause profonde.
  - **A3** : rapport de résolution de problème tenant sur une page (format Lean).

### 3.10 Analyse arrêts + Export Excel
- **`/analyse/arrets`** : Pareto détaillé des arrêts.
- **`/dashboard/export/excel`** : génération du rapport mensuel Excel à partager avec la direction.

---

## 4. Profil CHEF DE PRODUCTION — `prod@cuf.cm` (2 min)

- **On montre** : après connexion, on arrive sur **le même cockpit riche** que le chef scierie, avec accès aux mêmes écrans d'analyse.
- **Ce qu'on dit** : « Le chef de production dispose de la vision complète de la performance, orientée production. »

---

## 5. Profil DIRECTEUR / PDG — `pdg@cuf.cm` (2 min)

- **Écran** : dashboard exécutif — `/dashboard/pdg`.
- **On montre** : les indicateurs de haut niveau (production, TRS, manque à gagner, tendances) à jour.
- **Ce qu'on dit** : « La direction voit la synthèse sans entrer dans le détail terrain : l'outil sert toute la chaîne hiérarchique. »

---

## 6. Profil ADMINISTRATEUR — `admin@cuf.cm` (3 min)

### 6.1 Paramètres — `/admin/parametres`
- **On montre** : on modifie un **prix FOB** par essence (ex. Ayous) ou l'**objectif m³**, on enregistre, puis on retourne sur `/dashboard/pertes` → **les montants ont changé**.
- **Ce qu'on dit** : « L'outil est **paramétrable** : prix, seuils, objectifs. Il s'adapte à l'évolution du marché sans retoucher le code. »
- **Prix FOB actuels** : Ayous 407 149 · Bilinga 446 051 · Iroko 262 833 · Movingui 262 383 FCFA/m³.

### 6.2 Utilisateurs — `/admin/utilisateurs`
- **On montre** : la liste des comptes, la création d'un opérateur, la réinitialisation d'un mot de passe.
- **Ce qu'on dit** : « L'admin gère les comptes et les droits, en toute autonomie. »

---

## 7. Fil conducteur à tenir devant le jury (le récit)

Enchaîne les profils comme une **histoire de la donnée**, du terrain à la direction :

1. **L'opérateur saisit** une fiche au poste (profil opérateur).
2. **Le chef contrôle et valide** cette fiche, puis lit son cockpit (profil chef).
3. Le cockpit **révèle un problème** (machine critique, cause d'arrêt dominante, manque à gagner).
4. Le chef **analyse** (Pareto → Ishikawa → 5 Pourquoi) et **crée une action** corrective.
5. L'app **mesure l'effet** de l'action (avant/après, FCFA évités).
6. **La direction** consulte la synthèse (profil PDG).
7. **L'admin** ajuste un prix → tout se recalcule (profil admin).

> C'est exactement la **boucle DMAIC** du mémoire : Définir → Mesurer → Analyser → Améliorer → Contrôler. L'application matérialise cette boucle.

---

## 8. Checklist express (à cocher pendant les répétitions)

- [ ] Connexion + redirection par rôle
- [ ] Opérateur : nouvelle fiche + **anti-chevauchement** refusé
- [ ] Opérateur : corriger une fiche « À corriger » et re-soumettre
- [ ] Opérateur : fiche papier / feuille de relevé
- [ ] Chef : cockpit (verdict, TRS, manque à gagner, priorités)
- [ ] Chef : Fiches — les 4 tuiles de statut affichent des nombres, chacune cliquable
- [ ] Chef : valider une fiche + demander une correction
- [ ] Chef : Machines (Pareto), Production, Qualité
- [ ] Chef : **Pertes** (FCFA D/P/Q + prix) — l'écran réparé
- [ ] Chef : créer une action + voir le bilan FCFA
- [ ] Chef : Recommandations (format + niveau de confiance)
- [ ] Chef : Ishikawa 6M + 5 Pourquoi + rapport A3
- [ ] Chef : Export Excel
- [ ] Prod : même cockpit riche
- [ ] PDG : dashboard exécutif à jour
- [ ] Admin : modifier un prix → impact sur les pertes
- [ ] Admin : gérer un utilisateur

---

## 9. Si quelque chose cloche pendant la démo (secours)

| Symptôme | Cause probable | Réponse immédiate |
|---|---|---|
| « Ce site est inaccessible » / connexion refusée | Le serveur est arrêté (fenêtre PowerShell fermée) | Relancer `python run.py`, garder la fenêtre ouverte |
| Un écran semble vide | Filtre de période trop court | Choisir « Toutes les dates » dans le sélecteur |
| Erreur serveur sur une page | Fichier de code incohérent (rare) | Le noter, passer à l'écran suivant, ne pas bloquer |
| PowerShell dit « py n'est pas reconnu » | Python vient du Microsoft Store | Utiliser `python` au lieu de `py` |

> **Règle d'or** : ne jamais coller de texte dans la fenêtre PowerShell qui fait tourner le serveur — sinon tu l'arrêtes. Utilise une **deuxième** fenêtre pour toute autre commande.

# Note d'impact mémoire — P18 : Poka-yoke volume deux niveaux non-bloquants (F4)

> Générée le : 2026-05-27
> Commit : `9e44180` — feat(operateur): poka-yoke volume deux niveaux non-bloquants (F4)
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `saisie.py`, `formulaire.html`, `style.css`

---

## 1. Résumé de la fonctionnalité

F4 ajoute une validation inline de détection — et non de prévention — sur le champ `volume_entrée` du formulaire de saisie opérateur. Lorsqu'un volume saisi dépasse la capacité théorique de la machine pour le créneau horaire renseigné, une alerte non-bloquante apparaît directement sous la ligne de production concernée, sans empêcher l'opérateur de soumettre la fiche.

Deux niveaux d'alerte distincts :

| Niveau | Condition | Couleur | Message |
|---|---|---|---|
| Orange (soft) | `volume_entrée > capacité_h × durée_créneau` | Ochre `--wp-ochre` | « Volume inhabituellement élevé — dépasse la capacité théorique du créneau (X.XX m³). » |
| Rouge (hard) | `volume_entrée > capacité_h × durée_créneau × 1.3` | Terracotta `--wp-terracotta` | « Volume impossible pour ce créneau (max théorique : X.XX m³) — vérifiez la saisie. » |

Le seuil rouge à 1.3× est délibéré : un TRS de 100 % est techniquement atteignable sur de très courts créneaux, il ne justifie pas un blocage. C'est le franchissement de 130 % qui signale une faute de frappe évidente (ex : 15,0 m³ au lieu de 1,50 m³). L'alerte orange intervient dès 100 % pour alerter sans alarmer.

**Aucune alerte sur les valeurs basses.** Ce choix est au cœur de F4 : voir section 4.

---

## 2. Décision d'architecture — trois niveaux, zéro blocage

**Pourquoi côté client et non côté serveur ?** La validation serveur rejette la saisie et force une nouvelle tentative. Ici, le signal doit être immédiat (à la frappe), doux et purement informatif — exactement ce que le JavaScript inline permet sans allez-retour réseau.

| Niveau | Élément | Rôle |
|---|---|---|
| Python | `capacites_essences` dict dans `saisie.py` | Lit les clés `capacite_{essence}_h` depuis `Parametre` et les passe au template en JSON. |
| JS | Extension de `majProduction(index)` dans `formulaire.html` | Calcule `capaciteCreneau = capaciteH × (duree / 60)` et décide du niveau d'alerte. |
| CSS | `.wp-production-alert.is-warning` dans `style.css` | Surcharge couleur ochre sur le composant alerte existant (3 lignes). |

La variable `displayMessage = message || rangeMessage` préserve la priorité des erreurs structurelles existantes (heure fin ≤ début, conforme+déclassé > entrée). La variable `complet` ne dépend que de `message` (erreurs bloquantes), pas de `rangeMessage` : l'état « Complet » du bandeau de la carte n'est pas affecté par une alerte de volume. L'opérateur peut soumettre.

Aucun nouveau composant. Aucune route. Aucun appel réseau supplémentaire.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact de F4 |
|---|---|
| OS2 — Mesurer la production réelle via collecte terrain | **Direct.** F4 protège la qualité des données collectées en détectant les fautes de frappe grossières avant enregistrement. La mesure ne vaut que si les données sont saines. |
| OS3 — Calculer le TRS et estimer les pertes | **Indirect.** Un volume entrée erroné (ex : 15,0 au lieu de 1,50) fausserait le TRS et les pertes calculées. F4 réduit ce risque sans contraindre l'opérateur. |
| OS6 — Concevoir un outil de pilotage adapté | **Cohérent.** La validation est progressive (pas de mur d'erreur) et didactique (le message cite le max théorique chiffré). C'est le comportement attendu d'un outil adapté aux opérateurs semi-qualifiés saisissant sur téléphone. |

---

## 4. Impact sur la validité scientifique des données — point critique

**Décision fondamentale : aucune alerte sur les valeurs basses.**

L'hypothèse centrale H3 affirme que le TRS réel de la chaîne 4 est inférieur à 60 % en l'absence de système de mesure. Si F4 avait alerté les opérateurs lorsque leur production semble « trop faible », deux biais auraient pu s'introduire :

1. **Biais de désirabilité sociale** : l'opérateur, voyant un signal négatif, aurait pu arrondir ses volumes à la hausse pour éviter le message.
2. **Biais de seuil implicite** : une alerte basse aurait pu être lue comme « en dessous de cette valeur, votre travail est insuffisant », ce que l'outil n'a aucune légitimité à dire.

En n'alertant que sur les valeurs physiquement impossibles (côté haut), F4 élimine les fautes de frappe sans jamais orienter la saisie. Toutes les valeurs basses, même extrêmes, sont enregistrées sans commentaire. Le TRS calculé reflète donc la réalité terrain, y compris les postes catastrophiques qui sont précisément les données les plus précieuses pour H3.

Cette posture est identique à celle des capteurs de mesure industriels : ils signalent le hors-plage haut (saturation, débordement), jamais le hors-plage bas (arrêt machine, production nulle).

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. F4 ne crée aucune table ni migration. Les seuils de capacité théorique viennent de la table `Parametre` existante (`capacite_ayous_h`, `capacite_azobe_h`, `capacite_iroko_h`, `capacite_movingui_h` — toutes à 1,5625 m³/h dans l'instance actuelle). Aucun état persistant n'est ajouté.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.**

- **H1** (capacité théorique < 25 m³) : F4 utilise la capacité théorique comme seuil d'alerte, ce qui est cohérent avec H1. Si la bicoupe produit 1,5625 m³/h, un créneau de 8h a une capacité de 12,5 m³ — inférieure aux 25 m³ que H1 conteste. Les alertes ne prouvent rien sur H1 mais ne la contredisent pas.
- **H2** (pertes principalement organisationnelles) : non concernée. F4 agit sur la collecte, pas sur l'analyse des causes.
- **H3** (TRS réel < 60 %) : **protégée activement par le choix de n'alerter qu'en haut**. Voir section 4.
- **H4** (actions sans investissement majeur) : **cohérente.** F4 est gratuite (zéro infrastructure) et réduit le risque d'erreur de mesure qui aurait pu invalider les données de terrain. C'est exactement le type d'amélioration à coût nul que H4 valorise.

**Point d'attention — fenêtre conditionnelle :** L'alerte ne se déclenche que si l'opérateur a renseigné à la fois l'heure de début, l'heure de fin ET le volume entrée. Si l'un des trois est absent, aucun signal n'apparaît. Ce comportement est correct : sans durée connue, on ne peut pas calculer la capacité du créneau. Il n'y a pas de faux positif.

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| `capacites_essences` dict | `saisie.py` (helper inline dans le render) | Map `{essence: float}` construite depuis `Parametre.get(f'capacite_{normalise_essence(e)}_h')` pour chaque essence de `Config.ESSENCES`. Passée en JSON au template. |
| `capacitesEssences` const | `formulaire.html` | Constante JS injectée via `{{ capacites_essences \| tojson }}`. Accessible dans `majProduction()`. |
| Bloc `rangeMessage` / `rangeIsWarning` | `formulaire.html` — `majProduction()` | Calcul `capaciteCreneau`, comparaison 1.0× et 1.3×, séparation du `message` bloquant et du `rangeMessage` non-bloquant. `displayMessage = message \|\| rangeMessage` pour l'affichage. |
| `.wp-production-alert.is-warning` | `style.css` | Modificateur ochre (3 lignes) sur le composant alerte déjà existant. |

---

## 8. Utilisabilité terrain et adoption

L'alerte est conçue pour un opérateur saisissant sur téléphone avec les mains sales après un poste de sciage.

1. **Inline et immédiate** — le message apparaît dès la modification du champ, sans clic supplémentaire. L'opérateur voit le problème avant de scroller vers le bouton Soumettre.
2. **Chiffrée** — le message cite explicitement le maximum théorique calculé (ex : « max théorique : 6.25 m³ »). L'opérateur peut vérifier lui-même si sa valeur est plausible.
3. **Non-bloquante** — si la valeur est correcte malgré l'alerte (cas exceptionnel possible), l'opérateur soumet sans friction. Pas de popup, pas de modal, pas de confirmation.
4. **Deux teintes distinctes** — ochre pour « attention » et terracotta pour « probablement une erreur ». Ce gradient visuel est plus informatif qu'un seul rouge uniforme et évite la fatigue d'alerte.
5. **Silencieuse quand inutile** — aucun état affiché quand tout va bien. L'alerte n'existe pas visuellement tant qu'elle n'est pas déclenchée.

---

## 9. Ce que cela change pour le mémoire

| Section du mémoire | Mise à jour requise |
|---|---|
| OS2 — Collecte terrain / qualité des données | Mentionner F4 comme mécanisme de contrôle de cohérence côté saisie. La base de données est « protégée en haut » contre les fautes de frappe sans introduire de biais de sélection vers le bas. |
| OS6 — Outil de pilotage adapté | F4 illustre la conception orientée terrain : validation progressive, non-bloquante, chiffrée. Référence possible à Nakajima (1988) sur la détection plutôt que la correction. |
| Méthodologie — fiabilité des données | Citer explicitement le choix d'absence d'alerte basse comme décision méthodologique, cohérente avec la collecte d'un TRS potentiellement faible. |
| Limite à signaler | La capacité théorique dans `Parametre` (1,5625 m³/h) est une valeur provisoire ; si elle est recalibrée après mesures terrain (OS1), les seuils d'alerte se mettront à jour automatiquement sans modifier le code. |

---

> **Vérification réalisée :** injection JSON vérifiée via curl authentifié sur `/saisie/nouveau` — `capacitesEssences = {"Ayous": 1.5625, "Azobé": 1.5625, "Iroko": 1.5625, "Movingui": 1.5625}` correctement présent dans le HTML servi. Logique JS vérifiée par lecture du code (condition `!message`, séparation `rangeMessage` / `message`, `displayMessage`, toggle `.is-warning`). Aucun test UI navigateur (Chromium indisponible).

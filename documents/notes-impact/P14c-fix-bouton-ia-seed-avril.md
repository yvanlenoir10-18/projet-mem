# Note d'impact — P14c : Fix bouton IA + seed avril 2026
> Commit : 180beec — fix(reco): bouton IA cassé (guillemets JSON dans onclick) + seed avril 2026
> Date : 2026-05-15
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Correction d'un bug bloquant qui empêchait le bouton « Analyser avec l'IA » de répondre au clic. Le handler `onclick="analyserIA('CODE', {{ contexte_json }})"` produisait du HTML malformé dès que le JSON contenait des guillemets doubles (ce qui est systématique : `{"trs_moyen": 35}`), ce qui cassait l'attribut HTML et rendait le bouton inerte. Le navigateur n'émettait aucune erreur visible, expliquant le symptôme « rien ne se passe ».

La correction adopte le pattern moderne `data-*` : les paramètres sont stockés dans `data-code` et `data-contexte` (attribut à guillemets simples, JSON HTML-safe via le filtre `|tojson` de Flask). Le binding du clic se fait au `DOMContentLoaded` via `addEventListener` sur la classe `.wp-btn-ia`. Cette approche est robuste à tous les caractères spéciaux et conforme aux bonnes pratiques HTML5.

En parallèle, le script de seed est ajusté pour générer toutes les équipes du mois d'avril 2026 (30 jours, 60 équipes) au lieu de la fenêtre glissante « today − 30 jours », conformément à la demande utilisateur.

---

## 2. Fichiers modifiés

| Fichier | Action |
|---|---|
| `cuf-pilotage/app/templates/recommandations/index.html` | Remplacement `onclick="…"` par `data-code` + `data-contexte`. Ajout binding au `DOMContentLoaded`. |
| `cuf-pilotage/seed_data.py` | `JOUR_DEBUT = date(2026,4,1)`, `JOUR_FIN = date(2026,4,30)`, boucle ascendante au lieu de `today - jour_offset` |

---

## 3. Lien avec les objectifs du mémoire

L'OS6 (outil de pilotage) suppose que l'interface utilisateur soit réellement utilisable. Un bouton inerte sans feedback rend l'OS6 partiellement caduc : la Couche 2 IA (P14) restait inaccessible. Cette correction restaure la fonctionnalité prévue et garantit que la démonstration du moteur de recommandations à CUF Ebolowa sera fluide.

---

## 4. Lien avec les hypothèses de recherche

Aucune hypothèse n'est affectée — il s'agit d'un correctif d'interface, pas d'une modification de méthodologie. **Aucune hypothèse contredite.**

---

## 5. Architecture technique

`✶ Insight ─────────────────────────────────────`
Le bug venait d'un anti-pattern classique en templating HTML : insérer du JSON directement dans un attribut HTML à guillemets doubles. Flask `|tojson` produit du JSON HTML-safe pour les `<script>` mais pas pour les attributs. La règle est : `<script>const data = {{ x|tojson }};</script>` fonctionne ; `<button onclick="f({{ x|tojson }})">` ne fonctionne pas. La solution canonique est `data-*` avec attribut à guillemets simples.
`─────────────────────────────────────────────────`

Le test de rendu via `app.test_client()` a permis de vérifier que :
- Le bouton est rendu avec `data-contexte='{"manque": 0.0, "nb_postes": 32, ...}'` bien formé
- L'endpoint POST `/recommandations/ai/<code>` répond 200 avec une payload JSON valide
- Sans clé `.env`, l'erreur « Aucun moteur IA configuré » remonte correctement à l'UI

---

## 6. Contraintes respectées

- **R7** (pas de nouvelle table DB) : aucun changement de schéma
- **R6** (pas de code sans validation) : bug remonté par l'utilisateur, correction validée par test fonctionnel
- Compatibilité ascendante : le format de réponse JSON de l'endpoint reste identique

---

## 7. Limites

L'attribut `data-contexte` peut grossir si le contexte contient beaucoup de champs (actuellement 5 champs, < 200 octets), mais reste très en deçà des limites pratiques des navigateurs (plusieurs Mo). Aucune limite atteinte dans le cas d'usage CUF.

---

## 8. Commandes Windows

```powershell
# Récupérer les corrections
git pull origin claude/install-claude-excel-6MGzv

# Régénérer la base avec avril 2026 complet
python seed_data.py

# Relancer Flask
.\start.ps1
```

Puis dans le navigateur, sur `/recommandations/`, le bouton IA déclenche désormais l'appel POST visible dans l'onglet Réseau des DevTools (F12).

---

## 9. Bibliographie associée

Aucune nouvelle référence — il s'agit d'une correction technique. La documentation officielle MDN sur les attributs `data-*` (HTML5 spec) et le mécanisme `dataset` JavaScript ont guidé la solution.

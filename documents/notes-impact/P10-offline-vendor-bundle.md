# Note d'impact — P10 : Bundle hors-ligne (vendor assets)
> Commit : `14767d3` — feat(offline): bundle Bootstrap, Bootstrap Icons, Chart.js et Manrope en local
> Date : 2026-05-11
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Suppression de toutes les dépendances CDN externes de l'application Flask CUF Pilotage. Bootstrap 5.3.0 (CSS + JS bundle), Bootstrap Icons 1.11.0 (CSS + polices woff/woff2), Chart.js 4.4.0 (UMD build) et la police Manrope (graisses 400 à 800, subset latin) sont désormais servis localement depuis `cuf-pilotage/app/static/vendor/`. Le fichier `style.css` remplace l'`@import` Google Fonts par cinq déclarations `@font-face` locales. Les templates `base.html`, `errors/404.html` et `errors/500.html` utilisent `url_for('static', filename='vendor/…')` à la place des liens CDN.

---

## 2. Fichiers modifiés ou créés

| Fichier | Type | Action |
|---|---|---|
| `app/static/vendor/bootstrap/bootstrap.min.css` | CSS | Créé (228 Ko) |
| `app/static/vendor/bootstrap/bootstrap.bundle.min.js` | JS | Créé (79 Ko) |
| `app/static/vendor/bootstrap-icons/bootstrap-icons.css` | CSS | Créé (96 Ko) |
| `app/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2` | Police | Créé (128 Ko) |
| `app/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff` | Police | Créé (173 Ko) |
| `app/static/vendor/chartjs/chart.umd.min.js` | JS | Créé (UMD build) |
| `app/static/vendor/fonts/manrope/manrope-{400…800}.woff2` | Police | Créé (5 fichiers) |
| `app/static/css/style.css` | CSS | Modifié — `@import` → `@font-face` |
| `app/templates/base.html` | HTML | Modifié — 4 liens CDN → `url_for` |
| `app/templates/errors/404.html` | HTML | Modifié — 3 liens CDN → `url_for` |
| `app/templates/errors/500.html` | HTML | Modifié — 3 liens CDN → `url_for` |

---

## 3. Objectif spécifique du mémoire servi

**OS6 — Concevoir un outil de pilotage adapté** : l'objectif OS6 précise que le tableau de bord doit être utilisable sur le terrain à la scierie CUF, dont la connexion internet est inexistante ou très instable. Un outil qui dépend de CDN externes ne peut pas fonctionner dans ce contexte. Cette modification rend l'application autonome : elle tourne entièrement en local (Flask + SQLite + assets statiques), sans aucune requête réseau au chargement.

---

## 4. Lien avec les hypothèses de recherche

**H4 — Des actions correctives sans investissement majeur permettent d'améliorer le TRS** : l'accessibilité de l'outil de pilotage est une condition préalable à son utilisation. Un tableau de bord inaccessible hors ligne ne peut pas soutenir un suivi continu des performances. Cette modification renforce directement la faisabilité de H4 en garantissant que l'outil peut être utilisé sur site sans infrastructure réseau.

**Aucune contradiction avec les hypothèses H1, H2, H3.** Ces hypothèses portent sur les données de production et non sur l'infrastructure du tableau de bord.

---

## 5. Technique utilisée et choix architectural

Les fichiers ont été obtenus via `npm install` depuis la machine Linux (bootstrap@5.3.0, bootstrap-icons@1.11.0, chart.js@4.4.0, @fontsource/manrope), puis copiés dans `static/vendor/` et committés dans Git. Cette approche évite :
- un script de téléchargement à maintenir côté utilisateur,
- une dépendance à `npm` sur la machine Windows de production,
- toute requête réseau au runtime.

Pour Manrope, seul le subset latin a été retenu (5 fichiers woff2, un par graisse). Le CSS Bootstrap Icons utilise des chemins relatifs (`./fonts/…`) qui résolvent correctement depuis l'URL de service Flask (`/static/vendor/bootstrap-icons/`). Le `package.json` et `package-lock.json` générés par npm ne sont pas committés (non nécessaires en production).

---

## 6. Contrainte respectée

**Règle R7** : la base `instance/cuf.db` n'a pas été touchée. Aucune migration de schéma. La modification est purement statique (assets + templates).

---

## 7. Limites identifiées

- **Mises à jour manuelles** : si Bootstrap ou Chart.js sort une version corrective de sécurité, les fichiers dans `vendor/` devront être remplacés manuellement et recommittés. Il n'y a pas de mécanisme de mise à jour automatique.
- **Taille du repo** : l'ajout des assets binaires (woff, woff2, JS minifié) alourdit le repo d'environ 700 Ko. C'est acceptable pour un projet local, mais à surveiller si d'autres assets sont ajoutés.
- **Chart.js non minifié** : la version npm de Chart.js 4.4.0 ne fournit pas de fichier `.min.js` dans `dist/`. Le build UMD non minifié est utilisé (fonctionnellement identique, légèrement plus lourd).
- **Subset latin uniquement** : la police Manrope n'inclut que les caractères latins. Les noms propres ou termes en langues à alphabets étendus tomberaient sur le fallback `system-ui`. Non pertinent pour CUF (contenus en français uniquement).

---

## 8. Commandes Windows pour appliquer

```powershell
git pull origin claude/install-claude-excel-6MGzv
python run.py
```

L'application est ensuite accessible sur `http://127.0.0.1:5000` sans connexion internet.

---

## 9. Références bibliographiques mobilisées

- **Kankkunen & Holopainen (2024)** — Daily management system, UPM Plywood : souligne que l'accessibilité physique et la simplicité d'accès à l'outil de pilotage sont des déterminants critiques de son adoption sur le terrain. Un tableau de bord nécessitant internet serait inutilisable dans un contexte de production industrielle isolé.
- **Laine (2024)** — Reporting visuel, Metsä Board : insiste sur la disponibilité permanente des indicateurs visuels pour les opérateurs, condition qui ne peut être satisfaite qu'avec un outil fonctionnant indépendamment de l'infrastructure réseau.

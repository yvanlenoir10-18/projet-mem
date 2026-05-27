# Plan — Correction 6 bugs profil opérateur

**Branche :** `claude/install-claude-excel-6MGzv`  
**Date :** 2026-05-27

---

## Context

L'analyse du profil opérateur a révélé 6 problèmes bloquants ou dégradants pour la qualité des données collectées terrain. Certains (Bug 1) faussent directement le TRS calculé — ce qui compromet la validité scientifique de l'hypothèse H3 du mémoire (TRS < 60%). Les autres dégradent l'expérience de saisie ou la complétude des données. L'utilisateur a validé les 6 corrections.

---

## Fichiers modifiés

| Fichier | Bugs |
|---|---|
| `app/models.py` | Bug 1 |
| `app/routes/saisie.py` | Bug 1, 2, 3, 5 |
| `app/templates/saisie/formulaire.html` | Bug 2, 4, 6 |
| `app/templates/saisie/historique.html` | Bug 5 |
| `app/templates/saisie/detail.html` | Bug 5 |

---

## Bug 1 — heure_fin ne peut jamais être ≤ heure_debut

**Problème :** `Arret.calcule_duree()` (models.py:220-226) fait `max(0, résultat)`, convertissant silencieusement une heure inversée en 0 minute. Cela gonfle le TRS artificiellement.

**Fix :**

1. **`models.py` — `calcule_duree()`** : supprimer le `max(0, ...)` et lever une `ValueError` si le résultat est ≤ 0. La méthode doit retourner `True` si OK, `False` (ou lever) si invalide.

```python
def calcule_duree(self):
    try:
        h_d, m_d = map(int, self.heure_debut.split(':'))
        h_f, m_f = map(int, self.heure_fin.split(':'))
        delta = (h_f * 60 + m_f) - (h_d * 60 + m_d)
        if delta <= 0:
            raise ValueError("fin <= debut")
        self.duree_min = delta
    except (ValueError, AttributeError):
        self.duree_min = 0
        raise  # re-raise pour que la route puisse bloquer
```

Alternativement (plus simple et sans casser le contrat existant) : ne pas raise, mais retourner un booléen et laisser la route valider.

**Approche retenue — validation dans la route** : `calcule_duree()` reste silencieuse (compatibilité) mais on ajoute une validation explicite dans `saisie.py` **avant** le `db.session.add`. Pour chaque arrêt parsé, vérifier que `heure_fin > heure_debut` (comparaison string HH:MM fonctionne si format correct, sinon convertir). Si invalide → `flash(..., 'danger')` et `return _render_form(...)` avec données préservées.

**Localisation dans saisie.py :** après la boucle de parsing des arrêts dans `nouveau_poste()` (lignes 160-175 environ), avant `db.session.add`.

---

## Bug 2 — Essence obligatoire, aucune essence par défaut

**Problème :** Le `<select>` essence peut avoir une valeur pré-sélectionnée par le navigateur, et `saisie.py:157` fait `if not essence: continue` — sautant silencieusement les lignes sans essence plutôt qu'alerter.

**Fix :**

1. **`formulaire.html` — template production row** : s'assurer que la première `<option>` est `value=""` et que c'est la seule sélectionnée par défaut :
```html
<option value="" selected>-- Choisir l'essence --</option>
<option value="Ayous">Ayous</option>
...
```
Retirer tout attribut `selected` sur les essences.

2. **`saisie.py` — `nouveau_poste()` et `modifier_equipe()`** : remplacer le `continue` silencieux par une détection de lignes incomplètes :
```python
for i, essence in enumerate(essences):
    vol_e = vol_entrees[i] if i < len(vol_entrees) else ''
    vol_c = vol_conformes[i] if i < len(vol_conformes) else ''
    vol_d = vol_declass[i] if i < len(vol_declass) else ''
    # Si une ligne a des volumes mais pas d'essence → erreur bloquante
    has_volumes = any(v.strip() for v in [vol_e, vol_c, vol_d])
    if not essence and has_volumes:
        flash("Veuillez sélectionner une essence pour chaque ligne de production.", 'danger')
        return _render_form(...)  # avec données préservées
    if not essence:
        continue  # ligne vide, on ignore
```

---

## Bug 3 — Virgule comme séparateur décimal + préservation des données sur erreur

**Problème :**
- `float("12,5")` lève `ValueError` — les opérateurs francophones tapent des virgules
- Sur exception, le formulaire est re-rendu vide (données perdues)

**Fix :**

1. **`saisie.py` — fonction helper `_parse_float()`** : remplacer dans `_extraire_productions_arrets()` :
```python
def _parse_float(val):
    """Accepte virgule (12,5) et point (12.5) comme séparateur décimal."""
    if not val:
        return 0.0
    return float(str(val).replace(',', '.').strip())
```
Utiliser `_parse_float()` partout où `float(vol_entrees[i])` est appelé.

2. **`saisie.py` — `nouveau_poste()` et `modifier_equipe()`** : sur `except Exception`, passer les données du formulaire à `_render_form()` :
```python
except Exception as e:
    db.session.rollback()
    flash(f"Erreur : {str(e)}", 'danger')
    return _render_form(
        productions_donnees=_extraire_donnees_brutes_form(),
        arrets_donnees=_extraire_arrets_bruts_form(),
    )
```
Cela suppose que `_render_form()` accepte ces paramètres et les passe au template, et que le template `formulaire.html` utilise déjà `ajouterProductionAvecDonnees(data)` et `ajouterArretAvecDonnees(data)` (confirmé : fonctions présentes).

---

## Bug 4 — Validation client-side en temps réel

**Problème :** La validation de cohérence (`_verifier_coherence`) ne tourne qu'au submit. L'opérateur ne sait pas qu'il fait une erreur pendant la saisie.

**Fix dans `formulaire.html`** — JavaScript à ajouter dans `{% block scripts %}` :

```javascript
// Validation inline temps réel

function validerLigneProduction(index) {
  const entree = parseFloat(document.querySelector(`.vol-entree-${index}`)?.value?.replace(',','.')) || 0;
  const conforme = parseFloat(document.querySelector(`.vol-conforme-${index}`)?.value?.replace(',','.')) || 0;
  const declass = parseFloat(document.querySelector(`.vol-declass-${index}`)?.value?.replace(',','.')) || 0;
  const errDiv = document.getElementById(`err-prod-${index}`);
  if (!errDiv) return;
  if (entree > 0 && (conforme + declass) > entree + 0.01) {
    errDiv.textContent = "⚠ Conforme + Déclassé > Entrée";
    errDiv.style.display = 'block';
  } else {
    errDiv.textContent = '';
    errDiv.style.display = 'none';
  }
}

function validerLigneArret(index) {
  const debut = document.getElementById(`arret_debut_${index}`)?.value;
  const fin = document.getElementById(`arret_fin_${index}`)?.value;
  const errDiv = document.getElementById(`err-arret-${index}`);
  if (!errDiv || !debut || !fin) return;
  if (fin <= debut) {
    errDiv.textContent = "⚠ Heure de fin doit être après l'heure de début";
    errDiv.style.display = 'block';
  } else {
    errDiv.textContent = '';
    errDiv.style.display = 'none';
  }
}
```

- Ajouter `<div id="err-prod-{index}" class="text-danger small mt-1" style="display:none"></div>` sous chaque ligne production dans le template
- Ajouter `<div id="err-arret-{index}" ...>` sous chaque ligne arrêt
- Connecter `oninput="validerLigneProduction(${index})"` sur les champs de volume, `onchange="validerLigneArret(${index})"` sur les champs d'heure
- Bloquer le submit via `form.addEventListener('submit', ...)` si des erreurs inline sont visibles

---

## Bug 5 — Feedback motivant pour l'opérateur

**Contrainte :** R7 — pas de nouvelle table DB. Calcul depuis `Equipe` filtré par `user_id`.

**Fix dans `saisie.py` — `historique()`** : calculer des stats personnelles avant le render :

```python
# Stats personnelles opérateur (pas de nouvelle table, filtre user_id)
from datetime import date, timedelta
equipes_user = Equipe.query.filter_by(user_id=current_user.id).all()
equipes_soumises = [e for e in equipes_user if e.statut in ('soumis', 'verrouille') and e.trs_global]
nb_equipes = len(equipes_soumises)
trs_moyen = round(sum(e.trs_global for e in equipes_soumises) / nb_equipes, 1) if nb_equipes else None
meilleur_trs = max((e.trs_global for e in equipes_soumises), default=None)
# Tendance : comparer 7 derniers jours vs 7 jours précédents
aujourd_hui = date.today()
recentes = [e for e in equipes_soumises if e.date >= aujourd_hui - timedelta(days=7)]
precedentes = [e for e in equipes_soumises if aujourd_hui - timedelta(days=14) <= e.date < aujourd_hui - timedelta(days=7)]
trs_recent = round(sum(e.trs_global for e in recentes)/len(recentes),1) if recentes else None
trs_prec = round(sum(e.trs_global for e in precedentes)/len(precedentes),1) if precedentes else None
tendance = 'up' if (trs_recent and trs_prec and trs_recent > trs_prec) else 'down' if (trs_recent and trs_prec and trs_recent < trs_prec) else 'flat'
```

Passer à template : `stats_operateur={nb_equipes, trs_moyen, meilleur_trs, trs_recent, tendance}`.

**Fix dans `historique.html`** — bloc motivant avant le tableau (uniquement si `current_user.role == 'operateur'`) :

```html
{% if current_user.role == 'operateur' and stats_operateur %}
<div class="wp-card mb-4 p-4" style="border-left: 4px solid var(--wp-leaf);">
  <div class="d-flex align-items-center gap-3">
    <div style="font-size:2rem;">🌱</div>
    <div>
      <div style="font-weight:800; color:var(--wp-emerald);">
        {% if stats_operateur.nb_equipes == 0 %}
          Bienvenue ! Votre premier poste compte.
        {% elif stats_operateur.trs_moyen >= 65 %}
          Excellent travail, continuez comme ça !
        {% elif stats_operateur.trs_moyen >= 50 %}
          Bonne dynamique — chaque poste rapproche de l'objectif.
        {% else %}
          Chaque saisie aide à comprendre et améliorer la chaîne.
        {% endif %}
      </div>
      <div class="d-flex gap-4 mt-2 flex-wrap">
        <div><span class="wp-muted">Postes saisis :</span> <strong>{{ stats_operateur.nb_equipes }}</strong></div>
        {% if stats_operateur.trs_moyen %}
        <div><span class="wp-muted">TRS moyen :</span> <strong>{{ stats_operateur.trs_moyen }}%</strong></div>
        {% endif %}
        {% if stats_operateur.meilleur_trs %}
        <div><span class="wp-muted">Meilleur TRS :</span> <strong style="color:var(--wp-leaf);">{{ stats_operateur.meilleur_trs }}%</strong></div>
        {% endif %}
        {% if stats_operateur.tendance == 'up' %}
        <div class="wp-delta-up">↑ En progression cette semaine</div>
        {% elif stats_operateur.tendance == 'down' %}
        <div class="wp-delta-down">↓ Semaine plus difficile — continuez !</div>
        {% endif %}
      </div>
    </div>
  </div>
</div>
{% endif %}
```

**Fix dans `detail.html`** — après les KPI cards (ligne 155 environ), ajouter un bloc d'encouragement conditionnel :

```html
{% if current_user.role == 'operateur' and equipe.statut in ('soumis', 'verrouille') %}
<div class="alert mt-3" style="background:var(--wp-cream-2); border-left:4px solid var(--wp-leaf); border-radius:12px;">
  <strong>Merci pour cette saisie !</strong>
  {% if equipe.trs_global >= 65 %}
  Ce poste est au-dessus de la moyenne — excellent !
  {% elif equipe.trs_global >= 50 %}
  TRS dans la plage normale. Chaque donnée compte pour l'analyse.
  {% else %}
  TRS bas ce poste — les arrêts documentés aident à identifier les causes.
  {% endif %}
  <br><small class="text-muted">Ces données alimentent le tableau de bord du chef de production.</small>
</div>
{% endif %}
```

---

## Bug 6 — Ergonomie mobile du formulaire

**Problème :** Les lignes production/arrêt utilisent `col-md-2` — 6 colonnes côte à côte sur desktop, qui stackent une par une sur mobile (illisible).

**Fix dans `formulaire.html`** — restructurer chaque ligne production en layout 2-colonnes sur mobile :

**Avant (chaque champ) :**
```html
<div class="col-md-2">...</div>
```

**Après — productions :**
```html
<!-- Essence : pleine largeur sur mobile, 2/12 sur desktop -->
<div class="col-12 col-md-2">Essence select</div>
<!-- Entrée + Conformes : 2 colonnes sur mobile (col-6), 2/12 sur desktop -->
<div class="col-6 col-md-2">Entrée grumes</div>
<div class="col-6 col-md-2">Conformes</div>
<!-- Déclassé + Déchets : 2 colonnes sur mobile -->
<div class="col-6 col-md-2">Déclassé</div>
<div class="col-6 col-md-2">Déchets (readonly)</div>
<!-- Bouton supprimer : pleine largeur sur mobile -->
<div class="col-12 col-md-1 d-flex align-items-end">Supprimer</div>
```

**Après — arrêts :**
```html
<div class="col-12 col-md-2">Machine select</div>
<div class="col-6 col-md-2">Heure début</div>
<div class="col-6 col-md-2">Heure fin</div>
<div class="col-12 col-md-3">Cause</div>
<div class="col-10 col-md-2">Catégorie</div>
<div class="col-2 col-md-1">Supprimer</div>
```

Ajouter aussi `style="min-height:44px"` sur tous les boutons Ajouter/Supprimer pour ciblage tactile correct.

---

## Ordre d'implémentation

1. `models.py` — Bug 1 (calcule_duree propre)
2. `saisie.py` — Bugs 1+2+3 ensemble (validation arrêts, essence obligatoire, _parse_float, preserve data)
3. `formulaire.html` — Bugs 2+4+6 (no default essence, JS inline validation, mobile layout)
4. `saisie.py` — Bug 5 (stats_operateur dans historique())
5. `historique.html` + `detail.html` — Bug 5 (blocs motivants)

---

## Vérification

1. Lancer l'appli : `cd cuf-pilotage && flask run`
2. Se connecter en tant qu'opérateur
3. **Bug 1** : Créer un arrêt avec heure_fin < heure_debut → message d'erreur rouge, formulaire conservé
4. **Bug 2** : Entrer des volumes sans sélectionner d'essence → message d'erreur, formulaire conservé ; vérifier que le select commence vide
5. **Bug 3** : Entrer "12,5" dans un champ volume → accepté ; provoquer une erreur → vérifier que le formulaire est re-rendu avec les données saisies
6. **Bug 4** : Entrer conforme + déclassé > entrée → message rouge inline immédiat sans soumettre ; même test sur heures inversées
7. **Bug 5** : Se connecter en opérateur, aller sur historique → bloc stats visible avec TRS moyen et badge tendance ; aller sur le détail d'un poste soumis → message d'encouragement
8. **Bug 6** : Ouvrir formulaire sur mobile (ou DevTools resize < 576px) → champs en 2 colonnes, pas en 1 par ligne

Commit : `fix(operateur): validation arrêts/essence/virgule + feedback motivant + mobile`

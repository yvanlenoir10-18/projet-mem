# Reprise P4 — Export Excel enrichi

> Statut : Code validé dans le chat, NON encore écrit dans export.py
> Branche : claude/install-claude-excel-6MGzv
> Fichier cible : cuf-pilotage/app/services/export.py (253 lignes, version P1)

---

## Ce qui est fait (validé dans la conversation)

6 fonctions écrites et approuvées feuille par feuille :

| # | Fonction | Feuille Excel |
|---|---|---|
| 1 | `_feuille_resume(wb, equipes, mois, annee, nb_brouillons=0)` | Résumé — KPIs + pertes D/P/Q + top 5 Pareto + alerte rouge prix |
| 2 | `_feuille_production(wb, equipes)` | Production — détail journalier enrichi (statut, rendement, traçabilité) |
| 3 | `_feuille_trs(wb, equipes)` | TRS/OEE — synthèse Matin/Après-midi + tableau journalier |
| 4 | `_feuille_essence(wb, equipes)` | Analyse essence — volumes + rendement + prix + pertes Q |
| 5 | `_feuille_maintenance(wb, equipes)` | Maintenance — arrêts enrichis (Planifié/Non-planifié + Impact TRS) |
| 6 | `_feuille_pareto(wb, equipes)` | Pareto — toutes causes, machines, catégories, % cumulé, gras 80% |

Deux helpers nouveaux :
- `_ligne_total(ws, row, vals_par_col, label, col_label)` — ligne de totaux stylée
- `_prix_manquants(equipes) -> bool` — détecte prix non saisis

## Ce qui reste à faire

1. Réécrire `cuf-pilotage/app/services/export.py` entier avec les 6 fonctions
2. Modifier `cuf-pilotage/app/routes/dashboard.py` route `export_excel()` :
   - Ajouter comptage brouillons avant l'appel
   - Passer `nb_brouillons` à `generer_rapport_excel()`
3. Vérifier syntaxe Python
4. Commit + push

## Nouvelle signature principale

```python
def generer_rapport_excel(equipes, mois, annee, nb_brouillons=0):
    wb = Workbook()
    _feuille_resume(wb, equipes, mois, annee, nb_brouillons)
    _feuille_production(wb, equipes)
    _feuille_trs(wb, equipes)
    _feuille_essence(wb, equipes)
    _feuille_maintenance(wb, equipes)
    _feuille_pareto(wb, equipes)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
```

## Patch dashboard.py (route export_excel)

Ajouter après la requête `equipes = Equipe.query...` :

```python
nb_brouillons = Equipe.query.filter(
    Equipe.date >= debut, Equipe.date < fin,
    Equipe.statut == 'brouillon'
).count()
```

Et modifier l'appel :
```python
contenu = generer_rapport_excel(equipes, mois, annee, nb_brouillons)
```

## Décisions P4 validées

- Pas de graphiques openpyxl — tableaux colorés uniquement
- Feuille TRS : synthèse créneaux en haut + tableau journalier en dessous
- Alerte rouge dans Résumé si prix manquants (pas de "N/D" dans cellules)
- Export enrichi remplace l'export simple (un seul bouton)
- Analyse essence : volumes + rendement + prix + pertes Q décomposées
- Gestion explicite prix nuls dans toutes les feuilles concernées

## Règle anti-timeout pour la nouvelle conversation

Écrire export.py en 3 appels Write séparés :
- Appel 1 : imports + palette + helpers (lignes 1-80)
- Appel 2 : _feuille_resume + _feuille_production (lignes 81-200)
- Appel 3 : _feuille_trs + _feuille_essence + _feuille_maintenance + _feuille_pareto + generer_rapport_excel (lignes 201-fin)

"""
Service d'export Excel — Rapport mensuel Chaîne 4, Scierie CUF.
3 feuilles : Résumé | Équipes | Arrêts
"""
import io
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.models import Parametre
from app.services.trs import pareto_arrets, couleur_trs, calcule_pertes_equipe

VERT_FONCE  = "1B5E20"
VERT_CLAIR  = "C8E6C9"
ORANGE_PALE = "FFE0B2"
ROUGE_PALE  = "FFCDD2"
JAUNE_PALE  = "FFF9C4"
BLANC       = "FFFFFF"
GRIS_CLAIR  = "F5F5F5"

NOMS_MOIS = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
             'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']


def _style_entete(cell, bg_hex=VERT_FONCE, fg_hex=BLANC, taille=11, gras=True):
    cell.font = Font(bold=gras, color=fg_hex, size=taille, name='Calibri')
    cell.fill = PatternFill("solid", fgColor=bg_hex)
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    thin = Side(style='thin', color='BBBBBB')
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)


def _style_cellule(cell, gras=False, couleur_bg=None, align='center'):
    cell.font = Font(bold=gras, size=10, name='Calibri')
    cell.alignment = Alignment(horizontal=align, vertical='center')
    if couleur_bg:
        cell.fill = PatternFill("solid", fgColor=couleur_bg)
    thin = Side(style='thin', color='DDDDDD')
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)


def _bg_trs(valeur):
    if valeur is None:
        return GRIS_CLAIR
    if valeur >= 70:
        return VERT_CLAIR
    if valeur >= 50:
        return JAUNE_PALE
    return ROUGE_PALE


# ── Feuille 1 : Résumé ───────────────────────────────────────────────────────

def _creer_feuille_resume(wb, equipes, mois, annee):
    ws = wb.active
    ws.title = "Résumé"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 25

    ws.merge_cells('A1:B1')
    t = ws['A1']
    t.value = "RAPPORT MENSUEL — CHAÎNE 4, CUF EBOLOWA"
    t.font = Font(bold=True, size=14, color=BLANC, name='Calibri')
    t.fill = PatternFill("solid", fgColor=VERT_FONCE)
    t.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 32

    ws.merge_cells('A2:B2')
    st = ws['A2']
    st.value = f"{NOMS_MOIS[mois]} {annee}"
    st.font = Font(bold=True, size=12, color="333333", name='Calibri')
    st.alignment = Alignment(horizontal='center', vertical='center')
    st.fill = PatternFill("solid", fgColor=VERT_CLAIR)
    ws.row_dimensions[2].height = 22

    if not equipes:
        ws['A4'] = "Aucune équipe enregistrée pour cette période."
        return

    trs_valeurs = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen = round(sum(trs_valeurs) / len(trs_valeurs), 1) if trs_valeurs else 0
    production_reelle = round(sum(e.volume_sorti for e in equipes), 1)
    objectif_m3 = float(Parametre.get('objectif_m3', 12.5))
    production_cible = objectif_m3 * len(equipes)
    ecart = round(production_cible - production_reelle, 1)

    pertes_total = sum(calcule_pertes_equipe(e)['total'] for e in equipes)
    duree_totale_arrets = sum(e.duree_totale_arrets for e in equipes)

    donnees = [
        ("Nombre d'équipes enregistrées", len(equipes)),
        ("TRS moyen", f"{trs_moyen}%"),
        ("Benchmark international (cible)", "≥ 60%"),
        ("Production réelle", f"{production_reelle} m³"),
        ("Production objectif", f"{production_cible} m³"),
        ("Écart (production non réalisée)", f"{ecart} m³"),
        ("Pertes financières estimées", f"{pertes_total:,.0f} FCFA"),
        ("Durée totale des arrêts", f"{duree_totale_arrets} min"),
        ("Date de génération", date.today().strftime("%d/%m/%Y")),
    ]

    ws.row_dimensions[3].height = 10
    for i, (label, valeur) in enumerate(donnees, start=4):
        ws.row_dimensions[i].height = 22
        c_label = ws.cell(row=i, column=1, value=label)
        c_val   = ws.cell(row=i, column=2, value=valeur)
        bg = GRIS_CLAIR if i % 2 == 0 else BLANC
        if label == "TRS moyen":
            bg = _bg_trs(trs_moyen)
        elif label == "Pertes financières estimées":
            bg = ROUGE_PALE
        _style_cellule(c_label, gras=True, couleur_bg=bg, align='left')
        _style_cellule(c_val, couleur_bg=bg)

    row_top = len(donnees) + 6
    ws.merge_cells(f'A{row_top}:B{row_top}')
    titre_top = ws[f'A{row_top}']
    titre_top.value = "TOP CAUSES D'ARRÊT (analyse Pareto)"
    _style_entete(titre_top, bg_hex="B71C1C")
    ws.row_dimensions[row_top].height = 22

    for j, h in enumerate(['Cause', 'Durée (min)'], start=1):
        c = ws.cell(row=row_top + 1, column=j, value=h)
        _style_entete(c, bg_hex="37474F")
    ws.row_dimensions[row_top + 1].height = 20

    pareto = pareto_arrets(equipes)
    for k, item in enumerate(pareto[:5], start=row_top + 2):
        c1 = ws.cell(row=k, column=1, value=item['cause'])
        c2 = ws.cell(row=k, column=2, value=item['duree'])
        bg = ROUGE_PALE if k == row_top + 2 else (ORANGE_PALE if k == row_top + 3 else BLANC)
        _style_cellule(c1, couleur_bg=bg, align='left')
        _style_cellule(c2, couleur_bg=bg)
        ws.row_dimensions[k].height = 20


# ── Feuille 2 : Équipes ──────────────────────────────────────────────────────

def _creer_feuille_equipes(wb, equipes):
    ws = wb.create_sheet("Équipes")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'A2'

    entetes = [
        'Date', 'Équipe', 'Essences', 'Effectif',
        'Entrée (m³)', 'Conforme (m³)', 'Déclassé (m³)', 'Déchets (m³)',
        'Arrêts (min)', 'TRS (%)', 'Dispo (%)', 'Perf (%)', 'Qualité (%)',
        'Perte D (FCFA)', 'Perte P (FCFA)', 'Perte Q (FCFA)', 'Perte totale (FCFA)',
        'Notes'
    ]
    largeurs = [14, 12, 20, 10, 12, 11, 11, 11, 12, 10, 10, 10, 12, 14, 14, 14, 16, 30]

    for j, (h, w) in enumerate(zip(entetes, largeurs), start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
        c = ws.cell(row=1, column=j, value=h)
        _style_entete(c)
    ws.row_dimensions[1].height = 30

    for i, e in enumerate(equipes, start=2):
        pertes = calcule_pertes_equipe(e)
        valeurs = [
            e.date.strftime('%d/%m/%Y') if e.date else '',
            e.numero_equipe,
            e.essences_label,
            e.effectif,
            e.volume_entree,
            e.volume_conforme,
            e.volume_declass,
            e.volume_dechets,
            e.duree_totale_arrets,
            e.trs_global,
            e.trs_disponibilite,
            e.trs_performance,
            e.trs_qualite,
            pertes['perte_d'],
            pertes['perte_p'],
            pertes['perte_q'],
            pertes['total'],
            e.notes or ''
        ]
        bg_ligne = BLANC if i % 2 == 0 else GRIS_CLAIR
        for j, val in enumerate(valeurs, start=1):
            c = ws.cell(row=i, column=j, value=val)
            if j == 9:
                bg = _bg_trs(e.trs_global)
            elif j in (11, 12, 13):
                bg = _bg_trs(val)
            elif j in (14, 15, 16, 17):
                bg = ROUGE_PALE if (val or 0) > 0 else bg_ligne
            else:
                bg = bg_ligne
            _style_cellule(c, couleur_bg=bg, align='left' if j == 17 else 'center')
        ws.row_dimensions[i].height = 18


# ── Feuille 3 : Arrêts ───────────────────────────────────────────────────────

def _creer_feuille_arrets(wb, equipes):
    ws = wb.create_sheet("Arrêts")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'A2'

    entetes = ['Date', 'Équipe', 'Essences', 'Machine',
               'Heure début', 'Heure fin', 'Durée (min)', 'Cause', 'Catégorie']
    largeurs = [14, 12, 18, 16, 12, 10, 12, 40, 22]

    for j, (h, w) in enumerate(zip(entetes, largeurs), start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
        c = ws.cell(row=1, column=j, value=h)
        _style_entete(c, bg_hex="37474F")
    ws.row_dimensions[1].height = 28

    ligne = 2
    for e in equipes:
        for a in e.arrets:
            valeurs = [
                e.date.strftime('%d/%m/%Y') if e.date else '',
                e.numero_equipe,
                e.essences_label,
                a.machine,
                a.heure_debut,
                a.heure_fin,
                a.duree_min,
                a.cause,
                a.categorie
            ]
            bg = ROUGE_PALE if a.categorie == 'Mécanique' else (
                 ORANGE_PALE if a.categorie == 'Organisationnelle' else (
                 JAUNE_PALE if a.categorie == 'Maintenance planifiée' else BLANC))
            for j, val in enumerate(valeurs, start=1):
                c = ws.cell(row=ligne, column=j, value=val)
                _style_cellule(c, couleur_bg=bg, align='left' if j in (8, 9) else 'center')
            ws.row_dimensions[ligne].height = 18
            ligne += 1

    if ligne == 2:
        ws.cell(row=2, column=1, value="Aucun arrêt enregistré pour cette période.")


# ── Fonction principale ──────────────────────────────────────────────────────

def generer_rapport_excel(equipes, mois, annee):
    wb = Workbook()
    _creer_feuille_resume(wb, equipes, mois, annee)
    _creer_feuille_equipes(wb, equipes)
    _creer_feuille_arrets(wb, equipes)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

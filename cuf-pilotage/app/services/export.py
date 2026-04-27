"""
Service d'export Excel — Rapport mensuel Chaîne 4, Scierie CUF.

Génère un fichier .xlsx en mémoire avec 3 feuilles :
  1. Résumé    — KPIs mensuels (TRS, production, pertes FCFA, top causes)
  2. Postes    — Toutes les lignes avec D/P/Q colorisés
  3. Arrêts    — Détail de chaque arrêt machine

Usage :
    from app.services.export import generer_rapport_excel
    contenu_bytes = generer_rapport_excel(postes, mois=4, annee=2026)
    # → envoyer comme réponse Flask avec send_file()
"""
import io
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter

from app.models import Parametre
from app.services.trs import pareto_arrets, couleur_trs

# ── Palette de couleurs CUF ─────────────────────────────────────────────────
VERT_FONCE   = "1B5E20"   # En-têtes principaux
VERT_CLAIR   = "C8E6C9"   # Ligne paire (vert très pâle)
ORANGE       = "FF8F00"
ROUGE        = "C62828"
JAUNE_PALE   = "FFF9C4"
ORANGE_PALE  = "FFE0B2"
ROUGE_PALE   = "FFCDD2"
BLANC        = "FFFFFF"
GRIS_CLAIR   = "F5F5F5"

NOMS_MOIS = [
    '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
]


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


def _couleur_bg_trs(valeur):
    """Renvoie la couleur de fond hex selon la valeur TRS."""
    if valeur is None:
        return GRIS_CLAIR
    if valeur >= 70:
        return VERT_CLAIR
    if valeur >= 50:
        return JAUNE_PALE
    return ROUGE_PALE


# ── Feuille 1 : Résumé ──────────────────────────────────────────────────────

def _creer_feuille_resume(wb, postes, mois, annee):
    ws = wb.active
    ws.title = "Résumé"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 25

    # Titre principal
    ws.merge_cells('A1:B1')
    titre = ws['A1']
    titre.value = f"RAPPORT MENSUEL — CHAÎNE 4, CUF EBOLOWA"
    titre.font = Font(bold=True, size=14, color=BLANC, name='Calibri')
    titre.fill = PatternFill("solid", fgColor=VERT_FONCE)
    titre.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 32

    ws.merge_cells('A2:B2')
    sous_titre = ws['A2']
    sous_titre.value = f"{NOMS_MOIS[mois]} {annee}"
    sous_titre.font = Font(bold=True, size=12, color="333333", name='Calibri')
    sous_titre.alignment = Alignment(horizontal='center', vertical='center')
    sous_titre.fill = PatternFill("solid", fgColor=VERT_CLAIR)
    ws.row_dimensions[2].height = 22

    if not postes:
        ws['A4'] = "Aucun poste enregistré pour cette période."
        return

    # Calculs agrégés
    trs_valeurs = [p.trs_global for p in postes if p.trs_global is not None]
    trs_moyen = round(sum(trs_valeurs) / len(trs_valeurs), 1) if trs_valeurs else 0
    production_reelle = round(sum(p.volume_sorti or 0 for p in postes), 1)
    objectif_m3 = float(Parametre.get('objectif_m3', 25))
    production_cible = objectif_m3 * len(postes)
    ecart = round(production_cible - production_reelle, 1)

    # Pertes FCFA par essence
    from app.services.trs import calcule_pertes_fcfa
    pertes_total = sum(calcule_pertes_fcfa(p) for p in postes)

    # Durée totale arrêts
    duree_totale_arrets = sum(p.duree_totale_arrets for p in postes)

    # Données par lignes
    donnees = [
        ("Nombre de postes enregistrés", len(postes)),
        ("TRS moyen", f"{trs_moyen}%"),
        ("Benchmark international (cible)", "≥ 60%"),
        ("Production réelle", f"{production_reelle} m³"),
        ("Production objectif", f"{production_cible} m³"),
        ("Écart (production non réalisée)", f"{ecart} m³"),
        ("Pertes financières estimées", f"{pertes_total:,.0f} FCFA"),
        ("Durée totale des arrêts", f"{duree_totale_arrets} min"),
        ("Date de génération", date.today().strftime("%d/%m/%Y")),
    ]

    ws.row_dimensions[3].height = 10  # espace vide

    for i, (label, valeur) in enumerate(donnees, start=4):
        row = ws.row_dimensions[i]
        row.height = 22
        c_label = ws.cell(row=i, column=1, value=label)
        c_val = ws.cell(row=i, column=2, value=valeur)

        bg = GRIS_CLAIR if i % 2 == 0 else BLANC
        # Couleur spéciale pour TRS
        if label == "TRS moyen":
            bg = _couleur_bg_trs(trs_moyen)
        elif label == "Pertes financières estimées":
            bg = ROUGE_PALE

        _style_cellule(c_label, gras=True, couleur_bg=bg, align='left')
        _style_cellule(c_val, couleur_bg=bg)

    # Top causes
    row_top = len(donnees) + 6
    ws.merge_cells(f'A{row_top}:B{row_top}')
    titre_top = ws[f'A{row_top}']
    titre_top.value = "TOP CAUSES D'ARRÊT (analyse Pareto)"
    _style_entete(titre_top, bg_hex="B71C1C")
    ws.row_dimensions[row_top].height = 22

    entetes_pareto = ['Cause', 'Durée (min)']
    for j, h in enumerate(entetes_pareto, start=1):
        c = ws.cell(row=row_top + 1, column=j, value=h)
        _style_entete(c, bg_hex="37474F")
    ws.row_dimensions[row_top + 1].height = 20

    pareto = pareto_arrets(postes)
    for k, item in enumerate(pareto[:5], start=row_top + 2):
        c1 = ws.cell(row=k, column=1, value=item['cause'])
        c2 = ws.cell(row=k, column=2, value=item['duree'])
        bg = ROUGE_PALE if k == row_top + 2 else (ORANGE_PALE if k == row_top + 3 else BLANC)
        _style_cellule(c1, couleur_bg=bg, align='left')
        _style_cellule(c2, couleur_bg=bg)
        ws.row_dimensions[k].height = 20


# ── Feuille 2 : Détail des postes ───────────────────────────────────────────

def _creer_feuille_postes(wb, postes):
    ws = wb.create_sheet("Postes")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'A2'  # Figer la première ligne d'en-têtes

    entetes = [
        'Date', 'Poste', 'Essence',
        'Entrée (m³)', 'Scié (m³)', 'Rebut (m³)', 'Rendement (%)',
        'Conformes', 'Défectueux', 'Effectif',
        'Arrêts (min)', 'TRS (%)', 'Disponibilité (%)', 'Performance (%)', 'Qualité (%)',
        'Notes'
    ]
    largeurs = [14, 12, 11, 12, 11, 11, 13, 10, 11, 10, 12, 10, 16, 14, 12, 30]

    for j, (h, w) in enumerate(zip(entetes, largeurs), start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
        c = ws.cell(row=1, column=j, value=h)
        _style_entete(c)
    ws.row_dimensions[1].height = 30

    for i, p in enumerate(postes, start=2):
        rendement = round(p.rendement_matiere * 100, 1) if p.rendement_matiere else None
        valeurs = [
            p.date.strftime('%d/%m/%Y') if p.date else '',
            p.numero_poste,
            p.essence,
            p.volume_entree,
            p.volume_sorti,
            p.volume_rebut,
            rendement,
            p.nb_planches_conformes,
            p.nb_planches_defectueuses,
            p.effectif,
            p.duree_totale_arrets,
            p.trs_global,
            p.trs_disponibilite,
            p.trs_performance,
            p.trs_qualite,
            p.notes or ''
        ]

        bg_ligne = BLANC if i % 2 == 0 else GRIS_CLAIR
        trs_val = p.trs_global

        for j, val in enumerate(valeurs, start=1):
            c = ws.cell(row=i, column=j, value=val)
            # Colonne TRS global : couleur selon performance
            if j == 12:
                bg = _couleur_bg_trs(trs_val)
            elif j in (13, 14, 15):
                bg = _couleur_bg_trs(val)
            else:
                bg = bg_ligne
            _style_cellule(c, couleur_bg=bg, align='center' if j != 16 else 'left')

        ws.row_dimensions[i].height = 18


# ── Feuille 3 : Détail des arrêts ───────────────────────────────────────────

def _creer_feuille_arrets(wb, postes):
    ws = wb.create_sheet("Arrêts")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'A2'

    entetes = ['Date', 'Poste', 'Essence', 'Machine', 'Heure début', 'Heure fin', 'Durée (min)', 'Cause', 'Catégorie']
    largeurs = [14, 12, 11, 16, 12, 10, 12, 40, 22]

    for j, (h, w) in enumerate(zip(entetes, largeurs), start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
        c = ws.cell(row=1, column=j, value=h)
        _style_entete(c, bg_hex="37474F")
    ws.row_dimensions[1].height = 28

    ligne = 2
    for p in postes:
        for a in p.arrets:
            valeurs = [
                p.date.strftime('%d/%m/%Y') if p.date else '',
                p.numero_poste,
                p.essence,
                a.machine,
                a.heure_debut,
                a.heure_fin,
                a.duree_min,
                a.cause,
                a.categorie
            ]
            bg = ROUGE_PALE if a.categorie == 'Mécanique' else (
                 ORANGE_PALE if a.categorie == 'Organisationnelle' else (
                 JAUNE_PALE if a.categorie == 'Maintenance planifiée' else BLANC
            ))
            for j, val in enumerate(valeurs, start=1):
                c = ws.cell(row=ligne, column=j, value=val)
                _style_cellule(c, couleur_bg=bg, align='left' if j in (8, 9) else 'center')
            ws.row_dimensions[ligne].height = 18
            ligne += 1

    if ligne == 2:
        ws.cell(row=2, column=1, value="Aucun arrêt enregistré pour cette période.")


# ── Fonction principale ──────────────────────────────────────────────────────

def generer_rapport_excel(postes, mois, annee):
    """
    Génère un rapport mensuel Excel en mémoire.

    Args:
        postes : liste d'objets Poste (avec leurs Arrets chargés)
        mois   : int (1-12)
        annee  : int (ex. 2026)

    Returns:
        bytes — contenu du fichier .xlsx
    """
    wb = Workbook()

    _creer_feuille_resume(wb, postes, mois, annee)
    _creer_feuille_postes(wb, postes)
    _creer_feuille_arrets(wb, postes)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

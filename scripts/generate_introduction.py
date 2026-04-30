"""
Génère le document Word de l'Introduction du mémoire CUF.
Usage : python scripts/generate_introduction.py
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../documents/introduction_CUF.docx")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# ── Couleurs ────────────────────────────────────────────────────────────────
VERT_FORET  = RGBColor(0x1A, 0x4D, 0x2E)   # titres principaux
MARRON_BOIS = RGBColor(0x6B, 0x3A, 0x2A)   # sous-titres
GRIS_TEXTE  = RGBColor(0x22, 0x22, 0x22)   # corps de texte

def set_page_margins(doc, top=2.5, bottom=2.5, left=3.0, right=2.5):
    """Marges en centimètres."""
    section = doc.sections[0]
    section.top_margin    = Cm(top)
    section.bottom_margin = Cm(bottom)
    section.left_margin   = Cm(left)
    section.right_margin  = Cm(right)

def set_run_font(run, bold=False, italic=False, size=12, color=GRIS_TEXTE):
    run.bold   = bold
    run.italic = italic
    run.font.size  = Pt(size)
    run.font.color.rgb = color
    run.font.name      = "Times New Roman"

def add_heading(doc, text, level=1, color=VERT_FORET, size=14, space_before=18, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    p.paragraph_format.alignment    = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_run_font(run, bold=True, size=size, color=color)
    # Soulignement léger sur titres de niveau 1
    if level == 1:
        run.underline = True
    return p

def add_subheading(doc, text, size=12, color=MARRON_BOIS):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(text)
    set_run_font(run, bold=True, size=size, color=color)
    return p

def add_body(doc, text, justified=True, first_line=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(8)
    p.paragraph_format.line_spacing = Pt(18)
    if justified:
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if first_line:
        p.paragraph_format.first_line_indent = Cm(1.25)
    run = p.add_run(text)
    set_run_font(run, size=12)
    return p

def add_bold_inline(doc, label, text):
    """Paragraphe avec un label en gras suivi de texte normal."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(8)
    p.paragraph_format.line_spacing = Pt(18)
    p.paragraph_format.alignment    = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.25)
    r_label = p.add_run(label)
    set_run_font(r_label, bold=True, size=12)
    r_text = p.add_run(text)
    set_run_font(r_text, size=12)
    return p

def add_separator(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.alignment    = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("— ✦ —")
    run.font.size  = Pt(10)
    run.font.color.rgb = VERT_FORET

def add_horizontal_rule(doc):
    """Filet de séparation horizontal."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '1A4D2E')
    pBdr.append(bottom)
    pPr.append(pBdr)

# ════════════════════════════════════════════════════════════════════════════
# DOCUMENT
# ════════════════════════════════════════════════════════════════════════════

doc = Document()
set_page_margins(doc)

# ── En-tête institutionnel ───────────────────────────────────────────────────
def add_entete(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("UNIVERSITÉ D'EBOLOWA")
    set_run_font(r, bold=True, size=11, color=VERT_FORET)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Institut Supérieur d'Agriculture, du Bois, de l'Eau et de l'Environnement (ISABEE)")
    set_run_font(r2, size=10, color=GRIS_TEXTE)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Département Foresterie, Sciences et Technologies du Bois")
    set_run_font(r3, size=10, color=GRIS_TEXTE)

    doc.add_paragraph()
    add_horizontal_rule(doc)
    doc.add_paragraph()

add_entete(doc)

# ── Titre du mémoire ─────────────────────────────────────────────────────────
p_titre = doc.add_paragraph()
p_titre.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_titre.paragraph_format.space_before = Pt(6)
p_titre.paragraph_format.space_after  = Pt(4)
r_titre = p_titre.add_run("MÉMOIRE DE MASTER 2")
set_run_font(r_titre, bold=True, size=13, color=VERT_FORET)

p_sous = doc.add_paragraph()
p_sous.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sous.paragraph_format.space_after = Pt(2)
r_sous = p_sous.add_run("Présenté par BWAME EBENGUE CARLOS YVAN  |  Matricule 21ISFS0606")
set_run_font(r_sous, size=10, color=GRIS_TEXTE)

p_annee = doc.add_paragraph()
p_annee.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_annee.paragraph_format.space_after = Pt(2)
r_annee = p_annee.add_run("Année académique 2025-2026  |  Encadreur : Dr Tchiofo Rodine")
set_run_font(r_annee, size=10, color=GRIS_TEXTE)

doc.add_paragraph()
add_horizontal_rule(doc)
doc.add_paragraph()

# ── Titre du sujet ───────────────────────────────────────────────────────────
p_sujet = doc.add_paragraph()
p_sujet.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sujet.paragraph_format.space_before = Pt(8)
p_sujet.paragraph_format.space_after  = Pt(16)
r_sujet = p_sujet.add_run(
    "Amélioration des performances de production de la chaîne 4\n"
    "de la scierie industrielle CUF d'Ebolowa"
)
set_run_font(r_sujet, bold=True, size=15, color=VERT_FORET)

add_horizontal_rule(doc)
doc.add_paragraph()

# ════════════════════════════════════════════════════════════════════════════
# INTRODUCTION
# ════════════════════════════════════════════════════════════════════════════

add_heading(doc, "INTRODUCTION", level=1, size=16)
doc.add_paragraph()

# ── 1. Contexte et justificatif ──────────────────────────────────────────────
add_heading(doc, "1.  Contexte et justificatif", level=2, color=MARRON_BOIS, size=13, space_before=12)

add_body(doc,
    "Le secteur forestier occupe une place structurante dans l'économie camerounaise. "
    "Il contribue à hauteur de 3,8 % du produit intérieur brut national et représente "
    "la troisième source d'exportation du pays, après le cacao et les hydrocarbures "
    "(Banque mondiale, 2024). En 2022, les exportations forestières ont atteint "
    "314,8 milliards de francs CFA, dont 14 à 16 % générés par le bois scié, qui "
    "s'impose comme l'un des segments les plus dynamiques de la filière. Le Cameroun "
    "se distingue par ailleurs comme le premier exportateur mondial de sapelli et "
    "d'iroko sciés, avec 737 000 tonnes exportées cette même année, ce qui témoigne "
    "d'un potentiel productif considérable. Ce secteur emploie environ 45 000 personnes, "
    "dont 22 000 dans le secteur informel, ce qui en fait un pilier social autant "
    "qu'économique pour les régions forestières du pays."
)

add_body(doc,
    "Pourtant, malgré ce potentiel, les performances des scieries camerounaises demeurent "
    "en deçà des standards internationaux. Les travaux de Danwé, Bindzi et Meva'a (2012) "
    "ont montré que le rendement matière des scieries du pays oscille entre 30 et 36 %, "
    "là où les benchmarks internationaux s'établissent à 60 % et au-delà. Cette "
    "sous-performance n'est pas propre au Cameroun : Ngobi et al. (2023) documentent "
    "un rendement de 32 % en Ouganda avec une efficience de 26,6 %, et Cheboiwo, "
    "Macharia et Kiprop (2023) établissent que les scieries kényanes opèrent en moyenne "
    "à moins d'un tiers de leur capacité optimale. À l'échelle de l'Afrique centrale, "
    "Karsenty (2021) confirme un rendement matière moyen de 35 %, révélant un écart "
    "structurel persistant entre ce que les équipements pourraient produire et ce qu'ils "
    "produisent réellement."
)

add_body(doc,
    "La scierie industrielle CUF (Cameroon United Forests) d'Ebolowa s'inscrit dans ce "
    "contexte. Entreprise de grande envergure dotée de quatre chaînes de sciage, elle "
    "transforme les principales essences commerciales de la région du Sud — ayous, azobé, "
    "iroko et movingui — pour des marchés locaux et à l'exportation. La chaîne 4, objet "
    "de la présente étude, concentre une part significative de la production de l'entreprise. "
    "Or, à l'arrivée du stagiaire sur le site, aucune feuille de relevé, aucun tableau de "
    "suivi et aucun historique structuré de la production de cette chaîne n'existaient. "
    "L'objectif de production affiché — 25 mètres cubes par poste — n'avait jamais fait "
    "l'objet d'une vérification technique et avait été fixé de manière empirique, sans "
    "référence aux capacités réelles des équipements."
)

add_body(doc,
    "C'est dans ce vide documentaire et analytique que la présente étude trouve sa "
    "justification. Améliorer les performances d'une chaîne de production sans en "
    "connaître la capacité réelle ni les causes des pertes revient à traiter un symptôme "
    "sans diagnostic. Il est donc nécessaire, avant toute proposition d'action, d'établir "
    "des références techniques solides, de mesurer la réalité du terrain et d'identifier "
    "les facteurs qui freinent la performance de la chaîne 4."
)

# ── 2. Problème et problématique ─────────────────────────────────────────────
add_heading(doc, "2.  Problème et problématique", level=2, color=MARRON_BOIS, size=13, space_before=14)

add_body(doc,
    "La chaîne 4 de la scierie CUF d'Ebolowa présente un déficit de production persistant "
    "et non documenté. L'objectif de 25 mètres cubes par poste n'est pas atteint : la "
    "production réelle se situe entre 10 et 20 mètres cubes, soit un écart pouvant "
    "dépasser 60 %. Cet écart est connu de l'encadrement, mais il n'a jamais été mesuré "
    "ni analysé. La valeur cible elle-même ne repose sur aucune base technique — elle "
    "résulte d'une estimation empirique, sans lien avec les caractéristiques réelles des "
    "machines ni avec les propriétés des essences transformées. En l'absence de données "
    "structurées, de référence théorique établie et d'outils de diagnostic, les responsables "
    "de CUF ne disposent d'aucun levier pour agir sur des causes identifiées. Toutes les "
    "décisions relatives à la production de la chaîne 4 sont donc prises à l'aveugle."
)

# Problématique en encadré visuel
p_pb = doc.add_paragraph()
p_pb.paragraph_format.left_indent   = Cm(1.0)
p_pb.paragraph_format.right_indent  = Cm(1.0)
p_pb.paragraph_format.space_before  = Pt(6)
p_pb.paragraph_format.space_after   = Pt(6)
p_pb.paragraph_format.alignment     = WD_ALIGN_PARAGRAPH.JUSTIFY
r_label = p_pb.add_run("Problématique : ")
set_run_font(r_label, bold=True, italic=True, size=12, color=VERT_FORET)
r_pb = p_pb.add_run(
    "Dans quelle mesure l'absence de référence technique de production, de système de "
    "mesure et de diagnostic des pertes compromet-elle les performances de production de "
    "la chaîne 4 de la scierie industrielle CUF d'Ebolowa, et quelles actions correctives "
    "permettraient d'y remédier de façon durable ?"
)
set_run_font(r_pb, italic=True, size=12, color=GRIS_TEXTE)

# Bordure gauche verte sur l'encadré
pPr = p_pb._p.get_or_add_pPr()
pBdr = OxmlElement('w:pBdr')
left = OxmlElement('w:left')
left.set(qn('w:val'), 'single')
left.set(qn('w:sz'), '12')
left.set(qn('w:space'), '12')
left.set(qn('w:color'), '1A4D2E')
pBdr.append(left)
pPr.append(pBdr)

doc.add_paragraph()

# ── 3. Objectif général et objectifs spécifiques ─────────────────────────────
add_heading(doc, "3.  Objectif général et objectifs spécifiques", level=2, color=MARRON_BOIS, size=13, space_before=14)

add_subheading(doc, "Objectif général", size=11, color=VERT_FORET)
add_body(doc,
    "L'objectif général de cette étude est d'améliorer les performances de production "
    "de la chaîne 4 de la scierie industrielle CUF d'Ebolowa en établissant sa capacité "
    "théorique réelle, en mesurant sa production réelle, en diagnostiquant les causes des "
    "pertes et en proposant des actions correctives mesurables accompagnées d'un outil "
    "de pilotage adapté."
)

add_subheading(doc, "Objectifs spécifiques", size=11, color=VERT_FORET)
add_body(doc,
    "Pour atteindre cet objectif général, six objectifs spécifiques ont été définis. "
    "Le premier consiste à déterminer la capacité théorique réelle de la chaîne 4 à "
    "partir des caractéristiques techniques des machines et des essences transformées. "
    "Le deuxième vise à mesurer la production réelle de la chaîne à travers un système "
    "de collecte de données mis en place sur le terrain. Le troisième porte sur "
    "l'évaluation de l'écart entre la capacité théorique et la production réelle, le "
    "calcul du Taux de Rendement Synthétique (TRS) de la chaîne 4 et l'estimation du "
    "coût financier des pertes enregistrées. Le quatrième objectif est d'identifier et "
    "de hiérarchiser les causes responsables de cet écart à l'aide d'outils d'analyse "
    "appropriés. Le cinquième objectif vise à proposer des actions correctives prioritaires "
    "et à estimer les gains de production et les bénéfices financiers attendus de leur "
    "mise en œuvre. Enfin, le sixième objectif est de concevoir un outil de pilotage "
    "adapté aux besoins des différents responsables de CUF, afin d'assurer un suivi "
    "continu des performances de la chaîne 4."
)

# ── 4. Hypothèses de recherche ───────────────────────────────────────────────
add_heading(doc, "4.  Hypothèses de recherche", level=2, color=MARRON_BOIS, size=13, space_before=14)

add_body(doc,
    "Quatre hypothèses guident cette étude. La première postule que la capacité théorique "
    "réelle de la chaîne 4 est inférieure à l'objectif de 25 mètres cubes par poste "
    "actuellement fixé par CUF, ce qui remettrait en cause le bien-fondé même de cet "
    "objectif. La deuxième hypothèse avance que les pertes de performance sont "
    "principalement d'origine organisationnelle et opérationnelle, et non liées à des "
    "défaillances techniques des équipements — autrement dit, que des améliorations sont "
    "possibles sans remplacement de machines. La troisième hypothèse stipule qu'en "
    "l'absence de système de mesure, le TRS réel de la chaîne 4 est inférieur à 60 %, "
    "seuil en dessous duquel Jonsson et Lesshammar (1999) identifient une performance "
    "insuffisante justifiant une intervention structurée. La quatrième et dernière "
    "hypothèse est que des actions correctives ciblées, sans investissement majeur en "
    "équipement, permettent d'améliorer significativement le TRS et de réduire les pertes "
    "financières de manière mesurable."
)

# ── Pied de page ─────────────────────────────────────────────────────────────
doc.add_paragraph()
add_horizontal_rule(doc)
p_footer = doc.add_paragraph()
p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_f = p_footer.add_run(
    "BWAME EBENGUE CARLOS YVAN  ·  21ISFS0606  ·  ISABEE — Université d'Ebolowa  ·  2025-2026"
)
set_run_font(r_f, size=9, color=RGBColor(0x88, 0x88, 0x88))

# ── Sauvegarde ───────────────────────────────────────────────────────────────
doc.save(OUTPUT_PATH)
print(f"✅ Document généré : {OUTPUT_PATH}")

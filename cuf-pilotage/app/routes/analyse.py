"""
Routes d'analyse — Page Pareto dédiée.

Cette page répond à la question : "Quelles sont les causes majeures
de perte de production sur la Chaîne 4 ?" selon le principe 80/20.

Filtres disponibles :
    - Période : 7j / 30j / 90j / depuis le début
    - Machine : Bicoupe / Scie de tête / etc.
    - Catégorie de cause : Mécanique / Organisationnelle / etc.
"""
from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import date, timedelta

from ..models import Poste, Arret
from ..services.trs import pareto_arrets
from config import Config

analyse_bp = Blueprint('analyse', __name__, url_prefix='/analyse')


@analyse_bp.route('/arrets')
@login_required
def arrets():
    """
    Page Pareto des arrêts avec filtres multicritères.

    Paramètres GET optionnels :
        jours     : 7 / 30 / 90 / 0 (tout)
        machine   : nom de la machine (ou vide = toutes)
        categorie : catégorie de cause (ou vide = toutes)
    """
    # --- 1. Récupérer les filtres ---
    jours     = int(request.args.get('jours', 30))
    machine   = request.args.get('machine', '').strip()
    categorie = request.args.get('categorie', '').strip()

    # --- 2. Filtrer les postes par période ---
    if jours > 0:
        depuis = date.today() - timedelta(days=jours)
        postes = Poste.query.filter(Poste.date >= depuis).all()
    else:
        postes = Poste.query.all()

    # --- 3. Filtrer les arrêts par machine et catégorie ---
    arrets_filtres = []
    for p in postes:
        for a in p.arrets:
            if machine and a.machine != machine:
                continue
            if categorie and a.categorie != categorie:
                continue
            arrets_filtres.append({
                'poste_id':  p.id,
                'date':      p.date,
                'numero_poste': p.numero_poste,
                'essence':   p.essence,
                'machine':   a.machine,
                'heure_debut': a.heure_debut,
                'heure_fin': a.heure_fin,
                'duree_min': a.duree_min or 0,
                'cause':     a.cause,
                'categorie': a.categorie,
            })

    # Trier par date décroissante pour le tableau
    arrets_filtres.sort(key=lambda x: (x['date'], x['heure_debut']), reverse=True)

    # --- 4. Calculer le Pareto sur les postes filtrés ---
    #    (en respectant aussi les filtres machine/catégorie)
    class ArretFiltreur:
        """Objet léger pour simuler un Poste avec arrets filtrés."""
        def __init__(self, arrets):
            self.arrets = arrets

    # Reconstituer des "pseudo-postes" avec arrêts filtrés pour pareto_arrets
    class FakeArret:
        def __init__(self, d):
            self.duree_min = d['duree_min']
            self.cause     = d['cause']
            self.categorie = d['categorie']
    pseudo = [ArretFiltreur([FakeArret(a) for a in arrets_filtres])]
    pareto = pareto_arrets(pseudo)

    # --- 5. Statistiques agrégées ---
    total_arrets = sum(a['duree_min'] for a in arrets_filtres)
    nb_arrets    = len(arrets_filtres)

    # Répartition par machine
    par_machine = {}
    for a in arrets_filtres:
        par_machine.setdefault(a['machine'], 0)
        par_machine[a['machine']] += a['duree_min']
    par_machine = sorted(par_machine.items(), key=lambda x: x[1], reverse=True)

    # Répartition par catégorie
    par_categorie = {}
    for a in arrets_filtres:
        par_categorie.setdefault(a['categorie'], 0)
        par_categorie[a['categorie']] += a['duree_min']
    par_categorie = sorted(par_categorie.items(), key=lambda x: x[1], reverse=True)

    # Indice Pareto 80% : combien de causes expliquent 80% des pertes ?
    nb_causes_80 = 0
    for p in pareto:
        nb_causes_80 += 1
        if p['pct_cumule'] >= 80:
            break

    stats = {
        'nb_arrets':     nb_arrets,
        'total_minutes': total_arrets,
        'total_heures':  round(total_arrets / 60, 1),
        'nb_causes_80':  nb_causes_80,
        'nb_causes_total': len(pareto),
        'par_machine':   par_machine,
        'par_categorie': par_categorie,
    }

    # --- 6. Données pour graphiques Chart.js ---
    # Pareto : top 10 pour ne pas saturer le graphique
    pareto_top = pareto[:10]
    chart_labels     = [p['cause'] for p in pareto_top]
    chart_durees     = [p['duree'] for p in pareto_top]
    chart_cumul      = [p['pct_cumule'] for p in pareto_top]

    return render_template('analyse/arrets.html',
                           arrets=arrets_filtres,
                           pareto=pareto,
                           stats=stats,
                           jours=jours,
                           machine=machine,
                           categorie=categorie,
                           machines=Config.MACHINES,
                           categories=Config.CATEGORIES_ARRET,
                           chart_labels=chart_labels,
                           chart_durees=chart_durees,
                           chart_cumul=chart_cumul)

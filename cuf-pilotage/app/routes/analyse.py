"""
Routes d'analyse — Page Pareto dédiée.
"""
from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import date, timedelta
from ..models import Equipe
from ..services.trs import pareto_arrets
from ..utils import roles_required
from config import Config

analyse_bp = Blueprint('analyse', __name__, url_prefix='/analyse')


@analyse_bp.route('/arrets')
@login_required
@roles_required('chef', 'admin')
def arrets():
    jours     = int(request.args.get('jours', 30))
    machine   = request.args.get('machine', '').strip()
    categorie = request.args.get('categorie', '').strip()

    if jours > 0:
        depuis = date.today() - timedelta(days=jours)
        equipes = Equipe.query.filter(Equipe.date >= depuis).all()
    else:
        equipes = Equipe.query.all()

    arrets_filtres = []
    for e in equipes:
        essences_str = e.essences_label
        for a in e.arrets:
            if machine and a.machine != machine:
                continue
            if categorie and a.categorie != categorie:
                continue
            arrets_filtres.append({
                'poste_id':     e.id,
                'date':         e.date,
                'numero_poste': e.numero_equipe,
                'essence':      essences_str,
                'machine':      a.machine,
                'heure_debut':  a.heure_debut,
                'heure_fin':    a.heure_fin,
                'duree_min':    a.duree_min or 0,
                'cause':        a.cause,
                'categorie':    a.categorie,
            })

    arrets_filtres.sort(key=lambda x: (x['date'], x['heure_debut']), reverse=True)

    class _FakeArret:
        def __init__(self, d):
            self.duree_min = d['duree_min']
            self.cause     = d['cause']
            self.categorie = d['categorie']

    class _FakeEquipe:
        def __init__(self, arrets):
            self.arrets = arrets

    pseudo = [_FakeEquipe([_FakeArret(a) for a in arrets_filtres])]
    pareto = pareto_arrets(pseudo)

    total_arrets = sum(a['duree_min'] for a in arrets_filtres)
    nb_arrets    = len(arrets_filtres)

    par_machine = {}
    for a in arrets_filtres:
        par_machine.setdefault(a['machine'], 0)
        par_machine[a['machine']] += a['duree_min']
    par_machine = sorted(par_machine.items(), key=lambda x: x[1], reverse=True)

    par_categorie = {}
    for a in arrets_filtres:
        par_categorie.setdefault(a['categorie'], 0)
        par_categorie[a['categorie']] += a['duree_min']
    par_categorie = sorted(par_categorie.items(), key=lambda x: x[1], reverse=True)

    nb_causes_80 = 0
    for p in pareto:
        nb_causes_80 += 1
        if p['pct_cumule'] >= 80:
            break

    stats = {
        'nb_arrets':       nb_arrets,
        'total_minutes':   total_arrets,
        'total_heures':    round(total_arrets / 60, 1),
        'nb_causes_80':    nb_causes_80,
        'nb_causes_total': len(pareto),
        'par_machine':     par_machine,
        'par_categorie':   par_categorie,
    }

    pareto_top   = pareto[:10]
    chart_labels = [p['cause'] for p in pareto_top]
    chart_durees = [p['duree'] for p in pareto_top]
    chart_cumul  = [p['pct_cumule'] for p in pareto_top]

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

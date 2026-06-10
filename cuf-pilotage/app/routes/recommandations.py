"""
Routes des prescriptions de pilotage — Couche 1 : règles déterministes (100 % hors ligne).

  GET /recommandations/  : page principale (prescriptions actives pour le rôle)
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from datetime import date, timedelta
from collections import defaultdict
from ..models import Equipe, STATUTS_ANALYSES, Probleme
from ..services.recommandations import analyse_recommandations
from ..services.trs import manque_a_gagner_agrege, pareto_arrets
from ..utils import roles_required

recos_bp = Blueprint('recommandations', __name__, url_prefix='/recommandations')

_STATUTS = STATUTS_ANALYSES


def _equipes_periode(jours=30):
    depuis = date.today() - timedelta(days=jours)
    return Equipe.query.filter(
        Equipe.date >= depuis,
        Equipe.statut.in_(_STATUTS)
    ).all()


def _contexte_extra(equipes, manque):
    """Calcule les clés de contexte enrichies depuis les données des équipes."""
    # Machine critique (temps d'arrêt cumulé le plus élevé)
    arrets_par_machine = defaultdict(int)
    for e in equipes:
        for a in e.arrets:
            if a.duree_min and a.machine:
                arrets_par_machine[a.machine] += a.duree_min
    machine_critique = None
    machine_arrets_h = 0.0
    if arrets_par_machine:
        machine_critique = max(arrets_par_machine, key=arrets_par_machine.get)
        machine_arrets_h = round(arrets_par_machine[machine_critique] / 60, 1)

    # Cause dominante par catégorie d'arrêt
    pareto = pareto_arrets(equipes)
    cause_dominante = None
    cause_dominante_pct = 0.0
    cause_dominante_fcfa = 0
    if pareto:
        cat_totals = defaultdict(int)
        total_duree = sum(r['duree'] for r in pareto)
        for r in pareto:
            cat = r.get('categorie') or 'Autre'
            cat_totals[cat] += r['duree']
        if cat_totals and total_duree > 0:
            top_cat = max(cat_totals, key=cat_totals.get)
            cause_dominante = top_cat
            cause_dominante_pct = round(cat_totals[top_cat] / total_duree * 100, 1)
            cause_dominante_fcfa = round(manque * cause_dominante_pct / 100)

    # Essence la plus déclassée (ratio volume_declass / (conforme + declass))
    essence_vol = defaultdict(lambda: {'conf': 0.0, 'dec': 0.0})
    for e in equipes:
        for p in e.productions:
            if p.essence:
                essence_vol[p.essence]['conf'] += p.volume_conforme
                essence_vol[p.essence]['dec']  += p.volume_declass
    essence_declass = None
    declass_pct_essence = 0.0
    for ess, vols in essence_vol.items():
        total = vols['conf'] + vols['dec']
        if total > 0:
            pct = round(vols['dec'] / total * 100, 1)
            if pct > declass_pct_essence:
                declass_pct_essence = pct
                essence_declass = ess

    return {
        'machine_critique':     machine_critique,
        'machine_arrets_h':     machine_arrets_h,
        'cause_dominante':      cause_dominante,
        'cause_dominante_pct':  cause_dominante_pct,
        'cause_dominante_fcfa': cause_dominante_fcfa,
        'essence_declass':      essence_declass,
        'declass_pct_essence':  declass_pct_essence,
    }


@recos_bp.route('/')
@login_required
@roles_required('chef', 'prod', 'pdg', 'admin')
def index():
    jours   = int(request.args.get('jours', 30))
    equipes = _equipes_periode(jours)
    role    = current_user.role

    trs_vals  = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen = round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else None
    manque    = manque_a_gagner_agrege(equipes).get('manque_a_gagner_estime', 0.0)

    extra    = _contexte_extra(equipes, manque)
    toutes   = analyse_recommandations(equipes, contexte_extra=extra)
    visibles = [r for r in toutes if role in r['roles']]

    # Problèmes Ishikawa déjà ouverts par code prescription
    problemes_par_reco = {
        p.reco_code: p.id
        for p in Probleme.query.filter(
            Probleme.origine_type == 'recommandation',
            Probleme.reco_code.isnot(None),
        ).all()
    }

    contexte_global = {
        'trs_moyen': trs_moyen,
        'manque':    manque,
        'nb_postes': len(equipes),
    }

    return render_template(
        'recommandations/index.html',
        recommandations=visibles,
        contexte_global=contexte_global,
        nb_total=len(toutes),
        jours=jours,
        problemes_par_reco=problemes_par_reco,
    )

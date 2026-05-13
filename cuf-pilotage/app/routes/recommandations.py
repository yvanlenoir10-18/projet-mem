"""
Routes du moteur de recommandations — P14.

  GET  /recommandations/          : page principale (recommandations actives pour le rôle)
  POST /recommandations/ai/<code> : endpoint AJAX — enrichissement IA on-demand
"""
from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import login_required, current_user
from datetime import date, timedelta
from ..models import Equipe
from ..services.recommandations import analyse_recommandations, top_n_recommandations, _REGLES
from ..services.reco_ai import ai_enrichissement, cache_invalidate
from ..utils import roles_required

recos_bp = Blueprint('recommandations', __name__, url_prefix='/recommandations')

_STATUTS = ('soumis', 'verrouille')


def _equipes_periode(jours=30):
    depuis = date.today() - timedelta(days=jours)
    return Equipe.query.filter(
        Equipe.date >= depuis,
        Equipe.statut.in_(_STATUTS)
    ).all()


@recos_bp.route('/')
@login_required
@roles_required('chef', 'pdg', 'admin')
def index():
    jours   = int(request.args.get('jours', 30))
    equipes = _equipes_periode(jours)
    role    = current_user.role

    toutes   = analyse_recommandations(equipes)
    visibles = [r for r in toutes if role in r['roles']]

    # Contexte agrégé pour l'affichage de l'en-tête et pour le pass au JS
    trs_vals  = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen = round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else None

    from ..services.trs import manque_a_gagner_agrege
    manque = manque_a_gagner_agrege(equipes).get('manque_a_gagner_estime', 0.0)

    contexte_global = {
        'trs_moyen':  trs_moyen,
        'manque':     manque,
        'nb_postes':  len(equipes),
    }

    return render_template(
        'recommandations/index.html',
        recommandations=visibles,
        contexte_global=contexte_global,
        nb_total=len(toutes),
        jours=jours,
    )


@recos_bp.route('/ai/<code>', methods=['POST'])
@login_required
@roles_required('chef', 'pdg', 'admin')
def enrichissement_ai(code):
    codes_valides = {r['code'] for r in _REGLES}
    if code not in codes_valides:
        abort(400)

    force  = request.args.get('force', '').lower() == '1'
    if force:
        cache_invalidate(code)

    contexte = request.get_json(silent=True) or {}
    resultat = ai_enrichissement(code, contexte)
    return jsonify(resultat)

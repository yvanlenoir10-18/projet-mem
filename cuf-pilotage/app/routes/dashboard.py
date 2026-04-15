"""
Routes des tableaux de bord.
- Vue Chef Scierie : analyse opérationnelle (TRS, Pareto, volumes)
- Vue PDG         : synthèse financière (FCFA, objectifs, traffic light)
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from datetime import date, timedelta
from sqlalchemy import func
from ..models import db, Poste, Arret, Parametre
from ..services.trs import pareto_arrets, couleur_trs, calcule_pertes_fcfa

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def _get_postes_periode(jours=30):
    """Récupère les postes des N derniers jours."""
    depuis = date.today() - timedelta(days=jours)
    return Poste.query.filter(Poste.date >= depuis)\
                      .order_by(Poste.date.desc()).all()


@dashboard_bp.route('/chef')
@login_required
def vue_chef():
    """
    Tableau de bord Chef Scierie.
    Affiche TRS semaine, Pareto arrêts, volumes par essence, comparaison postes.
    """
    jours = int(request.args.get('jours', 30))
    postes = _get_postes_periode(jours)

    if not postes:
        return render_template('chef/dashboard.html',
                               postes=[], pareto=[], stats={}, jours=jours)

    # --- Statistiques générales ---
    trs_valeurs = [p.trs_global for p in postes if p.trs_global is not None]
    trs_moyen   = round(sum(trs_valeurs) / len(trs_valeurs), 1) if trs_valeurs else 0

    total_produit = sum(p.volume_sorti for p in postes)
    total_rebut   = sum(p.volume_rebut for p in postes)
    total_arrets  = sum(p.duree_totale_arrets for p in postes)

    # --- Pareto des causes d'arrêt ---
    pareto = pareto_arrets(postes)

    # --- TRS par essence ---
    par_essence = {}
    for p in postes:
        if p.essence not in par_essence:
            par_essence[p.essence] = {'volumes': [], 'trs': []}
        par_essence[p.essence]['volumes'].append(p.volume_sorti)
        if p.trs_global:
            par_essence[p.essence]['trs'].append(p.trs_global)

    essence_stats = []
    for essence, data in par_essence.items():
        trs_e = data['trs']
        essence_stats.append({
            'essence': essence,
            'volume_total': round(sum(data['volumes']), 2),
            'trs_moyen': round(sum(trs_e) / len(trs_e), 1) if trs_e else 0,
        })

    # --- Comparaison Matin vs Après-midi ---
    matin     = [p for p in postes if p.numero_poste == 'Matin']
    apres_midi = [p for p in postes if p.numero_poste == 'Apres-midi']

    def trs_moyen_groupe(groupe):
        vals = [p.trs_global for p in groupe if p.trs_global]
        return round(sum(vals) / len(vals), 1) if vals else 0

    stats = {
        'trs_moyen': trs_moyen,
        'couleur_trs': couleur_trs(trs_moyen),
        'total_produit': round(total_produit, 2),
        'total_rebut': round(total_rebut, 2),
        'total_arrets_h': round(total_arrets / 60, 1),
        'nb_postes': len(postes),
        'trs_matin': trs_moyen_groupe(matin),
        'trs_apres_midi': trs_moyen_groupe(apres_midi),
        'essence_stats': essence_stats,
    }

    # Données pour graphique TRS quotidien (Chart.js)
    # Grouper par date, calculer TRS moyen par jour
    trs_par_date = {}
    for p in sorted(postes, key=lambda x: x.date):
        d = p.date.isoformat()
        if d not in trs_par_date:
            trs_par_date[d] = []
        if p.trs_global:
            trs_par_date[d].append(p.trs_global)

    chart_labels = list(trs_par_date.keys())
    chart_trs    = [
        round(sum(v) / len(v), 1) if v else 0
        for v in trs_par_date.values()
    ]

    return render_template('chef/dashboard.html',
                           postes=postes[:10],
                           pareto=pareto[:8],
                           stats=stats,
                           jours=jours,
                           chart_labels=chart_labels,
                           chart_trs=chart_trs)


@dashboard_bp.route('/pdg')
@login_required
def vue_pdg():
    """
    Tableau de bord PDG.
    5 KPI max, pertes en FCFA, traffic light, tendance mensuelle.
    """
    # Mois courant
    aujourd_hui = date.today()
    debut_mois  = aujourd_hui.replace(day=1)
    postes_mois = Poste.query.filter(Poste.date >= debut_mois).all()

    objectif   = float(Parametre.get('objectif_m3', 25))
    nb_postes  = len(postes_mois)

    production_reelle = sum(p.volume_sorti for p in postes_mois)
    production_cible  = objectif * nb_postes

    trs_vals  = [p.trs_global for p in postes_mois if p.trs_global]
    trs_moyen = round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else 0

    # Pertes financières totales du mois
    perte_totale = sum(calcule_pertes_fcfa(p) for p in postes_mois)

    # Top 3 causes d'arrêt du mois
    pareto = pareto_arrets(postes_mois)[:3]

    # Tendance sur 6 mois (TRS moyen mensuel)
    tendance = []
    for i in range(5, -1, -1):
        mois_ref = (aujourd_hui.replace(day=1) - timedelta(days=30 * i))
        debut    = mois_ref.replace(day=1)
        # fin du mois
        if mois_ref.month == 12:
            fin = mois_ref.replace(year=mois_ref.year + 1, month=1, day=1)
        else:
            fin = mois_ref.replace(month=mois_ref.month + 1, day=1)

        postes_m = Poste.query.filter(
            Poste.date >= debut, Poste.date < fin
        ).all()
        vals = [p.trs_global for p in postes_m if p.trs_global]
        tendance.append({
            'mois': debut.strftime('%b %Y'),
            'trs':  round(sum(vals) / len(vals), 1) if vals else 0
        })

    return render_template('pdg/dashboard.html',
                           trs_moyen=trs_moyen,
                           couleur_trs=couleur_trs(trs_moyen),
                           production_reelle=round(production_reelle, 1),
                           production_cible=round(production_cible, 1),
                           perte_fcfa=int(perte_totale),
                           nb_postes=nb_postes,
                           pareto=pareto,
                           tendance=tendance,
                           mois_courant=aujourd_hui.strftime('%B %Y'))

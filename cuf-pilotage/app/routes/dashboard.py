"""
Routes des tableaux de bord.
- Vue Chef Scierie : analyse opérationnelle (TRS, Pareto, volumes)
- Vue PDG         : synthèse financière (FCFA, objectifs, traffic light)
- Export Excel    : rapport mensuel téléchargeable
"""
from flask import Blueprint, render_template, request, send_file, abort
from flask_login import login_required
from datetime import date, timedelta
import io
from ..models import db, Equipe, Parametre
from ..services.trs import pareto_arrets, couleur_trs, calcule_pertes_equipe, calcule_pertes_fcfa
from ..services.export import generer_rapport_excel

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

NOMS_MOIS = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
             'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']


def _mois_disponibles(n=12):
    aujourd_hui = date.today()
    result = []
    annee, mois = aujourd_hui.year, aujourd_hui.month
    for i in range(n):
        result.append({'label': f"{NOMS_MOIS[mois]} {annee}",
                       'mois': mois, 'annee': annee, 'actif': (i == 0)})
        mois -= 1
        if mois == 0:
            mois = 12
            annee -= 1
    return result


def _get_equipes_periode(jours=30):
    depuis = date.today() - timedelta(days=jours)
    return Equipe.query.filter(Equipe.date >= depuis)\
                       .order_by(Equipe.date.desc()).all()


@dashboard_bp.route('/chef')
@login_required
def vue_chef():
    jours = int(request.args.get('jours', 30))
    equipes = _get_equipes_periode(jours)

    if not equipes:
        return render_template('chef/dashboard.html',
                               postes=[], pareto=[], stats={}, jours=jours)

    trs_valeurs  = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen    = round(sum(trs_valeurs) / len(trs_valeurs), 1) if trs_valeurs else 0
    total_produit = sum(e.volume_sorti for e in equipes)
    total_rebut   = sum(e.volume_rebut for e in equipes)
    total_arrets  = sum(e.duree_totale_arrets for e in equipes)

    pareto = pareto_arrets(equipes)

    # TRS par essence (agrège sur les lignes de production)
    par_essence = {}
    for e in equipes:
        for p in e.productions:
            if p.essence not in par_essence:
                par_essence[p.essence] = {'volumes': [], 'trs': []}
            par_essence[p.essence]['volumes'].append(p.volume_sorti)
        if e.trs_global:
            for p in e.productions:
                par_essence[p.essence]['trs'].append(e.trs_global)

    essence_stats = []
    for essence, data in par_essence.items():
        trs_e = data['trs']
        essence_stats.append({
            'essence': essence,
            'volume_total': round(sum(data['volumes']), 2),
            'trs_moyen': round(sum(trs_e) / len(trs_e), 1) if trs_e else 0,
        })

    matin      = [e for e in equipes if e.numero_equipe == 'Matin']
    apres_midi = [e for e in equipes if e.numero_equipe == 'Apres-midi']

    def trs_moyen_groupe(groupe):
        vals = [e.trs_global for e in groupe if e.trs_global]
        return round(sum(vals) / len(vals), 1) if vals else 0

    stats = {
        'trs_moyen':        trs_moyen,
        'couleur_trs':      couleur_trs(trs_moyen),
        'total_produit':    round(total_produit, 2),
        'total_rebut':      round(total_rebut, 2),
        'total_arrets_h':   round(total_arrets / 60, 1),
        'nb_postes':        len(equipes),
        'trs_matin':        trs_moyen_groupe(matin),
        'trs_apres_midi':   trs_moyen_groupe(apres_midi),
        'essence_stats':    essence_stats,
    }

    trs_par_date = {}
    for e in sorted(equipes, key=lambda x: x.date):
        d = e.date.isoformat()
        if d not in trs_par_date:
            trs_par_date[d] = []
        if e.trs_global:
            trs_par_date[d].append(e.trs_global)

    chart_labels = list(trs_par_date.keys())
    chart_trs    = [round(sum(v) / len(v), 1) if v else 0 for v in trs_par_date.values()]

    return render_template('chef/dashboard.html',
                           postes=equipes[:10],
                           pareto=pareto[:8],
                           stats=stats,
                           jours=jours,
                           chart_labels=chart_labels,
                           chart_trs=chart_trs,
                           mois_options=_mois_disponibles())


@dashboard_bp.route('/pdg')
@login_required
def vue_pdg():
    aujourd_hui = date.today()
    debut_mois  = aujourd_hui.replace(day=1)
    equipes_mois = Equipe.query.filter(Equipe.date >= debut_mois).all()

    objectif   = float(Parametre.get('objectif_m3', 12.5))
    nb_postes  = len(equipes_mois)

    production_reelle = sum(e.volume_sorti for e in equipes_mois)
    production_cible  = objectif * nb_postes

    trs_vals  = [e.trs_global for e in equipes_mois if e.trs_global]
    trs_moyen = round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else 0

    perte_totale = sum(calcule_pertes_fcfa(e) for e in equipes_mois)

    pareto = pareto_arrets(equipes_mois)[:3]

    tendance = []
    for i in range(5, -1, -1):
        mois_ref = (aujourd_hui.replace(day=1) - timedelta(days=30 * i))
        debut = mois_ref.replace(day=1)
        if mois_ref.month == 12:
            fin = mois_ref.replace(year=mois_ref.year + 1, month=1, day=1)
        else:
            fin = mois_ref.replace(month=mois_ref.month + 1, day=1)
        equipes_m = Equipe.query.filter(Equipe.date >= debut, Equipe.date < fin).all()
        vals = [e.trs_global for e in equipes_m if e.trs_global]
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
                           mois_courant=aujourd_hui.strftime('%B %Y'),
                           mois_options=_mois_disponibles())


@dashboard_bp.route('/pertes')
@login_required
def pertes():
    """Page de drill-down des pertes financières D/P/Q."""
    jours = int(request.args.get('jours', 30))
    equipes = _get_equipes_periode(jours)

    total_d = total_p = total_q = 0.0

    # Pertes D agrégées par machine
    par_machine = {}
    # Pertes Q agrégées par essence
    par_essence_q = {}
    # Pertes D agrégées par cause d'arrêt
    par_cause = {}

    for e in equipes:
        p = calcule_pertes_equipe(e)
        total_d += p['perte_d']
        total_p += p['perte_p']
        total_q += p['perte_q']

        # Prix moyen pondéré de cette équipe (pour attribuer Perte D à chaque machine)
        vol_total = e.volume_sorti
        if vol_total > 0 and e.productions:
            from ..services.trs import _prix_production
            prix_moyen = sum(_prix_production(pr) * pr.volume_sorti for pr in e.productions) / vol_total
        else:
            prix_moyen = 0.0

        capacite_h = float(Parametre.get('capacite_equipe_h', 1.5625))

        for a in e.arrets:
            if not a.duree_min or a.categorie == 'Maintenance planifiée':
                continue
            perte_arret = (a.duree_min / 60) * capacite_h * prix_moyen

            if a.machine not in par_machine:
                par_machine[a.machine] = {'perte': 0.0, 'duree': 0, 'count': 0}
            par_machine[a.machine]['perte']  += perte_arret
            par_machine[a.machine]['duree']  += a.duree_min
            par_machine[a.machine]['count']  += 1

            cle_cause = a.cause[:50]
            if cle_cause not in par_cause:
                par_cause[cle_cause] = {'perte': 0.0, 'duree': 0, 'categorie': a.categorie}
            par_cause[cle_cause]['perte'] += perte_arret
            par_cause[cle_cause]['duree'] += a.duree_min

        # Perte Q par essence
        taux_revente = float(Parametre.get('taux_revente_rebut', 0.30))
        from ..services.trs import _prix_production
        for pr in e.productions:
            pq = pr.volume_sorti * pr.rebut_pct * _prix_production(pr) * (1 - taux_revente)
            if pr.essence not in par_essence_q:
                par_essence_q[pr.essence] = {'perte': 0.0, 'volume_rebut': 0.0}
            par_essence_q[pr.essence]['perte']       += pq
            par_essence_q[pr.essence]['volume_rebut'] += pr.volume_rebut_calcule

    # Tri par perte décroissante
    machines_triees = sorted(par_machine.items(), key=lambda x: x[1]['perte'], reverse=True)
    causes_triees   = sorted(par_cause.items(),   key=lambda x: x[1]['perte'], reverse=True)[:10]
    essences_triees = sorted(par_essence_q.items(), key=lambda x: x[1]['perte'], reverse=True)

    total_global = total_d + total_p + total_q

    return render_template('dashboard/pertes.html',
                           jours=jours,
                           total_d=int(total_d),
                           total_p=int(total_p),
                           total_q=int(total_q),
                           total_global=int(total_global),
                           machines=machines_triees,
                           causes=causes_triees,
                           essences=essences_triees,
                           nb_equipes=len(equipes))


@dashboard_bp.route('/export/excel')
@login_required
def export_excel():
    aujourd_hui = date.today()
    try:
        mois  = int(request.args.get('mois', aujourd_hui.month))
        annee = int(request.args.get('annee', aujourd_hui.year))
        if not (1 <= mois <= 12) or annee < 2020:
            abort(400)
    except (ValueError, TypeError):
        abort(400)

    debut = date(annee, mois, 1)
    fin   = date(annee, mois + 1, 1) if mois < 12 else date(annee + 1, 1, 1)

    equipes = Equipe.query.filter(
        Equipe.date >= debut, Equipe.date < fin
    ).order_by(Equipe.date.asc()).all()

    contenu = generer_rapport_excel(equipes, mois, annee)

    noms_mois = ['', 'Janv', 'Fevr', 'Mars', 'Avri', 'Mai', 'Juin',
                 'Juil', 'Aout', 'Sept', 'Octo', 'Nove', 'Dece']
    nom_fichier = f"CUF_Chaine4_{noms_mois[mois]}{annee}.xlsx"

    return send_file(
        io.BytesIO(contenu),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=nom_fichier
    )

"""
Routes des tableaux de bord.
- Vue Chef Scierie : analyse opérationnelle (TRS, Pareto, volumes)
- Vue PDG         : synthèse financière (FCFA, objectifs, traffic light)
- Export Excel    : rapport mensuel téléchargeable
"""
from collections import defaultdict
import statistics
from flask import Blueprint, render_template, request, send_file, abort
from flask_login import login_required, current_user
from datetime import date, timedelta
import io
from ..models import db, Equipe, Parametre
from ..services.trs import (
    pareto_arrets, couleur_trs,
    calcule_pertes_equipe, calcule_pertes_fcfa, decompose_dpq,
    calcule_manque_gagner, manque_a_gagner_agrege,
)
from ..services.export import generer_rapport_excel
from ..services.controles_saisie import compte_anomalies_periode
from ..services.cumuls import vue_executive_pdg
from ..services.recommandations import top_n_recommandations
from ..utils import roles_required
from config import Config

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

NOMS_MOIS = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
             'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']


def _format_duree(minutes):
    if not minutes:
        return '—'
    h, m = divmod(minutes, 60)
    if h == 0:
        return f"{m}min"
    if m == 0:
        return f"{h}h00"
    return f"{h}h{m:02d}"


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


_STATUTS_ANALYSES = ('soumis', 'verrouille')

_LABELS_JOURS_FR = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']


def _alertes_chef(aujourd_hui):
    """P7 — Calcule les alertes du Chef : saisies manquantes (7j) + brouillons oubliés (>2j)."""
    # P7-A1 — Saisies manquantes sur les 7 derniers jours ouvrés (lun-sam)
    debut_check = aujourd_hui - timedelta(days=7)
    postes_attendus = []
    j = debut_check
    while j < aujourd_hui:
        if j.weekday() < 6:  # 0=lun ... 5=sam ; 6=dim exclu
            for shift in ('Matin', 'Apres-midi'):
                postes_attendus.append((j, shift))
        j += timedelta(days=1)

    postes_existants = {
        (e.date, e.numero_equipe)
        for e in Equipe.query.filter(
            Equipe.date >= debut_check,
            Equipe.date < aujourd_hui
        ).all()
    }

    saisies_manquantes = [
        {
            'date':     d,
            'shift':    s,
            'date_iso': d.isoformat(),
            'date_fmt': f"{_LABELS_JOURS_FR[d.weekday()]} {d.strftime('%d/%m')}",
        }
        for (d, s) in postes_attendus
        if (d, s) not in postes_existants
    ]

    # P7-A2 — Brouillons oubliés (créés il y a plus de 2 jours par l'utilisateur courant)
    seuil_brouillon = aujourd_hui - timedelta(days=2)
    brouillons_oublies_q = Equipe.query.filter(
        Equipe.user_id == current_user.id,
        Equipe.statut == 'brouillon',
        Equipe.date <= seuil_brouillon,
    ).order_by(Equipe.date.asc()).all()

    brouillons_oublies = [
        {
            'id':       e.id,
            'date_fmt': f"{_LABELS_JOURS_FR[e.date.weekday()]} {e.date.strftime('%d/%m')}",
            'shift':    e.numero_equipe,
            'jours':    (aujourd_hui - e.date).days,
        }
        for e in brouillons_oublies_q
    ]

    return {
        'saisies_manquantes': saisies_manquantes,
        'brouillons_oublies': brouillons_oublies,
    }


def _get_equipes_periode(jours=30):
    depuis = date.today() - timedelta(days=jours)
    return Equipe.query.filter(
        Equipe.date >= depuis,
        Equipe.statut.in_(_STATUTS_ANALYSES)
    ).order_by(Equipe.date.desc()).all()


@dashboard_bp.route('/chef')
@login_required
@roles_required('chef', 'admin')
def vue_chef():
    aujourd_hui = date.today()
    jours = int(request.args.get('jours', 30))

    try:
        mois_sel  = int(request.args.get('mois',  0))
        annee_sel = int(request.args.get('annee', 0))
    except (ValueError, TypeError):
        mois_sel = annee_sel = 0

    if mois_sel and annee_sel and 1 <= mois_sel <= 12 and annee_sel >= 2020:
        debut_m = date(annee_sel, mois_sel, 1)
        fin_m   = date(annee_sel, mois_sel + 1, 1) if mois_sel < 12 else date(annee_sel + 1, 1, 1)
        equipes = Equipe.query.filter(
            Equipe.date >= debut_m, Equipe.date < fin_m,
            Equipe.statut.in_(_STATUTS_ANALYSES)
        ).order_by(Equipe.date.desc()).all()
        label_periode = f"{NOMS_MOIS[mois_sel]} {annee_sel}"
        mode_mois = True
        jours = (fin_m - debut_m).days
    else:
        equipes = _get_equipes_periode(jours)
        label_periode = f"{jours} derniers jours"
        mode_mois = False

    if not equipes:
        return render_template('chef/dashboard.html',
                               postes=[], pareto=[], stats={}, jours=jours,
                               matrice={}, machines=Config.MACHINES,
                               categories=Config.CATEGORIES_ARRET,
                               decomposition=None, scorecard=None,
                               regularite=None, gain_potentiel=None,
                               mode_mois=mode_mois, label_periode=label_periode,
                               mois_options=_mois_disponibles(),
                               alertes=_alertes_chef(aujourd_hui))

    trs_valeurs  = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen    = round(sum(trs_valeurs) / len(trs_valeurs), 1) if trs_valeurs else 0
    total_produit = sum(e.volume_sorti for e in equipes)
    total_declass = round(sum(e.volume_declass for e in equipes), 2)
    total_arrets  = sum(e.duree_totale_arrets for e in equipes)

    # TRS par essence (agrège sur les lignes de production)
    par_essence = {}
    for e in equipes:
        for p in e.productions:
            if p.essence not in par_essence:
                par_essence[p.essence] = {'volumes': [], 'trs': []}
            par_essence[p.essence]['volumes'].append(p.volume_conforme + p.volume_declass)
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
        'total_declass':    total_declass,
        'total_arrets_h':   round(total_arrets / 60, 1),
        'nb_postes':        len(equipes),
        'trs_matin':        trs_moyen_groupe(matin),
        'trs_apres_midi':   trs_moyen_groupe(apres_midi),
        'essence_stats':    essence_stats,
    }

    # F4 — Score de régularité (CV du TRS)
    trs_valides = [e.trs_global for e in equipes
                   if e.trs_global is not None and e.trs_global > 0]
    if len(trs_valides) >= 10:
        moyenne    = statistics.mean(trs_valides)
        ecart_type = statistics.stdev(trs_valides)  # n-1, écart-type échantillon
        cv = (ecart_type / moyenne) * 100 if moyenne > 0 else 0

        # SEUILS PROVISOIRES — recalibrer après 60 jours données CUF réelles
        if cv < 10:
            label_reg, couleur_reg = 'régulier', 'success'
        elif cv < 25:
            label_reg, couleur_reg = 'variable', 'warning'
        else:
            label_reg, couleur_reg = 'instable', 'danger'

        essences_dures = {'Azobé', 'Iroko'}
        a_essence_dure = any(
            p.essence in essences_dures
            for e in equipes
            for p in e.productions
        )

        regularite = {
            'cv':           round(cv, 1),
            'n':            len(trs_valides),
            'label':        label_reg,
            'couleur':      couleur_reg,
            'essence_note': a_essence_dure,
        }
    else:
        regularite = None

    trs_par_date = {}
    for e in sorted(equipes, key=lambda x: x.date):
        d = e.date.isoformat()
        if d not in trs_par_date:
            trs_par_date[d] = []
        if e.trs_global:
            trs_par_date[d].append(e.trs_global)

    chart_labels = list(trs_par_date.keys())
    chart_trs    = [round(sum(v) / len(v), 1) if v else 0 for v in trs_par_date.values()]

    # Décomposition cascade D × P × Q en m³ perdus (F1)
    duree_poste   = float(Parametre.get('duree_poste', 480))
    capacite_h    = float(Parametre.get('capacite_equipe_h', 1.5625))
    cap_par_poste = capacite_h * (duree_poste / 60)  # m³ produits si TRS=100%

    cap_total_m3 = cap_par_poste * len(equipes)
    perte_d_m3   = 0.0
    perte_p_m3   = 0.0
    perte_q_m3   = 0.0
    for e in equipes:
        d, p, q = decompose_dpq(e)
        perte_d_m3 += (1 - d)         * cap_par_poste
        perte_p_m3 += d * (1 - p)     * cap_par_poste
        perte_q_m3 += d * p * (1 - q) * cap_par_poste

    vol_produit = max(0.0, cap_total_m3 - perte_d_m3 - perte_p_m3 - perte_q_m3)

    def _pct(part):
        return round(part / cap_total_m3 * 100, 1) if cap_total_m3 > 0 else 0

    decomposition = {
        'cap_total':    round(cap_total_m3, 1),
        'vol_produit':  round(vol_produit, 1),
        'perte_d':      round(perte_d_m3, 1),
        'perte_p':      round(perte_p_m3, 1),
        'perte_q':      round(perte_q_m3, 1),
        'perte_total':  round(perte_d_m3 + perte_p_m3 + perte_q_m3, 1),
        'pct_produit':  _pct(vol_produit),
        'pct_d':        _pct(perte_d_m3),
        'pct_p':        _pct(perte_p_m3),
        'pct_q':        _pct(perte_q_m3),
    }

    # F3 — Calculateur potentiel gain FCFA
    from ..services.trs import _prix_production
    total_vol_prod = 0.0
    total_val_prod = 0.0
    for e in equipes:
        for p in e.productions:
            vol = p.volume_conforme + p.volume_declass
            total_vol_prod += vol
            total_val_prod += vol * _prix_production(p)

    prix_moyen_fcfa = round(total_val_prod / total_vol_prod) if total_vol_prod > 0 else 0

    gain_potentiel = {
        'cap_total':  round(cap_total_m3, 1),
        'vol_actuel': round(vol_produit, 1),
        'trs_actuel': stats['trs_moyen'],
        'prix_moyen': prix_moyen_fcfa,
    }

    # Scorecard semaine courante (lun-sam) — F5
    lundi    = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    samedi   = lundi + timedelta(days=5)
    equipes_semaine = Equipe.query.filter(
        Equipe.date >= lundi, Equipe.date <= samedi
    ).all()
    index_eq = {(e.date, e.numero_equipe): e for e in equipes_semaine}

    LABELS_JOURS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam']
    SHIFTS = ['Matin', 'Apres-midi']

    scorecard_days = []
    for i in range(6):
        jour = lundi + timedelta(days=i)
        cellules = {}
        for shift in SHIFTS:
            eq = index_eq.get((jour, shift))
            if eq is None:
                cellules[shift] = {'state': 'absent', 'display': '—', 'couleur': 'secondary'}
            elif eq.statut == 'brouillon':
                cellules[shift] = {'state': 'brouillon', 'display': '⏳', 'couleur': 'warning'}
            else:
                trs = eq.trs_global or 0
                if trs >= 70:
                    coul = 'success'
                elif trs >= 50:
                    coul = 'warning'
                else:
                    coul = 'danger'
                cellules[shift] = {
                    'state':   'submitted',
                    'display': f"{trs:.0f}%",
                    'couleur': coul,
                }
        scorecard_days.append({
            'label_court':   LABELS_JOURS[i],
            'label_complet': jour.strftime('%d/%m'),
            'is_today':      (jour == aujourd_hui),
            'shifts':        cellules,
        })

    scorecard = {
        'week_label': f"Semaine du {lundi.strftime('%d/%m')} au {samedi.strftime('%d/%m')}",
        'days':       scorecard_days,
        'shifts':     SHIFTS,
    }

    # Matrice criticité arrêts : machine × catégorie
    matrice_raw = defaultdict(lambda: {'duree': 0, 'count': 0})
    for e in equipes:
        for arret in e.arrets:
            if arret.duree_min:
                cle = (arret.machine, arret.categorie)
                matrice_raw[cle]['duree'] += arret.duree_min
                matrice_raw[cle]['count'] += 1

    matrice = {}
    for m in Config.MACHINES:
        matrice[m] = {}
        for c in Config.CATEGORIES_ARRET:
            data = matrice_raw.get((m, c), {'duree': 0, 'count': 0})
            duree = data['duree']
            if duree == 0:
                couleur_cell = ''
            elif duree > 120:
                couleur_cell = 'table-danger'
            elif duree >= 30:
                couleur_cell = 'table-warning'
            else:
                couleur_cell = 'table-success'
            matrice[m][c] = {
                'duree': duree,
                'duree_fmt': _format_duree(duree),
                'count': data['count'],
                'couleur': couleur_cell,
            }

    alertes = _alertes_chef(aujourd_hui)

    # P11 — Manque à gagner estimé agrégé sur la période (CA potentiel − CA valorisé)
    manque_periode = manque_a_gagner_agrege(equipes)

    # P12 — Compteur d'anomalies de saisie sur la période
    anomalies_periode = compte_anomalies_periode(equipes)

    # P14 — Top 3 recommandations pour le chef (30 derniers jours)
    top_recos = top_n_recommandations(equipes, role='chef', n=3)

    return render_template('chef/dashboard.html',
                           postes=equipes[:10],
                           stats=stats,
                           jours=jours,
                           chart_labels=chart_labels,
                           chart_trs=chart_trs,
                           mois_options=_mois_disponibles(),
                           mode_mois=mode_mois,
                           label_periode=label_periode,
                           matrice=matrice,
                           machines=Config.MACHINES,
                           categories=Config.CATEGORIES_ARRET,
                           decomposition=decomposition,
                           scorecard=scorecard,
                           regularite=regularite,
                           gain_potentiel=gain_potentiel,
                           manque_periode=manque_periode,
                           anomalies_periode=anomalies_periode,
                           top_recos=top_recos,
                           alertes=alertes)


@dashboard_bp.route('/pdg')
@login_required
@roles_required('pdg', 'admin')
def vue_pdg():
    from ..services.trs import _prix_production as _prix

    aujourd_hui = date.today()

    # ── Filtre : mois complet OU période libre ────────────────────────────
    date_debut_s = request.args.get('date_debut', '').strip()
    date_fin_s   = request.args.get('date_fin',   '').strip()
    mode_libre   = False

    if date_debut_s and date_fin_s:
        try:
            debut      = date.fromisoformat(date_debut_s)
            fin        = date.fromisoformat(date_fin_s) + timedelta(days=1)
            mode_libre = True
        except ValueError:
            pass

    if not mode_libre:
        try:
            mois  = int(request.args.get('mois',  aujourd_hui.month))
            annee = int(request.args.get('annee', aujourd_hui.year))
            if not (1 <= mois <= 12) or annee < 2020:
                mois, annee = aujourd_hui.month, aujourd_hui.year
        except (ValueError, TypeError):
            mois, annee = aujourd_hui.month, aujourd_hui.year
        debut = date(annee, mois, 1)
        fin   = date(annee, mois + 1, 1) if mois < 12 else date(annee + 1, 1, 1)
    else:
        mois  = debut.month
        annee = debut.year

    # ── Équipes de la période ─────────────────────────────────────────────
    equipes_mois = Equipe.query.filter(
        Equipe.date >= debut, Equipe.date < fin,
        Equipe.statut.in_(_STATUTS_ANALYSES)
    ).all()

    nb_brouillons = Equipe.query.filter(
        Equipe.date >= debut, Equipe.date < fin,
        Equipe.statut == 'brouillon'
    ).count()

    prix_manquants = any(
        (p.volume_conforme + p.volume_declass) > 0 and _prix(p) == 0
        for e in equipes_mois for p in e.productions
    )

    # ── KPIs ──────────────────────────────────────────────────────────────
    objectif          = float(Parametre.get('objectif_m3', 12.5))
    nb_postes         = len(equipes_mois)
    production_reelle = sum(e.volume_sorti for e in equipes_mois)
    production_cible  = objectif * nb_postes

    trs_vals  = [e.trs_global for e in equipes_mois if e.trs_global is not None]
    trs_moyen = round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else 0
    perte_totale = sum(calcule_pertes_fcfa(e) for e in equipes_mois)

    # P11 — Manque à gagner estimé sur la période (indicateur principal P11)
    manque_periode = manque_a_gagner_agrege(equipes_mois)

    # Delta TRS vs même durée précédente
    duree      = (fin - debut).days
    debut_prec = debut - timedelta(days=duree)
    equipes_prec = Equipe.query.filter(
        Equipe.date >= debut_prec, Equipe.date < debut,
        Equipe.statut.in_(_STATUTS_ANALYSES)
    ).all()
    vals_prec = [e.trs_global for e in equipes_prec if e.trs_global is not None]
    trs_prec  = round(sum(vals_prec) / len(vals_prec), 1) if vals_prec else None
    delta_trs = round(trs_moyen - trs_prec, 1) if trs_prec is not None else None

    # ── Rendement matière par essence ─────────────────────────────────────
    ess_entree = defaultdict(float)
    ess_sorti  = defaultdict(float)
    for e in equipes_mois:
        for p in e.productions:
            ess_entree[p.essence] += p.volume_entree
            ess_sorti[p.essence]  += p.volume_conforme + p.volume_declass

    total_entree     = sum(ess_entree.values())
    rendement_global = round(sum(ess_sorti.values()) / total_entree * 100, 1) if total_entree > 0 else 0

    rendement_par_essence = []
    for ess in sorted(ess_entree):
        r = round(ess_sorti[ess] / ess_entree[ess] * 100, 1) if ess_entree[ess] > 0 else 0
        rendement_par_essence.append({
            'essence':   ess,
            'rendement': r,
            'couleur':   'success' if r >= 60 else ('warning' if r >= 40 else 'danger'),
        })

    # ── Pareto top 5 ─────────────────────────────────────────────────────
    pareto = pareto_arrets(equipes_mois)[:5]

    # ── Tendance TRS 12 derniers mois ─────────────────────────────────────
    tendance = []
    for i in range(11, -1, -1):
        m = aujourd_hui.month - i
        a = aujourd_hui.year
        while m <= 0:
            m += 12
            a -= 1
        d_m = date(a, m, 1)
        f_m = date(a, m + 1, 1) if m < 12 else date(a + 1, 1, 1)
        eq_m = Equipe.query.filter(
            Equipe.date >= d_m, Equipe.date < f_m,
            Equipe.statut.in_(_STATUTS_ANALYSES)
        ).all()
        v = [e.trs_global for e in eq_m if e.trs_global is not None]
        tendance.append({'mois': d_m.strftime('%b %y'), 'trs': round(sum(v) / len(v), 1) if v else 0})

    if mode_libre:
        label_periode = f"Du {debut.strftime('%d/%m/%Y')} au {(fin - timedelta(days=1)).strftime('%d/%m/%Y')}"
    else:
        label_periode = f"{NOMS_MOIS[mois]} {annee}"

    # P13 — Vue exécutive 4 horizons (jour / sem / mois / an) avec deltas
    vue_executive = vue_executive_pdg(aujourd_hui)

    # P14 — Top 3 recommandations pour le PDG (30 derniers jours)
    equipes_30j = Equipe.query.filter(
        Equipe.date >= aujourd_hui - timedelta(days=30),
        Equipe.statut.in_(_STATUTS_ANALYSES)
    ).all()
    top_recos_pdg = top_n_recommandations(equipes_30j, role='pdg', n=3)

    return render_template('pdg/dashboard.html',
                           trs_moyen=trs_moyen,
                           couleur_trs=couleur_trs(trs_moyen),
                           delta_trs=delta_trs,
                           production_reelle=round(production_reelle, 1),
                           production_cible=round(production_cible, 1),
                           perte_fcfa=int(perte_totale),
                           manque_periode=manque_periode,
                           nb_postes=nb_postes,
                           pareto=pareto,
                           tendance=tendance,
                           mois_courant=label_periode,
                           mois_options=_mois_disponibles(),
                           rendement_global=rendement_global,
                           rendement_par_essence=rendement_par_essence,
                           nb_brouillons=nb_brouillons,
                           prix_manquants=prix_manquants,
                           mode_libre=mode_libre,
                           debut_filtre=debut.isoformat(),
                           fin_filtre=(fin - timedelta(days=1)).isoformat(),
                           vue_executive=vue_executive,
                           top_recos_pdg=top_recos_pdg)


@dashboard_bp.route('/pertes')
@login_required
@roles_required('chef', 'admin')
def pertes():
    """Analyse mensuelle des pertes financières D/P/Q avec drill-down."""
    from ..services.trs import _prix_production

    aujourd_hui = date.today()
    try:
        mois  = int(request.args.get('mois',  aujourd_hui.month))
        annee = int(request.args.get('annee', aujourd_hui.year))
        if not (1 <= mois <= 12) or annee < 2020:
            mois, annee = aujourd_hui.month, aujourd_hui.year
    except (ValueError, TypeError):
        mois, annee = aujourd_hui.month, aujourd_hui.year

    debut = date(annee, mois, 1)
    fin   = date(annee, mois + 1, 1) if mois < 12 else date(annee + 1, 1, 1)

    equipes = Equipe.query.filter(
        Equipe.date >= debut, Equipe.date < fin,
        Equipe.statut.in_(_STATUTS_ANALYSES)
    ).order_by(Equipe.date.asc()).all()

    total_d = total_p = total_q = 0.0
    par_machine   = {}
    par_essence_q = {}
    par_shift     = {'Matin': {'perte_p': 0.0, 'nb': 0}, 'Apres-midi': {'perte_p': 0.0, 'nb': 0}}

    capacite_h   = float(Parametre.get('capacite_equipe_h', 1.5625))
    taux_revente = float(Parametre.get('taux_revente_rebut', 0.30))

    for e in equipes:
        pertes_e = calcule_pertes_equipe(e)
        total_d += pertes_e['perte_d']
        total_p += pertes_e['perte_p']
        total_q += pertes_e['perte_q']

        # Perte P ventilée par shift
        shift = e.numero_equipe if e.numero_equipe in par_shift else 'Matin'
        par_shift[shift]['perte_p'] += pertes_e['perte_p']
        par_shift[shift]['nb']      += 1

        # Prix moyen pondéré pour attribution Perte D par machine
        vol_total = e.volume_sorti
        if vol_total > 0 and e.productions:
            prix_moyen = sum(
                _prix_production(pr) * (pr.volume_conforme + pr.volume_declass)
                for pr in e.productions
            ) / vol_total
        else:
            prix_moyen = 0.0

        for a in e.arrets:
            if not a.duree_min or a.categorie == 'Maintenance planifiée':
                continue
            perte_arret = (a.duree_min / 60) * capacite_h * prix_moyen
            m = a.machine
            if m not in par_machine:
                par_machine[m] = {'perte': 0.0, 'duree': 0, 'count': 0, 'arrets': []}
            par_machine[m]['perte'] += perte_arret
            par_machine[m]['duree'] += a.duree_min
            par_machine[m]['count'] += 1
            par_machine[m]['arrets'].append({
                'date':        e.date.strftime('%d/%m/%Y'),
                'equipe':      e.numero_equipe,
                'cause':       a.cause,
                'categorie':   a.categorie,
                'duree':       a.duree_min,
                'perte':       int(perte_arret),
            })

        # Perte Q par essence (déclassé + déchets séparés)
        for pr in e.productions:
            pq_d  = pr.volume_declass  * _prix_production(pr) * (1 - taux_revente)
            pq_ch = pr.volume_dechets  * _prix_production(pr)
            ess   = pr.essence
            if ess not in par_essence_q:
                par_essence_q[ess] = {
                    'perte': 0.0, 'perte_declass': 0.0, 'perte_dechets': 0.0,
                    'volume_declass': 0.0, 'volume_dechets': 0.0,
                }
            par_essence_q[ess]['perte']          += pq_d + pq_ch
            par_essence_q[ess]['perte_declass']  += pq_d
            par_essence_q[ess]['perte_dechets']  += pq_ch
            par_essence_q[ess]['volume_declass'] += pr.volume_declass
            par_essence_q[ess]['volume_dechets'] += pr.volume_dechets

    pareto         = pareto_arrets(equipes)
    machines_tri   = sorted(par_machine.items(),   key=lambda x: x[1]['perte'], reverse=True)
    essences_tri   = sorted(par_essence_q.items(), key=lambda x: x[1]['perte'], reverse=True)
    total_global   = total_d + total_p + total_q

    # Arrondir pour affichage
    for _, data in par_machine.items():
        data['perte'] = int(data['perte'])
    for _, data in par_essence_q.items():
        data['perte']         = int(data['perte'])
        data['perte_declass'] = int(data['perte_declass'])
        data['perte_dechets'] = int(data['perte_dechets'])

    # P11 — Manque à gagner estimé sur la période (indicateur principal,
    # D/P/Q deviennent les causes probables affichées en second plan)
    manque_periode = manque_a_gagner_agrege(equipes)

    return render_template('dashboard/pertes.html',
                           mois=mois, annee=annee,
                           nom_mois=NOMS_MOIS[mois],
                           mois_options=_mois_disponibles(),
                           total_d=int(total_d),
                           total_p=int(total_p),
                           total_q=int(total_q),
                           total_global=int(total_global),
                           manque_periode=manque_periode,
                           machines=machines_tri,
                           essences=essences_tri,
                           par_shift=par_shift,
                           pareto=pareto[:10],
                           nb_equipes=len(equipes))


@dashboard_bp.route('/export/excel')
@login_required
@roles_required('chef', 'admin')
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
        Equipe.date >= debut, Equipe.date < fin,
        Equipe.statut.in_(_STATUTS_ANALYSES)
    ).order_by(Equipe.date.asc()).all()

    nb_brouillons = Equipe.query.filter(
        Equipe.date >= debut, Equipe.date < fin,
        Equipe.statut == 'brouillon'
    ).count()

    contenu = generer_rapport_excel(equipes, mois, annee, nb_brouillons)

    noms_mois = ['', 'Janv', 'Fevr', 'Mars', 'Avri', 'Mai', 'Juin',
                 'Juil', 'Aout', 'Sept', 'Octo', 'Nove', 'Dece']
    nom_fichier = f"CUF_Chaine4_{noms_mois[mois]}{annee}.xlsx"

    return send_file(
        io.BytesIO(contenu),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=nom_fichier
    )

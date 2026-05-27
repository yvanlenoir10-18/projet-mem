"""
Routes des tableaux de bord.
- Vue Chef Scierie : analyse opérationnelle (TRS, Pareto, volumes)
- Vue PDG         : synthèse financière (FCFA, objectifs, traffic light)
- Export Excel    : rapport mensuel téléchargeable
"""
from collections import defaultdict
import statistics
from flask import Blueprint, render_template, request, send_file, abort, url_for
from flask_login import login_required
from datetime import date, datetime, timedelta
import io
from ..models import (
    db, User, Equipe, Parametre, STATUT_A_CORRIGER, STATUT_A_VERIFIER,
    STATUT_BROUILLON, STATUT_VALIDE_CHEF, STATUT_VERROUILLE,
    STATUTS_ANALYSES, STATUTS_NON_ANALYSES, Probleme,
)
from ..services.trs import (
    pareto_arrets, couleur_trs,
    calcule_pertes_equipe, calcule_pertes_fcfa, decompose_dpq,
    calcule_manque_gagner, manque_a_gagner_agrege, calcule_trs_par_essence,
)
from ..services.export import generer_rapport_excel
from ..services.controles_saisie import compte_anomalies_periode, detecte_anomalies
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


def _commentaires_validation(equipe):
    commentaires = []
    if equipe.notes and equipe.notes.strip():
        commentaires.append(equipe.notes.strip())
    for arret in equipe.arrets:
        if arret.notes and arret.notes.strip():
            commentaires.append(
                f"{arret.machine} {arret.heure_debut}-{arret.heure_fin} : {arret.notes.strip()}"
            )
    return {
        'nb': len(commentaires),
        'extrait': commentaires[0][:120] if commentaires else '',
    }


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


_STATUTS_ANALYSES = STATUTS_ANALYSES

_LABELS_JOURS_FR = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
_SHIFTS_JOUR = ('Matin', 'Apres-midi')


def _safe_float_param(cle, defaut):
    try:
        return float(Parametre.get(cle, defaut))
    except (TypeError, ValueError):
        return float(defaut)


def _couleur_objectif(pct):
    if pct >= 100:
        return 'success'
    if pct >= 75:
        return 'warning'
    return 'danger'


def _couleur_simple(valeur, seuil_warning, seuil_danger, inverse=False):
    if inverse:
        if valeur > seuil_danger:
            return 'danger'
        if valeur >= seuil_warning:
            return 'warning'
        return 'success'
    if valeur >= seuil_danger:
        return 'success'
    if valeur >= seuil_warning:
        return 'warning'
    return 'danger'


def _poste_actif_maintenant():
    maintenant = datetime.now()
    minute_jour = maintenant.hour * 60 + maintenant.minute
    if 6 * 60 <= minute_jour < 14 * 60:
        return 'Matin', max(1, minute_jour - 6 * 60)
    if 14 * 60 <= minute_jour < 22 * 60:
        return 'Apres-midi', max(1, minute_jour - 14 * 60)
    return None, 0


def _equipes_jour_pilotage(aujourd_hui):
    statuts = tuple(dict.fromkeys((STATUT_A_VERIFIER, *STATUTS_ANALYSES)))
    return Equipe.query.filter(
        Equipe.date == aujourd_hui,
        Equipe.statut.in_(statuts),
    ).order_by(Equipe.numero_equipe.asc(), Equipe.cree_le.desc()).all()


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

    # P7-A2 — Brouillons oubliés (créés il y a plus de 2 jours, tous opérateurs)
    seuil_brouillon = aujourd_hui - timedelta(days=2)
    brouillons_oublies_q = Equipe.query.filter(
        Equipe.statut == STATUT_BROUILLON,
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

    fiches_a_verifier = []
    for e in Equipe.query.filter(
        Equipe.statut == STATUT_A_VERIFIER
    ).order_by(Equipe.date.desc(), Equipe.cree_le.desc()).limit(20).all():
        anomalies = detecte_anomalies(e)
        commentaires = _commentaires_validation(e)
        fiches_a_verifier.append({
            'id':       e.id,
            'date_fmt': f"{_LABELS_JOURS_FR[e.date.weekday()]} {e.date.strftime('%d/%m')}",
            'shift':    e.numero_equipe,
            'operateur': e.operateur_nom or e.saisie_par.nom,
            'nb_commentaires': commentaires['nb'],
            'commentaire_extrait': commentaires['extrait'],
            'nb_anomalies': len(anomalies),
            'codes_anomalies': ', '.join(a.get('code', '?') for a in anomalies[:3]),
            'priorite': len(anomalies) * 2 + commentaires['nb'],
        })
    fiches_a_verifier.sort(key=lambda f: f['priorite'], reverse=True)
    fiches_a_verifier = fiches_a_verifier[:8]

    return {
        'saisies_manquantes': saisies_manquantes,
        'brouillons_oublies': brouillons_oublies,
        'fiches_a_verifier': fiches_a_verifier,
    }


def _kpi_aujourdhui(aujourd_hui):
    equipes_jour = _equipes_jour_pilotage(aujourd_hui)
    objectif_poste = _safe_float_param('objectif_m3', 12.5)
    objectif_jour = objectif_poste * 2

    volume_conforme = sum(e.volume_conforme for e in equipes_jour)
    volume_declass = sum(e.volume_declass for e in equipes_jour)
    volume_entree = sum(e.volume_entree for e in equipes_jour)
    volume_sorti = volume_conforme + volume_declass

    pct_objectif = round((volume_conforme / objectif_jour) * 100, 1) if objectif_jour else 0
    ecart_m3 = round(volume_conforme - objectif_jour, 2)
    ecart_pct = round(((volume_conforme - objectif_jour) / objectif_jour) * 100, 1) if objectif_jour else 0

    fiches_attente = Equipe.query.filter(Equipe.statut == STATUT_A_VERIFIER).all()
    fiches_critiques = sum(
        1 for fiche in fiches_attente
        if any(a.get('niveau') == 'danger' for a in detecte_anomalies(fiche))
    )

    machine_stats = defaultdict(int)
    for equipe in equipes_jour:
        for arret in equipe.arrets:
            machine_stats[arret.machine] += arret.duree_min or 0
    machine_impact = None
    if machine_stats:
        machine, duree = max(machine_stats.items(), key=lambda item: item[1])
        machine_impact = {'nom': machine, 'duree': duree, 'duree_fmt': _format_duree(duree)}

    total_arrets = sum(e.duree_totale_arrets for e in equipes_jour)
    rendement = round((volume_sorti / volume_entree) * 100, 1) if volume_entree else 0
    seuil_rendement = _safe_float_param('seuil_rendement_min', 65)

    depuis_7j = aujourd_hui - timedelta(days=7)
    equipes_7j = Equipe.query.filter(
        Equipe.date >= depuis_7j,
        Equipe.date < aujourd_hui,
        Equipe.statut.in_(STATUTS_ANALYSES),
    ).all()
    entree_7j = sum(e.volume_entree for e in equipes_7j)
    sorti_7j = sum(e.volume_sorti for e in equipes_7j)
    rendement_7j = round((sorti_7j / entree_7j) * 100, 1) if entree_7j else None

    seuil_declass = _safe_float_param('seuil_declass_pct', 30)
    declass_pct = round((volume_declass / volume_sorti) * 100, 1) if volume_sorti else 0
    if declass_pct > seuil_declass:
        couleur_declass = 'danger'
    elif declass_pct >= seuil_declass * 0.8:
        couleur_declass = 'warning'
    else:
        couleur_declass = 'success'

    trs_vals = [e.trs_global for e in equipes_jour if e.trs_global is not None]
    trs_jour = round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else None

    shift_actif, minutes_ecoulees = _poste_actif_maintenant()
    projection = None
    if shift_actif:
        fiches_actives = Equipe.query.filter(
            Equipe.date == aujourd_hui,
            Equipe.numero_equipe == shift_actif,
            Equipe.statut.in_((STATUT_BROUILLON, STATUT_A_VERIFIER)),
        ).all()
        volume_actif = sum(e.volume_conforme for e in fiches_actives)
        if volume_actif > 0 and minutes_ecoulees > 0:
            projection = {
                'shift': shift_actif,
                'volume': round(volume_actif * (480 / minutes_ecoulees), 1),
                'minutes_ecoulees': minutes_ecoulees,
            }

    volume_attente = sum(e.volume_conforme for e in equipes_jour if e.statut == STATUT_A_VERIFIER)

    return {
        'objectif': {
            'realise': round(volume_conforme, 2),
            'objectif': round(objectif_jour, 2),
            'pct': pct_objectif,
            'pct_barre': min(100, pct_objectif),
            'ecart_m3': ecart_m3,
            'ecart_pct': ecart_pct,
            'couleur': _couleur_objectif(pct_objectif),
            'projection': projection,
            'volume_attente': round(volume_attente, 2),
        },
        'fiches': {
            'attente': len(fiches_attente),
            'critiques': fiches_critiques,
            'couleur': 'danger' if fiches_critiques else ('warning' if fiches_attente else 'success'),
        },
        'arrets': {
            'minutes': total_arrets,
            'duree_fmt': _format_duree(total_arrets),
            'machine_impact': machine_impact,
            'couleur': _couleur_simple(total_arrets, 60, 120, inverse=True),
        },
        'rendement': {
            'valeur': rendement,
            'seuil': seuil_rendement,
            'moyenne_7j': rendement_7j,
            'couleur': _couleur_simple(rendement, seuil_rendement * 0.9, seuil_rendement),
        },
        'declass': {
            'valeur': declass_pct,
            'seuil': seuil_declass,
            'couleur': couleur_declass,
        },
        'trs': {
            'valeur': trs_jour,
            'couleur': couleur_trs(trs_jour or 0),
        },
    }


def _postes_du_jour(aujourd_hui):
    equipes = Equipe.query.filter(
        Equipe.date == aujourd_hui
    ).order_by(Equipe.cree_le.desc()).all()
    par_shift = defaultdict(list)
    for equipe in equipes:
        par_shift[equipe.numero_equipe].append(equipe)

    labels_statut = {
        STATUT_BROUILLON: ('Brouillon', 'warning'),
        STATUT_A_VERIFIER: ('Chez le chef', 'info'),
        STATUT_A_CORRIGER: ('À corriger', 'warning'),
        STATUT_VALIDE_CHEF: ('Validée chef', 'success'),
        STATUT_VERROUILLE: ('Clôturée', 'secondary'),
    }

    postes = []
    for shift in _SHIFTS_JOUR:
        equipe = par_shift.get(shift, [None])[0]
        if equipe is None:
            postes.append({
                'shift': shift,
                'existe': False,
                'statut_label': 'Non saisi',
                'statut_couleur': 'secondary',
                'href': url_for('saisie.historique'),
            })
            continue

        statut_label, statut_couleur = labels_statut.get(equipe.statut, (equipe.statut, 'secondary'))
        rendement = round((equipe.volume_sorti / equipe.volume_entree) * 100, 1) if equipe.volume_entree else 0
        postes.append({
            'shift': shift,
            'existe': True,
            'id': equipe.id,
            'statut_label': statut_label,
            'statut_couleur': statut_couleur,
            'operateur': equipe.operateur_nom or (equipe.saisie_par.nom if equipe.saisie_par else 'Non renseigné'),
            'essences': equipe.essences_label or 'Aucune essence',
            'volume': round(equipe.volume_conforme, 2),
            'arrets': _format_duree(equipe.duree_totale_arrets),
            'rendement': rendement,
            'trs': equipe.trs_global,
            'href': url_for('saisie.detail_poste', poste_id=equipe.id),
            'nb_supplementaires': max(0, len(par_shift.get(shift, [])) - 1),
        })
    return postes


def _actions_immediates(aujourd_hui, alertes):
    actions = []

    fiches = list(alertes.get('fiches_a_verifier', [])) if alertes else []
    for fiche in fiches[:5]:
        niveau = 'danger' if fiche.get('nb_anomalies', 0) else 'warning'
        detail = f"{fiche['date_fmt']} · {fiche['shift']} · {fiche['operateur']}"
        if fiche.get('nb_anomalies', 0):
            detail += f" · {fiche['nb_anomalies']} alerte(s)"
        actions.append({
            'niveau': niveau,
            'icon': 'bi-shield-exclamation' if niveau == 'danger' else 'bi-clipboard-check',
            'titre': 'Fiche à contrôler',
            'detail': detail,
            'href': url_for('saisie.detail_poste', poste_id=fiche['id']),
            'cta': 'Ouvrir',
            'priorite': 100 if niveau == 'danger' else 80,
        })

    corrections = Equipe.query.filter(Equipe.statut == STATUT_A_CORRIGER).count()
    if corrections:
        actions.append({
            'niveau': 'info',
            'icon': 'bi-arrow-return-left',
            'titre': 'Fiches renvoyées en correction',
            'detail': f"{corrections} fiche(s) attendent un retour opérateur.",
            'href': url_for('dashboard.fiches_chef', statut=STATUT_A_CORRIGER),
            'cta': 'Suivre',
            'priorite': 50,
        })

    manquants = list(alertes.get('saisies_manquantes', [])) if alertes else []
    if manquants:
        actions.append({
            'niveau': 'warning',
            'icon': 'bi-calendar-x',
            'titre': 'Postes non saisis',
            'detail': f"{len(manquants)} poste(s) manquant(s) sur les 7 derniers jours.",
            'href': url_for('dashboard.fiches_chef', statut='tous'),
            'cta': 'Voir',
            'priorite': 60,
        })

    brouillons = list(alertes.get('brouillons_oublies', [])) if alertes else []
    if brouillons:
        actions.append({
            'niveau': 'info',
            'icon': 'bi-hourglass-split',
            'titre': 'Brouillons anciens',
            'detail': f"{len(brouillons)} brouillon(s) ont plus de 2 jours.",
            'href': url_for('dashboard.fiches_chef', statut=STATUT_BROUILLON),
            'cta': 'Suivre',
            'priorite': 40,
        })

    actions.sort(key=lambda item: item['priorite'], reverse=True)
    return actions[:8]


def _statut_fiche_chef(statut):
    labels = {
        STATUT_BROUILLON: ('Brouillon', 'warning'),
        STATUT_A_VERIFIER: ('Chez le chef', 'info'),
        STATUT_A_CORRIGER: ('À corriger', 'warning'),
        STATUT_VALIDE_CHEF: ('Validée', 'success'),
        STATUT_VERROUILLE: ('Clôturée', 'secondary'),
    }
    return labels.get(statut, (statut or 'Inconnu', 'secondary'))


def _periode_fiches_chef(periode):
    aujourd_hui = date.today()
    if periode == 'aujourd_hui':
        return aujourd_hui, aujourd_hui, "Aujourd'hui"
    if periode == 'semaine':
        return aujourd_hui - timedelta(days=aujourd_hui.weekday()), aujourd_hui, "Cette semaine"
    if periode == 'mois':
        return date(aujourd_hui.year, aujourd_hui.month, 1), aujourd_hui, "Ce mois"
    if periode == 'tout':
        return None, None, "Toutes les dates"
    return aujourd_hui - timedelta(days=30), aujourd_hui, "30 derniers jours"


def _action_fiche_chef(equipe):
    if equipe.statut == STATUT_A_VERIFIER:
        return {'label': 'Contrôler', 'couleur': 'primary'}
    if equipe.statut == STATUT_A_CORRIGER:
        return {'label': 'Suivre', 'couleur': 'warning'}
    if equipe.statut == STATUT_BROUILLON:
        return {'label': 'Voir brouillon', 'couleur': 'secondary'}
    return {'label': 'Voir', 'couleur': 'outline-secondary'}


def _fiches_chef_query(filtres):
    query = Equipe.query

    debut, fin, label = _periode_fiches_chef(filtres['periode'])
    if debut:
        query = query.filter(Equipe.date >= debut)
    if fin:
        query = query.filter(Equipe.date <= fin)

    statut = filtres['statut']
    if statut == 'validees':
        query = query.filter(Equipe.statut.in_((STATUT_VALIDE_CHEF, STATUT_VERROUILLE)))
    elif statut in (STATUT_BROUILLON, STATUT_A_VERIFIER, STATUT_A_CORRIGER, STATUT_VALIDE_CHEF, STATUT_VERROUILLE):
        query = query.filter(Equipe.statut == statut)

    if filtres['equipe'] in ('Matin', 'Apres-midi'):
        query = query.filter(Equipe.numero_equipe == filtres['equipe'])

    if filtres['operateur_id']:
        query = query.filter(Equipe.user_id == filtres['operateur_id'])

    return query.order_by(Equipe.date.desc(), Equipe.cree_le.desc()).all(), label


def _ligne_fiche_chef(equipe):
    anomalies = detecte_anomalies(equipe)
    nb_bloquantes = sum(1 for a in anomalies if a.get('niveau') == 'danger')
    nb_warnings = sum(1 for a in anomalies if a.get('niveau') == 'warning')
    statut_label, statut_couleur = _statut_fiche_chef(equipe.statut)
    action = _action_fiche_chef(equipe)

    return {
        'id': equipe.id,
        'date': equipe.date,
        'date_fmt': equipe.date.strftime('%d/%m/%Y') if equipe.date else '—',
        'equipe': equipe.numero_equipe,
        'operateur': equipe.operateur_nom or (equipe.saisie_par.nom if equipe.saisie_par else 'Non renseigné'),
        'rempli_par': equipe.rempli_par_nom or (equipe.saisie_par.nom if equipe.saisie_par else 'Non renseigné'),
        'essences': equipe.essences_label or '—',
        'volume': round(equipe.volume_conforme, 2),
        'volume_sorti': round(equipe.volume_sorti, 2),
        'trs': equipe.trs_global,
        'arrets_min': equipe.duree_totale_arrets,
        'arrets_fmt': _format_duree(equipe.duree_totale_arrets),
        'statut': equipe.statut,
        'statut_label': statut_label,
        'statut_couleur': statut_couleur,
        'nb_anomalies': len(anomalies),
        'nb_bloquantes': nb_bloquantes,
        'nb_warnings': nb_warnings,
        'premiere_anomalie': anomalies[0]['titre'] if anomalies else '',
        'action': action,
        'href': url_for('saisie.detail_poste', poste_id=equipe.id),
        'search_blob': ' '.join([
            str(equipe.id),
            equipe.date.isoformat() if equipe.date else '',
            equipe.numero_equipe or '',
            equipe.operateur_nom or '',
            equipe.rempli_par_nom or '',
            equipe.essences_label or '',
            ' '.join(a.machine for a in equipe.arrets),
            ' '.join(a.cause for a in equipe.arrets),
        ]).lower(),
    }


def _filtrer_lignes_fiches(lignes, filtres):
    recherche = filtres['q'].lower()
    niveau = filtres['anomalies']

    if recherche:
        lignes = [l for l in lignes if recherche in l['search_blob']]
    if niveau == 'bloquantes':
        lignes = [l for l in lignes if l['nb_bloquantes'] > 0]
    elif niveau == 'avertissements':
        lignes = [l for l in lignes if l['nb_warnings'] > 0 and l['nb_bloquantes'] == 0]
    elif niveau == 'sans':
        lignes = [l for l in lignes if l['nb_anomalies'] == 0]
    return lignes


def _compteurs_fiches_chef(lignes):
    return {
        'total': len(lignes),
        'a_verifier': sum(1 for l in lignes if l['statut'] == STATUT_A_VERIFIER),
        'a_corriger': sum(1 for l in lignes if l['statut'] == STATUT_A_CORRIGER),
        'brouillons': sum(1 for l in lignes if l['statut'] == STATUT_BROUILLON),
        'validees': sum(1 for l in lignes if l['statut'] in (STATUT_VALIDE_CHEF, STATUT_VERROUILLE)),
        'bloquantes': sum(1 for l in lignes if l['nb_bloquantes'] > 0),
        'warnings': sum(1 for l in lignes if l['nb_warnings'] > 0),
    }


def _periode_depuis_jours(jours):
    try:
        jours = int(jours)
    except (TypeError, ValueError):
        jours = 30
    if jours not in (7, 30, 90, 0):
        jours = 30
    depuis = None if jours == 0 else date.today() - timedelta(days=jours)
    label = 'Toutes les dates' if jours == 0 else f'{jours} derniers jours'
    return jours, depuis, label


def _equipes_machines(jours, mode):
    jours, depuis, label = _periode_depuis_jours(jours)
    statuts = list(STATUTS_ANALYSES)
    if mode == 'temps_reel':
        statuts.append(STATUT_A_VERIFIER)
    query = Equipe.query.filter(Equipe.statut.in_(tuple(statuts)))
    if depuis:
        query = query.filter(Equipe.date >= depuis)
    return query.order_by(Equipe.date.desc()).all(), jours, label


def _ligne_arret_machine(equipe, arret):
    return {
        'poste_id': equipe.id,
        'date': equipe.date,
        'date_fmt': equipe.date.strftime('%d/%m/%Y') if equipe.date else '—',
        'shift': equipe.numero_equipe,
        'machine': arret.machine,
        'heure_debut': arret.heure_debut,
        'heure_fin': arret.heure_fin,
        'duree': arret.duree_min or 0,
        'duree_fmt': _format_duree(arret.duree_min or 0),
        'impact': arret.duree_impact_min,
        'impact_fmt': _format_duree(arret.duree_impact_min),
        'cause': arret.cause,
        'categorie': arret.categorie,
        'notes': (arret.notes or '').strip(),
        'essences': equipe.essences_label,
        'operateur': equipe.operateur_nom or (equipe.saisie_par.nom if equipe.saisie_par else 'Non renseigné'),
        'href': url_for('saisie.detail_poste', poste_id=equipe.id),
    }


def _analyse_machines(equipes, machine_filtre=None):
    machine_stats = {
        machine: {
            'machine': machine,
            'duree': 0,
            'count': 0,
            'impact': 0,
            'causes': defaultdict(lambda: {'duree': 0, 'count': 0}),
            'categories': defaultdict(lambda: {'duree': 0, 'count': 0}),
            'shifts': defaultdict(lambda: {'duree': 0, 'count': 0}),
            'postes': set(),
        }
        for machine in Config.MACHINES
    }
    arrets = []

    for equipe in equipes:
        for arret in equipe.arrets:
            if machine_filtre and arret.machine != machine_filtre:
                continue
            duree = arret.duree_min or 0
            machine = arret.machine or 'Autre'
            if machine not in machine_stats:
                machine_stats[machine] = {
                    'machine': machine,
                    'duree': 0,
                    'count': 0,
                    'impact': 0,
                    'causes': defaultdict(lambda: {'duree': 0, 'count': 0}),
                    'categories': defaultdict(lambda: {'duree': 0, 'count': 0}),
                    'shifts': defaultdict(lambda: {'duree': 0, 'count': 0}),
                    'postes': set(),
                }
            stats = machine_stats[machine]
            stats['duree'] += duree
            stats['count'] += 1
            stats['impact'] += arret.duree_impact_min
            stats['postes'].add(equipe.id)
            stats['causes'][arret.cause]['duree'] += duree
            stats['causes'][arret.cause]['count'] += 1
            stats['categories'][arret.categorie]['duree'] += duree
            stats['categories'][arret.categorie]['count'] += 1
            stats['shifts'][equipe.numero_equipe]['duree'] += duree
            stats['shifts'][equipe.numero_equipe]['count'] += 1
            arrets.append(_ligne_arret_machine(equipe, arret))

    machines = []
    for stats in machine_stats.values():
        causes = sorted(
            [{'nom': nom, **data} for nom, data in stats['causes'].items()],
            key=lambda item: (item['duree'], item['count']),
            reverse=True,
        )
        categories = sorted(
            [{'nom': nom, **data} for nom, data in stats['categories'].items()],
            key=lambda item: (item['duree'], item['count']),
            reverse=True,
        )
        duree = stats['duree']
        count = stats['count']
        if duree > 120 or count >= 5:
            statut, couleur = 'Critique', 'danger'
        elif duree >= 45 or count >= 2:
            statut, couleur = 'Surveiller', 'warning'
        else:
            statut, couleur = 'Normal', 'success'
        machines.append({
            'machine': stats['machine'],
            'duree': duree,
            'duree_fmt': _format_duree(duree),
            'count': count,
            'moyenne': round(duree / count, 1) if count else 0,
            'impact': stats['impact'],
            'impact_fmt': _format_duree(stats['impact']),
            'cause_principale': causes[0] if causes else None,
            'categorie_principale': categories[0] if categories else None,
            'matin': stats['shifts'].get('Matin', {'duree': 0, 'count': 0}),
            'apres_midi': stats['shifts'].get('Apres-midi', {'duree': 0, 'count': 0}),
            'nb_postes': len(stats['postes']),
            'statut': statut,
            'couleur': couleur,
        })

    machines.sort(key=lambda item: (item['duree'], item['count']), reverse=True)
    arrets.sort(key=lambda item: (item['duree'], item['date']), reverse=True)
    arrets_longs = [a for a in arrets if a['duree'] >= 45][:12]
    return machines, arrets, arrets_longs


def _recurrences_machines(arrets):
    recurrences = []
    par_machine = defaultdict(list)
    par_cause = defaultdict(list)
    par_combo = defaultdict(list)
    for arret in arrets:
        par_machine[arret['machine']].append(arret)
        par_cause[arret['cause']].append(arret)
        par_combo[(arret['machine'], arret['cause'])].append(arret)

    for machine, items in par_machine.items():
        if len(items) >= 3:
            recurrences.append({
                'niveau': 'warning' if len(items) < 5 else 'danger',
                'titre': f'{machine} revient souvent',
                'detail': f"{len(items)} arrêt(s), {sum(i['duree'] for i in items)} min cumulées.",
                'href': url_for('dashboard.machines_chef', machine=machine),
            })
    for cause, items in par_cause.items():
        if len(items) >= 3:
            recurrences.append({
                'niveau': 'warning',
                'titre': f'Cause récurrente : {cause}',
                'detail': f"{len(items)} occurrence(s), machines : {', '.join(sorted(set(i['machine'] for i in items)))}.",
                'href': url_for('analyse.arrets', jours=30),
            })
    for (machine, cause), items in par_combo.items():
        if len(items) >= 2 and sum(i['duree'] for i in items) >= 90:
            recurrences.append({
                'niveau': 'danger',
                'titre': f'{machine} · {cause}',
                'detail': f"{len(items)} occurrence(s), {sum(i['duree'] for i in items)} min. Priorité diagnostic.",
                'href': url_for('dashboard.machines_chef', machine=machine),
            })

    recurrences.sort(key=lambda item: 0 if item['niveau'] == 'danger' else 1)
    return recurrences[:8]


def _synthese_machines(machines, arrets):
    total_duree = sum(m['duree'] for m in machines)
    total_count = sum(m['count'] for m in machines)
    machine_top = next((m for m in machines if m['count'] > 0), None)
    return {
        'total_arrets': total_count,
        'total_duree': total_duree,
        'total_duree_fmt': _format_duree(total_duree),
        'machine_top': machine_top,
        'arrets_longs': sum(1 for a in arrets if a['duree'] >= 45),
        'machines_touchees': sum(1 for m in machines if m['count'] > 0),
    }


def _equipes_production(jours, mode):
    jours, depuis, label = _periode_depuis_jours(jours)
    statuts = list(STATUTS_ANALYSES)
    if mode == 'temps_reel':
        statuts.append(STATUT_A_VERIFIER)
    query = Equipe.query.filter(Equipe.statut.in_(tuple(statuts)))
    if depuis:
        query = query.filter(Equipe.date >= depuis)
    return query.order_by(Equipe.date.desc(), Equipe.numero_equipe.asc()).all(), jours, label


def _rendement_matiere(volume_entree, volume_sorti):
    return round((volume_sorti / volume_entree) * 100, 1) if volume_entree else 0


def _couleur_atteinte(pct):
    if pct >= 100:
        return 'success'
    if pct >= 75:
        return 'warning'
    return 'danger'


def _resume_production(equipes):
    objectif_poste = _safe_float_param('objectif_m3', 12.5)
    objectif_jour = objectif_poste * 2

    par_jour = defaultdict(list)
    for equipe in equipes:
        par_jour[equipe.date].append(equipe)

    jours_lignes = []
    for jour, equipes_jour in sorted(par_jour.items(), reverse=True):
        volume = sum(e.volume_conforme for e in equipes_jour)
        volume_sorti = sum(e.volume_sorti for e in equipes_jour)
        volume_entree = sum(e.volume_entree for e in equipes_jour)
        objectif = objectif_jour
        pct = round((volume / objectif) * 100, 1) if objectif else 0
        arrets = sum(e.duree_totale_arrets for e in equipes_jour)
        jours_lignes.append({
            'date': jour,
            'date_iso': jour.isoformat(),
            'date_fmt': jour.strftime('%d/%m/%Y'),
            'label_court': _LABELS_JOURS_FR[jour.weekday()] if jour.weekday() < len(_LABELS_JOURS_FR) else '',
            'nb_postes': len(equipes_jour),
            'volume': round(volume, 2),
            'volume_sorti': round(volume_sorti, 2),
            'objectif': round(objectif, 2),
            'pct': pct,
            'pct_barre': min(100, pct),
            'ecart': round(volume - objectif, 2),
            'couleur': _couleur_atteinte(pct),
            'rendement': _rendement_matiere(volume_entree, volume_sorti),
            'arrets': arrets,
            'arrets_fmt': _format_duree(arrets),
            'href': url_for('dashboard.fiches_chef', statut='tous', periode='tout', q=jour.isoformat()),
            'analyse_url': url_for(
                'problemes.nouveau',
                origine_type='machine',
                origine_label=f'Production sous objectif - {jour.strftime("%d/%m/%Y")}',
                contexte_quoi='Production sous objectif',
                contexte_quand=jour.strftime('%d/%m/%Y'),
                contexte_combien=f'{round(volume, 2)} m³ réalisés sur {round(objectif, 2)} m³ attendus',
                origine_url=url_for('dashboard.production_chef', jours=30),
            ),
        })

    total_volume = sum(j['volume'] for j in jours_lignes)
    total_objectif = sum(j['objectif'] for j in jours_lignes)
    total_sorti = sum(e.volume_sorti for e in equipes)
    total_entree = sum(e.volume_entree for e in equipes)
    total_arrets = sum(e.duree_totale_arrets for e in equipes)
    pct_total = round((total_volume / total_objectif) * 100, 1) if total_objectif else 0

    return {
        'objectif_poste': round(objectif_poste, 2),
        'objectif_jour': round(objectif_jour, 2),
        'volume': round(total_volume, 2),
        'objectif': round(total_objectif, 2),
        'pct': pct_total,
        'pct_barre': min(100, pct_total),
        'ecart': round(total_volume - total_objectif, 2),
        'couleur': _couleur_atteinte(pct_total),
        'rendement': _rendement_matiere(total_entree, total_sorti),
        'arrets': total_arrets,
        'arrets_fmt': _format_duree(total_arrets),
        'nb_postes': len(equipes),
        'nb_jours': len(jours_lignes),
        'jours': jours_lignes,
        'jours_sous_objectif': [j for j in jours_lignes if j['pct'] < 75][:8],
    }


def _comparaison_equipes_production(equipes):
    groupes = []
    for shift in _SHIFTS_JOUR:
        items = [e for e in equipes if e.numero_equipe == shift]
        volume = sum(e.volume_conforme for e in items)
        sortie = sum(e.volume_sorti for e in items)
        entree = sum(e.volume_entree for e in items)
        arrets = sum(e.duree_totale_arrets for e in items)
        trs_vals = [e.trs_global for e in items if e.trs_global is not None]
        objectif = _safe_float_param('objectif_m3', 12.5) * len(items)
        pct = round((volume / objectif) * 100, 1) if objectif else 0
        groupes.append({
            'shift': shift,
            'nb_postes': len(items),
            'volume': round(volume, 2),
            'objectif': round(objectif, 2),
            'pct': pct,
            'couleur': _couleur_atteinte(pct),
            'rendement': _rendement_matiere(entree, sortie),
            'arrets': arrets,
            'arrets_fmt': _format_duree(arrets),
            'trs': round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else None,
        })
    return groupes


def _analyse_essences_production(equipes):
    stats = defaultdict(lambda: {
        'essence': '',
        'entree': 0.0,
        'conforme': 0.0,
        'declass': 0.0,
        'dechets': 0.0,
        'postes': set(),
    })
    for equipe in equipes:
        for prod in equipe.productions:
            essence = prod.essence or 'Non renseignée'
            s = stats[essence]
            s['essence'] = essence
            s['entree'] += prod.volume_entree or 0
            s['conforme'] += prod.volume_conforme or 0
            s['declass'] += prod.volume_declass or 0
            s['dechets'] += prod.volume_dechets or 0
            s['postes'].add(equipe.id)

    lignes = []
    for s in stats.values():
        sortie = s['conforme'] + s['declass']
        declass_pct = round((s['declass'] / sortie) * 100, 1) if sortie else 0
        rendement = _rendement_matiere(s['entree'], sortie)
        if rendement < 55 or declass_pct > _safe_float_param('seuil_declass_pct', 30):
            couleur = 'danger'
        elif rendement < 65:
            couleur = 'warning'
        else:
            couleur = 'success'
        lignes.append({
            'essence': s['essence'],
            'entree': round(s['entree'], 2),
            'conforme': round(s['conforme'], 2),
            'declass': round(s['declass'], 2),
            'dechets': round(s['dechets'], 2),
            'sortie': round(sortie, 2),
            'rendement': rendement,
            'declass_pct': declass_pct,
            'nb_postes': len(s['postes']),
            'couleur': couleur,
            'analyse_url': url_for(
                'problemes.nouveau',
                origine_type='manuel',
                origine_label=f'Essence à surveiller - {s["essence"]}',
                contexte_quoi=f'Rendement ou déclassement à surveiller sur {s["essence"]}',
                contexte_ou=s['essence'],
                contexte_combien=f'Rendement {rendement}% · déclassé {declass_pct}%',
                origine_url=url_for('dashboard.production_chef', jours=30),
            ),
        })
    lignes.sort(key=lambda item: (item['rendement'], -item['declass_pct']))
    return lignes


def _postes_extremes_production(equipes):
    objectif_poste = _safe_float_param('objectif_m3', 12.5)
    lignes = []
    for e in equipes:
        pct = round((e.volume_conforme / objectif_poste) * 100, 1) if objectif_poste else 0
        lignes.append({
            'id': e.id,
            'date': e.date,
            'date_fmt': e.date.strftime('%d/%m/%Y') if e.date else '—',
            'shift': e.numero_equipe,
            'operateur': e.operateur_nom or (e.saisie_par.nom if e.saisie_par else 'Non renseigné'),
            'essences': e.essences_label or '—',
            'volume': round(e.volume_conforme, 2),
            'objectif': round(objectif_poste, 2),
            'pct': pct,
            'couleur': _couleur_atteinte(pct),
            'arrets_fmt': _format_duree(e.duree_totale_arrets),
            'href': url_for('saisie.detail_poste', poste_id=e.id),
            'analyse_url': url_for(
                'problemes.nouveau',
                origine_type='fiche',
                origine_label=f'Poste sous objectif #{e.id}',
                equipe_id=e.id,
                contexte_quoi='Poste sous objectif de production',
                contexte_quand=f'{e.date.strftime("%d/%m/%Y")} · {e.numero_equipe}' if e.date else e.numero_equipe,
                contexte_ou=e.essences_label,
                contexte_combien=f'{round(e.volume_conforme, 2)} m³ sur {round(objectif_poste, 2)} m³',
                origine_url=url_for('saisie.detail_poste', poste_id=e.id),
            ),
        })
    lignes.sort(key=lambda item: item['pct'])
    return {
        'pires': lignes[:8],
        'meilleurs': list(reversed(lignes[-5:])) if lignes else [],
    }


def _projection_production_active():
    shift_actif, minutes_ecoulees = _poste_actif_maintenant()
    if not shift_actif:
        return None
    fiches = Equipe.query.filter(
        Equipe.date == date.today(),
        Equipe.numero_equipe == shift_actif,
        Equipe.statut.in_((STATUT_BROUILLON, STATUT_A_VERIFIER)),
    ).all()
    volume = sum(e.volume_conforme for e in fiches)
    if not fiches or volume <= 0:
        return None
    projection = volume * (480 / max(1, minutes_ecoulees))
    objectif_poste = _safe_float_param('objectif_m3', 12.5)
    pct = round((projection / objectif_poste) * 100, 1) if objectif_poste else 0
    return {
        'shift': shift_actif,
        'minutes_ecoulees': minutes_ecoulees,
        'volume_actuel': round(volume, 2),
        'projection': round(projection, 2),
        'objectif': round(objectif_poste, 2),
        'pct': pct,
        'couleur': _couleur_atteinte(pct),
    }


def _resume_qualite(equipes):
    entree = sum(e.volume_entree for e in equipes)
    conforme = sum(e.volume_conforme for e in equipes)
    declass = sum(e.volume_declass for e in equipes)
    dechets = sum(e.volume_dechets for e in equipes)
    sortie = conforme + declass
    rendement = _rendement_matiere(entree, sortie)
    declass_pct = round((declass / sortie) * 100, 1) if sortie else 0
    dechets_pct = round((dechets / entree) * 100, 1) if entree else 0
    seuil_declass = _safe_float_param('seuil_declass_pct', 30)
    seuil_rendement = _safe_float_param('seuil_rendement_min', 65)

    if rendement < seuil_rendement * 0.85 or declass_pct > seuil_declass:
        couleur = 'danger'
    elif rendement < seuil_rendement or declass_pct >= seuil_declass * 0.8:
        couleur = 'warning'
    else:
        couleur = 'success'

    return {
        'entree': round(entree, 2),
        'conforme': round(conforme, 2),
        'declass': round(declass, 2),
        'dechets': round(dechets, 2),
        'sortie': round(sortie, 2),
        'rendement': rendement,
        'declass_pct': declass_pct,
        'dechets_pct': dechets_pct,
        'seuil_declass': seuil_declass,
        'seuil_rendement': seuil_rendement,
        'couleur': couleur,
        'nb_postes': len(equipes),
    }


def _qualite_par_essence(equipes):
    seuil_declass = _safe_float_param('seuil_declass_pct', 30)
    seuil_rendement = _safe_float_param('seuil_rendement_min', 65)
    stats = defaultdict(lambda: {
        'essence': '',
        'entree': 0.0,
        'conforme': 0.0,
        'declass': 0.0,
        'dechets': 0.0,
        'postes': set(),
    })

    for equipe in equipes:
        for prod in equipe.productions:
            essence = prod.essence or 'Non renseignée'
            s = stats[essence]
            s['essence'] = essence
            s['entree'] += prod.volume_entree or 0
            s['conforme'] += prod.volume_conforme or 0
            s['declass'] += prod.volume_declass or 0
            s['dechets'] += prod.volume_dechets or 0
            s['postes'].add(equipe.id)

    lignes = []
    for s in stats.values():
        sortie = s['conforme'] + s['declass']
        rendement = _rendement_matiere(s['entree'], sortie)
        declass_pct = round((s['declass'] / sortie) * 100, 1) if sortie else 0
        dechets_pct = round((s['dechets'] / s['entree']) * 100, 1) if s['entree'] else 0
        if rendement < seuil_rendement * 0.85 or declass_pct > seuil_declass:
            couleur = 'danger'
        elif rendement < seuil_rendement or declass_pct >= seuil_declass * 0.8:
            couleur = 'warning'
        else:
            couleur = 'success'
        lignes.append({
            'essence': s['essence'],
            'entree': round(s['entree'], 2),
            'conforme': round(s['conforme'], 2),
            'declass': round(s['declass'], 2),
            'dechets': round(s['dechets'], 2),
            'sortie': round(sortie, 2),
            'rendement': rendement,
            'declass_pct': declass_pct,
            'dechets_pct': dechets_pct,
            'nb_postes': len(s['postes']),
            'couleur': couleur,
            'analyse_url': url_for(
                'problemes.nouveau',
                origine_type='manuel',
                origine_label=f'Qualité matière - {s["essence"]}',
                contexte_quoi=f'Rendement matière ou déclassement à surveiller sur {s["essence"]}',
                contexte_ou=s['essence'],
                contexte_combien=f'Rendement {rendement}% · déclassé {declass_pct}% · déchets {dechets_pct}%',
                origine_url=url_for('dashboard.qualite_chef', jours=30),
            ),
        })
    lignes.sort(key=lambda item: (item['couleur'] == 'success', item['rendement'], -item['declass_pct']))
    return lignes


def _qualite_par_shift(equipes):
    groupes = []
    for shift in _SHIFTS_JOUR:
        items = [e for e in equipes if e.numero_equipe == shift]
        entree = sum(e.volume_entree for e in items)
        conforme = sum(e.volume_conforme for e in items)
        declass = sum(e.volume_declass for e in items)
        dechets = sum(e.volume_dechets for e in items)
        sortie = conforme + declass
        groupes.append({
            'shift': shift,
            'nb_postes': len(items),
            'entree': round(entree, 2),
            'conforme': round(conforme, 2),
            'declass': round(declass, 2),
            'dechets': round(dechets, 2),
            'rendement': _rendement_matiere(entree, sortie),
            'declass_pct': round((declass / sortie) * 100, 1) if sortie else 0,
            'dechets_pct': round((dechets / entree) * 100, 1) if entree else 0,
        })
    return groupes


def _fiches_qualite_a_surveiller(equipes):
    seuil_declass = _safe_float_param('seuil_declass_pct', 30)
    seuil_rendement = _safe_float_param('seuil_rendement_min', 65)
    lignes = []
    for equipe in equipes:
        entree = equipe.volume_entree
        sortie = equipe.volume_sorti
        rendement = _rendement_matiere(entree, sortie)
        declass_pct = round((equipe.volume_declass / sortie) * 100, 1) if sortie else 0
        dechets_pct = round((equipe.volume_dechets / entree) * 100, 1) if entree else 0
        score = 0
        raisons = []
        if rendement < seuil_rendement:
            score += int(seuil_rendement - rendement) + 20
            raisons.append(f'Rendement {rendement}%')
        if declass_pct > seuil_declass:
            score += int(declass_pct - seuil_declass) + 20
            raisons.append(f'Déclassé {declass_pct}%')
        if dechets_pct > 35:
            score += int(dechets_pct - 35) + 10
            raisons.append(f'Déchets {dechets_pct}%')
        if score <= 0:
            continue
        lignes.append({
            'id': equipe.id,
            'date': equipe.date,
            'date_fmt': equipe.date.strftime('%d/%m/%Y') if equipe.date else '—',
            'shift': equipe.numero_equipe,
            'operateur': equipe.operateur_nom or (equipe.saisie_par.nom if equipe.saisie_par else 'Non renseigné'),
            'essences': equipe.essences_label or '—',
            'entree': round(entree, 2),
            'conforme': round(equipe.volume_conforme, 2),
            'declass': round(equipe.volume_declass, 2),
            'dechets': round(equipe.volume_dechets, 2),
            'rendement': rendement,
            'declass_pct': declass_pct,
            'dechets_pct': dechets_pct,
            'raisons': raisons,
            'score': score,
            'href': url_for('saisie.detail_poste', poste_id=equipe.id),
            'analyse_url': url_for(
                'problemes.nouveau',
                origine_type='fiche',
                origine_label=f'Qualité matière fiche #{equipe.id}',
                equipe_id=equipe.id,
                contexte_quoi='Rendement matière ou déclassement anormal',
                contexte_quand=f'{equipe.date.strftime("%d/%m/%Y")} · {equipe.numero_equipe}' if equipe.date else equipe.numero_equipe,
                contexte_ou=equipe.essences_label,
                contexte_combien=' · '.join(raisons),
                origine_url=url_for('saisie.detail_poste', poste_id=equipe.id),
            ),
        })
    lignes.sort(key=lambda item: item['score'], reverse=True)
    return lignes[:12]


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
    alertes = _alertes_chef(aujourd_hui)
    kpi_jour = _kpi_aujourdhui(aujourd_hui)
    postes_du_jour = _postes_du_jour(aujourd_hui)
    actions_immediates = _actions_immediates(aujourd_hui, alertes)
    nb_problemes_ouverts = Probleme.query.filter(
        Probleme.statut.in_(('ouvert', 'en_analyse'))
    ).count()

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
                               kpi_jour=kpi_jour,
                               postes_du_jour=postes_du_jour,
                               actions_immediates=actions_immediates,
                               alertes=alertes,
                               nb_problemes_ouverts=nb_problemes_ouverts)

    trs_valeurs  = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen    = round(sum(trs_valeurs) / len(trs_valeurs), 1) if trs_valeurs else 0
    total_produit = sum(e.volume_sorti for e in equipes)
    total_declass = round(sum(e.volume_declass for e in equipes), 2)
    total_arrets  = sum(e.duree_totale_arrets for e in equipes)

    essence_stats = calcule_trs_par_essence(equipes)

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
            elif eq.statut == STATUT_BROUILLON:
                cellules[shift] = {'state': 'brouillon', 'display': '⏳', 'couleur': 'warning'}
            elif eq.statut == STATUT_A_VERIFIER:
                cellules[shift] = {'state': 'a_verifier', 'display': 'Chez le chef', 'couleur': 'info'}
            elif eq.statut == STATUT_A_CORRIGER:
                cellules[shift] = {'state': 'a_corriger', 'display': 'À corriger', 'couleur': 'warning'}
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
                           kpi_jour=kpi_jour,
                           postes_du_jour=postes_du_jour,
                           actions_immediates=actions_immediates,
                           alertes=alertes,
                           nb_problemes_ouverts=nb_problemes_ouverts)


@dashboard_bp.route('/chef/fiches')
@login_required
@roles_required('chef', 'admin')
def fiches_chef():
    """Liste de contrôle des fiches côté chef scierie."""
    filtres = {
        'statut': request.args.get('statut', STATUT_A_VERIFIER).strip(),
        'periode': request.args.get('periode', '30j').strip(),
        'equipe': request.args.get('equipe', '').strip(),
        'operateur_id': request.args.get('operateur_id', '').strip(),
        'anomalies': request.args.get('anomalies', '').strip(),
        'q': request.args.get('q', '').strip(),
    }
    try:
        filtres['operateur_id'] = int(filtres['operateur_id']) if filtres['operateur_id'] else None
    except ValueError:
        filtres['operateur_id'] = None

    equipes, label_periode_fiches = _fiches_chef_query(filtres)
    lignes_base = [_ligne_fiche_chef(equipe) for equipe in equipes]
    compteurs_base = _compteurs_fiches_chef(lignes_base)
    lignes = _filtrer_lignes_fiches(lignes_base, filtres)
    compteurs_resultats = _compteurs_fiches_chef(lignes)

    utilisateurs = User.query.filter(
        User.role.in_(('operateur', 'chef', 'admin'))
    ).order_by(User.nom.asc()).all()

    return render_template(
        'chef/fiches.html',
        fiches=lignes,
        compteurs_base=compteurs_base,
        compteurs_resultats=compteurs_resultats,
        filtres=filtres,
        label_periode=label_periode_fiches,
        utilisateurs=utilisateurs,
        statuts={
            STATUT_A_VERIFIER: 'Chez le chef',
            STATUT_A_CORRIGER: 'À corriger',
            STATUT_BROUILLON: 'Brouillons',
            'validees': 'Validées / clôturées',
            'tous': 'Tous les statuts',
        },
    )


@dashboard_bp.route('/chef/machines')
@login_required
@roles_required('chef', 'admin')
def machines_chef():
    """Diagnostic Machines & Arrêts pour le chef scierie."""
    jours = request.args.get('jours', 30)
    mode = request.args.get('mode', 'officiel').strip()
    if mode not in ('officiel', 'temps_reel'):
        mode = 'officiel'
    machine = request.args.get('machine', '').strip()
    if machine not in Config.MACHINES:
        machine = ''

    equipes, jours, label_periode = _equipes_machines(jours, mode)
    machines, arrets, arrets_longs = _analyse_machines(equipes, machine or None)
    recurrences = _recurrences_machines(arrets)
    synthese = _synthese_machines(machines, arrets)

    return render_template(
        'chef/machines.html',
        jours=jours,
        mode=mode,
        machine=machine,
        label_periode=label_periode,
        machines=machines,
        arrets=arrets[:80],
        arrets_longs=arrets_longs,
        recurrences=recurrences,
        synthese=synthese,
        machines_options=Config.MACHINES,
    )


@dashboard_bp.route('/chef/production')
@login_required
@roles_required('chef', 'admin')
def production_chef():
    """Production & Objectifs pour le chef scierie."""
    jours = request.args.get('jours', 30)
    mode = request.args.get('mode', 'officiel').strip()
    if mode not in ('officiel', 'temps_reel'):
        mode = 'officiel'

    equipes, jours, label_periode = _equipes_production(jours, mode)
    resume = _resume_production(equipes)
    comparaison = _comparaison_equipes_production(equipes)
    essences = _analyse_essences_production(equipes)
    extremes = _postes_extremes_production(equipes)
    projection = _projection_production_active()

    return render_template(
        'chef/production.html',
        jours=jours,
        mode=mode,
        label_periode=label_periode,
        resume=resume,
        comparaison=comparaison,
        essences=essences,
        extremes=extremes,
        projection=projection,
    )


@dashboard_bp.route('/chef/qualite')
@login_required
@roles_required('chef', 'admin')
def qualite_chef():
    """Qualité / Matière pour le chef scierie."""
    jours = request.args.get('jours', 30)
    mode = request.args.get('mode', 'officiel').strip()
    if mode not in ('officiel', 'temps_reel'):
        mode = 'officiel'

    equipes, jours, label_periode = _equipes_production(jours, mode)
    resume = _resume_qualite(equipes)
    essences = _qualite_par_essence(equipes)
    shifts = _qualite_par_shift(equipes)
    fiches_a_surveiller = _fiches_qualite_a_surveiller(equipes)

    return render_template(
        'chef/qualite.html',
        jours=jours,
        mode=mode,
        label_periode=label_periode,
        resume=resume,
        essences=essences,
        shifts=shifts,
        fiches_a_surveiller=fiches_a_surveiller,
    )


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
        Equipe.statut.in_(STATUTS_NON_ANALYSES)
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
    taux_revente = float(Parametre.get('taux_revente_rebut', 0.70))
    valeur_dechets_m3 = float(Parametre.get('valeur_dechets_m3', 0))

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
            duree_impact = a.duree_impact_min
            if not duree_impact:
                continue
            perte_arret = (duree_impact / 60) * capacite_h * prix_moyen
            m = a.machine
            if m not in par_machine:
                par_machine[m] = {'perte': 0.0, 'duree': 0, 'count': 0, 'arrets': []}
            par_machine[m]['perte'] += perte_arret
            par_machine[m]['duree'] += duree_impact
            par_machine[m]['count'] += 1
            par_machine[m]['arrets'].append({
                'date':        e.date.strftime('%d/%m/%Y'),
                'equipe':      e.numero_equipe,
                'cause':       a.cause,
                'categorie':   a.categorie,
                'duree':       duree_impact,
                'duree_reelle': a.duree_min,
                'duree_prevue': a.duree_prevue_min,
                'perte':       int(perte_arret),
            })

        # Perte Q par essence (déclassé + déchets séparés)
        for pr in e.productions:
            pq_d  = pr.volume_declass  * _prix_production(pr) * (1 - taux_revente)
            pq_ch = pr.volume_dechets  * max(0, _prix_production(pr) - valeur_dechets_m3)
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
        Equipe.statut.in_(STATUTS_NON_ANALYSES)
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

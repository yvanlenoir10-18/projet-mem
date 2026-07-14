"""
Routes des tableaux de bord.
- Vue Chef Scierie : analyse opérationnelle (TRS, Pareto, volumes)
- Vue PDG         : synthèse financière (FCFA, objectifs, traffic light)
- Export Excel    : rapport mensuel téléchargeable
"""
from collections import defaultdict
import statistics
from flask import Blueprint, render_template, request, send_file, abort, url_for, redirect, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import date, datetime, timedelta
import io
from ..models import (
    db, User, Equipe, Parametre, STATUT_A_CORRIGER, STATUT_A_VERIFIER,
    STATUT_BROUILLON, STATUT_VALIDE_CHEF, STATUT_VERROUILLE,
    STATUTS_ANALYSES, STATUTS_NON_ANALYSES, Probleme, Arret, ActionChef, ActionChefEvenement,
)
from ..services.trs import (
    pareto_arrets, couleur_trs,
    calcule_pertes_equipe, calcule_pertes_fcfa, decompose_dpq,
    calcule_manque_gagner, manque_a_gagner_agrege, calcule_trs_par_essence,
    cascade_economique,
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


def _parse_date_action(valeur):
    valeur = (valeur or '').strip()
    if not valeur:
        return None
    try:
        return date.fromisoformat(valeur)
    except ValueError:
        return None


def _action_statut_meta(statut):
    label, couleur = ACTION_CHEF_STATUTS.get(statut, (statut or 'Inconnu', 'secondary'))
    return {'label': label, 'couleur': couleur}


def _action_type_label(type_action):
    return dict(ACTION_CHEF_TYPES).get(type_action, type_action or 'Autre')


def _signal_temporel_action(action):
    today = date.today()
    if action.est_terminee:
        return {
            'label': 'Terminée',
            'detail': action.echeance.strftime('%d/%m/%Y') if action.echeance else 'Sans délai',
            'couleur': 'success',
            'icon': 'bi-check-circle',
        }
    if not action.echeance:
        return {
            'label': 'Sans délai',
            'detail': 'À dater si cette action doit rester suivie',
            'couleur': 'secondary',
            'icon': 'bi-calendar-plus',
        }
    delta = (action.echeance - today).days
    if delta < 0:
        return {
            'label': 'En retard',
            'detail': f"{abs(delta)} jour(s) de retard",
            'couleur': 'danger',
            'icon': 'bi-alarm',
        }
    if delta == 0:
        return {
            'label': "Aujourd'hui",
            'detail': 'À vérifier ce jour',
            'couleur': 'warning',
            'icon': 'bi-calendar-check',
        }
    if delta <= 3:
        return {
            'label': 'Sous 3 jours',
            'detail': f"Échéance dans {delta} jour(s)",
            'couleur': 'info',
            'icon': 'bi-calendar-event',
        }
    return {
        'label': 'Planifiée',
        'detail': f"Échéance le {action.echeance.strftime('%d/%m/%Y')}",
        'couleur': 'secondary',
        'icon': 'bi-calendar3',
    }


def _stats_actions_chef():
    today = date.today()
    soon = today + timedelta(days=3)
    ouvertes_query = ActionChef.query.filter(ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS))
    return {
        'ouvertes': ouvertes_query.count(),
        'retard': ouvertes_query.filter(ActionChef.echeance < today).count(),
        'aujourd_hui': ouvertes_query.filter(ActionChef.echeance == today).count(),
        'bientot': ouvertes_query.filter(
            ActionChef.echeance > today,
            ActionChef.echeance <= soon,
        ).count(),
        'sans_delai': ouvertes_query.filter(ActionChef.echeance.is_(None)).count(),
        'a_faire': ActionChef.query.filter_by(statut='a_faire').count(),
        'en_cours': ActionChef.query.filter_by(statut='en_cours').count(),
        'fait': ActionChef.query.filter_by(statut='fait').count(),
    }


def _responsables_actions_chef(limite=None):
    """Synthèse simple des actions ouvertes par responsable texte."""
    today = date.today()
    responsables = defaultdict(lambda: {
        'responsable': '',
        'ouvertes': 0,
        'retard': 0,
        'aujourd_hui': 0,
        'en_cours': 0,
    })
    actions = ActionChef.query.filter(
        ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS)
    ).all()

    for action in actions:
        nom = (action.responsable or 'Non renseigné').strip() or 'Non renseigné'
        cle = nom.lower()
        stats = responsables[cle]
        stats['responsable'] = nom
        stats['ouvertes'] += 1
        if action.statut == 'en_cours':
            stats['en_cours'] += 1
        if action.echeance and action.echeance < today:
            stats['retard'] += 1
        elif action.echeance == today:
            stats['aujourd_hui'] += 1

    lignes = sorted(
        responsables.values(),
        key=lambda item: (item['retard'], item['aujourd_hui'], item['ouvertes']),
        reverse=True,
    )
    return lignes[:limite] if limite else lignes


def _machines_actions_chef(limite=None):
    """Synthèse simple des actions ouvertes rattachées à une machine."""
    today = date.today()
    machines = defaultdict(lambda: {
        'machine': '',
        'ouvertes': 0,
        'retard': 0,
        'aujourd_hui': 0,
        'en_cours': 0,
    })
    actions = ActionChef.query.filter(
        ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS),
        ActionChef.machine.isnot(None),
    ).all()

    for action in actions:
        nom = (action.machine or '').strip()
        if not nom:
            continue
        cle = nom.lower()
        stats = machines[cle]
        stats['machine'] = nom
        stats['ouvertes'] += 1
        if action.statut == 'en_cours':
            stats['en_cours'] += 1
        if action.echeance and action.echeance < today:
            stats['retard'] += 1
        elif action.echeance == today:
            stats['aujourd_hui'] += 1

    lignes = sorted(
        machines.values(),
        key=lambda item: (item['retard'], item['aujourd_hui'], item['ouvertes']),
        reverse=True,
    )
    return lignes[:limite] if limite else lignes


def _suggestions_responsables_action_chef(responsable_courant=None):
    """Suggestions pour le champ responsable : défauts + valeurs déjà utilisées."""
    suggestions = {}
    for nom in RESPONSABLES_ACTION_CHEF_DEFAUT:
        suggestions[nom.lower()] = nom

    valeurs = ActionChef.query.with_entities(ActionChef.responsable).filter(
        ActionChef.responsable.isnot(None)
    ).distinct().all()
    for (nom,) in valeurs:
        nom = (nom or '').strip()
        if nom:
            suggestions[nom.lower()] = nom

    responsable_courant = (responsable_courant or '').strip()
    if responsable_courant:
        suggestions[responsable_courant.lower()] = responsable_courant

    return sorted(suggestions.values(), key=lambda item: item.lower())


def _tracer_transition_action_chef(action, nouveau_statut, note=None, ancien_statut=None):
    """Ajoute un événement métier lisible après une création ou un changement de statut."""
    if not action.id:
        db.session.flush()
    db.session.add(ActionChefEvenement(
        action_id=action.id,
        ancien_statut=ancien_statut,
        nouveau_statut=nouveau_statut,
        note=(note or '').strip() or None,
        auteur_id=current_user.id,
    ))


def _evenements_action_chef(action, limite=6):
    evenements = []
    for evenement in action.evenements[:limite]:
        ancien = _action_statut_meta(evenement.ancien_statut)['label'] if evenement.ancien_statut else None
        nouveau = _action_statut_meta(evenement.nouveau_statut)['label']
        evenements.append({
            'id': evenement.id,
            'titre': f"{ancien} → {nouveau}" if ancien else f"Créée · {nouveau}",
            'note': evenement.note,
            'auteur': evenement.auteur.nom if evenement.auteur else '—',
            'date_fmt': evenement.cree_le.strftime('%d/%m/%Y à %H:%M') if evenement.cree_le else '—',
        })
    return evenements


def _stats_arrets_machine_periode(machine, debut, fin):
    """Durée et nombre d'arrêts validés pour une machine sur une période."""
    arrets = Arret.query.join(Equipe).filter(
        Arret.machine.ilike(machine),
        Equipe.statut.in_(STATUTS_ANALYSES),
        Equipe.date >= debut,
        Equipe.date <= fin,
    ).all()
    minutes = sum(arret.duree_impact_min for arret in arrets)
    return {
        'count': len(arrets),
        'minutes': minutes,
        'minutes_fmt': _format_duree(minutes),
    }


def _bilan_efficacite_action_chef(action, aujourd_hui=None):
    """Compare les arrêts machine avant/après une action terminée."""
    if action.statut != 'fait' or not action.machine or not action.termine_le:
        return None

    aujourd_hui = aujourd_hui or date.today()
    date_fin_action = action.termine_le.date()
    recul_jours = max(0, (aujourd_hui - date_fin_action).days)
    fenetre_jours = min(7, recul_jours)

    if fenetre_jours < 2:
        return {
            'niveau': 'observation',
            'label': 'À observer',
            'couleur': 'info',
            'icon': 'bi-hourglass-split',
            'detail': "Pas encore assez de recul après la clôture.",
            'fenetre_jours': fenetre_jours,
        }

    avant = _stats_arrets_machine_periode(
        action.machine,
        date_fin_action - timedelta(days=fenetre_jours),
        date_fin_action - timedelta(days=1),
    )
    apres = _stats_arrets_machine_periode(
        action.machine,
        date_fin_action + timedelta(days=1),
        date_fin_action + timedelta(days=fenetre_jours),
    )

    if avant['minutes'] == 0 and apres['minutes'] == 0:
        niveau, label, couleur, icon = 'stable', 'Aucun arrêt observé', 'success', 'bi-check-circle'
        detail = "Aucun arrêt validé avant ou après l'action sur la fenêtre observée."
    elif avant['minutes'] == 0:
        niveau, label, couleur, icon = 'a_revoir', 'À revoir', 'danger', 'bi-exclamation-octagon'
        detail = "Des arrêts apparaissent après l'action alors qu'aucun n'était observé avant."
    else:
        reduction_pct = round(((avant['minutes'] - apres['minutes']) / avant['minutes']) * 100)
        if reduction_pct >= 20:
            niveau, label, couleur, icon = 'amelioration', 'Amélioration visible', 'success', 'bi-graph-down-arrow'
            detail = f"Temps d'arrêt réduit de {reduction_pct}% sur une fenêtre comparable."
        elif apres['minutes'] > avant['minutes']:
            hausse_pct = abs(reduction_pct)
            niveau, label, couleur, icon = 'a_revoir', 'À revoir', 'danger', 'bi-exclamation-octagon'
            detail = f"Temps d'arrêt en hausse de {hausse_pct}% malgré l'action."
        else:
            niveau, label, couleur, icon = 'a_surveiller', 'À surveiller', 'warning', 'bi-eye'
            detail = "Évolution encore trop faible pour conclure."

    return {
        'niveau': niveau,
        'label': label,
        'couleur': couleur,
        'icon': icon,
        'detail': detail,
        'fenetre_jours': fenetre_jours,
        'avant': avant,
        'apres': apres,
    }


def _stats_boucle_amelioration_actions_chef(aujourd_hui=None, depuis_jours=30):
    """Synthèse des résultats observés après les actions machine terminées."""
    aujourd_hui = aujourd_hui or date.today()
    depuis = datetime.combine(
        aujourd_hui - timedelta(days=depuis_jours),
        datetime.min.time(),
    )
    actions = ActionChef.query.filter(
        ActionChef.statut == 'fait',
        ActionChef.machine.isnot(None),
        ActionChef.termine_le.isnot(None),
        ActionChef.termine_le >= depuis,
    ).all()
    stats = {
        'ouvertes': ActionChef.query.filter(
            ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS)
        ).count(),
        'terminees_machine': len(actions),
        'efficaces': 0,
        'observation': 0,
        'a_surveiller': 0,
        'a_revoir': 0,
    }
    for action in actions:
        bilan = _bilan_efficacite_action_chef(action, aujourd_hui=aujourd_hui)
        niveau = bilan.get('niveau') if bilan else None
        if niveau in ('amelioration', 'stable'):
            stats['efficaces'] += 1
        elif niveau in ('observation', 'a_surveiller', 'a_revoir'):
            stats[niveau] += 1
    return stats


def _efficacite_actions_par_machine(aujourd_hui=None, depuis_jours=30, limite=None):
    """Regroupe les effets observés des actions terminées par machine."""
    aujourd_hui = aujourd_hui or date.today()
    depuis = datetime.combine(
        aujourd_hui - timedelta(days=depuis_jours),
        datetime.min.time(),
    )
    actions = ActionChef.query.filter(
        ActionChef.statut == 'fait',
        ActionChef.machine.isnot(None),
        ActionChef.termine_le.isnot(None),
        ActionChef.termine_le >= depuis,
    ).all()
    machines = defaultdict(lambda: {
        'machine': '',
        'terminees': 0,
        'efficaces': 0,
        'observation': 0,
        'a_surveiller': 0,
        'a_revoir': 0,
    })
    for action in actions:
        machine = (action.machine or '').strip()
        if not machine:
            continue
        bilan = _bilan_efficacite_action_chef(action, aujourd_hui=aujourd_hui)
        niveau = bilan.get('niveau') if bilan else None
        stats = machines[machine.lower()]
        stats['machine'] = machine
        stats['terminees'] += 1
        if niveau in ('amelioration', 'stable'):
            stats['efficaces'] += 1
        elif niveau in ('observation', 'a_surveiller', 'a_revoir'):
            stats[niveau] += 1

    lignes = sorted(
        machines.values(),
        key=lambda item: (
            item['a_revoir'],
            item['a_surveiller'],
            item['observation'],
            item['terminees'],
        ),
        reverse=True,
    )
    return lignes[:limite] if limite else lignes


def _ligne_action_chef(action, inclure_evenements=False):
    statut = _action_statut_meta(action.statut)
    signal = _signal_temporel_action(action)
    ligne = {
        'id': action.id,
        'titre': action.titre,
        'type_action': action.type_action,
        'type_label': _action_type_label(action.type_action),
        'description': action.description,
        'responsable': action.responsable,
        'echeance': action.echeance,
        'echeance_fmt': action.echeance.strftime('%d/%m/%Y') if action.echeance else 'Sans délai',
        'statut': action.statut,
        'statut_label': statut['label'],
        'statut_couleur': statut['couleur'],
        'retard': action.est_en_retard,
        'signal_temporel': signal,
        'origine_type': action.origine_type,
        'origine_label': action.origine_label,
        'origine_url': action.origine_url,
        'machine': action.machine,
        'motif_classe_sans_action': action.motif_classe_sans_action,
        'note_resultat': action.note_resultat,
        'bilan_efficacite': _bilan_efficacite_action_chef(action),
        'cree_par': action.cree_par.nom if action.cree_par else '—',
        'cree_le': action.cree_le,
    }
    if inclure_evenements:
        ligne['evenements'] = _evenements_action_chef(action)
    return ligne


def _actions_chef_urgentes(aujourd_hui, limite=3):
    """Actions ouvertes à regarder en premier sur l'accueil chef."""
    bientot = aujourd_hui + timedelta(days=3)
    actions = ActionChef.query.filter(
        ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS),
        ActionChef.echeance.isnot(None),
        ActionChef.echeance <= bientot,
    ).order_by(
        ActionChef.echeance.asc(),
        ActionChef.cree_le.desc(),
    ).limit(limite).all()

    lignes = []
    for action in actions:
        ligne = _ligne_action_chef(action)
        if action.echeance and action.echeance < aujourd_hui:
            statut_filtre = 'retard'
        elif action.echeance == aujourd_hui:
            statut_filtre = 'aujourd_hui'
        else:
            statut_filtre = 'bientot'
        ligne['href'] = url_for(
            'dashboard.actions_chef',
            statut=statut_filtre,
            q=action.titre,
        )
        lignes.append(ligne)
    return lignes


def _actions_chef_a_revoir(aujourd_hui, limite=None, depuis_jours=30):
    """Actions machine terminées récemment mais sans amélioration observée."""
    depuis = datetime.combine(
        aujourd_hui - timedelta(days=depuis_jours),
        datetime.min.time(),
    )
    actions = ActionChef.query.filter(
        ActionChef.statut == 'fait',
        ActionChef.machine.isnot(None),
        ActionChef.termine_le.isnot(None),
        ActionChef.termine_le >= depuis,
    ).order_by(ActionChef.termine_le.desc()).all()

    lignes = []
    for action in actions:
        ligne = _ligne_action_chef(action)
        bilan = ligne.get('bilan_efficacite')
        if not bilan or bilan.get('niveau') != 'a_revoir':
            continue
        ligne['href'] = url_for(
            'dashboard.actions_chef',
            statut='fait',
            q=action.titre,
        )
        origine_label = f"Action inefficace #{action.id} - {action.machine}"
        contexte_combien = (
            f"Temps d'arrêt avant : {bilan['avant']['minutes_fmt']} · "
            f"après : {bilan['apres']['minutes_fmt']}. {bilan['detail']}"
        )
        ligne['href_nouvelle_action'] = url_for(
            'dashboard.nouvelle_action_chef',
            machine=action.machine,
            origine_type='machine',
            origine_label=origine_label,
            origine_url=ligne['href'],
            titre=f"Nouvelle action sur {action.machine}",
            type_action='maintenance',
            description=(
                f"Réévaluer l'intervention sur {action.machine} : "
                f"{contexte_combien}"
            ),
        )
        ligne['href_analyse'] = url_for(
            'problemes.nouveau',
            origine_type='machine',
            origine_label=origine_label,
            origine_url=ligne['href'],
            contexte_quoi=f"Action terminée mais inefficace sur {action.machine}",
            contexte_quand="Après une première intervention clôturée",
            contexte_ou=action.machine,
            contexte_combien=contexte_combien,
        )
        lignes.append(ligne)
        if limite and len(lignes) >= limite:
            break
    return lignes


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

ACTION_CHEF_STATUTS = {
    'a_faire': ('À faire', 'warning'),
    'en_cours': ('En cours', 'info'),
    'fait': ('Fait', 'success'),
    'abandonne': ('Abandonné', 'secondary'),
    'classe_sans_action': ('Classé sans action', 'secondary'),
}
ACTION_CHEF_STATUTS_OUVERTS = ('a_faire', 'en_cours')
RESPONSABLES_ACTION_CHEF_DEFAUT = [
    'Maintenance',
    'Chef parc',
    'Chef équipe matin',
    'Chef équipe après-midi',
    'Chef scierie',
    'Qualité',
    'Admin',
]
ACTION_CHEF_TYPES = [
    ('maintenance', 'Maintenance'),
    ('approvisionnement', 'Approvisionnement bois'),
    ('qualite', 'Qualité / matière'),
    ('controle_fiche', 'Contrôle fiche'),
    ('organisation', 'Organisation poste'),
    ('formation', 'Formation / consigne'),
    ('surveillance', 'Surveillance'),
    ('autre', 'Autre'),
]
ACTION_CHEF_ORIGINES = {
    'libre': 'Libre',
    'fiche': 'Fiche',
    'machine': 'Machine',
    'probleme': 'Résolution',
    'recommandation': 'Recommandation',
}


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

    # P0-3 — Signal d'état pour le cockpit : tant qu'aucune fiche n'est saisie
    # aujourd'hui, on affiche un message d'attente plutôt qu'une rangée de zéros.
    derniere = Equipe.query.filter(
        Equipe.date < aujourd_hui,
        Equipe.statut.in_(STATUTS_ANALYSES),
    ).order_by(Equipe.date.desc()).first()
    derniere_activite = derniere.date.strftime('%d/%m/%Y') if derniere else None

    return {
        'vide': not equipes_jour,
        'derniere_activite': derniere_activite,
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

    actions_retard = ActionChef.query.filter(
        ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS),
        ActionChef.echeance < aujourd_hui,
    ).count()
    if actions_retard:
        actions.append({
            'niveau': 'danger',
            'icon': 'bi-alarm',
            'titre': 'Actions en retard',
            'detail': f"{actions_retard} action(s) chef ont dépassé leur délai.",
            'href': url_for('dashboard.actions_chef', statut='retard'),
            'cta': 'Traiter',
            'priorite': 120,
        })

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


def _machine_prioritaire_recent(aujourd_hui, jours=7):
    """Retourne la machine qui consomme le plus de temps d'arrêt récent."""
    depuis = aujourd_hui - timedelta(days=jours)
    statuts = tuple(dict.fromkeys((STATUT_A_VERIFIER, *STATUTS_ANALYSES)))
    equipes = Equipe.query.filter(
        Equipe.date >= depuis,
        Equipe.date <= aujourd_hui,
        Equipe.statut.in_(statuts),
    ).all()

    nb_postes = len(equipes)
    machines = defaultdict(lambda: {'duree': 0, 'count': 0, 'impact': 0, 'causes': defaultdict(int)})
    for equipe in equipes:
        for arret in equipe.arrets:
            duree = arret.duree_min or 0
            if duree <= 0:
                continue
            stats = machines[arret.machine]
            stats['duree'] += duree
            stats['count'] += 1
            stats['impact'] += arret.duree_impact_min or 0
            stats['causes'][arret.cause or arret.categorie or 'Cause non précisée'] += duree

    if not machines:
        return None

    machine, stats = max(machines.items(), key=lambda item: item[1]['duree'])
    cause = None
    if stats['causes']:
        cause, cause_duree = max(stats['causes'].items(), key=lambda item: item[1])
    else:
        cause_duree = 0

    duree_poste = float(Parametre.get('duree_poste', 480))
    capacite_totale = nb_postes * duree_poste
    disponibilite_pct = round((1 - stats['impact'] / capacite_totale) * 100, 1) if capacite_totale > 0 else None

    return {
        'machine': machine,
        'duree': stats['duree'],
        'duree_fmt': _format_duree(stats['duree']),
        'count': stats['count'],
        'cause': cause,
        'cause_duree': cause_duree,
        'jours': jours,
        'disponibilite_pct': disponibilite_pct,
    }


def _alerte_soir_decroche(aujourd_hui, jours=3, seuil_pts=15):
    """Renvoie un dict si l'équipe Apres-midi décroche systématiquement sur `jours` jours."""
    depuis = aujourd_hui - timedelta(days=jours - 1)
    equipes = Equipe.query.filter(
        Equipe.date >= depuis,
        Equipe.date <= aujourd_hui,
        Equipe.statut.in_(tuple(STATUTS_ANALYSES)),
    ).all()

    par_jour = defaultdict(lambda: {'Matin': [], 'Apres-midi': []})
    for e in equipes:
        if e.trs_global is not None and e.numero_equipe in ('Matin', 'Apres-midi'):
            par_jour[e.date][e.numero_equipe].append(e.trs_global)

    jours_valides = []
    for d, shifts in par_jour.items():
        if shifts['Matin'] and shifts['Apres-midi']:
            trs_matin = sum(shifts['Matin']) / len(shifts['Matin'])
            trs_soir = sum(shifts['Apres-midi']) / len(shifts['Apres-midi'])
            jours_valides.append({'date': d, 'matin': trs_matin, 'soir': trs_soir})

    if len(jours_valides) < jours:
        return None

    decrochages = [j for j in jours_valides if j['soir'] < j['matin'] - seuil_pts]
    if len(decrochages) < jours:
        return None

    trs_matin_moy = round(sum(j['matin'] for j in jours_valides) / len(jours_valides), 1)
    trs_soir_moy = round(sum(j['soir'] for j in jours_valides) / len(jours_valides), 1)
    return {
        'trs_matin_moy': trs_matin_moy,
        'trs_soir_moy': trs_soir_moy,
        'ecart': round(trs_matin_moy - trs_soir_moy, 1),
        'jours': jours,
    }


def _alerte_declassement_essence(equipes):
    """Renvoie la liste des essences dont le taux de déclassement dépasse le seuil."""
    if not equipes:
        return []
    lignes = _qualite_par_essence(equipes)
    seuil = _safe_float_param('seuil_declass_pct', 30)
    alertes = [
        {
            'essence': l['essence'],
            'declass_pct': l['declass_pct'],
            'seuil': seuil,
            'depassement': round(l['declass_pct'] - seuil, 1),
        }
        for l in lignes
        if l['declass_pct'] > seuil
    ]
    alertes.sort(key=lambda a: a['depassement'], reverse=True)
    return alertes


def _action_ouverte_similaire(origine_type=None, origine_label=None, machine=None):
    query = ActionChef.query.filter(ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS))

    if machine:
        action = query.filter(ActionChef.machine == machine).order_by(
            ActionChef.echeance.is_(None),
            ActionChef.echeance.asc(),
            ActionChef.cree_le.desc(),
        ).first()
        if action:
            return action

    if origine_label:
        filtre = ActionChef.origine_label == origine_label
        if origine_type:
            filtre = (ActionChef.origine_type == origine_type) & filtre
        return query.filter(filtre).order_by(
            ActionChef.echeance.is_(None),
            ActionChef.echeance.asc(),
            ActionChef.cree_le.desc(),
        ).first()

    return None


def _probleme_ouvert_similaire(origine_label=None, reco_code=None):
    query = Probleme.query.filter(Probleme.statut.in_(('ouvert', 'en_analyse', 'cause_identifiee')))
    if reco_code:
        probleme = query.filter(Probleme.reco_code == reco_code).order_by(Probleme.cree_le.desc()).first()
        if probleme:
            return probleme
    if origine_label:
        return query.filter(Probleme.origine_label == origine_label).order_by(Probleme.cree_le.desc()).first()
    return None


def _action_secondaire_suivi(action):
    recherche = action.machine or action.origine_label or action.titre
    return {
        'label': 'Suivre action existante',
        'icon': 'bi-check2-square',
        'href': url_for('dashboard.actions_chef', statut='ouvertes', q=recherche),
        'couleur': 'outline-success',
    }


def _action_secondaire_suivi_probleme(probleme):
    return {
        'label': 'Suivre analyse ouverte',
        'icon': 'bi-diagram-3',
        'href': url_for('problemes.detail', probleme_id=probleme.id),
        'couleur': 'outline-success',
    }


def _statut_global(trs_moyen, alertes):
    """P1-1 — Verdict cockpit VERT / ORANGE / ROUGE."""
    nb_saisies = len(alertes.get('saisies_manquantes', [])) if alertes else 0
    nb_fiches_anomalies = sum(
        1 for f in (alertes.get('fiches_a_verifier', []) or [])
        if f.get('nb_anomalies', 0) > 0
    )
    details = []
    if nb_saisies:
        details.append(f"{nb_saisies} saisie{'s' if nb_saisies > 1 else ''} manquante{'s' if nb_saisies > 1 else ''}")
    if nb_fiches_anomalies:
        details.append(f"{nb_fiches_anomalies} fiche{'s' if nb_fiches_anomalies > 1 else ''} avec anomalie{'s' if nb_fiches_anomalies > 1 else ''}")

    if trs_moyen < 50 or nb_saisies >= 3:
        return {
            'code': 'rouge', 'icon': 'bi-x-circle-fill', 'label': 'HORS CONTRÔLE',
            'color': 'var(--wp-terracotta)', 'bg': 'rgba(180,60,50,0.07)', 'border': 'var(--wp-terracotta)',
            'detail': ' · '.join(details) if details else f'TRS {trs_moyen}% — sous le seuil critique (50%)',
        }
    elif trs_moyen < 60 or nb_saisies > 0 or nb_fiches_anomalies > 0:
        return {
            'code': 'orange', 'icon': 'bi-exclamation-circle-fill', 'label': 'À SURVEILLER',
            'color': 'var(--wp-ochre)', 'bg': 'rgba(197,151,58,0.07)', 'border': 'var(--wp-ochre)',
            'detail': ' · '.join(details) if details else f'TRS {trs_moyen}% — proche du seuil objectif (60%)',
        }
    else:
        return {
            'code': 'vert', 'icon': 'bi-check-circle-fill', 'label': 'SOUS CONTRÔLE',
            'color': 'var(--wp-leaf)', 'bg': 'rgba(63,138,92,0.07)', 'border': 'var(--wp-leaf)',
            'detail': 'Aucune anomalie détectée',
        }


def _priorites_chef(aujourd_hui, kpi_jour, alertes, nb_problemes_ouverts, stats_actions_chef):
    """
    P3.10 — Synthèse décisionnelle courte.
    Elle ne remplace pas les KPI : elle traduit les signaux en choix d'action.
    """
    priorites = []

    def add(niveau, icon, titre, signal, decision, href, cta, score, action_secondaire=None):
        priorites.append({
            'niveau': niveau,
            'icon': icon,
            'titre': titre,
            'signal': signal,
            'decision': decision,
            'href': href,
            'cta': cta,
            'score': score,
            'action_secondaire': action_secondaire,
        })

    nb_retard = stats_actions_chef.get('retard', 0) if stats_actions_chef else 0
    if nb_retard:
        add(
            'danger',
            'bi-alarm',
            'Lever les actions en retard',
            f"{nb_retard} action(s) ont dépassé leur délai.",
            "Commencer par les actions déjà décidées : elles bloquent souvent la résolution réelle.",
            url_for('dashboard.actions_chef', statut='retard'),
            'Traiter les retards',
            120,
        )

    fiches = list(alertes.get('fiches_a_verifier', [])) if alertes else []
    fiche_risque = next((f for f in fiches if f.get('nb_anomalies', 0) > 0), fiches[0] if fiches else None)
    if fiche_risque:
        nb_anomalies = fiche_risque.get('nb_anomalies', 0)
        niveau = 'danger' if nb_anomalies else 'warning'
        signal = (
            f"Fiche {fiche_risque['date_fmt']} · {fiche_risque['shift']} · "
            f"{fiche_risque['operateur']}"
        )
        if nb_anomalies:
            signal += f" · {nb_anomalies} anomalie(s)"
        add(
            niveau,
            'bi-shield-exclamation' if nb_anomalies else 'bi-clipboard-check',
            'Contrôler la fiche la plus risquée',
            signal,
            "Valider seulement si les données sont cohérentes ; sinon renvoyer avec un message précis.",
            url_for('saisie.detail_poste', poste_id=fiche_risque['id']),
            'Ouvrir la fiche',
            110 if nb_anomalies else 85,
        )

    machine_top = _machine_prioritaire_recent(aujourd_hui, jours=7)
    if machine_top and machine_top['duree'] >= 60:
        niveau = 'danger' if machine_top['duree'] >= 180 or machine_top['count'] >= 3 else 'warning'
        cause_txt = f" Cause dominante : {machine_top['cause']}." if machine_top.get('cause') else ''
        origine_label = machine_top['machine']
        if machine_top.get('cause'):
            origine_label = f"{machine_top['machine']} - {machine_top['cause']}"
        machine_url = url_for('dashboard.machines_chef', jours=7, mode='temps_reel', machine=machine_top['machine'])
        action_existante = _action_ouverte_similaire(
            origine_type='machine',
            origine_label=origine_label,
            machine=machine_top['machine'],
        )
        add(
            niveau,
            'bi-tools',
            'Regarder la machine prioritaire',
            f"{machine_top['machine']} cumule {machine_top['duree_fmt']} sur 7 jours.{cause_txt}",
            "Décider si un diagnostic maintenance, matière ou méthode doit être lancé.",
            machine_url,
            'Voir machines',
            95,
            action_secondaire=_action_secondaire_suivi(action_existante) if action_existante else {
                'label': 'Créer action maintenance',
                'icon': 'bi-plus-circle',
                'couleur': 'primary',
                'href': url_for(
                    'dashboard.nouvelle_action_chef',
                    origine_type='machine',
                    machine=machine_top['machine'],
                    origine_label=origine_label,
                    origine_url=machine_url,
                    titre=f"Action sur {machine_top['machine']}",
                    type_action='maintenance',
                    responsable='Maintenance',
                    description=(
                        f"Vérifier {machine_top['machine']} : "
                        f"{machine_top['duree_fmt']} d'arrêts sur 7 jours"
                        + (f", cause dominante {machine_top['cause']}." if machine_top.get('cause') else ".")
                    ),
                ),
            },
        )

    objectif = (kpi_jour or {}).get('objectif', {})
    pct_objectif = objectif.get('pct', 0) or 0
    objectif_jour = objectif.get('objectif', 0) or 0
    if objectif_jour and pct_objectif < 100:
        niveau = 'danger' if pct_objectif < 75 else 'warning'
        production_url = url_for('dashboard.production_chef', jours=7, mode='temps_reel')
        origine_objectif = 'Objectif du jour non atteint'
        action_existante = _action_ouverte_similaire(
            origine_type='recommandation',
            origine_label=origine_objectif,
        )
        add(
            niveau,
            'bi-bullseye',
            "Suivre l'écart à l'objectif",
            f"Objectif du jour à {pct_objectif}% · écart {objectif.get('ecart_m3', 0)} m³.",
            "Comparer les postes et les essences avant de demander une action terrain.",
            production_url,
            'Voir production',
            75 if niveau == 'danger' else 55,
            action_secondaire=_action_secondaire_suivi(action_existante) if action_existante else {
                'label': 'Créer action organisation',
                'icon': 'bi-plus-circle',
                'couleur': 'primary',
                'href': url_for(
                    'dashboard.nouvelle_action_chef',
                    origine_type='recommandation',
                    origine_label=origine_objectif,
                    origine_url=production_url,
                    titre="Rattraper l'écart à l'objectif",
                    type_action='organisation',
                    responsable='Chef scierie',
                    description=(
                        f"Analyser l'écart du jour : objectif à {pct_objectif}% "
                        f"({objectif.get('ecart_m3', 0)} m³). Comparer postes, essences et arrêts."
                    ),
                ),
            },
        )

    declass = (kpi_jour or {}).get('declass', {})
    declass_val = declass.get('valeur', 0) or 0
    declass_seuil = declass.get('seuil', 30) or 30
    if declass_val >= declass_seuil * 0.8 and declass_val > 0:
        niveau = 'danger' if declass_val > declass_seuil else 'warning'
        qualite_url = url_for('dashboard.qualite_chef', jours=7, mode='temps_reel')
        origine_declass = 'Déclassement élevé'
        probleme_existant = _probleme_ouvert_similaire(
            origine_label=origine_declass,
            reco_code='DECLASS_EXCESSIF',
        )
        add(
            niveau,
            'bi-gem',
            'Comprendre le déclassement',
            f"Taux du jour : {declass_val}% pour un seuil de {declass_seuil}%.",
            "Vérifier si le problème vient de la matière, du sciage, des dimensions ou du classement.",
            qualite_url,
            'Voir qualité',
            70 if niveau == 'danger' else 50,
            action_secondaire=_action_secondaire_suivi_probleme(probleme_existant) if probleme_existant else {
                'label': 'Lancer analyse',
                'icon': 'bi-diagram-3',
                'couleur': 'primary',
                'href': url_for(
                    'problemes.nouveau',
                    origine_type='recommandation',
                    origine_label=origine_declass,
                    origine_url=qualite_url,
                    reco_code='DECLASS_EXCESSIF',
                    titre='Analyser le déclassement élevé',
                    contexte_quoi='Déclassement élevé ou proche du seuil',
                    contexte_quand=aujourd_hui.strftime('%d/%m/%Y'),
                    contexte_ou='Chaîne 4',
                    contexte_combien=f"{declass_val}% pour un seuil de {declass_seuil}%",
                ),
            },
        )

    if nb_problemes_ouverts:
        add(
            'info',
            'bi-diagram-3',
            'Clore les analyses ouvertes',
            f"{nb_problemes_ouverts} analyse(s) Ishikawa / 5 Pourquoi encore ouvertes.",
            "Transformer les causes racines en actions ou clôturer les analyses terminées.",
            url_for('problemes.liste'),
            'Ouvrir résolution',
            35,
        )

    priorites.sort(key=lambda item: item['score'], reverse=True)
    return priorites[:5]


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
    ecart = round(objectif_poste - projection, 2)
    capacite_h = float(Parametre.get('capacite_equipe_h', 1.5625))
    rattrapage_min = round(ecart / capacite_h * 60) if ecart > 0 and capacite_h > 0 else 0
    return {
        'shift': shift_actif,
        'minutes_ecoulees': minutes_ecoulees,
        'volume_actuel': round(volume, 2),
        'projection': round(projection, 2),
        'objectif': round(objectif_poste, 2),
        'pct': pct,
        'couleur': _couleur_atteinte(pct),
        'ecart_objectif': ecart,
        'rattrapage_min': rattrapage_min,
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


def _tracabilite_validation(date_debut, date_fin=None):
    """P0-2 — Sur quelles fiches reposent les indicateurs du chef ?

    Distingue les fiches comptabilisées (validées + verrouillées, seules
    incluses dans les calculs) des fiches non prises en compte (brouillon,
    à vérifier, à corriger), sur la même fenêtre que le tableau de bord.
    Aucune table nouvelle (règle R7) : simple comptage par statut.
    """
    q = Equipe.query.filter(Equipe.date >= date_debut)
    if date_fin is not None:
        q = q.filter(Equipe.date < date_fin)
    par_statut = defaultdict(int)
    for f in q.all():
        par_statut[f.statut] += 1

    comptabilisees = sum(par_statut[s] for s in STATUTS_ANALYSES)
    non_comptabilisees = sum(par_statut[s] for s in STATUTS_NON_ANALYSES)

    # Dernière mise à jour = soumission la plus récente parmi les fiches comptées.
    derniere_q = Equipe.query.filter(
        Equipe.date >= date_debut,
        Equipe.statut.in_(STATUTS_ANALYSES),
    )
    if date_fin is not None:
        derniere_q = derniere_q.filter(Equipe.date < date_fin)
    derniere = derniere_q.order_by(Equipe.soumis_le.desc()).first()
    maj = derniere.soumis_le.strftime('%d/%m/%Y à %H:%M') if derniere and derniere.soumis_le else None

    return {
        'comptabilisees': comptabilisees,
        'non_comptabilisees': non_comptabilisees,
        'a_verifier': par_statut.get(STATUT_A_VERIFIER, 0),
        'a_corriger': par_statut.get(STATUT_A_CORRIGER, 0),
        'brouillon': par_statut.get(STATUT_BROUILLON, 0),
        'maj': maj,
    }


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
    stats_actions_chef = _stats_actions_chef()
    actions_chef_urgentes = _actions_chef_urgentes(aujourd_hui)
    actions_chef_a_revoir = _actions_chef_a_revoir(aujourd_hui)
    priorites_chef = _priorites_chef(
        aujourd_hui, kpi_jour, alertes, nb_problemes_ouverts, stats_actions_chef
    )
    machine_top = _machine_prioritaire_recent(aujourd_hui, jours=7)
    alerte_soir = _alerte_soir_decroche(aujourd_hui)
    projection_active = _projection_production_active()

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
        trace_debut, trace_fin = debut_m, fin_m
    else:
        equipes = _get_equipes_periode(jours)
        label_periode = f"{jours} derniers jours"
        mode_mois = False
        trace_debut, trace_fin = aujourd_hui - timedelta(days=jours), None

    tracabilite = _tracabilite_validation(trace_debut, trace_fin)

    if not equipes:
        return render_template('chef/dashboard.html',
                               postes=[], pareto=[], stats={}, jours=jours,
                               matrice={}, machines=Config.MACHINES,
                               categories=Config.CATEGORIES_ARRET,
                               decomposition=None, scorecard=None,
                               regularite=None, gain_potentiel=None,
                               mode_mois=mode_mois, label_periode=label_periode,
                               mois_options=_mois_disponibles(),
                               tracabilite=tracabilite,
                               kpi_jour=kpi_jour,
                               postes_du_jour=postes_du_jour,
                               actions_immediates=actions_immediates,
                               alertes=alertes,
                               nb_problemes_ouverts=nb_problemes_ouverts,
                               stats_actions_chef=stats_actions_chef,
                               actions_chef_urgentes=actions_chef_urgentes,
                               actions_chef_a_revoir=actions_chef_a_revoir,
                               priorites_chef=priorites_chef,
                               statut_global=None,
                               machine_top=machine_top,
                               pareto_chef=[],
                               alerte_soir=alerte_soir,
                               alerte_declass=[],
                               projection_active=projection_active)

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

        essences_dures = {'Bilinga', 'Iroko'}
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

    # P1-1 cockpit décisionnel
    statut_global = _statut_global(trs_moyen, alertes)
    pareto_chef = pareto_arrets(equipes)[:3]

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
                           tracabilite=tracabilite,
                           kpi_jour=kpi_jour,
                           postes_du_jour=postes_du_jour,
                           actions_immediates=actions_immediates,
                           alertes=alertes,
                           nb_problemes_ouverts=nb_problemes_ouverts,
                           stats_actions_chef=stats_actions_chef,
                           actions_chef_urgentes=actions_chef_urgentes,
                           actions_chef_a_revoir=actions_chef_a_revoir,
                           priorites_chef=priorites_chef,
                           statut_global=statut_global,
                           machine_top=machine_top,
                           pareto_chef=pareto_chef,
                           alerte_soir=alerte_soir,
                           alerte_declass=_alerte_declassement_essence(equipes),
                           projection_active=projection_active)


@dashboard_bp.route('/chef/v2')
@login_required
@roles_required('chef', 'prod', 'admin')
def vue_chef_v2():
    """Chef Scierie V2 — Vue 1 « LE POINT ».

    Écran de premier regard : verdict + priorités + montants FCFA, puis la
    cascade économique réconciliée (« où part la valeur ») et, à part, la
    lecture des causes probables D/P/Q (attribution indicative, non additive).

    Route parallèle : /chef (vue_chef) reste intacte comme fallback. Cette vue
    ne réécrit aucun moteur — elle réagence des fonctions existantes.
    """
    aujourd_hui = date.today()
    jours = int(request.args.get('jours', 7))

    alertes  = _alertes_chef(aujourd_hui)
    kpi_jour = _kpi_aujourdhui(aujourd_hui)
    nb_problemes_ouverts = Probleme.query.filter(
        Probleme.statut.in_(('ouvert', 'en_analyse'))
    ).count()
    stats_actions_chef = _stats_actions_chef()
    priorites_chef = _priorites_chef(
        aujourd_hui, kpi_jour, alertes, nb_problemes_ouverts, stats_actions_chef
    )[:3]
    machine_top = _machine_prioritaire_recent(aujourd_hui, jours=7)

    equipes = _get_equipes_periode(jours)
    label_periode = f"{jours} derniers jours"

    if not equipes:
        return render_template('chef/v2.html',
                               jours=jours, label_periode=label_periode,
                               equipes_vides=True,
                               statut_global=None, priorites_chef=priorites_chef,
                               machine_top=machine_top, cascade=None,
                               attribution=None, trs_moyen=0,
                               nb_postes=0,
                               nb_problemes_ouverts=nb_problemes_ouverts)

    trs_valeurs = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen   = round(sum(trs_valeurs) / len(trs_valeurs), 1) if trs_valeurs else 0
    statut_global = _statut_global(trs_moyen, alertes)

    # Cascade économique réconciliée (mesure : où part la valeur)
    cascade = cascade_economique(equipes)

    # Attribution causale D/P/Q en POIDS DIAGNOSTIC (%), sur les seuls postes en
    # déficit (cohérent avec la cascade). On affiche des parts, pas des FCFA bruts :
    # le D/P/Q dit QUELLE cause domine, pas un montant qui concurrencerait le manque.
    d = p = q = 0.0
    for e in equipes:
        m = calcule_manque_gagner(e)
        if m['valeur_potentielle'] - m['valeur_reelle_valorisee'] <= 0:
            continue                      # même périmètre que cascade_economique()
        pe = calcule_pertes_equipe(e)
        d += pe['perte_d']; p += pe['perte_p']; q += pe['perte_q']
    total = d + p + q
    if total > 0:
        pct_d = round(d / total * 100)
        pct_p = round(p / total * 100)
        pct_q = 100 - pct_d - pct_p       # résiduel → les 3 parts somment à 100
        attribution = {'pct_d': pct_d, 'pct_p': pct_p, 'pct_q': pct_q}
    else:
        attribution = None

    return render_template('chef/v2.html',
                           jours=jours, label_periode=label_periode,
                           equipes_vides=False,
                           statut_global=statut_global,
                           priorites_chef=priorites_chef,
                           machine_top=machine_top,
                           cascade=cascade,
                           attribution=attribution,
                           trs_moyen=trs_moyen,
                           nb_postes=len(equipes),
                           nb_problemes_ouverts=nb_problemes_ouverts)


@dashboard_bp.route('/prod')
@login_required
@roles_required('prod', 'admin')
def vue_prod():
    """Chef de Production V2 — cockpit autonome sur /dashboard/prod.

    Réutilise temporairement le même moteur et template que vue_chef_v2.
    Route propre à prod : prod@cuf.cm atterrit ici après login,
    pas sur /chef/v2 qui reste la route chef.
    """
    aujourd_hui = date.today()
    jours = int(request.args.get('jours', 7))

    alertes  = _alertes_chef(aujourd_hui)
    kpi_jour = _kpi_aujourdhui(aujourd_hui)
    nb_problemes_ouverts = Probleme.query.filter(
        Probleme.statut.in_(('ouvert', 'en_analyse'))
    ).count()
    stats_actions_chef = _stats_actions_chef()
    priorites_chef = _priorites_chef(
        aujourd_hui, kpi_jour, alertes, nb_problemes_ouverts, stats_actions_chef
    )[:3]
    machine_top = _machine_prioritaire_recent(aujourd_hui, jours=7)

    equipes = _get_equipes_periode(jours)
    label_periode = f"{jours} derniers jours"

    if not equipes:
        return render_template('chef/v2.html',
                               jours=jours, label_periode=label_periode,
                               equipes_vides=True,
                               statut_global=None, priorites_chef=priorites_chef,
                               machine_top=machine_top, cascade=None,
                               attribution=None, trs_moyen=0,
                               nb_postes=0,
                               nb_problemes_ouverts=nb_problemes_ouverts)

    trs_valeurs = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen   = round(sum(trs_valeurs) / len(trs_valeurs), 1) if trs_valeurs else 0
    statut_global = _statut_global(trs_moyen, alertes)

    cascade = cascade_economique(equipes)

    d = p = q = 0.0
    for e in equipes:
        m = calcule_manque_gagner(e)
        if m['valeur_potentielle'] - m['valeur_reelle_valorisee'] <= 0:
            continue
        pe = calcule_pertes_equipe(e)
        d += pe['perte_d']; p += pe['perte_p']; q += pe['perte_q']
    total = d + p + q
    if total > 0:
        pct_d = round(d / total * 100)
        pct_p = round(p / total * 100)
        pct_q = 100 - pct_d - pct_p
        attribution = {'pct_d': pct_d, 'pct_p': pct_p, 'pct_q': pct_q}
    else:
        attribution = None

    return render_template('chef/v2.html',
                           jours=jours, label_periode=label_periode,
                           equipes_vides=False,
                           statut_global=statut_global,
                           priorites_chef=priorites_chef,
                           machine_top=machine_top,
                           cascade=cascade,
                           attribution=attribution,
                           trs_moyen=trs_moyen,
                           nb_postes=len(equipes),
                           nb_problemes_ouverts=nb_problemes_ouverts)


@dashboard_bp.route('/chef/fiches')
@login_required
@roles_required('chef', 'prod', 'admin')
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
@roles_required('chef', 'prod', 'admin')
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
@roles_required('chef', 'prod', 'admin')
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
@roles_required('chef', 'prod', 'admin')
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


def _prefill_action_chef():
    origine_type = request.args.get('origine_type', 'libre').strip() or 'libre'
    if origine_type not in ACTION_CHEF_ORIGINES:
        origine_type = 'libre'

    equipe_id = None
    probleme_id = None
    try:
        equipe_id = int(request.args.get('equipe_id') or 0) or None
    except ValueError:
        equipe_id = None
    try:
        probleme_id = int(request.args.get('probleme_id') or 0) or None
    except ValueError:
        probleme_id = None

    equipe = Equipe.query.get(equipe_id) if equipe_id else None
    probleme = Probleme.query.get(probleme_id) if probleme_id else None
    machine = request.args.get('machine', '').strip()
    origine_label = request.args.get('origine_label', '').strip()
    origine_url = request.args.get('origine_url', '').strip()

    if probleme:
        origine_type = 'probleme'
        origine_label = origine_label or f"Résolution #{probleme.id} - {probleme.titre}"
        origine_url = origine_url or url_for('problemes.rapport', probleme_id=probleme.id)
    elif equipe:
        origine_type = 'fiche'
        origine_label = origine_label or f"Fiche #{equipe.id} - {equipe.date.strftime('%d/%m/%Y')} {equipe.numero_equipe}"
        origine_url = origine_url or url_for('saisie.detail_poste', poste_id=equipe.id)
    elif machine:
        origine_type = 'machine'
        origine_label = origine_label or f"Machine - {machine}"
        origine_url = origine_url or url_for('dashboard.machines_chef', machine=machine)

    titre = request.args.get('titre', '').strip()
    if not titre:
        if machine:
            titre = f"Action sur {machine}"
        elif probleme:
            titre = f"Action suite analyse #{probleme.id}"
        elif equipe:
            titre = f"Action suite fiche #{equipe.id}"
        else:
            titre = "Nouvelle action chef"

    return {
        'titre': titre,
        'type_action': request.args.get('type_action', 'autre').strip() or 'autre',
        'description': request.args.get('description', '').strip(),
        'responsable': request.args.get('responsable', '').strip(),
        'echeance': request.args.get('echeance', '').strip(),
        'origine_type': origine_type,
        'origine_label': origine_label,
        'origine_url': origine_url,
        'equipe_id': equipe.id if equipe else None,
        'probleme_id': probleme.id if probleme else None,
        'machine': machine,
        'statut': 'a_faire',
        'motif_classe_sans_action': '',
        'note_resultat': '',
    }


@dashboard_bp.route('/chef/actions')
@login_required
@roles_required('chef', 'prod', 'admin')
def actions_chef():
    """Liste des décisions et actions suivies par le chef scierie."""
    statut = request.args.get('statut', 'ouvertes').strip()
    origine_type = request.args.get('origine_type', '').strip()
    responsable = request.args.get('responsable', '').strip()
    machine = request.args.get('machine', '').strip()
    efficacite = request.args.get('efficacite', '').strip()
    q = request.args.get('q', '').strip()

    query = ActionChef.query
    today = date.today()
    soon = today + timedelta(days=3)
    if statut == 'ouvertes':
        query = query.filter(ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS))
    elif statut == 'retard':
        query = query.filter(
            ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS),
            ActionChef.echeance < today,
        )
    elif statut == 'aujourd_hui':
        query = query.filter(
            ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS),
            ActionChef.echeance == today,
        )
    elif statut == 'bientot':
        query = query.filter(
            ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS),
            ActionChef.echeance > today,
            ActionChef.echeance <= soon,
        )
    elif statut == 'sans_delai':
        query = query.filter(
            ActionChef.statut.in_(ACTION_CHEF_STATUTS_OUVERTS),
            ActionChef.echeance.is_(None),
        )
    elif statut in ACTION_CHEF_STATUTS:
        query = query.filter(ActionChef.statut == statut)

    if origine_type in ACTION_CHEF_ORIGINES:
        query = query.filter(ActionChef.origine_type == origine_type)

    responsables_tous = _responsables_actions_chef()
    responsables_actions = responsables_tous[:8]
    responsables_connus = [item['responsable'] for item in responsables_tous]
    if responsable:
        query = query.filter(ActionChef.responsable.ilike(responsable))
        if responsable not in responsables_connus:
            responsables_connus.append(responsable)

    machines_toutes = _machines_actions_chef()
    machines_actions = machines_toutes[:8]
    machines_connues = [item['machine'] for item in machines_toutes]
    if machine:
        query = query.filter(ActionChef.machine.ilike(machine))
        if machine not in machines_connues:
            machines_connues.append(machine)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            ActionChef.titre.ilike(like),
            ActionChef.description.ilike(like),
            ActionChef.responsable.ilike(like),
            ActionChef.origine_label.ilike(like),
            ActionChef.machine.ilike(like),
        ))

    actions = query.order_by(
        ActionChef.echeance.is_(None),
        ActionChef.echeance.asc(),
        ActionChef.cree_le.desc(),
    ).all()
    lignes_actions = [_ligne_action_chef(a, inclure_evenements=True) for a in actions]
    niveaux_efficacite = ('efficaces', 'observation', 'a_surveiller', 'a_revoir')
    if efficacite in niveaux_efficacite:
        def correspond_efficacite(ligne):
            bilan = ligne.get('bilan_efficacite') or {}
            niveau = bilan.get('niveau')
            if efficacite == 'efficaces':
                return niveau in ('amelioration', 'stable')
            return niveau == efficacite

        lignes_actions = [ligne for ligne in lignes_actions if correspond_efficacite(ligne)]
    else:
        efficacite = ''

    return render_template(
        'chef/actions.html',
        actions=lignes_actions,
        stats=_stats_actions_chef(),
        stats_boucle=_stats_boucle_amelioration_actions_chef(),
        efficacite_par_machine=_efficacite_actions_par_machine(limite=8),
        responsables_actions=responsables_actions,
        responsables_connus=sorted(responsables_connus, key=lambda item: item.lower()),
        machines_actions=machines_actions,
        machines_connues=sorted(machines_connues, key=lambda item: item.lower()),
        filtres={
            'statut': statut,
            'origine_type': origine_type,
            'responsable': responsable,
            'machine': machine,
            'efficacite': efficacite,
            'q': q,
        },
        statuts=ACTION_CHEF_STATUTS,
        origines=ACTION_CHEF_ORIGINES,
        types_action=ACTION_CHEF_TYPES,
    )


@dashboard_bp.route('/chef/actions/nouvelle', methods=['GET', 'POST'])
@login_required
@roles_required('chef', 'prod', 'admin')
def nouvelle_action_chef():
    """Création d'une action légère de pilotage."""
    valeurs = _prefill_action_chef()
    responsables_suggeres = _suggestions_responsables_action_chef(valeurs.get('responsable'))

    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        type_action = request.form.get('type_action', 'autre').strip()
        description = request.form.get('description', '').strip()
        responsable = request.form.get('responsable', '').strip()
        echeance = _parse_date_action(request.form.get('echeance'))
        statut = request.form.get('statut', 'a_faire').strip()
        motif = request.form.get('motif_classe_sans_action', '').strip()
        note_resultat = request.form.get('note_resultat', '').strip()
        origine_type = request.form.get('origine_type', 'libre').strip()

        if type_action not in dict(ACTION_CHEF_TYPES):
            type_action = 'autre'
        if statut not in ACTION_CHEF_STATUTS:
            statut = 'a_faire'
        if origine_type not in ACTION_CHEF_ORIGINES:
            origine_type = 'libre'

        erreurs = []
        if len(titre) < 4:
            erreurs.append("Donnez un titre clair à l'action.")
        if len(description) < 10:
            erreurs.append("Décrivez l'action à mener en au moins 10 caractères.")
        if len(responsable) < 2:
            erreurs.append("Indiquez un responsable, même sous forme simple : Maintenance, Chef parc, Chef équipe.")
        if statut == 'classe_sans_action' and len(motif) < 10:
            erreurs.append("Le motif est obligatoire pour classer sans action.")
        if statut == 'fait' and len(note_resultat) < 5:
            erreurs.append("Notez brièvement le résultat obtenu avant de marquer l'action comme faite.")

        try:
            equipe_id = int(request.form.get('equipe_id') or 0) or None
        except ValueError:
            equipe_id = None
        try:
            probleme_id = int(request.form.get('probleme_id') or 0) or None
        except ValueError:
            probleme_id = None

        if erreurs:
            for erreur in erreurs:
                flash(erreur, 'danger')
            valeurs.update(request.form.to_dict())
            valeurs['equipe_id'] = equipe_id
            valeurs['probleme_id'] = probleme_id
            valeurs['echeance'] = request.form.get('echeance', '')
            return render_template(
                'chef/action_form.html',
                action=valeurs,
                types_action=ACTION_CHEF_TYPES,
                statuts=ACTION_CHEF_STATUTS,
                origines=ACTION_CHEF_ORIGINES,
                responsables_suggeres=_suggestions_responsables_action_chef(responsable),
            )

        action = ActionChef(
            titre=titre,
            type_action=type_action,
            description=description,
            responsable=responsable,
            echeance=echeance,
            statut=statut,
            motif_classe_sans_action=motif if statut == 'classe_sans_action' else None,
            note_resultat=note_resultat if statut == 'fait' else None,
            origine_type=origine_type,
            origine_label=request.form.get('origine_label', '').strip() or None,
            origine_url=request.form.get('origine_url', '').strip() or None,
            equipe_id=equipe_id,
            probleme_id=probleme_id,
            machine=request.form.get('machine', '').strip() or None,
            cree_par_id=current_user.id,
            termine_le=datetime.utcnow() if statut in ('fait', 'abandonne', 'classe_sans_action') else None,
        )
        db.session.add(action)
        note_evenement = note_resultat if statut == 'fait' else (
            motif if statut == 'classe_sans_action' else "Action créée."
        )
        _tracer_transition_action_chef(action, statut, note=note_evenement)
        db.session.commit()
        flash("Action chef créée. Elle restera visible jusqu'à son traitement.", 'success')
        return redirect(url_for('dashboard.actions_chef'))

    return render_template(
        'chef/action_form.html',
        action=valeurs,
        types_action=ACTION_CHEF_TYPES,
        statuts=ACTION_CHEF_STATUTS,
        origines=ACTION_CHEF_ORIGINES,
        responsables_suggeres=responsables_suggeres,
    )


@dashboard_bp.route('/chef/actions/<int:action_id>/statut', methods=['POST'])
@login_required
@roles_required('chef', 'prod', 'admin')
def changer_statut_action_chef(action_id):
    """Mise à jour rapide du statut d'une action."""
    action = ActionChef.query.get_or_404(action_id)
    statut = request.form.get('statut', '').strip()
    motif = request.form.get('motif_classe_sans_action', '').strip()
    note_resultat = request.form.get('note_resultat', '').strip()

    if statut not in ACTION_CHEF_STATUTS:
        flash("Statut d'action invalide.", 'danger')
        return redirect(url_for('dashboard.actions_chef'))
    if statut == 'classe_sans_action' and len(motif) < 10:
        flash("Motif obligatoire pour classer une action sans suite.", 'danger')
        return redirect(url_for('dashboard.actions_chef'))
    if statut == 'fait' and len(note_resultat) < 5:
        flash("Notez brièvement le résultat obtenu avant de marquer l'action comme faite.", 'danger')
        return redirect(request.referrer or url_for('dashboard.actions_chef'))

    ancien_statut = action.statut
    action.statut = statut
    action.motif_classe_sans_action = motif if statut == 'classe_sans_action' else None
    if statut == 'fait':
        action.note_resultat = note_resultat
    elif ancien_statut == 'fait':
        action.note_resultat = None
    action.termine_le = datetime.utcnow() if statut in ('fait', 'abandonne', 'classe_sans_action') else None
    note_evenement = note_resultat if statut == 'fait' else (
        motif if statut == 'classe_sans_action' else None
    )
    if ancien_statut != statut or note_evenement:
        _tracer_transition_action_chef(
            action,
            statut,
            note=note_evenement,
            ancien_statut=ancien_statut,
        )
    db.session.commit()
    flash("Statut de l'action mis à jour.", 'success')
    return redirect(request.referrer or url_for('dashboard.actions_chef'))


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
@roles_required('chef', 'prod', 'admin')
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
    prix_essences_acc = {}  # P0-4 : prix de valorisation réellement utilisé par essence
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
            # P0-4 : prix effectif (snapshot figé à la soumission) pondéré par volume
            vol_pr = (pr.volume_conforme or 0) + (pr.volume_declass or 0)
            if vol_pr > 0:
                acc = prix_essences_acc.setdefault(pr.essence, {'val': 0.0, 'vol': 0.0})
                acc['val'] += _prix_production(pr) * vol_pr
                acc['vol'] += vol_pr
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

    # P0-4 — Prix de valorisation réellement utilisés sur la période (snapshots
    # figés à la soumission), consultables par le chef pour justifier les FCFA.
    prix_essences = sorted(
        ({'essence': ess, 'prix': int(round(acc['val'] / acc['vol']))}
         for ess, acc in prix_essences_acc.items() if acc['vol'] > 0),
        key=lambda x: x['essence']
    )

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
                           prix_essences=prix_essences,
                           par_shift=par_shift,
                           pareto=pareto[:10],
                           nb_equipes=len(equipes))


@dashboard_bp.route('/export/excel')
@login_required
@roles_required('chef', 'prod', 'admin')
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

"""
Cumuls et deltas par horizon temporel — wood_pilot.

Produit la vue exécutive PDG : pour chaque horizon (jour, semaine, mois, année),
calcule les indicateurs clés sur la période courante ET sur la période précédente
de même durée, puis fournit un delta relatif coloré.

Référence : Laine (2024), Kankkunen & Holopainen (2024) — les dashboards exécutifs
efficaces affichent toujours valeur courante + delta vs période précédente,
jamais juste la valeur seule. Sans delta, le PDG ne peut pas piloter une trajectoire.
"""
from datetime import date, timedelta
from ..models import Equipe, STATUTS_ANALYSES
from .trs import manque_a_gagner_agrege


_STATUTS_ANALYSES = STATUTS_ANALYSES


def _bornes_horizons(reference):
    """
    Pour une date de référence, renvoie les bornes des 4 horizons.
    Les périodes précédentes ont la même longueur (en jours) que les courantes,
    sauf le mois et l'année qui prennent le mois/année calendaire précédent complet.

    Retourne : dict[horizon -> (courant_debut, courant_fin, prec_debut, prec_fin)]
    Bornes inclusives à gauche, exclusives à droite (compatibles avec ORM).
    """
    aujourd_hui = reference
    hier = aujourd_hui - timedelta(days=1)

    # Semaine ISO : lundi = 0, dimanche = 6
    lundi_courant = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    lundi_precedent = lundi_courant - timedelta(days=7)
    dimanche_precedent = lundi_courant  # exclusif

    # Mois courant : 1er du mois → demain (pour inclure aujourd'hui)
    premier_mois = aujourd_hui.replace(day=1)
    # Mois précédent complet
    if premier_mois.month == 1:
        premier_mois_prec = premier_mois.replace(year=premier_mois.year - 1, month=12)
    else:
        premier_mois_prec = premier_mois.replace(month=premier_mois.month - 1)

    # Année courante : 1er janvier → demain
    premier_janvier = date(aujourd_hui.year, 1, 1)
    premier_janvier_prec = date(aujourd_hui.year - 1, 1, 1)

    demain = aujourd_hui + timedelta(days=1)

    return {
        'jour': {
            'label': aujourd_hui.strftime('%d/%m'),
            'label_prec': hier.strftime('%d/%m'),
            'courant_debut': aujourd_hui, 'courant_fin': demain,
            'prec_debut':    hier,        'prec_fin':    aujourd_hui,
        },
        'semaine': {
            'label': f"Sem. {aujourd_hui.isocalendar()[1]}",
            'label_prec': f"Sem. {lundi_precedent.isocalendar()[1]}",
            'courant_debut': lundi_courant,   'courant_fin': demain,
            'prec_debut':    lundi_precedent, 'prec_fin':    dimanche_precedent,
        },
        'mois': {
            'label': aujourd_hui.strftime('%b %Y'),
            'label_prec': premier_mois_prec.strftime('%b %Y'),
            'courant_debut': premier_mois,      'courant_fin': demain,
            'prec_debut':    premier_mois_prec, 'prec_fin':    premier_mois,
        },
        'annee': {
            'label': str(aujourd_hui.year),
            'label_prec': str(aujourd_hui.year - 1),
            'courant_debut': premier_janvier,      'courant_fin': demain,
            'prec_debut':    premier_janvier_prec, 'prec_fin':    premier_janvier,
        },
    }


def cumul_periode(date_debut, date_fin):
    """
    Calcule les indicateurs clés sur une période [date_debut, date_fin).
    Retourne dict : volume_conforme, trs_moyen, manque_a_gagner, nb_postes.
    """
    equipes = Equipe.query.filter(
        Equipe.date >= date_debut, Equipe.date < date_fin,
        Equipe.statut.in_(_STATUTS_ANALYSES)
    ).all()

    nb_postes = len(equipes)
    if nb_postes == 0:
        return {
            'volume_conforme': 0.0,
            'trs_moyen':       None,
            'manque_a_gagner': 0.0,
            'nb_postes':       0,
        }

    volume = sum(e.volume_conforme for e in equipes)
    trs_vals = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen = (sum(trs_vals) / len(trs_vals)) if trs_vals else None

    manque = manque_a_gagner_agrege(equipes).get('manque_a_gagner_estime', 0.0)

    return {
        'volume_conforme': round(volume, 1),
        'trs_moyen':       round(trs_moyen, 1) if trs_moyen is not None else None,
        'manque_a_gagner': manque,
        'nb_postes':       nb_postes,
    }


def calcule_delta(courant, precedent, inverse=False):
    """
    Calcule le delta relatif entre une valeur courante et une valeur précédente.
    Retourne dict : pct, direction, couleur, label.

    inverse=True : pour les indicateurs où une baisse est positive
                   (ex. manque à gagner : baisser = vert).

    Conventions :
      - courant ou precedent None  → direction='na'
      - precedent = 0              → direction='na' (évite +∞ trompeur)
      - |pct| < 2                  → direction='stable' (gris)
      - sinon                      → direction='up' ou 'down' selon signe
    """
    if courant is None or precedent is None or precedent == 0:
        return {
            'pct':       None,
            'direction': 'na',
            'couleur':   'muted',
            'label':     'N/A',
        }

    pct = round((courant - precedent) / precedent * 100, 1)

    if abs(pct) < 2:
        return {
            'pct':       pct,
            'direction': 'stable',
            'couleur':   'muted',
            'label':     f"{pct:+.1f}%",
        }

    if pct > 0:
        direction = 'up'
        couleur   = 'danger' if inverse else 'success'
    else:
        direction = 'down'
        couleur   = 'success' if inverse else 'danger'

    return {
        'pct':       pct,
        'direction': direction,
        'couleur':   couleur,
        'label':     f"{pct:+.1f}%",
    }


def vue_executive_pdg(reference=None):
    """
    Retourne la vue exécutive complète : 4 horizons × 4 indicateurs + deltas.
    Format prêt à être consommé par le template pdg/dashboard.html.
    """
    if reference is None:
        reference = date.today()

    bornes = _bornes_horizons(reference)
    resultat = {}

    for horizon, b in bornes.items():
        courant   = cumul_periode(b['courant_debut'], b['courant_fin'])
        precedent = cumul_periode(b['prec_debut'],    b['prec_fin'])

        resultat[horizon] = {
            'label':      b['label'],
            'label_prec': b['label_prec'],
            'courant':    courant,
            'precedent':  precedent,
            'deltas': {
                'volume_conforme': calcule_delta(
                    courant['volume_conforme'], precedent['volume_conforme']),
                'trs_moyen': calcule_delta(
                    courant['trs_moyen'], precedent['trs_moyen']),
                'manque_a_gagner': calcule_delta(
                    courant['manque_a_gagner'], precedent['manque_a_gagner'],
                    inverse=True),  # manque baisse = vert
                'nb_postes': calcule_delta(
                    courant['nb_postes'], precedent['nb_postes']),
            },
        }

    return resultat

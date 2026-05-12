"""
Contrôles qualité de saisie — Wood_Pilot_Ebolowa.

Détecte des anomalies non-bloquantes après soumission d'une équipe.
Les seuils sont paramétrables via la table Parametre.

Référence : Mncwango & Mdunge (2025) — la validation douce
(alerte + confirmation) produit une meilleure qualité de données
qu'une validation stricte qui pousse à contourner le contrôle.

Codes des règles :
  R1 — TRS bas sans arrêt déclaré (oubli probable des arrêts)
  R2 — Arrêt long sans commentaire (cause non documentée)
  R3 — Déclassé excessif (problème qualité matière ou réglage)
  R4 — Volume incohérent (poste produit 0 m³ sans explication)
"""
from ..models import Parametre


def _seuil(cle, defaut):
    try:
        return float(Parametre.get(cle, str(defaut)))
    except (TypeError, ValueError):
        return float(defaut)


def detecte_anomalies(equipe):
    """
    Retourne la liste des anomalies détectées pour une équipe.
    Chaque anomalie : dict avec code, niveau, icon, titre, description, suggestion.
    Liste vide si aucune anomalie ou si l'équipe est encore en brouillon.
    """
    if not equipe or equipe.statut == 'brouillon':
        return []

    anomalies = []

    seuil_trs         = _seuil('seuil_trs_anomalie',               40)
    seuil_arret_long  = _seuil('seuil_arret_long_minutes',         60)
    seuil_comment_min = _seuil('seuil_arret_long_commentaire_min', 10)
    seuil_declass_pct = _seuil('seuil_declass_pct',                30)

    # R1 — TRS bas sans arrêt déclaré
    if (equipe.trs_global is not None
            and equipe.trs_global < seuil_trs
            and equipe.duree_totale_arrets == 0):
        anomalies.append({
            'code': 'R1',
            'niveau': 'warning',
            'icon': 'bi-exclamation-triangle',
            'titre': f"TRS {equipe.trs_global}% mais aucun arrêt déclaré",
            'description': (
                f"Le TRS est inférieur à {int(seuil_trs)}% sans qu'aucun arrêt machine "
                "ne soit déclaré. Cela suggère que les arrêts du poste n'ont pas été "
                "saisis ou qu'une cadence anormale n'a pas été expliquée."
            ),
            'suggestion': "Revoir la feuille de relevé : un TRS bas s'explique presque toujours par des arrêts.",
        })

    # R2 — Arrêt long sans commentaire
    for arret in equipe.arrets:
        if arret.duree_min and arret.duree_min >= seuil_arret_long:
            commentaire = (arret.notes or '').strip()
            if len(commentaire) < seuil_comment_min:
                anomalies.append({
                    'code': 'R2',
                    'niveau': 'warning',
                    'icon': 'bi-chat-square-text',
                    'titre': f"Arrêt long de {arret.duree_min} min sur {arret.machine} sans commentaire",
                    'description': (
                        f"Un arrêt de {arret.duree_min} minutes ({arret.cause}) a été déclaré "
                        f"mais le commentaire est manquant ou trop court "
                        f"(moins de {int(seuil_comment_min)} caractères). "
                        "Un arrêt long mérite une explication pour permettre une analyse causale."
                    ),
                    'suggestion': "Ajouter un commentaire qui décrit la cause réelle (ex. roulement HS, attente pièce, panne électrique).",
                })

    # R3 — Déclassé excessif
    if equipe.volume_sorti > 0:
        pct_declass = (equipe.volume_declass / equipe.volume_sorti) * 100
        if pct_declass > seuil_declass_pct:
            anomalies.append({
                'code': 'R3',
                'niveau': 'warning',
                'icon': 'bi-tree',
                'titre': f"Volume déclassé élevé ({round(pct_declass, 1)}%)",
                'description': (
                    f"{equipe.volume_declass} m³ déclassés sur {equipe.volume_sorti} m³ "
                    f"sortis, soit {round(pct_declass, 1)}% — au-dessus du seuil "
                    f"de {int(seuil_declass_pct)}%. Cela peut signaler un problème "
                    "de réglage des scies, une matière première de qualité dégradée, "
                    "ou une erreur de classement."
                ),
                'suggestion': "Vérifier le réglage des scies et la qualité des grumes du poste.",
            })

    # R4 — Volume incohérent (poste sans production sans arrêt total)
    if equipe.volume_sorti == 0 and equipe.duree_totale_arrets < 480:
        anomalies.append({
            'code': 'R4',
            'niveau': 'danger',
            'icon': 'bi-x-octagon',
            'titre': "Aucune production déclarée",
            'description': (
                f"Aucun mètre cube sorti mais seulement {equipe.duree_totale_arrets} min "
                "d'arrêts déclarés sur un poste de 480 min. Soit la production a été "
                "oubliée, soit l'arrêt total du poste n'a pas été enregistré."
            ),
            'suggestion': "Vérifier la saisie des volumes ou ajouter un arrêt couvrant le poste entier.",
        })

    return anomalies


def compte_anomalies_periode(equipes):
    """
    Compte les postes avec au moins une anomalie sur une liste d'équipes.
    Retourne dict : nb_postes_concernes, nb_anomalies_total, par_code.
    """
    nb_postes = 0
    nb_total = 0
    par_code = {'R1': 0, 'R2': 0, 'R3': 0, 'R4': 0}
    for e in equipes:
        a = detecte_anomalies(e)
        if a:
            nb_postes += 1
            nb_total += len(a)
            for anomalie in a:
                par_code[anomalie['code']] = par_code.get(anomalie['code'], 0) + 1
    return {
        'nb_postes_concernes': nb_postes,
        'nb_anomalies_total':  nb_total,
        'par_code':            par_code,
    }

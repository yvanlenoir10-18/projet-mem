"""
Contrôles qualité de saisie — wood_pilot.

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
  R5 — Arrêt avec horaire invalide ou durée nulle
  R6 — Chevauchement d'arrêts sur la même machine
  R7 — Créneau essence incomplet ou invalide
  R8 — Chevauchement des créneaux d'essences
"""
from ..models import Parametre


def _seuil(cle, defaut):
    try:
        return float(Parametre.get(cle, str(defaut)))
    except (TypeError, ValueError):
        return float(defaut)


def _minutes(hhmm):
    try:
        h, m = map(int, hhmm.split(':'))
    except (AttributeError, ValueError):
        return None
    if h < 0 or h > 23 or m < 0 or m > 59:
        return None
    return h * 60 + m


def _fmt(minutes):
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


def _chevauchements_par_groupe(elements, cle_groupe, cle_label):
    """Retourne les chevauchements entre intervalles valides d'un même groupe."""
    groupes = {}
    for element in elements:
        debut = _minutes(element.heure_debut)
        fin = _minutes(element.heure_fin)
        if debut is None or fin is None or fin <= debut:
            continue
        groupe = cle_groupe(element)
        groupes.setdefault(groupe, []).append((debut, fin, cle_label(element)))

    chevauchements = []
    for groupe, intervalles in groupes.items():
        intervalles.sort(key=lambda item: (item[0], item[1]))
        for precedent, courant in zip(intervalles, intervalles[1:]):
            debut_prec, fin_prec, label_prec = precedent
            debut_courant, fin_courant, label_courant = courant
            if debut_courant < fin_prec:
                chevauchements.append({
                    'groupe': groupe,
                    'label_1': label_prec,
                    'label_2': label_courant,
                    'debut': _fmt(max(debut_prec, debut_courant)),
                    'fin': _fmt(min(fin_prec, fin_courant)),
                })
    return chevauchements


def detecte_anomalies(equipe, inclure_brouillon=False):
    """
    Retourne la liste des anomalies détectées pour une équipe.
    Chaque anomalie : dict avec code, niveau, icon, titre, description, suggestion.
    Liste vide si aucune anomalie. Les brouillons sont ignorés par défaut,
    sauf pour l'écran de vérification avant soumission.
    """
    if not equipe or (equipe.statut == 'brouillon' and not inclure_brouillon):
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
        if getattr(equipe, 'aucun_arret_confirme', False):
            titre = f"TRS {equipe.trs_global}% malgré aucun arrêt confirmé"
            description = (
                f"L'opérateur a confirmé qu'il n'y a eu aucun arrêt, mais le TRS reste "
                f"inférieur à {int(seuil_trs)}%. Le problème vient probablement des volumes, "
                "de la cadence ou d'une information terrain incomplète."
            )
            suggestion = "Vérifier les volumes, les créneaux d'essence et la cadence réelle du poste."
        else:
            titre = f"TRS {equipe.trs_global}% mais aucun arrêt déclaré"
            description = (
                f"Le TRS est inférieur à {int(seuil_trs)}% sans qu'aucun arrêt machine "
                "ne soit déclaré ni confirmé. Cela suggère que les arrêts du poste n'ont "
                "pas été saisis ou qu'une cadence anormale n'a pas été expliquée."
            )
            suggestion = "Revoir la feuille de relevé : ajouter les arrêts ou confirmer explicitement aucun arrêt."
        anomalies.append({
            'code': 'R1',
            'niveau': 'warning',
            'icon': 'bi-exclamation-triangle',
            'titre': titre,
            'description': description,
            'suggestion': suggestion,
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

    # R5 — Arrêt avec horaire invalide ou durée nulle
    for arret in equipe.arrets:
        debut = _minutes(arret.heure_debut)
        fin = _minutes(arret.heure_fin)
        if debut is None or fin is None:
            anomalies.append({
                'code': 'R5',
                'niveau': 'danger',
                'icon': 'bi-clock',
                'titre': f"Horaire invalide sur {arret.machine}",
                'description': (
                    f"L'arrêt {arret.machine} ({arret.cause}) contient un horaire non lisible : "
                    f"{arret.heure_debut} → {arret.heure_fin}. Le calcul de durée devient fragile."
                ),
                'suggestion': "Corriger l'heure de début et l'heure de fin avec le format HH:MM.",
            })
        elif fin <= debut:
            anomalies.append({
                'code': 'R5',
                'niveau': 'danger',
                'icon': 'bi-clock',
                'titre': f"Arrêt à durée nulle ou négative sur {arret.machine}",
                'description': (
                    f"L'arrêt {arret.machine} ({arret.cause}) va de {arret.heure_debut} "
                    f"à {arret.heure_fin}. L'heure de fin doit être après l'heure de début."
                ),
                'suggestion': "Vérifier la feuille terrain : l'arrêt doit avoir une durée réelle positive.",
            })

    # R6 — Deux arrêts se chevauchent sur la même machine
    chevauchements_arrets = _chevauchements_par_groupe(
        equipe.arrets,
        cle_groupe=lambda a: a.machine,
        cle_label=lambda a: a.cause,
    )
    for chev in chevauchements_arrets:
        anomalies.append({
            'code': 'R6',
            'niveau': 'danger',
            'icon': 'bi-intersect',
            'titre': f"Deux arrêts se chevauchent sur {chev['groupe']}",
            'description': (
                f"Sur {chev['groupe']}, les arrêts « {chev['label_1']} » et "
                f"« {chev['label_2']} » se chevauchent entre {chev['debut']} "
                f"et {chev['fin']}. Une même machine ne peut pas être arrêtée "
                "deux fois en parallèle pour deux causes différentes."
            ),
            'suggestion': "Fusionner les deux arrêts si c'est la même cause, ou corriger les heures.",
        })

    # R7 — Créneau essence incomplet ou invalide
    for prod in equipe.productions:
        debut = _minutes(prod.heure_debut)
        fin = _minutes(prod.heure_fin)
        if bool(prod.heure_debut) != bool(prod.heure_fin):
            anomalies.append({
                'code': 'R7',
                'niveau': 'danger',
                'icon': 'bi-hourglass-split',
                'titre': f"Créneau incomplet pour {prod.essence}",
                'description': (
                    f"La ligne {prod.essence} contient seulement une partie du créneau "
                    f"({prod.heure_debut or 'début manquant'} → {prod.heure_fin or 'fin manquante'}). "
                    "Le TRS par essence ne peut pas être expliqué correctement."
                ),
                'suggestion': "Renseigner l'heure de début et l'heure de fin de traitement de l'essence.",
            })
        elif prod.heure_debut and prod.heure_fin and (debut is None or fin is None):
            anomalies.append({
                'code': 'R7',
                'niveau': 'danger',
                'icon': 'bi-hourglass-split',
                'titre': f"Horaire d'essence invalide pour {prod.essence}",
                'description': (
                    f"Le créneau de {prod.essence} n'est pas lisible : "
                    f"{prod.heure_debut} → {prod.heure_fin}."
                ),
                'suggestion': "Corriger le créneau avec le format HH:MM.",
            })
        elif debut is not None and fin is not None and fin <= debut:
            anomalies.append({
                'code': 'R7',
                'niveau': 'danger',
                'icon': 'bi-hourglass-split',
                'titre': f"Créneau d'essence incohérent pour {prod.essence}",
                'description': (
                    f"{prod.essence} est renseigné de {prod.heure_debut} à {prod.heure_fin}. "
                    "L'heure de fin doit être après l'heure de début."
                ),
                'suggestion': "Corriger le créneau de traitement avant d'analyser le TRS par essence.",
            })

    # R8 — Deux essences se chevauchent sur la même ligne de sciage
    chevauchements_essences = _chevauchements_par_groupe(
        equipe.productions,
        cle_groupe=lambda p: 'ligne de sciage',
        cle_label=lambda p: p.essence,
    )
    for chev in chevauchements_essences:
        anomalies.append({
            'code': 'R8',
            'niveau': 'danger',
            'icon': 'bi-layers-half',
            'titre': "Deux créneaux d'essences se chevauchent",
            'description': (
                f"Les essences {chev['label_1']} et {chev['label_2']} se chevauchent "
                f"entre {chev['debut']} et {chev['fin']}. Sur une même ligne de sciage, "
                "une seule essence doit être traitée à la fois."
            ),
            'suggestion': "Corriger les heures ou créer deux séquences séparées si l'essence a été reprise plus tard.",
        })

    return anomalies


def compte_anomalies_periode(equipes):
    """
    Compte les postes avec au moins une anomalie sur une liste d'équipes.
    Retourne dict : nb_postes_concernes, nb_anomalies_total, par_code.
    """
    nb_postes = 0
    nb_total = 0
    par_code = {f'R{i}': 0 for i in range(1, 9)}
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

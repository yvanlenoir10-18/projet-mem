"""
Routes de saisie des équipes de travail.
L'agent administratif entre ici les données d'une équipe (poste 8h).
Une équipe peut contenir plusieurs lignes de production (essences différentes).

Workflow statut :
  brouillon → a_verifier → valide_chef → verrouille
  a_verifier → a_corriger → a_verifier
  Seul l'auteur peut envoyer son brouillon ou une fiche renvoyée.
  Chef/admin valident avant intégration aux tableaux de bord.
  Admin uniquement peut rouvrir une fiche clôturée.
"""
import json
import math
import os
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, abort,
    current_app, send_from_directory,
)
from flask_login import login_required, current_user
from sqlalchemy import and_, func, or_
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from ..models import (
    db, User, Equipe, Production, Arret, AuditCorrection, Parametre, normalise_essence,
    STATUT_A_CORRIGER, STATUT_A_VERIFIER, STATUT_BROUILLON,
    STATUT_VALIDE_CHEF, STATUT_VERROUILLE,
)
from ..utils import roles_required
from ..services.trs import (
    calcule_trs, calcule_pertes_equipe, calcule_manque_gagner,
    calcule_trs_production, couleur_trs,
)
from ..services.controles_saisie import detecte_anomalies
from config import Config

saisie_bp = Blueprint('saisie', __name__, url_prefix='/saisie')

FICHE_PAPIER_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}
FICHE_PAPIER_MIME_TYPES = {
    'pdf': {'application/pdf'},
    'png': {'image/png'},
    'jpg': {'image/jpeg'},
    'jpeg': {'image/jpeg'},
    'webp': {'image/webp'},
}

CORRECTION_CIBLES = [
    ('field-date', 'Date du poste'),
    ('field-equipe', 'Équipe / poste'),
    ('field-effectif', 'Effectif présent'),
    ('field-responsable', 'Responsable du poste'),
    ('field-rempli-par', 'Fiche remplie par'),
    ('bloc-origine', 'Origine / fiche papier'),
    ('bloc-productions', 'Production par essence'),
    ('bloc-arrets', 'Arrêts machine'),
    ('bloc-commentaires', 'Commentaires pour le chef'),
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _verifier_coherence(equipe):
    """P7-V1 — Vérifie la cohérence métier d'une équipe avant envoi/validation.

    Retourne None si tout est cohérent, sinon un message d'erreur explicite.
    Bloquant : empêche l'envoi ou la validation si une incohérence est détectée.
    """
    # Cohérence date : pas de saisie dans le futur
    if equipe.date > date.today():
        return (f"Incohérence : la date du poste ({equipe.date.strftime('%d/%m/%Y')}) "
                f"est dans le futur. Corrigez la date avant d'envoyer la fiche.")

    # Cohérence volume : Σ(conforme + déclassé) ≤ Σ entrée
    total_entree = sum(p.volume_entree for p in equipe.productions)
    total_sorti  = sum(p.volume_conforme + p.volume_declass for p in equipe.productions)
    if total_sorti > total_entree + 0.01:  # tolérance 0.01 m³ pour arrondis
        return (f"Incohérence : volumes sortis ({total_sorti:.2f} m³) supérieurs au volume "
                f"entré ({total_entree:.2f} m³). Vérifiez les saisies de production — "
                f"les déchets doivent être positifs.")

    # Les incohérences horaires sont désormais des alertes non bloquantes
    # dans controles_saisie.detecte_anomalies(), pour respecter le workflow terrain.

    # Cohérence durée arrêts : Σ duree_min ≤ duree_poste
    duree_poste  = float(Parametre.get('duree_poste', 480))
    total_arrets = sum(a.duree_min or 0 for a in equipe.arrets)
    if total_arrets > duree_poste:
        return (f"Incohérence : durée totale d'arrêts ({total_arrets} min) supérieure à "
                f"la durée du poste ({duree_poste:.0f} min). Vérifiez les heures d'arrêt.")

    return None


def _controle_fiche_operateur(equipe):
    """Retourne les points manquants ou à relire avant envoi au chef."""
    bloquants = []
    attentions = []

    if not equipe.productions:
        bloquants.append({
            'titre': "Aucune production saisie",
            'description': "Ajoutez au moins un passage d'essence avec les volumes du poste.",
            'action': "Cliquer sur Modifier puis Ajouter une essence.",
        })
    else:
        for prod in equipe.productions:
            nom = prod.essence or 'Essence sans nom'
            creneau = prod.creneau_traitement
            if not prod.heure_debut or not prod.heure_fin:
                bloquants.append({
                    'titre': f"Créneau manquant pour {nom}",
                    'description': f"Le passage {nom} n'a pas d'heure de début et de fin complète.",
                    'action': "Renseigner les heures de traitement avant l'envoi.",
                })
            if not prod.volume_entree or prod.volume_entree <= 0:
                bloquants.append({
                    'titre': f"Volume entrée manquant pour {nom}",
                    'description': f"Le passage {nom} ({creneau}) n'a pas de volume entrée supérieur à 0 m³.",
                    'action': "Renseigner le volume de grumes entré pour cette essence.",
                })
            elif (prod.volume_conforme + prod.volume_declass) <= 0:
                attentions.append({
                    'titre': f"Aucune sortie utile pour {nom}",
                    'description': f"{nom} a un volume entrée, mais aucun volume conforme ou déclassé.",
                    'action': "Vérifier si le poste a réellement produit 0 m³ utile.",
                })

    if equipe.productions and all((p.volume_entree or 0) <= 0 for p in equipe.productions):
        bloquants.append({
            'titre': "Aucun volume entrée exploitable",
            'description': "Toutes les lignes de production ont un volume entrée nul.",
            'action': "Compléter au moins un volume entrée avant l'envoi.",
        })

    coherence = _verifier_coherence(equipe)
    if coherence:
        bloquants.append({
            'titre': "Incohérence métier",
            'description': coherence,
            'action': "Corriger la fiche avant de l'envoyer au chef.",
        })

    if not equipe.arrets and not equipe.aucun_arret_confirme:
        attentions.append({
            'titre': "Arrêts non confirmés",
            'description': "Aucun arrêt n'est saisi et l'option « Aucun arrêt » n'est pas confirmée.",
            'action': "Ajouter les arrêts ou cliquer sur « Aucun arrêt » dans le formulaire.",
        })
    if equipe.mode_saisie == 'papier' and not equipe.fiche_papier_fichier:
        bloquants.append({
            'titre': "Fiche papier non jointe",
            'description': "La fiche est déclarée comme ressaisie depuis papier, mais aucun scan/photo n'est joint.",
            'action': "Joindre la fiche papier signée avant l'envoi au chef.",
        })
    if equipe.mode_saisie == 'papier' and not equipe.fiche_papier_signee:
        bloquants.append({
            'titre': "Signature papier non confirmée",
            'description': "La fiche vient du papier, mais la case « fiche papier signée » n'est pas cochée.",
            'action': "Cocher la case après contrôle de la fiche terrain signée.",
        })
    if equipe.statut == STATUT_A_CORRIGER and equipe.correction_motif:
        attentions.append({
            'titre': "Correction demandée par le chef",
            'description': "Cette fiche revient d'une correction demandée par le chef.",
            'action': "Relire son message avant de renvoyer la fiche.",
        })

    return {'bloquants': bloquants, 'attentions': attentions}


def _resume_operateur(equipe, controle, anomalies):
    sortie_utile = round(equipe.volume_conforme + equipe.volume_declass, 3)
    if equipe.arrets:
        arrets_label = f"{len(equipe.arrets)} arrêt{'s' if len(equipe.arrets) > 1 else ''} · {equipe.duree_totale_arrets} min"
    elif equipe.aucun_arret_confirme:
        arrets_label = "Aucun arrêt confirmé"
    else:
        arrets_label = "Arrêts non confirmés"

    a_relire = [p['titre'] for p in controle['bloquants']]
    a_relire += [p['titre'] for p in controle['attentions']]
    a_relire += [a.get('titre', a.get('code', 'Alerte')) for a in anomalies[:3]]

    transmis = [
        "Production par essence et créneaux",
        "Volumes entrée, conformes, déclassés",
        "Arrêts machine et commentaires terrain",
    ]
    if equipe.notes:
        transmis.append("Commentaire général pour le chef")
    if equipe.fiche_papier_fichier:
        transmis.append("Fiche papier jointe")

    return {
        'saisi': [
            f"{len(equipe.productions)} passage{'s' if len(equipe.productions) > 1 else ''} d'essence",
            f"{equipe.volume_entree} m³ entrée",
            f"{sortie_utile} m³ sortie utile",
            arrets_label,
        ],
        'a_relire': a_relire or ["Aucun blocage détecté"],
        'transmis': transmis,
    }


def _checklist_verification_operateur(equipe, controle, anomalies):
    """Prépare une checklist visuelle simple pour l'écran de vérification."""
    checklist = []

    if controle['bloquants']:
        checklist.append({
            'etat': 'danger',
            'titre': 'Production à compléter',
            'description': f"{len(controle['bloquants'])} point bloquant avant envoi.",
        })
    elif equipe.productions and (equipe.volume_conforme + equipe.volume_declass) > 0:
        checklist.append({
            'etat': 'success',
            'titre': 'Production complète',
            'description': 'Essences, horaires et volumes utiles sont renseignés.',
        })
    else:
        checklist.append({
            'etat': 'warning',
            'titre': 'Production à relire',
            'description': 'Vérifier que les volumes sortis reflètent bien le poste.',
        })

    if equipe.arrets:
        checklist.append({
            'etat': 'success',
            'titre': 'Arrêts saisis',
            'description': f"{len(equipe.arrets)} arrêt{'s' if len(equipe.arrets) > 1 else ''} transmis au chef.",
        })
    elif equipe.aucun_arret_confirme:
        checklist.append({
            'etat': 'success',
            'titre': 'Aucun arrêt confirmé',
            'description': "L'absence d'arrêt est explicitement confirmée.",
        })
    else:
        checklist.append({
            'etat': 'warning',
            'titre': 'Arrêts à confirmer',
            'description': 'Ajouter les arrêts ou confirmer clairement aucun arrêt.',
        })

    if equipe.mode_saisie == 'papier':
        if equipe.fiche_papier_signee and equipe.fiche_papier_fichier:
            checklist.append({
                'etat': 'success',
                'titre': 'Fiche papier jointe',
                'description': 'La preuve terrain signée accompagne la saisie.',
            })
        else:
            checklist.append({
                'etat': 'danger',
                'titre': 'Fiche papier manquante',
                'description': 'Joindre la fiche signée avant envoi au chef.',
            })
    else:
        checklist.append({
            'etat': 'success',
            'titre': 'Saisie directe',
            'description': "La fiche a été remplie directement dans l'application.",
        })

    arrets_commentes = any((a.notes or '').strip() for a in equipe.arrets)
    if (equipe.notes or '').strip() or arrets_commentes:
        checklist.append({
            'etat': 'success',
            'titre': 'Commentaires prêts',
            'description': 'Les observations terrain seront visibles par le chef.',
        })
    else:
        checklist.append({
            'etat': 'warning',
            'titre': 'Commentaires optionnels',
            'description': 'Ajouter un commentaire si un contexte terrain doit être expliqué.',
        })

    if controle['bloquants']:
        checklist.append({
            'etat': 'danger',
            'titre': 'Envoi bloqué',
            'description': 'Corriger les points rouges avant de transmettre.',
        })
    elif anomalies or controle['attentions']:
        checklist.append({
            'etat': 'warning',
            'titre': 'Envoi possible avec alerte',
            'description': 'Relire les points orange avant de transmettre.',
        })
    else:
        checklist.append({
            'etat': 'success',
            'titre': 'Fiche prête',
            'description': 'La fiche peut être envoyée au chef.',
        })

    return checklist


def _peut_modifier(equipe):
    """Retourne True si l'utilisateur courant peut modifier cette équipe."""
    if equipe.statut in (STATUT_BROUILLON, STATUT_A_CORRIGER):
        return equipe.user_id == current_user.id
    if equipe.statut in (STATUT_A_VERIFIER, STATUT_VALIDE_CHEF) and not equipe.est_verrouille:
        return current_user.role in ('prod', 'admin')
    return False


def _peut_soumettre(equipe):
    return equipe.statut in (STATUT_BROUILLON, STATUT_A_CORRIGER) and equipe.user_id == current_user.id


def _peut_valider_chef(equipe):
    return (
        current_user.role in ('prod', 'admin')
        and equipe.statut == STATUT_A_VERIFIER
        and not equipe.est_verrouille
    )


def _peut_demander_correction(equipe):
    if current_user.role not in ('prod', 'admin'):
        return False
    if equipe.statut not in (STATUT_A_VERIFIER, STATUT_VALIDE_CHEF, STATUT_VERROUILLE):
        return False
    if equipe.est_verrouille and current_user.role != 'admin':
        return False
    return True


def _validation_chef_resume(equipe, anomalies):
    """Prépare une synthèse actionnable pour la page de validation chef."""
    bloquantes = [a for a in anomalies if a.get('niveau') == 'danger']
    avertissements = [a for a in anomalies if a.get('niveau') == 'warning']
    informations = [a for a in anomalies if a.get('niveau') not in ('danger', 'warning')]

    points = [
        {
            'label': 'En-tête',
            'etat': 'ok' if equipe.date and equipe.numero_equipe and equipe.operateur_nom and equipe.effectif else 'warning',
            'texte': f"{equipe.numero_equipe} · {equipe.effectif or 0} personne(s) · {equipe.operateur_nom or 'responsable manquant'}",
        },
        {
            'label': 'Production',
            'etat': 'ok' if equipe.productions and equipe.volume_sorti > 0 else 'danger',
            'texte': f"{len(equipe.productions)} essence(s) · {equipe.volume_conforme} m³ conformes",
        },
        {
            'label': 'Arrêts',
            'etat': 'ok' if equipe.arrets or equipe.aucun_arret_confirme else 'warning',
            'texte': (
                f"{len(equipe.arrets)} arrêt(s) · {equipe.duree_totale_arrets} min"
                if equipe.arrets else
                ("Aucun arrêt confirmé" if equipe.aucun_arret_confirme else "Aucun arrêt non confirmé")
            ),
        },
        {
            'label': 'Papier',
            'etat': 'ok' if equipe.mode_saisie != 'papier' or (equipe.fiche_papier_signee and equipe.fiche_papier_fichier) else 'danger',
            'texte': (
                "Saisie directe"
                if equipe.mode_saisie != 'papier' else
                ("Fiche papier jointe" if equipe.fiche_papier_fichier else "Fiche papier manquante")
            ),
        },
        {
            'label': 'Commentaires',
            'etat': 'ok' if (equipe.notes or any(a.notes for a in equipe.arrets)) else 'warning',
            'texte': "Commentaires présents" if (equipe.notes or any(a.notes for a in equipe.arrets)) else "Aucun commentaire terrain",
        },
    ]

    return {
        'visible': current_user.role in ('prod', 'admin'),
        'bloquantes': bloquantes,
        'avertissements': avertissements,
        'informations': informations,
        'nb_bloquantes': len(bloquantes),
        'nb_avertissements': len(avertissements),
        'peut_valider': _peut_valider_chef(equipe) and not bloquantes,
        'validation_bloquee': bool(bloquantes),
        'points': points,
    }


def _snapshot_equipe(equipe):
    """Photographie lisible des champs métier suivis dans l'audit."""
    return {
        'date': equipe.date.isoformat() if equipe.date else None,
        'poste': equipe.numero_equipe,
        'effectif': equipe.effectif,
        'operateur_nom': equipe.operateur_nom,
        'rempli_par_nom': equipe.rempli_par_nom,
        'mode_saisie': equipe.mode_saisie,
        'fiche_papier_signee': bool(equipe.fiche_papier_signee),
        'fiche_papier_fichier': equipe.fiche_papier_fichier,
        'aucun_arret_confirme': bool(equipe.aucun_arret_confirme),
        'correction_cible': equipe.correction_cible,
        'statut': equipe.statut,
        'notes': equipe.notes,
        'productions': [
            {
                'essence': p.essence,
                'heure_debut': p.heure_debut,
                'heure_fin': p.heure_fin,
                'volume_entree': p.volume_entree,
                'volume_conforme': p.volume_conforme,
                'volume_declass': p.volume_declass,
            }
            for p in equipe.productions
        ],
        'arrets': [
            {
                'machine': a.machine,
                'heure_debut': a.heure_debut,
                'heure_fin': a.heure_fin,
                'duree_min': a.duree_min,
                'duree_prevue_min': a.duree_prevue_min,
                'cause': a.cause,
                'categorie': a.categorie,
                'notes': a.notes,
            }
            for a in equipe.arrets
        ],
    }


def _json_audit(valeur):
    if valeur is None:
        return None
    return json.dumps(valeur, ensure_ascii=False, indent=2, sort_keys=True)


def _audit_correction(equipe, action, ancien_statut, nouveau_statut,
                      motif=None, resume=None, avant=None, apres=None):
    db.session.add(AuditCorrection(
        equipe_id=equipe.id,
        auteur_id=current_user.id,
        action=action,
        auteur_nom=current_user.nom,
        auteur_role=current_user.role,
        ancien_statut=ancien_statut,
        nouveau_statut=nouveau_statut,
        motif=motif,
        resume=resume,
        anciennes_valeurs=_json_audit(avant),
        nouvelles_valeurs=_json_audit(apres),
    ))


def _recalculer_trs(equipe):
    """Recalcule le TRS après synchronisation réelle des productions/arrêts."""
    db.session.flush()
    db.session.expire(equipe, ['productions', 'arrets'])
    return calcule_trs(equipe)


def _mode_saisie_valide(valeur):
    return valeur if valeur in ('directe', 'papier') else 'directe'


def _correction_cible_valide(valeur):
    cibles = {code for code, _label in CORRECTION_CIBLES}
    return valeur if valeur in cibles else 'bloc-productions'


def _libelle_correction_cible(valeur):
    return dict(CORRECTION_CIBLES).get(valeur, 'Production par essence')


def _activer_correction(equipe, motif, cible):
    """Expose le dernier renvoi actif sans remplacer l'audit complet."""
    equipe.correction_motif = motif
    equipe.correction_cible = cible
    equipe.correction_demandee_par = current_user.nom
    equipe.correction_demandee_le = datetime.utcnow()


def _vider_correction_active(equipe):
    """La correction n'est plus active après resoumission au chef."""
    equipe.correction_motif = None
    equipe.correction_cible = None
    equipe.correction_demandee_par = None
    equipe.correction_demandee_le = None


def _texte_obligatoire(valeur, libelle):
    texte = (valeur or '').strip()
    if not texte:
        raise ValueError(f"{libelle} est obligatoire.")
    return texte


def _float_non_negatif(valeur, libelle):
    texte = (valeur or '').strip()
    if not texte:
        return 0.0
    try:
        nombre = float(texte.replace(',', '.'))
    except ValueError as exc:
        raise ValueError(f"{libelle} doit être un nombre.") from exc
    if not math.isfinite(nombre):
        raise ValueError(f"{libelle} doit être un nombre valide.")
    if nombre < 0:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return nombre


def _int_non_negatif(valeur, libelle, defaut=None):
    texte = (valeur or '').strip()
    if not texte:
        if defaut is not None:
            return defaut
        return None
    try:
        nombre = int(texte)
    except ValueError as exc:
        raise ValueError(f"{libelle} doit être un nombre entier.") from exc
    if nombre < 0:
        raise ValueError(f"{libelle} ne peut pas être négatif.")
    return nombre


def _effectif_valide(valeur):
    effectif = _int_non_negatif(valeur, "L'effectif", defaut=10)
    if effectif < 1:
        raise ValueError("L'effectif doit être au moins égal à 1.")
    return effectif


def _categorie_arret_depuis_cause(cause_base):
    cause_base = (cause_base or '').strip()
    for cause in Config.CAUSES_ARRET_PREDEFINIES:
        if cause['cause'] == cause_base:
            return cause.get('categorie') or 'Autre'
    return 'Autre'


def _extension_autorisee(nom_fichier):
    if not nom_fichier or '.' not in nom_fichier:
        return False
    return nom_fichier.rsplit('.', 1)[1].lower() in FICHE_PAPIER_EXTENSIONS


def _signature_fichier_autorisee(fichier, extension):
    """Vérifie la signature binaire minimale du fichier joint."""
    position = fichier.stream.tell()
    entete = fichier.stream.read(16)
    fichier.stream.seek(position)

    signatures = {
        'pdf': entete.startswith(b'%PDF-'),
        'png': entete.startswith(b'\x89PNG\r\n\x1a\n'),
        'jpg': entete.startswith(b'\xff\xd8\xff'),
        'jpeg': entete.startswith(b'\xff\xd8\xff'),
        'webp': entete.startswith(b'RIFF') and entete[8:12] == b'WEBP',
    }
    return signatures.get(extension, False)


def _mime_fichier_autorise(fichier, extension):
    type_mime = (fichier.mimetype or '').lower()
    if not type_mime:
        return True
    return type_mime in FICHE_PAPIER_MIME_TYPES.get(extension, set())


def _dossier_fiches_papier():
    dossier = os.path.join(current_app.instance_path, 'fiches_papier')
    os.makedirs(dossier, exist_ok=True)
    return dossier


def _sauver_fiche_papier(equipe, fichier):
    """Sauvegarde une fiche papier signée jointe à une équipe."""
    if not fichier or not fichier.filename:
        return False
    if not _extension_autorisee(fichier.filename):
        raise ValueError("La fiche papier doit être un PDF ou une image JPG, PNG ou WEBP.")

    nom_original = fichier.filename
    nom_nettoye = secure_filename(nom_original)
    if not nom_nettoye or '.' not in nom_nettoye:
        raise ValueError("Le nom du fichier joint est invalide.")
    extension = nom_nettoye.rsplit('.', 1)[1].lower()
    if not _mime_fichier_autorise(fichier, extension):
        raise ValueError("Le type du fichier joint ne correspond pas à son extension.")
    if not _signature_fichier_autorisee(fichier, extension):
        raise ValueError("Le fichier joint ne semble pas être un PDF ou une image valide.")

    nom_stocke = f"fiche_{equipe.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{extension}"
    fichier.save(os.path.join(_dossier_fiches_papier(), nom_stocke))

    equipe.fiche_papier_fichier = nom_stocke
    equipe.fiche_papier_nom_original = nom_original
    equipe.fiche_papier_chargee_le = datetime.utcnow()
    equipe.fiche_papier_signee = True
    equipe.mode_saisie = 'papier'
    return True


def _extraire_productions_arrets(form):
    """Parse les listes de productions et arrêts depuis le formulaire POST."""
    essences      = form.getlist('prod_essence[]')
    prod_debuts   = form.getlist('prod_heure_debut[]')
    prod_fins     = form.getlist('prod_heure_fin[]')
    vol_entrees   = form.getlist('prod_volume_entree[]')
    vol_conformes = form.getlist('prod_volume_conforme[]')
    vol_declass   = form.getlist('prod_volume_declass[]')

    machines     = form.getlist('arret_machine[]')
    heures_debut = form.getlist('arret_debut[]')
    heures_fin   = form.getlist('arret_fin[]')
    causes       = form.getlist('arret_cause[]')
    details_causes = form.getlist('arret_cause_detail[]')
    categories   = form.getlist('arret_categorie[]')
    durees_prevues = form.getlist('arret_duree_prevue[]')
    notes_arrets = form.getlist('arret_notes[]')

    return (essences, prod_debuts, prod_fins, vol_entrees, vol_conformes, vol_declass,
            machines, heures_debut, heures_fin, causes, details_causes, categories,
            durees_prevues, notes_arrets)


def _minutes_horaire(valeur):
    """Convertit 'HH:MM' en minutes depuis minuit, ou None si invalide."""
    try:
        h, m = map(int, (valeur or '').split(':'))
        return h * 60 + m
    except (ValueError, AttributeError):
        return None


def _chevauchement_productions(essences, prod_debuts, prod_fins):
    """Détecte un chevauchement horaire entre lignes de production.

    La chaîne 4 est une machine unique (la bicoupe traite 100 % du bois) :
    deux essences ne peuvent pas être traitées sur des créneaux qui se
    recouvrent. Renvoie un message décrivant le premier conflit, ou None.
    Les bornes jointives (fin de l'une = début de l'autre) sont autorisées.
    """
    intervalles = []
    for i, essence in enumerate(essences):
        if not essence:
            continue
        debut = _minutes_horaire(prod_debuts[i] if i < len(prod_debuts) else None)
        fin = _minutes_horaire(prod_fins[i] if i < len(prod_fins) else None)
        if debut is None or fin is None or fin <= debut:
            continue
        intervalles.append((debut, fin, essence,
                            prod_debuts[i], prod_fins[i]))
    intervalles.sort()
    couvrant = None
    for it in intervalles:
        if couvrant is not None and it[0] < couvrant[1]:
            return (f"Chevauchement horaire : « {couvrant[2]} » "
                    f"({couvrant[3]}–{couvrant[4]}) et « {it[2]} » "
                    f"({it[3]}–{it[4]}) se recouvrent. La chaîne ne traite "
                    f"qu'une essence à la fois.")
        if couvrant is None or it[1] > couvrant[1]:
            couvrant = it
    return None


def _cause_arret_finale(cause_base, detail):
    """Construit la cause enregistrée à partir du choix rapide et du détail manuel."""
    cause_base = (cause_base or '').strip()
    detail = (detail or '').strip()
    if detail and cause_base == 'Autre':
        return detail
    if detail and cause_base == 'Changement de lame':
        return f"Changement de lame — {detail}"
    return cause_base


def _decode_cause_arret(cause):
    """Prépare l'affichage en modification : choix rapide + précision manuelle."""
    cause = (cause or '').strip()
    causes_connues = {c['cause'] for c in Config.CAUSES_ARRET_PREDEFINIES}
    prefixe = 'Changement de lame — '
    if cause.startswith(prefixe):
        return 'Changement de lame', cause[len(prefixe):].strip()
    if cause in causes_connues:
        return cause, ''
    if cause:
        return 'Autre', cause
    return 'Autre', ''


def _date_filtre(nom):
    valeur = request.args.get(nom, '').strip()
    if not valeur:
        return None
    try:
        return date.fromisoformat(valeur)
    except ValueError:
        return None


def _render_form(equipe=None):
    """Render le formulaire de saisie (création ou modification)."""
    productions_data = []
    arrets_data = []
    if equipe:
        productions_data = [
            {'essence': p.essence,
             'heure_debut': p.heure_debut,
             'heure_fin': p.heure_fin,
             'volume_entree': p.volume_entree,
             'volume_conforme': p.volume_conforme,
             'volume_declass': p.volume_declass}
            for p in equipe.productions
        ]
        arrets_data = [
            {
             'machine': a.machine,
             'heure_debut': a.heure_debut,
             'heure_fin': a.heure_fin,
             'cause': a.cause,
             'cause_base': _decode_cause_arret(a.cause)[0],
             'cause_detail': _decode_cause_arret(a.cause)[1],
             'categorie': a.categorie,
             'duree_prevue_min': a.duree_prevue_min,
             'notes': a.notes}
            for a in equipe.arrets
        ]

    form_action = (
        url_for('saisie.modifier_equipe', equipe_id=equipe.id)
        if equipe else url_for('saisie.nouveau_poste')
    )
    # P7 — Pré-remplissage via query params (lien depuis bannière saisies manquantes)
    date_initiale = request.args.get('date') if not equipe else None
    shift_initial = request.args.get('shift') if not equipe else None
    if shift_initial not in ('Matin', 'Apres-midi'):
        shift_initial = 'Matin'

    # F4 — Capacités théoriques par essence (poka-yoke volume)
    capacites_essences = {}
    for e in Config.ESSENCES:
        val = Parametre.get(f'capacite_{normalise_essence(e)}_h')
        if val:
            capacites_essences[e] = float(val)

    # F5 — Horaires standards par créneau + effectif du dernier poste (préremplissage)
    horaires_creneaux = {
        'Matin': {
            'debut': Parametre.get('shift_matin_debut', '06:00'),
            'fin':   Parametre.get('shift_matin_fin', '14:00'),
        },
        'Apres-midi': {
            'debut': Parametre.get('shift_apresmidi_debut', '14:00'),
            'fin':   Parametre.get('shift_apresmidi_fin', '22:00'),
        },
    }
    effectif_defaut = 10
    if equipe is None:
        derniere = (Equipe.query
                    .filter_by(user_id=current_user.id)
                    .order_by(Equipe.date.desc(), Equipe.cree_le.desc())
                    .first())
        if derniere and derniere.effectif:
            effectif_defaut = derniere.effectif

    return render_template('saisie/formulaire.html',
                           essences=Config.ESSENCES,
                           machines=Config.MACHINES,
                           categories=Config.CATEGORIES_ARRET,
                           causes_arret=Config.CAUSES_ARRET_PREDEFINIES,
                           today=date_initiale or date.today().isoformat(),
                           shift_initial=shift_initial,
                           equipe=equipe,
                           productions_data=productions_data,
                           arrets_data=arrets_data,
                           form_action=form_action,
                           capacites_essences=capacites_essences,
                           horaires_creneaux=horaires_creneaux,
                           effectif_defaut=effectif_defaut)


# ── Création ─────────────────────────────────────────────────────────────────

@saisie_bp.route('/nouveau', methods=['GET', 'POST'])
@login_required
@roles_required('operateur', 'prod', 'admin')
def nouveau_poste():
    """Formulaire de saisie d'une nouvelle équipe — sauvegardée en brouillon."""
    if request.method == 'POST':
        try:
            operateur_nom = _texte_obligatoire(
                request.form.get('operateur_nom'),
                "Le nom du responsable terrain",
            )
            rempli_par_nom = _texte_obligatoire(
                request.form.get('rempli_par_nom') or current_user.nom,
                "Le nom de la personne qui remplit la fiche",
            )

            equipe = Equipe(
                date=date.fromisoformat(request.form['date']),
                numero_equipe=request.form['numero_equipe'],
                effectif=_effectif_valide(request.form.get('effectif', 10)),
                operateur_nom=operateur_nom,
                rempli_par_nom=rempli_par_nom,
                mode_saisie=_mode_saisie_valide(request.form.get('mode_saisie', 'directe')),
                fiche_papier_signee=bool(request.form.get('fiche_papier_signee')),
                aucun_arret_confirme=request.form.get('aucun_arret_confirme') == '1',
                notes=request.form.get('notes', ''),
                statut=STATUT_BROUILLON,
                user_id=current_user.id
            )
            db.session.add(equipe)
            db.session.flush()
            _sauver_fiche_papier(equipe, request.files.get('fiche_papier'))

            (essences, prod_debuts, prod_fins, vol_entrees, vol_conformes, vol_declass,
             machines, heures_debut, heures_fin, causes, details_causes, categories,
             durees_prevues, notes_arrets) = \
                _extraire_productions_arrets(request.form)

            if not essences:
                flash("Au moins une ligne de production est requise.", 'danger')
                db.session.rollback()
                return _render_form()

            conflit_horaire = _chevauchement_productions(essences, prod_debuts, prod_fins)
            if conflit_horaire:
                flash(conflit_horaire, 'danger')
                db.session.rollback()
                return _render_form()

            for i, essence in enumerate(essences):
                # Bug 2 — essence obligatoire si des volumes sont saisis
                ve = (vol_entrees[i] if i < len(vol_entrees) else '').strip().replace(',', '.')
                try:
                    has_volume = float(ve) > 0 if ve else False
                except ValueError:
                    has_volume = bool(ve)
                if not essence and has_volume:
                    flash("Ligne de production incomplète : sélectionnez une essence avant d'entrer les volumes.", 'danger')
                    db.session.rollback()
                    return _render_form()
                if not essence:
                    continue
                prod = Production(
                    equipe_id=equipe.id,
                    essence=essence,
                    heure_debut=prod_debuts[i] if i < len(prod_debuts) and prod_debuts[i] else None,
                    heure_fin=prod_fins[i] if i < len(prod_fins) and prod_fins[i] else None,
                    volume_entree=_float_non_negatif(
                        vol_entrees[i] if i < len(vol_entrees) else '',
                        f"Volume entrée {essence}",
                    ),
                    volume_conforme=_float_non_negatif(
                        vol_conformes[i] if i < len(vol_conformes) else '',
                        f"Volume conforme {essence}",
                    ),
                    volume_declass=_float_non_negatif(
                        vol_declass[i] if i < len(vol_declass) else '',
                        f"Volume déclassé {essence}",
                    ),
                )
                db.session.add(prod)

            if equipe.aucun_arret_confirme:
                machines = []

            for i in range(len(machines)):
                if machines[i] and heures_debut[i] and heures_fin[i] and causes[i]:
                    # Bug 1 — heure_fin doit être strictement après heure_debut
                    if heures_fin[i] <= heures_debut[i]:
                        flash(
                            f"Arrêt {i+1} ({machines[i]}) : l'heure de fin ({heures_fin[i]}) "
                            f"doit être après l'heure de début ({heures_debut[i]}).",
                            'danger'
                        )
                        db.session.rollback()
                        return _render_form()
                    arret = Arret(
                        equipe_id=equipe.id,
                        machine=machines[i],
                        heure_debut=heures_debut[i],
                        heure_fin=heures_fin[i],
                        cause=_cause_arret_finale(
                            causes[i],
                            details_causes[i] if i < len(details_causes) else '',
                        ),
                        categorie=_categorie_arret_depuis_cause(causes[i]),
                        duree_prevue_min=_int_non_negatif(
                            durees_prevues[i] if i < len(durees_prevues) else '',
                            "Durée prévue d'arrêt",
                        ),
                        notes=notes_arrets[i] if i < len(notes_arrets) else None,
                    )
                    arret.calcule_duree()
                    db.session.add(arret)

            _recalculer_trs(equipe)
            db.session.commit()

            if request.form.get('action_apres') == 'verifier':
                flash("Brouillon enregistré. Relisez la fiche avant de l'envoyer au chef.", 'info')
                return redirect(url_for('saisie.verification_equipe', equipe_id=equipe.id))

            flash("Équipe sauvegardée en brouillon. Vérifiez puis envoyez au chef quand les données sont complètes.", 'info')
            return redirect(url_for('saisie.historique'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'enregistrement : {type(e).__name__} — {str(e)}", 'danger')

    return _render_form()


# ── Soumission ────────────────────────────────────────────────────────────────

@saisie_bp.route('/equipe/<int:equipe_id>/verification')
@login_required
@roles_required('operateur', 'prod', 'admin')
def verification_equipe(equipe_id):
    """Écran de contrôle terrain avant envoi au chef."""
    equipe = Equipe.query.get_or_404(equipe_id)
    if not _peut_soumettre(equipe):
        flash("Cette fiche ne peut pas être envoyée par votre compte.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    anomalies = detecte_anomalies(equipe, inclure_brouillon=True)
    controle = _controle_fiche_operateur(equipe)
    points_attention = controle['attentions']
    erreur_bloquante = controle['bloquants'][0]['description'] if controle['bloquants'] else None
    resume_operateur = _resume_operateur(equipe, controle, anomalies)

    resume = {
        'nb_essences': len(equipe.productions),
        'nb_arrets': len(equipe.arrets),
        'volume_entree': equipe.volume_entree,
        'volume_conforme': equipe.volume_conforme,
        'volume_declass': equipe.volume_declass,
        'volume_dechets': equipe.volume_dechets,
        'duree_arrets': equipe.duree_totale_arrets,
        'duree_impact': equipe.duree_arrets_impact,
    }

    return render_template(
        'saisie/verification.html',
        poste=equipe,
        anomalies=anomalies,
        points_attention=points_attention,
        controle=controle,
        erreur_bloquante=erreur_bloquante,
        resume=resume,
        resume_operateur=resume_operateur,
        checklist=_checklist_verification_operateur(equipe, controle, anomalies),
        peut_soumettre_final=erreur_bloquante is None,
    )


@saisie_bp.route('/equipe/<int:equipe_id>/soumettre', methods=['POST'])
@login_required
@roles_required('operateur', 'prod', 'admin')
def soumettre_equipe(equipe_id):
    """Transition brouillon/a_corriger → a_verifier. Fige les prix et recalcule le TRS final."""
    equipe = Equipe.query.get_or_404(equipe_id)
    ancien_statut = equipe.statut
    avant = _snapshot_equipe(equipe)

    if not _peut_soumettre(equipe):
        flash("Vous n'êtes pas autorisé à envoyer cette fiche.", 'danger')
        return redirect(url_for('saisie.historique'))

    controle = _controle_fiche_operateur(equipe)
    if controle['bloquants']:
        flash(f"Impossible d'envoyer : {controle['bloquants'][0]['description']}", 'danger')
        return redirect(url_for('saisie.verification_equipe', equipe_id=equipe_id))

    # Figer les prix au moment de la soumission (première fois uniquement)
    for prod in equipe.productions:
        if prod.prix_snapshot is None:
            prix = float(Parametre.get(f'prix_{normalise_essence(prod.essence)}', 0))
            prod.prix_snapshot = prix if prix > 0 else None

    action = 'resoumission' if ancien_statut == STATUT_A_CORRIGER else 'soumission_initiale'
    motif_correction = equipe.correction_motif if action == 'resoumission' else None
    equipe.statut    = STATUT_A_VERIFIER
    equipe.soumis_le = datetime.utcnow()
    if motif_correction:
        equipe.modifie_le = datetime.utcnow()
        equipe.modifie_par = current_user.nom
    _recalculer_trs(equipe)
    if action == 'resoumission':
        _vider_correction_active(equipe)
    apres = _snapshot_equipe(equipe)
    resume = (
        "Fiche corrigée et renvoyée au chef pour validation."
        if action == 'resoumission'
        else "Fiche envoyée au chef pour validation."
    )
    _audit_correction(
        equipe,
        action=action,
        ancien_statut=ancien_statut,
        nouveau_statut=equipe.statut,
        motif=motif_correction,
        resume=resume,
        avant=avant,
        apres=apres,
    )
    db.session.commit()

    flash(
        "Fiche envoyée au chef pour vérification. Elle est visible dans son suivi du jour, "
        "mais pas encore intégrée aux analyses validées.",
        'success'
    )
    return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))


# ── Modification ──────────────────────────────────────────────────────────────

@saisie_bp.route('/equipe/<int:equipe_id>/modifier', methods=['GET', 'POST'])
@login_required
@roles_required('operateur', 'prod', 'admin')
def modifier_equipe(equipe_id):
    """Formulaire pré-rempli pour modifier une fiche autorisée."""
    equipe = Equipe.query.get_or_404(equipe_id)
    ancien_statut = equipe.statut
    avant = _snapshot_equipe(equipe)

    if not _peut_modifier(equipe):
        flash("Cette équipe ne peut plus être modifiée.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    if request.method == 'POST':
        try:
            # Conserver les prix_snapshot existants avant suppression
            snapshots = {p.essence: p.prix_snapshot for p in equipe.productions}

            # Supprimer anciennes productions et arrêts
            for p in list(equipe.productions):
                db.session.delete(p)
            for a in list(equipe.arrets):
                db.session.delete(a)
            db.session.flush()

            # Mettre à jour les champs de l'équipe
            equipe.date           = date.fromisoformat(request.form['date'])
            equipe.numero_equipe  = request.form['numero_equipe']
            equipe.effectif       = _effectif_valide(request.form.get('effectif', 10))
            equipe.operateur_nom  = _texte_obligatoire(
                request.form.get('operateur_nom'),
                "Le nom du responsable terrain",
            )
            equipe.rempli_par_nom = _texte_obligatoire(
                request.form.get('rempli_par_nom') or current_user.nom,
                "Le nom de la personne qui remplit la fiche",
            )
            equipe.mode_saisie    = _mode_saisie_valide(request.form.get('mode_saisie', 'directe'))
            equipe.fiche_papier_signee = bool(request.form.get('fiche_papier_signee'))
            equipe.aucun_arret_confirme = request.form.get('aucun_arret_confirme') == '1'
            equipe.notes          = request.form.get('notes', '')

            _sauver_fiche_papier(equipe, request.files.get('fiche_papier'))

            (essences, prod_debuts, prod_fins, vol_entrees, vol_conformes, vol_declass,
             machines, heures_debut, heures_fin, causes, details_causes, categories,
             durees_prevues, notes_arrets) = \
                _extraire_productions_arrets(request.form)

            if not essences:
                flash("Au moins une ligne de production est requise.", 'danger')
                db.session.rollback()
                return _render_form(equipe)

            conflit_horaire = _chevauchement_productions(essences, prod_debuts, prod_fins)
            if conflit_horaire:
                flash(conflit_horaire, 'danger')
                db.session.rollback()
                return _render_form(equipe)

            for i, essence in enumerate(essences):
                # Bug 2 — essence obligatoire si des volumes sont saisis
                ve = (vol_entrees[i] if i < len(vol_entrees) else '').strip().replace(',', '.')
                try:
                    has_volume = float(ve) > 0 if ve else False
                except ValueError:
                    has_volume = bool(ve)
                if not essence and has_volume:
                    flash("Ligne de production incomplète : sélectionnez une essence avant d'entrer les volumes.", 'danger')
                    db.session.rollback()
                    return _render_form(equipe)
                if not essence:
                    continue
                prod = Production(
                    equipe_id=equipe.id,
                    essence=essence,
                    heure_debut=prod_debuts[i] if i < len(prod_debuts) and prod_debuts[i] else None,
                    heure_fin=prod_fins[i] if i < len(prod_fins) and prod_fins[i] else None,
                    volume_entree=_float_non_negatif(
                        vol_entrees[i] if i < len(vol_entrees) else '',
                        f"Volume entrée {essence}",
                    ),
                    volume_conforme=_float_non_negatif(
                        vol_conformes[i] if i < len(vol_conformes) else '',
                        f"Volume conforme {essence}",
                    ),
                    volume_declass=_float_non_negatif(
                        vol_declass[i] if i < len(vol_declass) else '',
                        f"Volume déclassé {essence}",
                    ),
                    prix_snapshot=snapshots.get(essence),
                )
                db.session.add(prod)

            if equipe.aucun_arret_confirme:
                machines = []

            for i in range(len(machines)):
                if machines[i] and heures_debut[i] and heures_fin[i] and causes[i]:
                    # Bug 1 — heure_fin doit être strictement après heure_debut
                    if heures_fin[i] <= heures_debut[i]:
                        flash(
                            f"Arrêt {i+1} ({machines[i]}) : l'heure de fin ({heures_fin[i]}) "
                            f"doit être après l'heure de début ({heures_debut[i]}).",
                            'danger'
                        )
                        db.session.rollback()
                        return _render_form(equipe)
                    arret = Arret(
                        equipe_id=equipe.id,
                        machine=machines[i],
                        heure_debut=heures_debut[i],
                        heure_fin=heures_fin[i],
                        cause=_cause_arret_finale(
                            causes[i],
                            details_causes[i] if i < len(details_causes) else '',
                        ),
                        categorie=_categorie_arret_depuis_cause(causes[i]),
                        duree_prevue_min=_int_non_negatif(
                            durees_prevues[i] if i < len(durees_prevues) else '',
                            "Durée prévue d'arrêt",
                        ),
                        notes=notes_arrets[i] if i < len(notes_arrets) else None,
                    )
                    arret.calcule_duree()
                    db.session.add(arret)

            _recalculer_trs(equipe)

            # Trace de modification sur les équipes déjà entrées dans le circuit de validation
            if equipe.statut in (
                STATUT_A_VERIFIER, STATUT_A_CORRIGER,
                STATUT_VALIDE_CHEF,
            ):
                equipe.modifie_le  = datetime.utcnow()
                equipe.modifie_par = current_user.nom
                _audit_correction(
                    equipe,
                    action='modification',
                    ancien_statut=ancien_statut,
                    nouveau_statut=equipe.statut,
                    motif=equipe.correction_motif,
                    resume="Fiche modifiée après entrée dans le circuit de validation.",
                    avant=avant,
                    apres=_snapshot_equipe(equipe),
                )

            db.session.commit()
            if request.form.get('action_apres') == 'verifier' and _peut_soumettre(equipe):
                flash("Modifications enregistrées. Relisez la fiche avant de l'envoyer au chef.", 'info')
                return redirect(url_for('saisie.verification_equipe', equipe_id=equipe.id))

            flash("Équipe mise à jour.", 'success')
            return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification : {type(e).__name__} — {str(e)}", 'danger')

    return _render_form(equipe)


# ── Duplication de structure ─────────────────────────────────────────────────

@saisie_bp.route('/poste/<int:poste_id>/dupliquer', methods=['POST'])
@login_required
@roles_required('operateur', 'prod', 'admin')
def dupliquer_poste(poste_id):
    """Crée un brouillon à partir de la structure d'une fiche existante."""
    source = Equipe.query.get_or_404(poste_id)
    if current_user.role == 'operateur' and source.user_id != current_user.id:
        abort(403)

    nouveau = Equipe(
        date=date.today(),
        numero_equipe=source.numero_equipe,
        effectif=source.effectif,
        operateur_nom=current_user.nom,
        rempli_par_nom=current_user.nom,
        mode_saisie='directe',
        fiche_papier_signee=False,
        aucun_arret_confirme=False,
        notes='',
        statut=STATUT_BROUILLON,
        user_id=current_user.id,
    )
    db.session.add(nouveau)
    db.session.flush()

    for prod in source.productions:
        db.session.add(Production(
            equipe_id=nouveau.id,
            essence=prod.essence,
            heure_debut=prod.heure_debut,
            heure_fin=prod.heure_fin,
            volume_entree=0,
            volume_conforme=0,
            volume_declass=0,
        ))

    db.session.commit()
    flash(
        "Structure reprise : une nouvelle fiche a été créée pour aujourd'hui. Vérifiez la date, puis complétez les volumes, arrêts et commentaires.",
        'warning',
    )
    return redirect(url_for('saisie.modifier_equipe', equipe_id=nouveau.id, reprise='1'))


# ── Validation Chef / Clôture / Réouverture ─────────────────────────────────

@saisie_bp.route('/equipe/<int:equipe_id>/valider-chef', methods=['POST'])
@login_required
@roles_required('prod', 'admin')
def valider_chef_equipe(equipe_id):
    """Transition a_verifier → valide_chef. Les dashboards intègrent alors la fiche."""
    equipe = Equipe.query.get_or_404(equipe_id)
    ancien_statut = equipe.statut
    avant = _snapshot_equipe(equipe)
    if not _peut_valider_chef(equipe):
        flash("Cette fiche ne peut pas être validée par votre compte.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    erreur = _verifier_coherence(equipe)
    if erreur:
        flash(erreur, 'danger')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    anomalies = detecte_anomalies(equipe)
    bloquantes = [a for a in anomalies if a.get('niveau') == 'danger']
    if bloquantes:
        titres = ', '.join(a.get('titre', a.get('code', 'anomalie')) for a in bloquantes[:3])
        flash(f"Validation impossible : {len(bloquantes)} anomalie(s) bloquante(s) à corriger. {titres}", 'danger')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    avertissements = [a for a in anomalies if a.get('niveau') == 'warning']
    motif_avertissements = request.form.get('motif_validation_avertissements', '').strip()
    if avertissements:
        if request.form.get('confirmer_avertissements') != '1':
            flash("Cette fiche contient des avertissements. Confirmez la validation consciente avant de continuer.", 'warning')
            return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))
        if len(motif_avertissements) < 10:
            flash("Expliquez brièvement pourquoi vous validez malgré les avertissements.", 'danger')
            return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    equipe.statut = STATUT_VALIDE_CHEF
    equipe.modifie_le = datetime.utcnow()
    equipe.modifie_par = current_user.nom
    _recalculer_trs(equipe)
    action_audit = 'validation_avec_avertissement' if avertissements else 'validation_chef'
    resume_audit = (
        f"Fiche validée malgré {len(avertissements)} avertissement(s) : {motif_avertissements}"
        if avertissements else
        "Fiche validée par le chef et intégrée aux tableaux de bord."
    )
    _audit_correction(
        equipe,
        action=action_audit,
        ancien_statut=ancien_statut,
        nouveau_statut=equipe.statut,
        motif=motif_avertissements or None,
        resume=resume_audit,
        avant=avant,
        apres=_snapshot_equipe(equipe),
    )
    db.session.commit()

    flash("Fiche validée par le chef. Elle est maintenant comptée dans les tableaux de bord.", 'success')
    return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

@saisie_bp.route('/equipe/<int:equipe_id>/verrouiller', methods=['POST'])
@login_required
@roles_required('prod', 'admin')
def verrouiller_equipe(equipe_id):
    """Transition valide_chef → verrouille (chef ou admin)."""
    equipe = Equipe.query.get_or_404(equipe_id)
    if equipe.statut != STATUT_VALIDE_CHEF:
        flash("Seule une fiche validée par le chef peut être clôturée.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))
    equipe.statut = STATUT_VERROUILLE
    db.session.commit()
    flash("Fiche clôturée — données définitives.", 'secondary')
    return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))


@saisie_bp.route('/equipe/<int:equipe_id>/deverrouiller', methods=['POST'])
@login_required
@roles_required('admin')
def deverrouiller_equipe(equipe_id):
    """Transition verrouille → valide_chef (admin uniquement)."""
    equipe = Equipe.query.get_or_404(equipe_id)
    if not equipe.est_verrouille:
        flash("Cette fiche n'est pas clôturée.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))
    equipe.statut = STATUT_VALIDE_CHEF
    db.session.commit()
    flash("Fiche rouverte. Elle reste validée chef et peut être corrigée.", 'info')
    return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))


@saisie_bp.route('/equipe/<int:equipe_id>/demander-correction', methods=['POST'])
@login_required
@roles_required('prod', 'admin')
def demander_correction(equipe_id):
    """Transition a_verifier/valide_chef/verrouille → a_corriger avec motif lisible."""
    equipe = Equipe.query.get_or_404(equipe_id)
    ancien_statut = equipe.statut
    avant = _snapshot_equipe(equipe)
    if not _peut_demander_correction(equipe):
        flash("Cette fiche ne peut pas être renvoyée à corriger.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    motif = request.form.get('motif_correction', '').strip()
    if len(motif) < 5:
        flash("Ajoutez un motif de correction clair avant de renvoyer la fiche.", 'danger')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    cible = _correction_cible_valide(request.form.get('correction_cible'))
    equipe.statut = STATUT_A_CORRIGER
    _activer_correction(equipe, motif, cible)
    equipe.modifie_le = datetime.utcnow()
    equipe.modifie_par = current_user.nom
    libelle_cible = _libelle_correction_cible(cible)
    _audit_correction(
        equipe,
        action='renvoi_correction',
        ancien_statut=ancien_statut,
        nouveau_statut=equipe.statut,
        motif=motif,
        resume=f"Fiche renvoyée à l'opérateur pour correction : {libelle_cible}.",
        avant=avant,
        apres=_snapshot_equipe(equipe),
    )
    db.session.commit()

    flash(f"Fiche renvoyée à corriger à l'opérateur. Zone indiquée : {libelle_cible}.", 'warning')
    return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))


# ── Consultation ──────────────────────────────────────────────────────────────

def _stats_operateur(user_id):
    """Stats de progression d'un opérateur, agrégées sur ses Equipe (aucune table dédiée).

    Composant partagé par l'accueil et l'historique : même calcul, même rendu.
    Ne compte que les postes effectivement soumis et porteurs d'un TRS, pour que
    la progression reflète des données validées, pas des brouillons.
    """
    # Charge toutes les equipes de l'opérateur en un seul appel DB.
    toutes = Equipe.query.filter_by(user_id=user_id).all()

    soumises = [
        e for e in toutes
        if e.statut in ('soumis', 'a_verifier', 'verrouille', 'valide_chef') and e.trs_global
    ]
    nb = len(soumises)
    trs_moyen = round(sum(e.trs_global for e in soumises) / nb, 1) if nb else None
    meilleur = max((e.trs_global for e in soumises), default=None)

    ref = date.today()
    recentes = [e for e in soumises if e.date >= ref - timedelta(days=7)]
    precedentes = [e for e in soumises
                   if ref - timedelta(days=14) <= e.date < ref - timedelta(days=7)]
    trs_rec = round(sum(e.trs_global for e in recentes) / len(recentes), 1) if recentes else None
    trs_prec = round(sum(e.trs_global for e in precedentes) / len(precedentes), 1) if precedentes else None
    if trs_rec and trs_prec:
        tendance = 'up' if trs_rec > trs_prec else ('down' if trs_rec < trs_prec else 'flat')
    else:
        tendance = 'flat'

    # F6 — Objectif hebdomadaire de régularité (nb de postes saisis, jamais le TRS → pas de biais H3)
    # Compte tous les postes soumis cette semaine, y compris ceux renvoyés en correction
    # (l'opérateur A soumis la fiche : elle compte pour la régularité même si renvoyée).
    debut_semaine = ref - timedelta(days=ref.weekday())  # lundi de la semaine courante
    postes_semaine = sum(
        1 for e in toutes
        if e.statut in ('soumis', 'a_verifier', 'a_corriger', 'verrouille', 'valide_chef')
        and e.date >= debut_semaine
    )
    try:
        objectif_hebdo = int(Parametre.get('objectif_postes_semaine', 5))
    except (TypeError, ValueError):
        objectif_hebdo = 5
    objectif_pct = min(100, round(postes_semaine / objectif_hebdo * 100)) if objectif_hebdo else 0

    # F6b — Record personnel : le dernier poste soumis établit-il un nouveau meilleur TRS ?
    record_battu = False
    record_trs = None
    if nb >= 2:
        derniere = max(soumises, key=lambda e: (e.date, e.cree_le or datetime.min))
        autres = [e.trs_global for e in soumises if e is not derniere]
        if autres and derniere.trs_global is not None and derniere.trs_global > max(autres):
            record_battu = True
            record_trs = derniere.trs_global

    return {
        'nb_equipes': nb,
        'trs_moyen': trs_moyen,
        'meilleur_trs': meilleur,
        'trs_recent': trs_rec,
        'tendance': tendance,
        'postes_semaine': postes_semaine,
        'objectif_hebdo': objectif_hebdo,
        'objectif_pct': objectif_pct,
        'objectif_atteint': postes_semaine >= objectif_hebdo,
        'record_battu': record_battu,
        'record_trs': record_trs,
    }


@saisie_bp.route('/accueil')
@login_required
@roles_required('operateur', 'prod', 'admin')
def accueil_operateur():
    """Accueil terrain orienté collecte pour le profil opérateur."""
    base_query = Equipe.query.filter(Equipe.user_id == current_user.id)
    brouillons = base_query.filter(Equipe.statut == STATUT_BROUILLON).order_by(
        Equipe.date.desc(), Equipe.cree_le.desc()
    ).all()
    a_corriger = base_query.filter(Equipe.statut == STATUT_A_CORRIGER).order_by(
        Equipe.date.desc(), Equipe.cree_le.desc()
    ).all()
    a_verifier = base_query.filter(Equipe.statut == STATUT_A_VERIFIER).order_by(
        Equipe.date.desc(), Equipe.cree_le.desc()
    ).all()
    fiches_recentes = base_query.order_by(
        Equipe.date.desc(), Equipe.cree_le.desc()
    ).limit(5).all()

    aujourd_hui = date.today()
    fiches_aujourdhui = base_query.filter(Equipe.date == aujourd_hui).count()
    shift_suggere = 'Matin' if datetime.now().hour < 12 else 'Apres-midi'

    dernier_brouillon = brouillons[0] if brouillons else None
    fiche_prioritaire = a_corriger[0] if a_corriger else dernier_brouillon

    stats_operateur = _stats_operateur(current_user.id) if current_user.role == 'operateur' else None

    return render_template(
        'saisie/accueil_operateur.html',
        brouillons=brouillons,
        a_corriger=a_corriger,
        a_verifier=a_verifier,
        fiches_recentes=fiches_recentes,
        dernier_brouillon=dernier_brouillon,
        fiche_prioritaire=fiche_prioritaire,
        fiches_aujourdhui=fiches_aujourdhui,
        date_jour=aujourd_hui,
        shift_suggere=shift_suggere,
        stats_operateur=stats_operateur,
    )


@saisie_bp.route('/historique')
@login_required
def historique():
    query = Equipe.query
    peut_voir_toutes = current_user.role in ('prod', 'admin', 'pdg')
    filtres = {
        'jour': request.args.get('jour', '').strip(),
        'user_id': request.args.get('user_id', '').strip(),
        'statut': request.args.get('statut', '').strip(),
        'essence': request.args.get('essence', '').strip(),
        'poste': request.args.get('poste', '').strip(),
        'mode_saisie': request.args.get('mode_saisie', '').strip(),
        'commentaires': request.args.get('commentaires', '').strip(),
    }

    if current_user.role == 'operateur':
        query = query.filter(Equipe.user_id == current_user.id)
        filtres['user_id'] = ''
    elif filtres['user_id']:
        try:
            query = query.filter(Equipe.user_id == int(filtres['user_id']))
        except ValueError:
            filtres['user_id'] = ''

    jour = _date_filtre('jour')
    if jour:
        query = query.filter(Equipe.date == jour)

    if filtres['statut'] == 'valide':
        query = query.filter(Equipe.statut.in_((
            STATUT_VALIDE_CHEF, STATUT_VERROUILLE,
        )))
    elif filtres['statut'] in (
        STATUT_BROUILLON, STATUT_A_VERIFIER, STATUT_A_CORRIGER,
        STATUT_VALIDE_CHEF, STATUT_VERROUILLE,
    ):
        query = query.filter(Equipe.statut == filtres['statut'])

    if filtres['essence'] in Config.ESSENCES:
        query = query.filter(Equipe.productions.any(Production.essence == filtres['essence']))

    if filtres['poste'] in ('Matin', 'Apres-midi'):
        query = query.filter(Equipe.numero_equipe == filtres['poste'])

    if filtres['mode_saisie'] in ('directe', 'papier'):
        query = query.filter(Equipe.mode_saisie == filtres['mode_saisie'])

    if filtres['commentaires'] == '1':
        query = query.filter(or_(
            and_(Equipe.notes.isnot(None), func.trim(Equipe.notes) != ''),
            Equipe.arrets.any(and_(Arret.notes.isnot(None), func.trim(Arret.notes) != '')),
        ))

    equipes = query.order_by(Equipe.date.desc(), Equipe.numero_equipe).all()
    utilisateurs = []
    if peut_voir_toutes:
        utilisateurs = User.query.filter(User.role.in_(('operateur', 'prod', 'admin'))).order_by(User.nom.asc()).all()

    # P12 — pré-calcul des anomalies pour drapeau dans la liste
    anomalies_par_poste = {e.id: detecte_anomalies(e) for e in equipes}

    # Bug 5 / F1 — Stats motivantes opérateur (composant partagé avec l'accueil)
    stats_op = _stats_operateur(current_user.id) if current_user.role == 'operateur' else None

    return render_template('saisie/historique.html',
                           postes=equipes,
                           anomalies_par_poste=anomalies_par_poste,
                           afficher_indicateurs=current_user.role in ('prod', 'pdg', 'admin'),
                           filtres=filtres,
                           utilisateurs=utilisateurs,
                           peut_voir_toutes=peut_voir_toutes,
                           essences=Config.ESSENCES,
                           stats_operateur=stats_op)


@saisie_bp.route('/poste/<int:poste_id>')
@login_required
def detail_poste(poste_id):
    equipe = Equipe.query.get_or_404(poste_id)
    if current_user.role == 'operateur' and equipe.user_id != current_user.id:
        abort(403)

    afficher_economie = current_user.role in ('prod', 'pdg', 'admin')
    pertes = calcule_pertes_equipe(equipe) if afficher_economie else None
    manque = calcule_manque_gagner(equipe) if afficher_economie else None  # P11 — indicateur principal
    couleur = couleur_trs(equipe.trs_global)
    anomalies = detecte_anomalies(equipe)  # P12 — contrôles qualité
    trs_productions = {
        prod.id: calcule_trs_production(prod)
        for prod in equipe.productions
    }
    return render_template('saisie/detail.html',
                           poste=equipe,
                           pertes=pertes,
                           manque=manque,
                           trs_productions=trs_productions,
                           perte_fcfa=pertes['total'] if pertes else 0,
                           afficher_economie=afficher_economie,
                           afficher_indicateurs=current_user.role in ('prod', 'pdg', 'admin'),
                           couleur_trs=couleur,
                           anomalies=anomalies,
                           validation_chef=_validation_chef_resume(equipe, anomalies),
                           correction_cibles=CORRECTION_CIBLES,
                           peut_soumettre=_peut_soumettre(equipe),
                           peut_valider_chef=_peut_valider_chef(equipe),
                           peut_modifier=_peut_modifier(equipe),
                           peut_verrouiller=(
                               equipe.statut == STATUT_VALIDE_CHEF
                               and not equipe.est_verrouille
                               and current_user.role in ('prod', 'admin')
                           ),
                           peut_deverrouiller=(
                               equipe.est_verrouille
                               and current_user.role == 'admin'
                           ),
                           peut_dupliquer=(
                               current_user.role in ('prod', 'admin')
                               or equipe.user_id == current_user.id
                           ) and current_user.role in ('operateur', 'prod', 'admin'),
                           peut_demander_correction=_peut_demander_correction(equipe))


# ── Feuille de relevé imprimable ──────────────────────────────────────────────

@saisie_bp.route('/feuille-releve')
@login_required
def feuille_releve():
    date_str = request.args.get('date', date.today().isoformat())
    shift    = request.args.get('shift', 'Matin')
    try:
        date_obj = date.fromisoformat(date_str)
        date_fmt = date_obj.strftime('%d/%m/%Y')
    except ValueError:
        date_obj = date.today()
        date_fmt = date_obj.strftime('%d/%m/%Y')
        date_str = date_obj.isoformat()
    return render_template(
        'saisie/feuille_releve.html',
        date_str=date_str,
        date_fmt=date_fmt,
        shift=shift,
        essences=Config.ESSENCES,
        machines=Config.MACHINES,
        categories=Config.CATEGORIES_ARRET,
        causes_arret=Config.CAUSES_ARRET_PREDEFINIES,
    )


@saisie_bp.route('/poste/<int:poste_id>/fiche')
@login_required
def fiche_poste(poste_id):
    """Fiche remplie imprimable/téléchargeable, sans indicateurs économiques."""
    equipe = Equipe.query.get_or_404(poste_id)
    if current_user.role == 'operateur' and equipe.user_id != current_user.id:
        abort(403)

    return render_template(
        'saisie/fiche_poste.html',
        poste=equipe,
        machines=Config.MACHINES,
        categories=Config.CATEGORIES_ARRET,
        causes_arret=Config.CAUSES_ARRET_PREDEFINIES,
        generation=datetime.now(),
    )


@saisie_bp.route('/poste/<int:poste_id>/fiche-papier')
@login_required
def fiche_papier_jointe(poste_id):
    """Ouvre la fiche papier signée jointe (PDF/photo)."""
    equipe = Equipe.query.get_or_404(poste_id)
    if current_user.role == 'operateur' and equipe.user_id != current_user.id:
        abort(403)
    if not equipe.fiche_papier_fichier:
        abort(404)

    return send_from_directory(
        _dossier_fiches_papier(),
        equipe.fiche_papier_fichier,
        as_attachment=False,
        download_name=equipe.fiche_papier_nom_original or equipe.fiche_papier_fichier,
    )


# ── Suppression ───────────────────────────────────────────────────────────────

@saisie_bp.route('/poste/<int:poste_id>/supprimer', methods=['POST'])
@login_required
def supprimer_poste(poste_id):
    equipe = Equipe.query.get_or_404(poste_id)
    if equipe.statut != STATUT_BROUILLON:
        flash("Seul un brouillon peut être supprimé.", 'warning')
        return redirect(url_for('saisie.historique'))
    if equipe.user_id != current_user.id:
        abort(403)
    db.session.delete(equipe)
    db.session.commit()
    flash("Brouillon supprimé.", 'info')
    return redirect(url_for('saisie.historique'))

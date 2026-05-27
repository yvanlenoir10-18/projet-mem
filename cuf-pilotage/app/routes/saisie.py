"""
Routes de saisie des équipes de travail.
L'agent administratif entre ici les données d'une équipe (poste 8h).
Une équipe peut contenir plusieurs lignes de production (essences différentes).

Workflow statut :
  brouillon → soumis → verrouillé
  Seul l'auteur peut soumettre son brouillon.
  Chef/admin peuvent modifier un soumis non verrouillé (avec trace).
  Admin uniquement peut déverrouiller.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, date
from ..models import db, Equipe, Production, Arret, Parametre, normalise_essence
from ..utils import roles_required
from ..services.trs import calcule_trs, calcule_pertes_equipe, calcule_manque_gagner, couleur_trs
from ..services.controles_saisie import detecte_anomalies
from config import Config

saisie_bp = Blueprint('saisie', __name__, url_prefix='/saisie')


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_float(val):
    """Accepte la virgule française ('12,5') et le point ('12.5') comme séparateur."""
    if not val:
        return 0.0
    return float(str(val).replace(',', '.').strip())


def _form_data_brut():
    """Extrait les données brutes du POST pour re-affichage après erreur (Bug 3)."""
    essences      = request.form.getlist('prod_essence[]')
    vol_entrees   = request.form.getlist('prod_volume_entree[]')
    vol_conformes = request.form.getlist('prod_volume_conforme[]')
    vol_declass   = request.form.getlist('prod_volume_declass[]')
    machines      = request.form.getlist('arret_machine[]')
    heures_debut  = request.form.getlist('arret_debut[]')
    heures_fin    = request.form.getlist('arret_fin[]')
    causes        = request.form.getlist('arret_cause[]')
    categories    = request.form.getlist('arret_categorie[]')

    prods = [
        {'essence':         essences[i]      if i < len(essences)      else '',
         'volume_entree':   vol_entrees[i]   if i < len(vol_entrees)   else '',
         'volume_conforme': vol_conformes[i] if i < len(vol_conformes) else '',
         'volume_declass':  vol_declass[i]   if i < len(vol_declass)   else '0'}
        for i in range(len(essences))
    ]
    arrs = [
        {'machine':     machines[i]     if i < len(machines)     else '',
         'heure_debut': heures_debut[i] if i < len(heures_debut) else '',
         'heure_fin':   heures_fin[i]   if i < len(heures_fin)   else '',
         'cause':       causes[i]       if i < len(causes)       else '',
         'categorie':   categories[i]   if i < len(categories)   else ''}
        for i in range(len(machines))
    ]
    return prods, arrs


def _verifier_coherence(equipe):
    """P7-V1 — Vérifie la cohérence métier d'une équipe avant soumission.

    Retourne None si tout est cohérent, sinon un message d'erreur explicite.
    Bloquant : empêche la soumission si une incohérence est détectée.
    """
    # Cohérence date : pas de saisie dans le futur
    if equipe.date > date.today():
        return (f"Incohérence : la date du poste ({equipe.date.strftime('%d/%m/%Y')}) "
                f"est dans le futur. Corrigez la date avant de soumettre.")

    # Cohérence volume : Σ(conforme + déclassé) ≤ Σ entrée
    total_entree = sum(p.volume_entree for p in equipe.productions)
    total_sorti  = sum(p.volume_conforme + p.volume_declass for p in equipe.productions)
    if total_sorti > total_entree + 0.01:  # tolérance 0.01 m³ pour arrondis
        return (f"Incohérence : volumes sortis ({total_sorti:.2f} m³) supérieurs au volume "
                f"entré ({total_entree:.2f} m³). Vérifiez les saisies de production — "
                f"les déchets doivent être positifs.")

    # Cohérence durée arrêts : Σ duree_min ≤ duree_poste
    duree_poste  = float(Parametre.get('duree_poste', 480))
    total_arrets = sum(a.duree_min or 0 for a in equipe.arrets)
    if total_arrets > duree_poste:
        return (f"Incohérence : durée totale d'arrêts ({total_arrets} min) supérieure à "
                f"la durée du poste ({duree_poste:.0f} min). Vérifiez les heures d'arrêt.")

    return None


def _peut_modifier(equipe):
    """Retourne True si l'utilisateur courant peut modifier cette équipe."""
    if equipe.statut == 'brouillon':
        return equipe.user_id == current_user.id
    if equipe.statut == 'soumis' and not equipe.est_verrouille:
        return current_user.role in ('chef', 'admin')
    return False


def _peut_soumettre(equipe):
    return equipe.statut == 'brouillon' and equipe.user_id == current_user.id


def _extraire_productions_arrets(form):
    """Parse les listes de productions et arrêts depuis le formulaire POST."""
    essences      = form.getlist('prod_essence[]')
    vol_entrees   = form.getlist('prod_volume_entree[]')
    vol_conformes = form.getlist('prod_volume_conforme[]')
    vol_declass   = form.getlist('prod_volume_declass[]')

    machines     = form.getlist('arret_machine[]')
    heures_debut = form.getlist('arret_debut[]')
    heures_fin   = form.getlist('arret_fin[]')
    causes       = form.getlist('arret_cause[]')
    categories   = form.getlist('arret_categorie[]')

    return (essences, vol_entrees, vol_conformes, vol_declass,
            machines, heures_debut, heures_fin, causes, categories)


def _render_form(equipe=None, productions_data=None, arrets_data=None):
    """Render le formulaire de saisie (création ou modification)."""
    if productions_data is None and equipe:
        productions_data = [
            {'essence': p.essence,
             'volume_entree': p.volume_entree,
             'volume_conforme': p.volume_conforme,
             'volume_declass': p.volume_declass}
            for p in equipe.productions
        ]
    if arrets_data is None and equipe:
        arrets_data = [
            {'machine': a.machine,
             'heure_debut': a.heure_debut,
             'heure_fin': a.heure_fin,
             'cause': a.cause,
             'categorie': a.categorie}
            for a in equipe.arrets
        ]
    productions_data = productions_data or []
    arrets_data      = arrets_data or []

    form_action = (
        url_for('saisie.modifier_equipe', equipe_id=equipe.id)
        if equipe else url_for('saisie.nouveau_poste')
    )
    # P7 — Pré-remplissage via query params (lien depuis bannière saisies manquantes)
    date_initiale = request.args.get('date') if not equipe else None
    shift_initial = request.args.get('shift') if not equipe else None
    if shift_initial not in ('Matin', 'Apres-midi'):
        shift_initial = 'Matin'

    return render_template('saisie/formulaire.html',
                           essences=Config.ESSENCES,
                           machines=Config.MACHINES,
                           categories=Config.CATEGORIES_ARRET,
                           today=date_initiale or date.today().isoformat(),
                           shift_initial=shift_initial,
                           equipe=equipe,
                           productions_data=productions_data,
                           arrets_data=arrets_data,
                           form_action=form_action)


# ── Création ─────────────────────────────────────────────────────────────────

@saisie_bp.route('/nouveau', methods=['GET', 'POST'])
@login_required
@roles_required('operateur', 'chef', 'admin')
def nouveau_poste():
    """Formulaire de saisie d'une nouvelle équipe — sauvegardée en brouillon."""
    if request.method == 'POST':
        prods_brut, arrs_brut = _form_data_brut()
        try:
            equipe = Equipe(
                date=date.fromisoformat(request.form['date']),
                numero_equipe=request.form['numero_equipe'],
                effectif=int(request.form.get('effectif', 10)),
                notes=request.form.get('notes', ''),
                statut='brouillon',
                user_id=current_user.id
            )
            db.session.add(equipe)
            db.session.flush()

            (essences, vol_entrees, vol_conformes, vol_declass,
             machines, heures_debut, heures_fin, causes, categories) = \
                _extraire_productions_arrets(request.form)

            if not essences:
                flash("Au moins une ligne de production est requise.", 'danger')
                db.session.rollback()
                return _render_form(productions_data=prods_brut, arrets_data=arrs_brut)

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
                    return _render_form(productions_data=prods_brut, arrets_data=arrs_brut)
                if not essence:
                    continue
                prod = Production(
                    equipe_id=equipe.id,
                    essence=essence,
                    volume_entree=_parse_float(vol_entrees[i]   if i < len(vol_entrees)   else ''),
                    volume_conforme=_parse_float(vol_conformes[i] if i < len(vol_conformes) else ''),
                    volume_declass=_parse_float(vol_declass[i]   if i < len(vol_declass)   else ''),
                )
                db.session.add(prod)

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
                        return _render_form(productions_data=prods_brut, arrets_data=arrs_brut)
                    arret = Arret(
                        equipe_id=equipe.id,
                        machine=machines[i],
                        heure_debut=heures_debut[i],
                        heure_fin=heures_fin[i],
                        cause=causes[i],
                        categorie=categories[i] if i < len(categories) else 'Autre'
                    )
                    arret.calcule_duree()
                    db.session.add(arret)

            db.session.flush()
            calcule_trs(equipe)
            db.session.commit()

            flash("Équipe sauvegardée en brouillon. Vérifiez et soumettez quand les données sont complètes.", 'info')
            return redirect(url_for('saisie.historique'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'enregistrement : {type(e).__name__} — {str(e)}", 'danger')
            return _render_form(productions_data=prods_brut, arrets_data=arrs_brut)

    return _render_form()


# ── Soumission ────────────────────────────────────────────────────────────────

@saisie_bp.route('/equipe/<int:equipe_id>/soumettre', methods=['POST'])
@login_required
@roles_required('operateur', 'chef', 'admin')
def soumettre_equipe(equipe_id):
    """Transition brouillon → soumis. Fige les prix et recalcule le TRS final."""
    equipe = Equipe.query.get_or_404(equipe_id)

    if not _peut_soumettre(equipe):
        flash("Vous n'êtes pas autorisé à soumettre cette équipe.", 'danger')
        return redirect(url_for('saisie.historique'))

    # Validation minimale : au moins une production avec volume > 0
    if not equipe.productions or all(p.volume_entree == 0 for p in equipe.productions):
        flash("Impossible de soumettre : aucune production avec des volumes saisis.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    # P7-V1 — Validations de cohérence (bloquantes)
    erreur = _verifier_coherence(equipe)
    if erreur:
        flash(erreur, 'danger')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    # Figer les prix au moment de la soumission (première fois uniquement)
    for prod in equipe.productions:
        if prod.prix_snapshot is None:
            prix = float(Parametre.get(f'prix_{normalise_essence(prod.essence)}', 0))
            prod.prix_snapshot = prix if prix > 0 else None

    equipe.statut    = 'soumis'
    equipe.soumis_le = datetime.utcnow()
    calcule_trs(equipe)
    db.session.commit()

    flash(f"Équipe soumise. TRS final : {equipe.trs_global}%", 'success')
    return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))


# ── Modification ──────────────────────────────────────────────────────────────

@saisie_bp.route('/equipe/<int:equipe_id>/modifier', methods=['GET', 'POST'])
@login_required
@roles_required('operateur', 'chef', 'admin')
def modifier_equipe(equipe_id):
    """Formulaire pré-rempli pour modifier un brouillon ou un soumis récent (chef/admin)."""
    equipe = Equipe.query.get_or_404(equipe_id)

    if not _peut_modifier(equipe):
        flash("Cette équipe ne peut plus être modifiée.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

    if request.method == 'POST':
        prods_brut, arrs_brut = _form_data_brut()
        try:
            snapshots = {p.essence: p.prix_snapshot for p in equipe.productions}

            for p in list(equipe.productions):
                db.session.delete(p)
            for a in list(equipe.arrets):
                db.session.delete(a)
            db.session.flush()

            equipe.date           = date.fromisoformat(request.form['date'])
            equipe.numero_equipe  = request.form['numero_equipe']
            equipe.effectif       = int(request.form.get('effectif', 10))
            equipe.notes          = request.form.get('notes', '')

            (essences, vol_entrees, vol_conformes, vol_declass,
             machines, heures_debut, heures_fin, causes, categories) = \
                _extraire_productions_arrets(request.form)

            if not essences:
                flash("Au moins une ligne de production est requise.", 'danger')
                db.session.rollback()
                return _render_form(equipe, productions_data=prods_brut, arrets_data=arrs_brut)

            for i, essence in enumerate(essences):
                ve = (vol_entrees[i] if i < len(vol_entrees) else '').strip().replace(',', '.')
                try:
                    has_volume = float(ve) > 0 if ve else False
                except ValueError:
                    has_volume = bool(ve)
                if not essence and has_volume:
                    flash("Ligne de production incomplète : sélectionnez une essence avant d'entrer les volumes.", 'danger')
                    db.session.rollback()
                    return _render_form(equipe, productions_data=prods_brut, arrets_data=arrs_brut)
                if not essence:
                    continue
                prod = Production(
                    equipe_id=equipe.id,
                    essence=essence,
                    volume_entree=_parse_float(vol_entrees[i]   if i < len(vol_entrees)   else ''),
                    volume_conforme=_parse_float(vol_conformes[i] if i < len(vol_conformes) else ''),
                    volume_declass=_parse_float(vol_declass[i]   if i < len(vol_declass)   else ''),
                    prix_snapshot=snapshots.get(essence),
                )
                db.session.add(prod)

            for i in range(len(machines)):
                if machines[i] and heures_debut[i] and heures_fin[i] and causes[i]:
                    if heures_fin[i] <= heures_debut[i]:
                        flash(
                            f"Arrêt {i+1} ({machines[i]}) : l'heure de fin ({heures_fin[i]}) "
                            f"doit être après l'heure de début ({heures_debut[i]}).",
                            'danger'
                        )
                        db.session.rollback()
                        return _render_form(equipe, productions_data=prods_brut, arrets_data=arrs_brut)
                    arret = Arret(
                        equipe_id=equipe.id,
                        machine=machines[i],
                        heure_debut=heures_debut[i],
                        heure_fin=heures_fin[i],
                        cause=causes[i],
                        categorie=categories[i] if i < len(categories) else 'Autre'
                    )
                    arret.calcule_duree()
                    db.session.add(arret)

            db.session.flush()
            calcule_trs(equipe)

            if equipe.statut == 'soumis':
                equipe.modifie_le  = datetime.utcnow()
                equipe.modifie_par = current_user.nom

            db.session.commit()
            flash("Équipe mise à jour.", 'success')
            return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification : {type(e).__name__} — {str(e)}", 'danger')
            return _render_form(equipe, productions_data=prods_brut, arrets_data=arrs_brut)

    return _render_form(equipe)


# ── Verrouillage / Déverrouillage ────────────────────────────────────────────

@saisie_bp.route('/equipe/<int:equipe_id>/verrouiller', methods=['POST'])
@login_required
@roles_required('chef', 'admin')
def verrouiller_equipe(equipe_id):
    """Transition soumis → verrouillé (chef ou admin)."""
    equipe = Equipe.query.get_or_404(equipe_id)
    if equipe.statut != 'soumis':
        flash("Seule une équipe soumise peut être verrouillée.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))
    equipe.statut = 'verrouille'
    db.session.commit()
    flash("Équipe verrouillée — données définitives.", 'secondary')
    return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))


@saisie_bp.route('/equipe/<int:equipe_id>/deverrouiller', methods=['POST'])
@login_required
@roles_required('admin')
def deverrouiller_equipe(equipe_id):
    """Transition verrouillé → soumis (admin uniquement)."""
    equipe = Equipe.query.get_or_404(equipe_id)
    if not equipe.est_verrouille:
        flash("Cette équipe n'est pas verrouillée.", 'warning')
        return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))
    equipe.statut = 'soumis'
    db.session.commit()
    flash("Équipe déverrouillée. Le chef peut maintenant corriger les données.", 'info')
    return redirect(url_for('saisie.detail_poste', poste_id=equipe_id))


# ── Consultation ──────────────────────────────────────────────────────────────

@saisie_bp.route('/historique')
@login_required
def historique():
    from datetime import timedelta
    equipes = Equipe.query.order_by(Equipe.date.desc(), Equipe.numero_equipe).all()
    anomalies_par_poste = {e.id: detecte_anomalies(e) for e in equipes}

    # Bug 5 — Stats motivantes pour l'opérateur (aucune nouvelle table, filtre user_id)
    stats_op = None
    if current_user.role == 'operateur':
        mes_equipes = [e for e in equipes if e.user_id == current_user.id]
        soumises    = [e for e in mes_equipes
                       if e.statut in ('soumis', 'verrouille') and e.trs_global]
        nb = len(soumises)
        trs_moy    = round(sum(e.trs_global for e in soumises) / nb, 1) if nb else None
        meilleur   = max((e.trs_global for e in soumises), default=None)
        aujourd_hui = date.today()
        recentes   = [e for e in soumises
                      if e.date >= aujourd_hui - timedelta(days=7)]
        precedentes = [e for e in soumises
                       if aujourd_hui - timedelta(days=14) <= e.date < aujourd_hui - timedelta(days=7)]
        trs_rec  = round(sum(e.trs_global for e in recentes)   / len(recentes),   1) if recentes   else None
        trs_prec = round(sum(e.trs_global for e in precedentes) / len(precedentes), 1) if precedentes else None
        if trs_rec and trs_prec:
            tendance = 'up' if trs_rec > trs_prec else ('down' if trs_rec < trs_prec else 'flat')
        else:
            tendance = 'flat'
        stats_op = {
            'nb_equipes':  nb,
            'trs_moyen':   trs_moy,
            'meilleur_trs': meilleur,
            'trs_recent':  trs_rec,
            'tendance':    tendance,
        }

    return render_template('saisie/historique.html',
                           postes=equipes,
                           anomalies_par_poste=anomalies_par_poste,
                           stats_operateur=stats_op)


@saisie_bp.route('/poste/<int:poste_id>')
@login_required
def detail_poste(poste_id):
    equipe = Equipe.query.get_or_404(poste_id)
    pertes = calcule_pertes_equipe(equipe)
    manque = calcule_manque_gagner(equipe)  # P11 — indicateur principal
    couleur = couleur_trs(equipe.trs_global)
    anomalies = detecte_anomalies(equipe)  # P12 — contrôles qualité
    return render_template('saisie/detail.html',
                           poste=equipe,
                           pertes=pertes,
                           manque=manque,
                           perte_fcfa=pertes['total'],
                           couleur_trs=couleur,
                           anomalies=anomalies,
                           peut_soumettre=_peut_soumettre(equipe),
                           peut_modifier=_peut_modifier(equipe),
                           peut_verrouiller=(
                               equipe.statut == 'soumis'
                               and not equipe.est_verrouille
                               and current_user.role in ('chef', 'admin')
                           ),
                           peut_deverrouiller=(
                               equipe.est_verrouille
                               and current_user.role == 'admin'
                           ))


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
    )


# ── Suppression ───────────────────────────────────────────────────────────────

@saisie_bp.route('/poste/<int:poste_id>/supprimer', methods=['POST'])
@login_required
def supprimer_poste(poste_id):
    equipe = Equipe.query.get_or_404(poste_id)
    if equipe.statut != 'brouillon':
        flash("Seul un brouillon peut être supprimé.", 'warning')
        return redirect(url_for('saisie.historique'))
    if equipe.user_id != current_user.id:
        abort(403)
    db.session.delete(equipe)
    db.session.commit()
    flash("Brouillon supprimé.", 'info')
    return redirect(url_for('saisie.historique'))

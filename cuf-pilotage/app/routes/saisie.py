"""
Routes de saisie des équipes de travail.
L'agent administratif entre ici les données d'une équipe (poste 8h).
Une équipe peut contenir plusieurs lignes de production (essences différentes).
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from ..models import db, Equipe, Production, Arret, normalise_essence
from ..services.trs import calcule_trs, calcule_pertes_equipe, couleur_trs
from config import Config

saisie_bp = Blueprint('saisie', __name__, url_prefix='/saisie')


@saisie_bp.route('/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_poste():
    """Formulaire de saisie d'une nouvelle équipe (multi-essence + arrêts)."""
    if request.method == 'POST':
        try:
            equipe = Equipe(
                date=date.fromisoformat(request.form['date']),
                numero_equipe=request.form['numero_equipe'],
                effectif=int(request.form.get('effectif', 10)),
                notes=request.form.get('notes', ''),
                statut='soumis',
                soumis_le=datetime.utcnow(),
                user_id=current_user.id
            )
            db.session.add(equipe)
            db.session.flush()  # obtenir equipe.id avant les enfants

            # ── Productions (multi-essence) ──────────────────────────────────
            essences     = request.form.getlist('prod_essence[]')
            vol_entrees  = request.form.getlist('prod_volume_entree[]')
            vol_sortis   = request.form.getlist('prod_volume_sorti[]')
            rebut_niveaux = request.form.getlist('prod_rebut_niveau[]')
            nb_conformes  = request.form.getlist('prod_nb_conformes[]')
            nb_defectueux = request.form.getlist('prod_nb_defectueux[]')

            if not essences:
                flash('Au moins une ligne de production est requise.', 'danger')
                db.session.rollback()
                return _render_form()

            for i, essence in enumerate(essences):
                if not essence:
                    continue
                v_entree = float(vol_entrees[i]) if i < len(vol_entrees) and vol_entrees[i] else 0
                v_sorti  = float(vol_sortis[i])  if i < len(vol_sortis)  and vol_sortis[i]  else 0
                niveau   = rebut_niveaux[i] if i < len(rebut_niveaux) else 'aucun'

                # Capturer le prix courant au moment de la soumission
                from ..models import Parametre
                prix_snap = float(Parametre.get(f'prix_{normalise_essence(essence)}', 0))

                prod = Production(
                    equipe_id=equipe.id,
                    essence=essence,
                    volume_entree=v_entree,
                    volume_sorti=v_sorti,
                    rebut_niveau=niveau,
                    nb_planches_conformes=int(nb_conformes[i]) if i < len(nb_conformes) and nb_conformes[i] else 0,
                    nb_planches_defectueuses=int(nb_defectueux[i]) if i < len(nb_defectueux) and nb_defectueux[i] else 0,
                    prix_snapshot=prix_snap if prix_snap > 0 else None,
                )
                db.session.add(prod)

            # ── Arrêts ───────────────────────────────────────────────────────
            machines     = request.form.getlist('arret_machine[]')
            heures_debut = request.form.getlist('arret_debut[]')
            heures_fin   = request.form.getlist('arret_fin[]')
            causes       = request.form.getlist('arret_cause[]')
            categories   = request.form.getlist('arret_categorie[]')

            for i in range(len(machines)):
                if machines[i] and heures_debut[i] and heures_fin[i] and causes[i]:
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

            # ── Calcul TRS ───────────────────────────────────────────────────
            calcule_trs(equipe)
            db.session.commit()

            flash(f'Équipe enregistrée. TRS calculé : {equipe.trs_global}%', 'success')
            return redirect(url_for('saisie.historique'))

        except (ValueError, KeyError) as e:
            db.session.rollback()
            flash(f'Erreur dans le formulaire : {str(e)}', 'danger')

    return _render_form()


def _render_form():
    return render_template('saisie/formulaire.html',
                           essences=Config.ESSENCES,
                           rebut_niveaux=['aucun', 'faible', 'moyen', 'fort'],
                           machines=Config.MACHINES,
                           categories=Config.CATEGORIES_ARRET,
                           today=date.today().isoformat())


@saisie_bp.route('/historique')
@login_required
def historique():
    equipes = Equipe.query.order_by(Equipe.date.desc(), Equipe.numero_equipe).all()
    return render_template('saisie/historique.html', postes=equipes)


@saisie_bp.route('/poste/<int:poste_id>')
@login_required
def detail_poste(poste_id):
    equipe = Equipe.query.get_or_404(poste_id)
    pertes = calcule_pertes_equipe(equipe)
    couleur = couleur_trs(equipe.trs_global)
    return render_template('saisie/detail.html', poste=equipe,
                           pertes=pertes,
                           perte_fcfa=pertes['total'],
                           couleur_trs=couleur)


@saisie_bp.route('/poste/<int:poste_id>/supprimer', methods=['POST'])
@login_required
def supprimer_poste(poste_id):
    equipe = Equipe.query.get_or_404(poste_id)
    db.session.delete(equipe)
    db.session.commit()
    flash('Équipe supprimée.', 'info')
    return redirect(url_for('saisie.historique'))

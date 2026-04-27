"""
Routes de saisie des postes de travail.
L'agent administratif entre les données d'un poste ici.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from ..models import db, Poste, Arret
from ..services.trs import calcule_trs, calcule_pertes_fcfa
from config import Config

saisie_bp = Blueprint('saisie', __name__, url_prefix='/saisie')


@saisie_bp.route('/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_poste():
    """Formulaire de saisie d'un nouveau poste (production + arrêts)."""
    if request.method == 'POST':
        # --- Récupérer les données du formulaire ---
        try:
            poste = Poste(
                date=date.fromisoformat(request.form['date']),
                numero_poste=request.form['numero_poste'],
                essence=request.form['essence'],
                volume_entree=float(request.form['volume_entree']),
                volume_sorti=float(request.form['volume_sorti']),
                volume_rebut=float(request.form.get('volume_rebut', 0)),
                nb_planches_conformes=int(request.form.get('nb_conformes', 0)),
                nb_planches_defectueuses=int(request.form.get('nb_defectueux', 0)),
                effectif=int(request.form.get('effectif', 10)),
                notes=request.form.get('notes', ''),
                user_id=current_user.id
            )

            # Validation : le rebut ne peut pas dépasser le volume sorti
            if poste.volume_rebut > poste.volume_sorti:
                flash('Le volume rebut ne peut pas dépasser le volume scié.', 'danger')
                return render_template('saisie/formulaire.html',
                                       essences=Config.ESSENCES,
                                       machines=Config.MACHINES,
                                       categories=Config.CATEGORIES_ARRET,
                                       today=date.today().isoformat())

            db.session.add(poste)
            db.session.flush()  # obtenir l'ID du poste avant de créer les arrêts

            # --- Sauvegarder les arrêts ---
            machines     = request.form.getlist('arret_machine[]')
            heures_debut = request.form.getlist('arret_debut[]')
            heures_fin   = request.form.getlist('arret_fin[]')
            causes       = request.form.getlist('arret_cause[]')
            categories   = request.form.getlist('arret_categorie[]')

            for i in range(len(machines)):
                if machines[i] and heures_debut[i] and heures_fin[i] and causes[i]:
                    arret = Arret(
                        poste_id=poste.id,
                        machine=machines[i],
                        heure_debut=heures_debut[i],
                        heure_fin=heures_fin[i],
                        cause=causes[i],
                        categorie=categories[i] if i < len(categories) else 'Autre'
                    )
                    arret.calcule_duree()
                    db.session.add(arret)

            db.session.flush()

            # --- Calculer le TRS automatiquement ---
            calcule_trs(poste)

            db.session.commit()
            flash(f'Poste enregistré. TRS calculé : {poste.trs_global}%', 'success')
            return redirect(url_for('saisie.historique'))

        except (ValueError, KeyError) as e:
            db.session.rollback()
            flash(f'Erreur dans le formulaire : {str(e)}', 'danger')

    return render_template('saisie/formulaire.html',
                           essences=Config.ESSENCES,
                           machines=Config.MACHINES,
                           categories=Config.CATEGORIES_ARRET,
                           today=date.today().isoformat())


@saisie_bp.route('/historique')
@login_required
def historique():
    """Liste des postes saisis, du plus récent au plus ancien."""
    postes = Poste.query.order_by(Poste.date.desc(), Poste.numero_poste).all()
    return render_template('saisie/historique.html', postes=postes)


@saisie_bp.route('/poste/<int:poste_id>')
@login_required
def detail_poste(poste_id):
    """Détail complet d'un poste : production, arrêts, TRS décomposé."""
    from ..services.trs import couleur_trs, calcule_pertes_fcfa
    poste = Poste.query.get_or_404(poste_id)
    perte = calcule_pertes_fcfa(poste)
    couleur = couleur_trs(poste.trs_global)
    return render_template('saisie/detail.html', poste=poste,
                           perte_fcfa=perte, couleur_trs=couleur)


@saisie_bp.route('/poste/<int:poste_id>/supprimer', methods=['POST'])
@login_required
def supprimer_poste(poste_id):
    """Suppression d'un poste (et ses arrêts en cascade)."""
    poste = Poste.query.get_or_404(poste_id)
    db.session.delete(poste)
    db.session.commit()
    flash('Poste supprimé.', 'info')
    return redirect(url_for('saisie.historique'))

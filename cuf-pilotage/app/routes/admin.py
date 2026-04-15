"""
Routes d'administration : gestion des paramètres CUF.
Prix de vente par essence, objectif production, capacité bicoupe.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Parametre

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _chef_ou_admin():
    """Vérifie que l'utilisateur est chef ou admin (pas simple saisie)."""
    return current_user.role in ('chef', 'pdg', 'admin')


@admin_bp.route('/parametres', methods=['GET', 'POST'])
@login_required
def parametres():
    """Page de configuration des paramètres métier de CUF."""
    if request.method == 'POST':
        cles = ['prix_ayous', 'prix_azobe', 'prix_iroko', 'prix_movingui',
                'objectif_m3', 'duree_poste', 'capacite_bicoupe']
        for cle in cles:
            valeur = request.form.get(cle)
            if valeur:
                p = Parametre.query.filter_by(cle=cle).first()
                if p:
                    p.valeur = valeur.strip()
                else:
                    db.session.add(Parametre(cle=cle, valeur=valeur.strip()))
        db.session.commit()
        flash('Paramètres mis à jour.', 'success')
        return redirect(url_for('admin.parametres'))

    params = {p.cle: p for p in Parametre.query.all()}
    return render_template('admin/parametres.html', params=params)

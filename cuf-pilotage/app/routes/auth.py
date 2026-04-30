"""
Routes d'authentification : login et logout.
Flask-Login gère les sessions utilisateur de façon sécurisée.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion. Redirige selon le rôle après login."""
    if current_user.is_authenticated:
        return _redirect_par_role(current_user.role)

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        utilisateur = User.query.filter_by(email=email, actif=True).first()

        if utilisateur and utilisateur.check_password(password):
            login_user(utilisateur)
            flash(f'Bienvenue, {utilisateur.nom} !', 'success')
            return _redirect_par_role(utilisateur.role)
        else:
            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_par_role(role):
    """Redirige vers la bonne page selon le rôle de l'utilisateur."""
    if role == 'pdg':
        return redirect(url_for('dashboard.vue_pdg'))
    if role == 'chef':
        return redirect(url_for('dashboard.vue_chef'))
    return redirect(url_for('saisie.nouveau_poste'))

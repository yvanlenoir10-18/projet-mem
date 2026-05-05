"""
Routes d'administration — WoodPilot CUF.
- Paramètres métier : prix essences, objectif, capacité (chef + admin)
- Gestion utilisateurs : CRUD complet (admin uniquement)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Parametre, User
from ..utils import roles_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ROLES_DISPONIBLES = ['operateur', 'chef', 'pdg', 'admin']


# ── Paramètres métier ─────────────────────────────────────────────────────────

@admin_bp.route('/parametres', methods=['GET', 'POST'])
@login_required
@roles_required('chef', 'admin')
def parametres():
    """Page de configuration des paramètres métier de CUF."""
    if request.method == 'POST':
        cles = ['prix_ayous', 'prix_azobe', 'prix_iroko', 'prix_movingui',
                'objectif_m3', 'duree_poste', 'capacite_equipe_h', 'taux_revente_rebut']
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


# ── Gestion utilisateurs (admin uniquement) ───────────────────────────────────

@admin_bp.route('/utilisateurs')
@login_required
@roles_required('admin')
def liste_utilisateurs():
    """Liste tous les utilisateurs de la plateforme."""
    utilisateurs = User.query.order_by(User.role, User.nom).all()
    return render_template('admin/users.html',
                           utilisateurs=utilisateurs,
                           roles=ROLES_DISPONIBLES,
                           mode='liste')


@admin_bp.route('/utilisateurs/nouveau', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def creer_utilisateur():
    """Formulaire de création d'un nouvel utilisateur."""
    if request.method == 'POST':
        nom   = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip().lower()
        role  = request.form.get('role', 'operateur')
        mdp   = request.form.get('password', '')

        if not nom or not email or not mdp:
            flash('Nom, email et mot de passe sont obligatoires.', 'danger')
            return render_template('admin/users.html',
                                   roles=ROLES_DISPONIBLES, mode='nouveau')

        if role not in ROLES_DISPONIBLES:
            flash('Rôle invalide.', 'danger')
            return render_template('admin/users.html',
                                   roles=ROLES_DISPONIBLES, mode='nouveau')

        if User.query.filter_by(email=email).first():
            flash(f"Un compte avec l'email {email} existe déjà.", 'danger')
            return render_template('admin/users.html',
                                   roles=ROLES_DISPONIBLES, mode='nouveau')

        u = User(nom=nom, email=email, role=role, actif=True)
        u.set_password(mdp)
        db.session.add(u)
        db.session.commit()
        flash(f'Utilisateur {nom} créé avec le rôle {role}.', 'success')
        return redirect(url_for('admin.liste_utilisateurs'))

    return render_template('admin/users.html',
                           roles=ROLES_DISPONIBLES, mode='nouveau')


@admin_bp.route('/utilisateurs/<int:user_id>/modifier', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def modifier_utilisateur(user_id):
    """Modifier le nom, email ou rôle d'un utilisateur."""
    u = User.query.get_or_404(user_id)

    if request.method == 'POST':
        nom   = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip().lower()
        role  = request.form.get('role', u.role)
        actif = request.form.get('actif') == '1'

        if not nom or not email:
            flash('Nom et email sont obligatoires.', 'danger')
            return render_template('admin/users.html',
                                   utilisateur=u,
                                   roles=ROLES_DISPONIBLES, mode='modifier')

        if role not in ROLES_DISPONIBLES:
            flash('Rôle invalide.', 'danger')
            return render_template('admin/users.html',
                                   utilisateur=u,
                                   roles=ROLES_DISPONIBLES, mode='modifier')

        doublon = User.query.filter(User.email == email, User.id != user_id).first()
        if doublon:
            flash(f"L'email {email} est déjà utilisé par un autre compte.", 'danger')
            return render_template('admin/users.html',
                                   utilisateur=u,
                                   roles=ROLES_DISPONIBLES, mode='modifier')

        u.nom   = nom
        u.email = email
        u.role  = role
        u.actif = actif
        db.session.commit()
        flash(f'Compte {nom} mis à jour.', 'success')
        return redirect(url_for('admin.liste_utilisateurs'))

    return render_template('admin/users.html',
                           utilisateur=u,
                           roles=ROLES_DISPONIBLES, mode='modifier')


@admin_bp.route('/utilisateurs/<int:user_id>/reset-mdp', methods=['POST'])
@login_required
@roles_required('admin')
def reset_mot_de_passe(user_id):
    """Réinitialise le mot de passe d'un utilisateur."""
    u = User.query.get_or_404(user_id)
    nouveau_mdp = request.form.get('nouveau_mdp', '').strip()

    if len(nouveau_mdp) < 6:
        flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
        return redirect(url_for('admin.modifier_utilisateur', user_id=user_id))

    u.set_password(nouveau_mdp)
    db.session.commit()
    flash(f'Mot de passe de {u.nom} réinitialisé.', 'success')
    return redirect(url_for('admin.liste_utilisateurs'))


@admin_bp.route('/utilisateurs/<int:user_id>/supprimer', methods=['POST'])
@login_required
@roles_required('admin')
def supprimer_utilisateur(user_id):
    """Supprime un utilisateur (impossible de se supprimer soi-même)."""
    u = User.query.get_or_404(user_id)

    if u.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin.liste_utilisateurs'))

    nom = u.nom
    db.session.delete(u)
    db.session.commit()
    flash(f'Compte de {nom} supprimé.', 'info')
    return redirect(url_for('admin.liste_utilisateurs'))

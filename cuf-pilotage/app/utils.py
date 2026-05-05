"""
Utilitaires transversaux — WoodPilot CUF.

Décorateur RBAC : roles_required(*roles)
  Usage : @roles_required('chef', 'admin')
  Renvoie 403 si l'utilisateur n'a pas le bon rôle.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


ROLES_VALIDES = ('operateur', 'chef', 'pdg', 'admin')

# Accueil par défaut selon le rôle
_ACCUEIL_ROLE = {
    'operateur': 'saisie.historique',
    'chef':      'dashboard.vue_chef',
    'pdg':       'dashboard.vue_pdg',
    'admin':     'dashboard.vue_chef',
}


def redirect_accueil():
    """Redirige l'utilisateur vers sa page d'accueil selon son rôle."""
    role = getattr(current_user, 'role', 'operateur')
    endpoint = _ACCUEIL_ROLE.get(role, 'saisie.historique')
    return redirect(url_for(endpoint))


def roles_required(*roles):
    """
    Décorateur RBAC — limite l'accès à une ou plusieurs rôles.

    Exemple :
        @roles_required('chef', 'admin')
        def ma_vue(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash("Vous n'avez pas accès à cette page.", 'danger')
                return redirect_accueil()
            return f(*args, **kwargs)
        return decorated
    return decorator

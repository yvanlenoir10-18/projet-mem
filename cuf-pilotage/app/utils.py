"""
Utilitaires transversaux — wood_pilot.

Décorateur RBAC : roles_required(*roles)
  Usage : @roles_required('prod', 'admin')
  Renvoie 403 si l'utilisateur n'a pas le bon rôle.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


ROLES_VALIDES = ('operateur', 'prod', 'pdg', 'admin')

# Accueil par défaut selon le rôle
_ACCUEIL_ROLE = {
    'operateur': 'saisie.accueil_operateur',
    'prod':      'dashboard.vue_prod',
    'pdg':       'dashboard.vue_pdg',
    'admin':     'dashboard.vue_prod',
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
        @roles_required('prod', 'admin')
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

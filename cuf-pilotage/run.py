"""
Point d'entrée de l'application Wood_Pilot_Ebolowa.
Lance le serveur Flask en mode développement.

Usage : python run.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # use_reloader=False évite la boucle de rechargement sur Windows Store Python
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

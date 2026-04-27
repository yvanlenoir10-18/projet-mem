"""
Point d'entrée WSGI pour PythonAnywhere.

Sur PythonAnywhere, remplacer VOTRE_USERNAME par votre nom d'utilisateur
dans le panneau Web > WSGI configuration file.
"""
import sys
import os

# Chemin absolu vers le dossier cuf-pilotage sur PythonAnywhere
# Exemple : /home/yvanlenoir/cuf-pilotage
project_home = os.path.dirname(os.path.abspath(__file__))

if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

from app import create_app
application = create_app()

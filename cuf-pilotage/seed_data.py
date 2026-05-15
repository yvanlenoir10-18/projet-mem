"""
Génération de données fictives — tout le mois d'avril 2026 × 2 équipes/jour = 60 équipes.
Permet d'accéder à toutes les fonctionnalités de l'app sans saisie manuelle.

Usage :
  python seed_data.py

Tout est aléatoire mais réaliste :
- volume_entree : 22-36 m³ par production
- volume_conforme / declass / dechets : selon rendement matière (60-85% conforme)
- 1 à 2 productions par équipe (mixage essences possible)
- 0 à 4 arrêts par équipe (15-90 min chacun)
- essences pondérées : Ayous 40%, Iroko 25%, Azobé 20%, Movingui 15%
- statut='verrouille' pour que les recommandations détectent les équipes
"""
import random
from datetime import date, timedelta, datetime
from app import create_app
from app.models import db, User, Equipe, Production, Arret, Parametre
from app.services.trs import calcule_trs

app = create_app()

# Mois ciblé pour les données fictives : avril 2026
ANNEE_CIBLE = 2026
MOIS_CIBLE  = 4
JOUR_DEBUT  = date(ANNEE_CIBLE, MOIS_CIBLE, 1)
JOUR_FIN    = date(ANNEE_CIBLE, MOIS_CIBLE, 30)
NB_JOURS    = (JOUR_FIN - JOUR_DEBUT).days + 1
ESSENCES_PONDEREES = (
    ['Ayous'] * 40 +
    ['Iroko'] * 25 +
    ['Azobé'] * 20 +
    ['Movingui'] * 15
)

MACHINES = ['Bicoupe', 'Scie de tête', 'Déligneuse', 'Ébouteuse']
CAUSES_PAR_CATEGORIE = {
    'Mécanique': [
        'Bourrage bois dans la lame',
        'Panne moteur',
        'Panne hydraulique',
        'Courroie cassée',
        'Bourrage planches sortie bicoupe',
    ],
    'Maintenance planifiée': [
        'Remplacement lame émoussée',
        'Affûtage lame préventif',
        'Lubrification roulements',
        'Vérification systèmes',
    ],
    'Organisationnelle': [
        'Réglage bicoupe pour nouvelle essence',
        'Absence opérateur',
        'Pause technique transition équipe',
        'Réunion sécurité',
    ],
    'Approvisionnement': [
        'Attente grumes — parc à grumes mal organisé',
        'Grumes non prêtes',
        'Retard livraison camions',
    ],
    'Qualité matière': [
        'Grume avec corps étranger',
        'Grumes trop petites — réglage',
        'Grumes noueuses — rebuts élevés',
    ],
}


def _genere_arrets():
    """Retourne une liste de 0 à 4 arrêts aléatoires."""
    nb = random.choices([0, 1, 2, 3, 4], weights=[10, 30, 35, 20, 5])[0]
    arrets = []
    heure_courante = 6 * 60 + random.randint(0, 30)  # début vers 06h00-06h30
    for _ in range(nb):
        duree = random.randint(15, 90)
        heure_courante += random.randint(45, 180)
        if heure_courante + duree > 22 * 60:
            break
        h_d, m_d = divmod(heure_courante, 60)
        h_f, m_f = divmod(heure_courante + duree, 60)
        categorie = random.choices(
            list(CAUSES_PAR_CATEGORIE.keys()),
            weights=[35, 15, 25, 15, 10]
        )[0]
        arrets.append({
            'machine':   random.choices(MACHINES, weights=[60, 20, 15, 5])[0],
            'debut':     f"{h_d:02d}:{m_d:02d}",
            'fin':       f"{h_f:02d}:{m_f:02d}",
            'cause':     random.choice(CAUSES_PAR_CATEGORIE[categorie]),
            'categorie': categorie,
        })
        heure_courante += duree
    return arrets


def _genere_productions():
    """Retourne 1 ou 2 productions avec essences mixtes possibles."""
    nb = random.choices([1, 2], weights=[70, 30])[0]
    essences_utilisees = []
    productions = []
    for _ in range(nb):
        # éviter doublons d'essence dans la même équipe
        ess = random.choice(ESSENCES_PONDEREES)
        while ess in essences_utilisees and len(essences_utilisees) < 4:
            ess = random.choice(ESSENCES_PONDEREES)
        essences_utilisees.append(ess)

        volume_entree = round(random.uniform(22.0, 36.0), 1)
        # Rendement matière 55-85% (conforme + declass)
        taux_conforme = random.uniform(0.55, 0.78)
        taux_declass  = random.uniform(0.05, 0.15)
        if taux_conforme + taux_declass > 0.90:
            taux_declass = 0.90 - taux_conforme

        # Prix par essence (FCFA / m³) — ordres de grandeur réalistes
        prix = {
            'Ayous':    180_000,
            'Iroko':    420_000,
            'Azobé':    280_000,
            'Movingui': 320_000,
        }[ess]
        productions.append({
            'essence':         ess,
            'volume_entree':   volume_entree,
            'volume_conforme': round(volume_entree * taux_conforme, 2),
            'volume_declass':  round(volume_entree * taux_declass, 2),
            'prix':            prix,
        })
    return productions


def inserer_donnees():
    with app.app_context():
        # Récupérer un utilisateur (saisie obligatoire)
        user = User.query.filter_by(role='operateur').first() or User.query.first()
        if not user:
            print("❌  Aucun utilisateur en base. Lancez l'app une fois pour seed les users.")
            return

        # Effacer les données existantes
        Arret.query.delete()
        Production.query.delete()
        Equipe.query.delete()
        db.session.commit()
        print(f"Base nettoyée. Génération avril {ANNEE_CIBLE} : {NB_JOURS} jours × 2 équipes…\n")

        random.seed(42)  # reproductibilité (changer pour des données différentes)
        compteur = 0

        for jour_offset in range(NB_JOURS):
            jour = JOUR_DEBUT + timedelta(days=jour_offset)

            for numero in ['Matin', 'Apres-midi']:
                equipe = Equipe(
                    date=jour,
                    numero_equipe=numero,
                    effectif=random.choice([8, 9, 10, 10, 10]),
                    statut='verrouille',
                    notes='',
                    cree_le=datetime.combine(jour, datetime.min.time()),
                    soumis_le=datetime.combine(jour, datetime.min.time()),
                    user_id=user.id,
                )
                db.session.add(equipe)
                db.session.flush()

                # Productions
                for p in _genere_productions():
                    db.session.add(Production(
                        equipe_id=equipe.id,
                        essence=p['essence'],
                        volume_entree=p['volume_entree'],
                        volume_conforme=p['volume_conforme'],
                        volume_declass=p['volume_declass'],
                        prix_snapshot=p['prix'],
                    ))

                # Arrêts
                for a in _genere_arrets():
                    arret = Arret(
                        equipe_id=equipe.id,
                        machine=a['machine'],
                        heure_debut=a['debut'],
                        heure_fin=a['fin'],
                        cause=a['cause'],
                        categorie=a['categorie'],
                    )
                    arret.calcule_duree()
                    db.session.add(arret)

                db.session.flush()
                calcule_trs(equipe)
                compteur += 1

                if compteur % 10 == 0 or compteur == NB_JOURS * 2:
                    print(f"  {compteur:02d}/{NB_JOURS * 2} | {jour} {numero:11s} | "
                          f"vol_sorti={equipe.volume_sorti:5.1f} m³ | "
                          f"TRS={equipe.trs_global:5.1f}%")

        db.session.commit()
        print(f"\n✅  {compteur} équipes insérées sur {NB_JOURS} jours.")
        print("✅  Connecte-toi : chef/password ou pdg/password — toutes les fonctionnalités sont accessibles.")


if __name__ == '__main__':
    inserer_donnees()

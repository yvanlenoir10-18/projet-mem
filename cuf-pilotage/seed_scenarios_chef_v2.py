"""
seed_scenarios_chef_v2.py — 4 mises en situation contrôlées pour tester
Chef Scierie V2 · Vue 1 « Le Point ».

But : remplacer les données aléatoires par 4 postes déterministes, chacun
illustrant UN type de signal, pour juger si « Le Point » se comprend en 5 s.

Lancer :  python seed_scenarios_chef_v2.py
Tester :  http://127.0.0.1:5000/dashboard/chef/v2   (compte prod@cuf.cm / cuf2026)

Les 4 scénarios (un poste Matin par jour, sur les 4 derniers jours) :
  1. Poste normal           — production ~objectif, peu d'arrêt → pas de déficit
  2. Arrêt Bicoupe long      — 180 min de panne Bicoupe → manque FCFA, D dominant
  3. Déclassement élevé      — beaucoup de déclassé Bilinga → manque FCFA, Q dominant
  4. Fiche incohérente       — statut « à vérifier » + arrêts qui se chevauchent
                               → priorité de contrôle, EXCLUE du manque officiel

Règles métier respectées : capacité 12,5 m³/poste · postes Matin/Apres-midi ·
machines Scie de tête / Bicoupe / Scie de tronçonnage · 4 essences.
"""
from datetime import date, datetime, timedelta

from app import create_app
from app.models import db, User, Equipe, Production, Arret
from app.services.trs import calcule_trs

app = create_app()

PRIX = {'Ayous': 180_000, 'Iroko': 420_000, 'Bilinga': 280_000, 'Movingui': 320_000}


def _poste(user, jour, essence, conforme, declass, entree, statut, arrets):
    """Crée un poste Matin déterministe : une production sur tout le poste (06h-14h)."""
    eq = Equipe(
        date=jour, numero_equipe='Matin', effectif=10,
        operateur_nom='Test Scénario', statut=statut, notes='',
        cree_le=datetime.combine(jour, datetime.min.time()),
        soumis_le=datetime.combine(jour, datetime.min.time()),
        user_id=user.id,
    )
    db.session.add(eq)
    db.session.flush()
    db.session.add(Production(
        equipe_id=eq.id, essence=essence,
        heure_debut='06:00', heure_fin='14:00',
        volume_entree=entree, volume_conforme=conforme,
        volume_declass=declass, prix_snapshot=PRIX[essence],
    ))
    for a in arrets:
        ar = Arret(equipe_id=eq.id, machine=a['machine'],
                   heure_debut=a['debut'], heure_fin=a['fin'],
                   cause=a['cause'], categorie=a['categorie'],
                   duree_prevue_min=None)
        ar.calcule_duree()
        db.session.add(ar)
    db.session.flush()
    calcule_trs(eq)
    return eq


def inserer():
    with app.app_context():
        user = (User.query.filter_by(role='operateur').first()
                or User.query.first())
        if not user:
            print("ERREUR — lancez l'app une fois pour créer les utilisateurs.")
            return

        Arret.query.delete()
        Production.query.delete()
        Equipe.query.delete()
        db.session.commit()

        today = date.today()

        # ── Scénario 1 — Poste normal ─────────────────────────────────────
        _poste(user, today - timedelta(days=3), 'Ayous',
               conforme=12.4, declass=0.4, entree=15.0, statut='verrouille',
               arrets=[{'machine': 'Scie de tronçonnage', 'debut': '09:30',
                        'fin': '09:45', 'cause': 'Réglage rapide',
                        'categorie': 'Réglage / outil'}])

        # ── Scénario 2 — Arrêt Bicoupe long ───────────────────────────────
        _poste(user, today - timedelta(days=2), 'Iroko',
               conforme=8.0, declass=0.5, entree=10.0, statut='verrouille',
               arrets=[{'machine': 'Bicoupe', 'debut': '08:00', 'fin': '11:00',
                        'cause': 'Panne moteur bicoupe',
                        'categorie': 'Panne machine'}])

        # ── Scénario 3 — Déclassement élevé ───────────────────────────────
        _poste(user, today - timedelta(days=1), 'Bilinga',
               conforme=6.0, declass=6.0, entree=13.0, statut='verrouille',
               arrets=[{'machine': 'Scie de tête', 'debut': '10:00',
                        'fin': '10:20', 'cause': 'Bois noueux',
                        'categorie': 'Qualité matière'}])

        # ── Scénario 4 — Fiche incohérente (à vérifier, arrêts qui se chevauchent)
        _poste(user, today, 'Movingui',
               conforme=5.0, declass=5.0, entree=12.0, statut='a_verifier',
               arrets=[
                   {'machine': 'Bicoupe', 'debut': '08:00', 'fin': '09:30',
                    'cause': 'Arrêt non précisé', 'categorie': 'Panne machine'},
                   {'machine': 'Bicoupe', 'debut': '09:00', 'fin': '10:00',
                    'cause': 'Arrêt non précisé', 'categorie': 'Panne machine'},
               ])

        db.session.commit()
        print("OK — 4 scénarios insérés (3 validés + 1 à vérifier).")
        print("Teste : http://127.0.0.1:5000/dashboard/chef/v2  (prod@cuf.cm / cuf2026)")


if __name__ == '__main__':
    inserer()

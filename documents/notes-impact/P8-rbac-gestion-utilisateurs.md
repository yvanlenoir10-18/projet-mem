# Note d'impact mémoire — P8 : Contrôle d'accès par rôle & gestion utilisateurs
**Commit :** `558148c` — `feat(rbac+admin): Phase 1 — contrôle d'accès par rôle + gestion utilisateurs`
**Date :** 2026-05-05
**Fichiers modifiés :** `app/utils.py` (nouveau, 45 lignes) · `app/routes/admin.py` (réécrit, +120 lignes) · `app/routes/dashboard.py` (+5 lignes) · `app/routes/saisie.py` (+8 lignes) · `app/routes/analyse.py` (+3 lignes) · `app/routes/auth.py` (+2 lignes) · `app/templates/base.html` (refonte sidebar + navbar) · `app/templates/admin/users.html` (nouveau, 200 lignes)

---

## 1. Ce qui a été implémenté

P8 introduit un **système de contrôle d'accès basé sur les rôles (RBAC)** et une **page d'administration des comptes utilisateurs**, répondant à la demande de cloisonnement de l'interface par profil.

### P8-RBAC — Décorateur centralisé `roles_required`

Un unique point de contrôle dans `app/utils.py` — `roles_required(*roles)` — utilisé comme décorateur sur chaque route Flask. Si l'utilisateur n'a pas le rôle requis, il reçoit un flash `danger` et est redirigé vers sa page d'accueil (pas d'erreur 403 brute : redirection douce vers son espace autorisé).

```python
def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if current_user.role not in roles:
                flash("Vous n'avez pas accès à cette page.", 'danger')
                return redirect_accueil()
            return f(*args, **kwargs)
        return decorated
    return decorator
```

### Matrice d'accès effective

| Route | Opérateur | Chef | PDG | Admin |
|---|---|---|---|---|
| `/saisie/nouveau` | ✓ | ✓ | ✗ | ✓ |
| `/saisie/historique` | ✓ | ✓ | ✓ | ✓ |
| `/saisie/equipe/*/verrouiller` | ✗ | ✓ | ✗ | ✓ |
| `/saisie/equipe/*/deverrouiller` | ✗ | ✗ | ✗ | ✓ |
| `/dashboard/chef` | ✗ | ✓ | ✗ | ✓ |
| `/dashboard/pertes` | ✗ | ✓ | ✗ | ✓ |
| `/analyse/arrets` | ✗ | ✓ | ✗ | ✓ |
| `/dashboard/pdg` | ✗ | ✗ | ✓ | ✓ |
| `/admin/parametres` | ✗ | ✓ | ✗ | ✓ |
| `/admin/utilisateurs` | ✗ | ✗ | ✗ | ✓ |

### P8-USERS — Gestion des comptes (admin uniquement)

Cinq nouvelles routes dans `admin.py` couvrent le cycle de vie complet d'un compte :

| Route | Action |
|---|---|
| `GET /admin/utilisateurs` | Liste tous les comptes avec rôle et statut |
| `GET/POST /admin/utilisateurs/nouveau` | Créer un compte (nom, email, rôle, mot de passe) |
| `GET/POST /admin/utilisateurs/<id>/modifier` | Modifier nom, email, rôle, actif/inactif |
| `POST /admin/utilisateurs/<id>/reset-mdp` | Réinitialiser le mot de passe (min. 6 car.) |
| `POST /admin/utilisateurs/<id>/supprimer` | Supprimer un compte (auto-suppression bloquée) |

### P8-NAV — Sidebar et navbar restructurées

La sidebar est maintenant **entièrement conditionnelle par rôle** avec des sections titrées (Analyses / Saisie / Configuration) et les nouveaux noms validés :
- "Pertes financières" au lieu d'"Analyse des pertes"
- "Causes d'arrêts" au lieu d'"Analyse des arrêts"
- L'app est renommée **WoodPilot** dans la navbar (style sombre repensé, badge rôle coloré par profil)

---

## 2. Lien avec les objectifs du mémoire

P8 répond à **OS6** (concevoir un outil de pilotage adapté aux besoins des différents responsables). OS6 n'exige pas seulement que l'outil existe — il exige qu'il soit **adapté à chaque utilisateur**. Un opérateur exposé aux tableaux financiers du PDG ne peut pas utiliser l'outil sereinement ; un PDG noyé dans les formulaires de saisie ne peut pas l'utiliser du tout.

P8 traduit OS6 en contrainte technique : la différenciation des vues n'est plus seulement visuelle (sidebar différente), elle est **architecturale** (routes inaccessibles côté serveur si le rôle ne correspond pas).

Le lien avec **OS2** est indirect : un opérateur qui ne voit que son espace de saisie est moins susceptible de modifier accidentellement des données d'un autre utilisateur. La qualité de la collecte dépend aussi de la clarté de l'interface proposée à chaque acteur.

---

## 3. Données et calculs mobilisés

Aucun nouveau calcul métier. P8 est une couche de **gouvernance et d'architecture**, pas d'analyse. Les seules opérations de données sont :

- `User.query.order_by(User.role, User.nom).all()` — lecture triée des comptes
- `User.query.filter_by(email=email).first()` — détection de doublon email avant création
- `User.query.filter(User.email == email, User.id != user_id).first()` — doublon à l'exclusion de l'utilisateur courant (modification sans conflit)
- `u.set_password(mdp)` — hachage bcrypt existant dans le modèle User

La vérification d'auto-suppression (`u.id == current_user.id`) est une protection de sécurité : l'administrateur ne peut pas se supprimer lui-même et ainsi verrouiller l'accès à la plateforme.

---

## 4. Hypothèses testées ou confirmées

**P8 ne contredit aucune hypothèse du mémoire.**

- **H3, H4** : non impactées directement. Le cloisonnement par rôle n'affecte pas le calcul du TRS ni des pertes. Les données restent les mêmes ; seul l'accès est différencié.
- **H1, H2** : non directement impactées.

**Point de vigilance :** la décision que le PDG ne puisse pas accéder au dashboard Chef (données opérationnelles shift par shift) est un choix de conception — pas une hypothèse du mémoire. Ce choix part du principe que le PDG a besoin d'une vue synthétique, pas d'un accès aux microdonnées. Si lors du terrain CUF le PDG souhaite accéder aux détails, il faudra ajuster la matrice d'accès (une ligne à changer dans le décorateur).

**Aucune contradiction signalée.** P8 est une couche de gouvernance transversale.

---

## 5. Ce que ce module permet de montrer dans le mémoire

- **Différenciation des personas réellement implémentée :** OS6 mentionne "trois vues différenciées" (opérateur / chef / PDG). P8 démontre que cette différenciation existe à niveau architectural, pas seulement à niveau HTML. La section Conception de l'outil peut décrire la matrice d'accès comme une décision de conception fondée sur les besoins métier de chaque acteur.
- **Sécurité sans complexité excessive :** le décorateur `roles_required` est 20 lignes de code pour protéger l'ensemble de l'application. C'est un exemple de sobriété technique adaptée au contexte CUF (outil interne, équipe réduite, pas de besoin d'OAuth ou LDAP).
- **Outil maintenable post-stage :** la page de gestion des utilisateurs permet au chef ou à un responsable CUF d'ajouter un opérateur, de lui donner ses accès et de lui réinitialiser son mot de passe sans intervention du stagiaire. C'est une condition nécessaire à la **pérennité de l'outil** après le départ de l'étudiant — argument fort pour la section Discussion / Recommandations.

---

## 6. Limites actuelles

- **Pas de double authentification (2FA) :** pour un outil interne sur réseau local CUF, ce n'est pas requis. À mentionner comme limite si la plateforme devait être exposée sur Internet.
- **Pas de gestion des sessions expirées :** Flask-Login maintient la session jusqu'à déconnexion manuelle. Si un opérateur oublie de se déconnecter, sa session reste active. Acceptable pour le contexte CUF (postes de travail physiques dédiés).
- **Email utilisé comme identifiant :** les opérateurs CUF n'ont peut-être pas d'adresse email professionnelle. En pratique, un email fictif au format `prenom.nom@cuf.local` peut être utilisé — il n'y a pas d'envoi d'email dans le système.
- **Pas de journalisation des actions admin :** qui a créé quel compte, à quelle date ? Le modèle User stocke `cree_le` mais pas "modifié_par". Acceptable pour un outil de stage mais à noter comme limite d'audit.
- **Reset mot de passe sans confirmation email :** l'admin voit le nouveau mot de passe en clair dans le formulaire et doit le transmettre manuellement à l'utilisateur. Risque minimal en contexte interne ; impraticable en contexte externe.

---

## 7. Vérification de cohérence avec les notes précédentes

La règle **R9** (`leçons.md` : contrôle d'accès par propriété, pas par rôle) est **complétée, non contredite** par P8. R9 s'appliquait à la visibilité des données (chaque utilisateur voit ses propres brouillons). P8 ajoute un niveau supérieur : contrôle d'accès à la fonctionnalité (telle route est accessible ou non). Les deux niveaux coexistent :
- Niveau fonctionnalité : `@roles_required(...)` — P8
- Niveau données : `Equipe.user_id == current_user.id` — R9

La note **P7-alertes-validations.md** documentait `_alertes_chef()` qui appelle `current_user.id` pour filtrer les brouillons. Cette logique **reste inchangée** — P8 ne touche pas aux filtres de données, seulement aux routes d'accès.

La note **00-cadrage-global-P1-P2-P3.md** documentait l'existence d'un champ `role` sur le modèle User. P8 l'exploite pleinement pour la première fois de manière centralisée — les vérifications `if current_user.role not in ('chef', 'admin')` dispersées dans les routes sont remplacées par le décorateur unifié.

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Jonsson & Lesshammar (1999) — OEE fondateur | L'accès différencié par rôle garantit que chaque acteur voit les indicateurs pertinents pour ses décisions. L'opérateur n'a pas besoin du TRS global ; le PDG n'a pas besoin du détail shift. |
| Kankkunen & Holopainen (2024) — Daily management UPM Plywood | Le management visuel quotidien nécessite une interface adaptée à l'utilisateur : le Chef voit ses alertes opérationnelles, le PDG voit sa synthèse financière. P8 est la condition technique de cette différenciation. |
| Steenkamp et al. (2017) — VMS open-source, Afrique du Sud | Un VMS multi-utilisateurs sans contrôle d'accès expose à des modifications non souhaitées de données. P8 applique le principe de moindre privilège décrit dans les bonnes pratiques des systèmes de collecte de terrain. |

---

## 9. Prochaines étapes

- **Phase 2 (UI/UX) :** refonte de l'interface — navigation par menus cliquables, pages séparées pour chaque section du dashboard Chef, design moderne couleurs bois/nature, page login redesignée, responsive mobile+desktop. C'est la suite directe de P8.
- **Créer les comptes réels chez CUF :** lors du terrain, créer via `/admin/utilisateurs` les comptes des opérateurs réels, du Chef de production et du PDG. Tester la connexion sur chaque appareil disponible.
- **Tester le cloisonnement sur Windows :** vérifier que le PDG connecté ne voit pas le lien "Saisir un poste" et est bien redirigé vers son tableau de bord financier.
- **Documenter la matrice d'accès dans le mémoire :** la section OS6 peut présenter le tableau rôle × fonctionnalité comme preuve que l'outil est "adapté aux besoins des différents responsables" (citation exacte de l'objectif spécifique 6).
- **Reconsidérer l'accès PDG si besoin terrain :** si le PDG souhaite voir certains détails opérationnels (ex. scorecard semaine), ajuster `@roles_required('pdg', 'chef', 'admin')` sur la route concernée — une ligne.

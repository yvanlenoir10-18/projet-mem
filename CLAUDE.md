# CLAUDE.md — App CUF (assako) — contexte verrouillé

> Lu automatiquement par Claude Code au début de chaque session. Contient le noyau métier verrouillé. Les détails de développement vivent dans le skill `brief-app-cuf` et le protocole `vibe-coding`.

## Projet
Application desktop de pilotage de la production de la chaîne 4 — scierie industrielle CUF, Ebolowa. Utilisée par **BWAME EBENGUE CARLOS YVAN** (analyse, export) et les **opérateurs** (saisie au niveau du poste). Soutient le mémoire M2 « Amélioration des performances de production de la chaîne 4 ».

## ⚠️ Règles métier verrouillées — ne jamais inventer, confondre ou approximer
- **25 m³/jour** = deux postes combinés. **12,5 m³/poste**. NE JAMAIS confondre le niveau jour et le niveau poste.
- Deux postes : matin **6h–14h**, soir **14h–23h**. Environ **10 opérateurs/poste**.
- Ordre exact des machines : **Scie de tête → Bicoupe → Scie de tronçonnage**.
  - Bicoupe : chariot en va-et-vient (coupe à l'aller et au retour ; plateaux par passes successives).
  - Scie de tronçonnage : délignage, éboutage, dédoublage.
- Lames : préventif **toutes les 2 h** ; immédiat à tout **changement d'essence tendre↔dure**.
- Essences (4 seulement) : **Ayous, Azobé, Iroko, Movingui**.
- Point de comptage terrain : **passage fixe AVANT la bicoupe**.
- Benchmarks : Cameroun 60 % (cible) ; pertes scieries 30–36 % ; Afrique centrale ~35 % ; Ouganda ~32 % ; Nigeria 46–58 %.

## Cadre du mémoire (cohérence app <-> mémoire)
4 OS. **OS1** = capacité théorique -> production réelle -> écart + TRS. OS2/OS3/OS4 = anciens OS4/OS5/OS6. Fil conducteur **DMAIC**. Hypothèses **H1–H4**.

## ⚠️ Règles app verrouillées
- Cible : **.exe Windows, 100 % hors ligne, stockage local uniquement**.
- UI **en français**, éléments **larges et tactiles** (saisie opérateur sur le terrain).
- Double usage : BWAME (analyse/export) vs opérateurs (saisie par poste).
- **Code existant** : lire l'existant AVANT toute modification. Ne jamais repartir de zéro.

## Méthode (protocole vibe-coding)
Cadrage avant code, une feature à la fois, screenshots pour l'UI, notes.md tenu à jour, **git commit avant tout changement**.

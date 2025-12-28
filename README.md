# SalleDispo
Application web temps réel pour la gestion et l'affichage des disponibilités de salles universitaires via l'analyse de calendriers ICS.

========================================================================
SalleDispo - APPLICATION DE GESTION DE SALLES EN TEMPS REEL
========================================================================

DESCRIPTION
-----------
SalleDispo est une application web intelligente destinee aux IUT et Universites. 
Elle permet aux etudiants et au personnel de trouver instantanement une salle libre 
pour travailler, en agregeant et en analysant les emplois du temps (fichiers ICS) 
de l'etablissement en temps reel.

L'objectif est d'optimiser l'occupation des locaux et de reduire le temps perdu 
a chercher une salle disponible.

=====================
CONTEXTE ET BESOIN
=====================

1. LE PROBLEME
   - Les emplois du temps changent constamment.
   - Trouver une salle libre implique souvent de verifier physiquement chaque salle.
   - L'information de disponibilite est souvent cloisonnee ou difficile d'acces.

2. LA SOLUTION
   CampusDispo centralise ces donnees dans une interface web responsive :
   - Lecture automatique des calendriers .ics des salles.
   - Calcul en temps reel de l'occupation.
   - Affichage des equipements (PC, Projecteur) et localisation.
   - Systeme de signalement d'incidents materiels.

========================================================================
FONCTIONNALITES CLES
========================================================================

A. RECHERCHE ET FILTRAGE
   - Disponibilite Temps Reel : Algorithme de detection des creneaux libres.
   - Calcul de progression : Barre visuelle indiquant l'avancement du cours actuel.
   - Filtres Avances : Par equipements, localisation (etage, aile) et duree.
   - Tri Automatique : Mise en avant des salles libres.

B. MODE "KIOSQUE" (FONCTIONNALITE TV)
   Une interface dediee aux ecrans TV presents dans les halls ou salles de projet :
   - Accessible sans authentification (Bouton d'acces rapide).
   - Design sombre (Dark Mode) pour le confort visuel et l'economie d'energie.
   - Defilement automatique (Auto-scroll) intelligent pour afficher toutes les salles.
   - Rafraichissement automatique des donnees toutes les 2 minutes.

C. MAINTENANCE ET SIGNALEMENT
   - Formulaire permettant aux utilisateurs de signaler un probleme (panne PC, menage...).
   - Affichage d'une alerte sur le tableau de bord pour prevenir les usagers.
   - Historique des signalements stocke en JSON.

D. SECURITE ET CONFIDENTIALITE
   - Authentification : Distingue les etudiants des administrateurs.
   - Anonymisation : Le detail du cours (nom du professeur) est masque pour les etudiants (RGPD).
   - Filtrage IP (Optionnel) : Restriction de l'acces au reseau Wi-Fi de l'etablissement.

========================================================================
STACK TECHNIQUE
========================================================================

BACKEND : Python (Flask)
   - icalendar : Parsing des fichiers .ics (compatible ADE / Google Calendar).
   - pytz : Gestion des fuseaux horaires (Europe/Paris).
   - Flask-Login : Gestion des sessions utilisateurs.

FRONTEND : HTML5, CSS3, Bootstrap 5.3
   - Interface responsive (Mobile / Desktop / TV).
   - Design moderne type "Glassmorphism".

DONNEES : Stockage Fichier (JSON)
   - Configuration legere ne necessitant pas de serveur SQL lourd.

========================================================================
STRUCTURE DU PROJET
========================================================================

/CampusDispo
|-- app.py                 # Coeur de l'application (Routes, Logique metier)
|-- config.json            # Configuration des salles (Places, Equipements...)
|-- reports.json           # Base de donnees des incidents (generee automatiquement)
|-- requirements.txt       # Liste des dependances Python
|
|-- salleICS/              # Dossier contenant les emplois du temps (.ics)
|   |-- 403.ics            # (Donnees fictives pour la demonstration)
|   |-- ...
|
|-- templates/             # Vues HTML
|   |-- base.html          # Structure principale
|   |-- index.html         # Tableau de bord & Filtres
|   |-- detail.html        # Vue detaillee d'une salle
|   |-- login.html         # Page de connexion
|   |-- tv.html            # Mode Affichage TV
|   |-- acces_refuse.html  # Page de blocage IP
|
|-- generer_test.py        # Script utilitaire pour generer des faux plannings

========================================================================
INSTALLATION ET DEMARRAGE
========================================================================

1. PREREQUIS
   - Python 3.10 ou superieur.

2. INSTALLATION DES DEPENDANCES
   Ouvrez un terminal a la racine du projet et executez :
   pip install -r requirements.txt

   (Si le fichier requirements n'est pas present : pip install flask flask-login icalendar pytz)

3. GENERATION DES DONNEES (DEMO)
   Pour tester l'application avec des donnees simulees :
   python generer_test.py

4. LANCEMENT
   python app.py

   L'application sera accessible a l'adresse : http://127.0.0.1:5001

========================================================================
IDENTIFIANTS ET ACCES
========================================================================

1. COMPTES UTILISATEURS (Pour administration et consultation detaillee)

ROLE        | IDENTIFIANT | MOT DE PASSE | DROITS
----------- | ----------- | ------------ | -------------------------------
Admin       | admin       | iut          | Acces complet, detail des cours
Etudiant    | etudiant    | salle        | Vue anonymisee (Occupé/Libre)

2. ACCES AFFICHAGE DYNAMIQUE (TV)
   - Pas d'identifiant requis.
   - Acces via le bouton "Mode TV" sur la page de connexion.
   - Acces direct via l'URL : /tv

========================================================================
NOTE SUR LA CONFIDENTIALITE (RGPD)
========================================================================

Ce code source contient uniquement des donnees fictives dans le dossier 
/salleICS a des fins de demonstration technique.

Dans un environnement de production, ce dossier doit etre peuple avec les 
exports ICS reels de l'etablissement. Le fichier .gitignore doit etre 
configure pour exclure ces fichiers reels du systeme de versionning.

========================================================================
AUTEUR ET DEVELOPPEMENT
========================================================================

Auteur : Heurtebise Johan
Projet personnel developpe en autonomie (etudiant en BUT Reseaux & Telecoms).

Note de developpement : 
Ce projet a ete developpe avec l'assistance d'outils d'Intelligence Artificielle 
pour l'optimisation des algorithmes de tri, la structure du code Flask et 
la generation de la documentation technique.

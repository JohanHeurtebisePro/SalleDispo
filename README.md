# SALLEDISPO - GESTIONNAIRE DE SALLES EN TEMPS REEL

## DESCRIPTION

SalleDispo est une application web intelligente destinée aux IUT et Universités. Elle permet aux étudiants et au personnel de trouver instantanément une salle libre pour travailler, en agrégeant et en analysant les emplois du temps (fichiers ICS) de l'établissement en temps réel.

L'objectif est d'optimiser l'occupation des locaux et de réduire le temps perdu à chercher une salle disponible dans les couloirs.

---

## CONTEXTE ET BESOIN

### 1. Le Problème
* Les emplois du temps changent constamment et les informations sur l'ENT ne sont pas toujours faciles d'accès rapidement.
* Trouver une salle libre implique souvent de vérifier physiquement chaque salle.
* L'information de disponibilité est souvent cloisonnée.

### 2. La Solution
SalleDispo centralise ces données dans une interface web responsive :
* Lecture automatique des calendriers ICS des salles (compatible exports ADE/ENT).
* Calcul en temps réel de l'occupation (Libre / Occupé / Bientôt occupée).
* Affichage des équipements (PC, Projecteur) et de la localisation.
* Système collaboratif de signalement d'incidents matériels.

---

## FONCTIONNALITES CLES

### A. Recherche et Filtrage Avancé
* **Disponibilité Temps Réel :** Algorithme de détection des créneaux libres avec gestion précise des fuseaux horaires.
* **Calcul de progression :** Barre visuelle indiquant l'avancement du cours actuel (pour savoir si la salle se libère bientôt).
* **Filtres Multi-critères :** Possibilité de filtrer par équipements (PC, Vidéo-projecteur), par localisation (étage, aile gauche/droite) et par durée disponible minimale.
* **Tri Automatique :** Mise en avant prioritaire des salles libres.

### B. Mode Kiosque (Fonctionnalité TV)
Une interface spécifique dédiée aux écrans TV présents dans les halls d'entrée ou les salles de projet :
* **Accessible sans authentification** via un bouton d'accès rapide.
* **Design "Dark Mode"** (Fond noir) pour le confort visuel et la protection des écrans.
* **Défilement automatique (Auto-scroll)** intelligent pour afficher l'ensemble des salles sans interaction humaine.
* **Rafraîchissement automatique** des données toutes les 2 minutes.

### C. Maintenance et Signalement
* Formulaire permettant aux utilisateurs de signaler un problème technique (panne PC, ménage nécessaire, matériel manquant).
* Affichage d'une alerte visuelle sur le tableau de bord pour prévenir les autres usagers.
* Historique des signalements stocké dans un fichier JSON persistant.

### D. Sécurité et Confidentialité
* **Authentification :** Distinction des rôles entre "Étudiant" (Vue restreinte) et "Administrateur" (Vue détaillée).
* **Anonymisation RGPD :** Le détail du cours (nom du professeur, matière exacte) est masqué pour les étudiants (remplacé par "Occupé"), seul l'administrateur voit le détail.
* **Filtrage IP (Optionnel) :** Fonctionnalité de restriction d'accès permettant d'autoriser l'application uniquement depuis le réseau Wi-Fi de l'établissement (protection contre les accès extérieurs).

---

## STACK TECHNIQUE

* **Backend :** Python 3.10+ avec Framework Flask.
    * Librairie `icalendar` : Parsing des fichiers ICS.
    * Librairie `pytz` : Gestion des fuseaux horaires (Europe/Paris).
    * `Flask-Login` : Gestion sécurisée des sessions utilisateurs.
* **Frontend :** HTML5, CSS3, Bootstrap 5.3.
    * Interface responsive adaptée aux Mobiles, Desktop et Ecrans TV.
    * Design moderne type "Glassmorphism".
* **Données :** Stockage Fichier (JSON).
    * Architecture légère sans base de données SQL (NoSQL file-based) pour faciliter le déploiement et la maintenance.

---

## STRUCTURE DU PROJET

```text
/SalleDispo
│
├── app.py                 # Coeur de l'application (Routes Flask, Logique metier, Securite)
├── config.json            # Configuration des salles (Nombre de places, Equipements, Etage...)
├── reports.json           # Base de donnees des incidents (generee automatiquement)
├── requirements.txt       # Liste des dependances Python necessaires
│
├── salleICS/              # Dossier contenant les emplois du temps (.ics)
│   ├── 403.ics            # (Fichiers fictifs pour la demonstration publique)
│   └── ...
│
├── templates/             # Vues HTML (Templates Jinja2)
│   ├── base.html          # Structure principale (Header, Navbar)
│   ├── index.html         # Tableau de bord principal & Filtres
│   ├── detail.html        # Vue detaillee d'une salle spécifique
│   ├── login.html         # Page de connexion
│   ├── tv.html            # Interface dediee au mode Affichage Dynamique
│   └── acces_refuse.html  # Page de blocage pour le filtrage IP
│
└── generer_test.py        # Script utilitaire pour generer des faux plannings de test

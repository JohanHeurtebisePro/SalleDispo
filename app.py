"""
PROJET : SalleDispo
AUTEUR : Heurtebise Johan
DATE   : 2025
DESCRIPTION :
    Application Flask de gestion de salles en temps réel pour Universités.
    Ce script assure le backend : lecture des fichiers ICS, gestion des utilisateurs,
    traitement des données calendaires et routage des pages web.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from icalendar import Calendar
from datetime import datetime, timedelta
import pytz
import os
import json
import locale
import re

app = Flask(__name__)

# =========================================================
# 🔐 SÉCURITÉ : GESTION DE LA CLÉ SECRÈTE
# =========================================================
# On récupère la clé depuis une variable d'environnement système.
# Si la variable n'existe pas (ex: en dev local), on utilise une clé par défaut.
# EN PROD : Définissez la variable d'environnement 'FLASK_SECRET_KEY'
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'cle_par_defaut_dev_a_changer_en_prod')

# =========================================================
# 🔐 CONFIGURATION LOGIN (Flask-Login)
# =========================================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirige l'utilisateur ici s'il n'est pas connecté

# Base de données utilisateurs simulée pour la démonstration.
# Dans un environnement de production, remplacer par une connexion LDAP ou SQL.
USERS_DB = {
    "admin": "admin",      # Accès Administrateur
}

class User(UserMixin):
    """Classe Utilisateur standard pour la gestion de session Flask-Login."""
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    """Charge l'utilisateur à partir de l'ID stocké dans la session."""
    if user_id in USERS_DB:
        return User(user_id)
    return None

# =========================================================
# 📁 CONFIGURATION DES CHEMINS ET FICHIERS
# =========================================================

# ⚠️ NOTE POUR GITHUB : Ce chemin est absolu et spécifique à la machine de développement.
# En production, utilisez un chemin relatif ou une variable d'environnement.
DOSSIER_CIBLE = "salleICS/"

# Chemins dynamiques basés sur l'emplacement du fichier app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FICHIER_CONFIG = os.path.join(BASE_DIR, "config.json")
FICHIER_REPORTS = os.path.join(BASE_DIR, "reports.json")

# Tentative de configuration de la locale en Français pour l'affichage des dates
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except:
    pass # Fallback sur la locale par défaut si fr_FR n'est pas installée

# =========================================================
# 🛠️ FONCTIONS UTILITAIRES (HELPERS)
# =========================================================

def get_reports(nom_salle):
    """Récupère la liste des incidents signalés pour une salle spécifique."""
    if not os.path.exists(FICHIER_REPORTS): return []
    try:
        with open(FICHIER_REPORTS, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(nom_salle, [])
    except: return []

def add_report(nom_salle, type_pb, description):
    """
    Enregistre un nouveau signalement d'incident dans le fichier JSON.
    Gère la persistance des données sans base de données SQL.
    """
    data = {}
    if os.path.exists(FICHIER_REPORTS):
        try:
            with open(FICHIER_REPORTS, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: pass
    
    if nom_salle not in data: data[nom_salle] = []
    
    # Détermine l'auteur : User ID si connecté, sinon "Public/TV"
    auteur = "Public/TV"
    if current_user.is_authenticated:
        auteur = current_user.id

    nouveau = {
        "type": type_pb,
        "desc": description,
        "date": datetime.now().strftime("%d/%m à %H:%M"),
        "auteur": auteur
    }
    # Insertion en début de liste pour avoir les plus récents en premier
    data[nom_salle].insert(0, nouveau)
    
    with open(FICHIER_REPORTS, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_infos_manuelles(nom_salle):
    """
    Charge les métadonnées statiques d'une salle (places, équipements) 
    depuis le fichier config.json.
    """
    default = {"nom_complet": f"Salle {nom_salle}", "places": "?", "pc": False, "projecteur": False, "description": "Pas d'info."}
    if not os.path.exists(FICHIER_CONFIG): return default
    try:
        with open(FICHIER_CONFIG, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(nom_salle, default)
    except: return default

def detecter_etage_aile(nom_simple, infos):
    """
    Algorithme heuristique pour déterminer l'étage et l'aile d'une salle
    basé sur son numéro (ex: 204 -> 2ème étage) ou la configuration manuelle.
    """
    etage = 0
    if "etage" in infos: etage = int(infos["etage"])
    elif nom_simple[0].isdigit(): etage = int(nom_simple[0])
    
    aile = "centre"
    if "aile" in infos: 
        aile = infos["aile"]
    else:
        # Logique par défaut : Pair = Droite, Impair = Gauche
        chiffres = re.findall(r'\d+', nom_simple)
        if chiffres:
            num = int(chiffres[0])
            aile = "droite" if num % 2 == 0 else "gauche"
    return etage, aile

# =========================================================
# 🧠 CŒUR DU SYSTÈME : ANALYSE DES ICS (LOGIQUE MÉTIER)
# =========================================================

def verifier_dispo_creneau(nom_fichier, start_req, end_req):
    """
    Vérifie si une salle est libre sur un créneau spécifique (pour les filtres).
    Retourne True si libre, False si occupée.
    """
    chemin = os.path.join(DOSSIER_CIBLE, nom_fichier)
    try:
        with open(chemin, 'rb') as f: cal = Calendar.from_ical(f.read())
        tz_paris = pytz.timezone('Europe/Paris')
        
        # Localisation des dates requises pour comparaison timezone-aware
        if start_req.tzinfo is None: start_req = tz_paris.localize(start_req)
        if end_req.tzinfo is None: end_req = tz_paris.localize(end_req)

        for component in cal.walk():
            if component.name == "VEVENT":
                dtstart_prop = component.get('dtstart')
                dtend_prop = component.get('dtend')
                if not dtstart_prop or not dtend_prop: continue
                
                dtstart = dtstart_prop.dt
                dtend = dtend_prop.dt

                # Normalisation des types de dates (Date vs DateTime)
                if not isinstance(dtstart, datetime):
                    dtstart = datetime.combine(dtstart, datetime.min.time())
                    dtend = datetime.combine(dtend, datetime.min.time())
                    dtstart = tz_paris.localize(dtstart)
                    dtend = tz_paris.localize(dtend)
                else:
                    if not hasattr(dtstart, 'tzinfo') or dtstart.tzinfo is None:
                        dtstart = tz_paris.localize(dtstart)
                        dtend = tz_paris.localize(dtend)
                    else:
                        dtstart = dtstart.astimezone(tz_paris)
                        dtend = dtend.astimezone(tz_paris)
                
                # Vérification de chevauchement de créneaux
                if dtstart < end_req and dtend > start_req:
                    return False
        return True
    except: return False

def get_salle_status(nom_fichier):
    """
    Analyse le fichier ICS pour déterminer l'état actuel de la salle :
    - OCCUPÉ (avec progression)
    - LIBRE (avec indication du prochain cours)
    - ERREUR (si fichier corrompu)
    """
    chemin_complet = os.path.join(DOSSIER_CIBLE, nom_fichier)
    if not os.path.exists(chemin_complet):
        return {"etat": "ERREUR", "color": "secondary", "msg": "Introuvable", "sub_msg": "", "progression": 0}

    try:
        with open(chemin_complet, 'rb') as f: 
            cal = Calendar.from_ical(f.read())
            
        # Utilisation stricte du fuseau Paris pour éviter les décalages UTC
        tz_paris = pytz.timezone('Europe/Paris')
        maintenant = datetime.now(tz_paris)
        
        prochain_cours = None
        delta_min = float('inf')
        cours_trouve = False
        
        for component in cal.walk():
            if component.name == "VEVENT":
                dtstart_prop = component.get('dtstart')
                dtend_prop = component.get('dtend')
                if not dtstart_prop or not dtend_prop: continue
                
                dtstart = dtstart_prop.dt
                dtend = dtend_prop.dt
                summary = str(component.get('summary')).replace('\\,', ',')

                # --- FIX COMPATIBILITÉ GOOGLE CALENDAR ---
                # Convertit les événements "Journée entière" (Date) en DateTime (Minuit)
                # pour permettre la comparaison avec "maintenant".
                if not isinstance(dtstart, datetime):
                    dtstart = datetime.combine(dtstart, datetime.min.time())
                    dtend = datetime.combine(dtend, datetime.min.time())
                    dtstart = tz_paris.localize(dtstart)
                    dtend = tz_paris.localize(dtend)
                else:
                    if not hasattr(dtstart, 'tzinfo') or dtstart.tzinfo is None:
                        dtstart = tz_paris.localize(dtstart)
                        dtend = tz_paris.localize(dtend)
                    else:
                        dtstart = dtstart.astimezone(tz_paris)
                        dtend = dtend.astimezone(tz_paris)
                # ---------------------------------------

                # 1. CAS OCCUPÉ : L'heure actuelle est dans le créneau
                if dtstart <= maintenant <= dtend:
                    fin_txt = dtend.strftime("%H:%M")
                    # Calcul du % de progression pour la barre visuelle
                    total = (dtend - dtstart).total_seconds()
                    ecoule = (maintenant - dtstart).total_seconds()
                    prog = int((ecoule/total)*100) if total > 0 else 100
                    return {"etat": "OCCUPÉ", "color": "danger", "msg": summary, "sub_msg": f"Fin à {fin_txt}", "progression": prog}

                # 2. CAS PROCHAIN COURS : On cherche le cours futur le plus proche
                if dtstart > maintenant:
                    cours_trouve = True
                    delta = (dtstart - maintenant).total_seconds()
                    if delta < delta_min:
                        delta_min = delta
                        debut_txt = dtstart.strftime("%H:%M")
                        if len(summary) > 30: summary = summary[:30] + "..."
                        prochain_cours = f"{debut_txt} : {summary}"

        # 3. RETOUR DE L'ÉTAT LIBRE
        if prochain_cours:
            return {"etat": "LIBRE", "color": "success", "msg": "Libre", "sub_msg": f"Prochain : {prochain_cours}", "progression": 0}
        elif cours_trouve:
            return {"etat": "LIBRE", "color": "success", "msg": "Libre", "sub_msg": "Plus de cours auj.", "progression": 0}
        else:
            return {"etat": "LIBRE", "color": "success", "msg": "Libre", "sub_msg": "Planning vide", "progression": 0}

    except Exception as e:
        print(f"❌ Erreur lecture {nom_fichier} : {e}")
        return {"etat": "ERREUR", "color": "warning", "msg": "Erreur", "sub_msg": "Fichier corrompu", "progression": 0}

def get_planning_etendu(nom_fichier):
    """
    Récupère la liste des événements des 15 prochains jours pour l'affichage détaillé.
    Retourne une liste de dictionnaires triés par date.
    """
    chemin_complet = os.path.join(DOSSIER_CIBLE, nom_fichier)
    liste_evenements = []
    try:
        with open(chemin_complet, 'rb') as f: 
            cal = Calendar.from_ical(f.read())
            
        tz_paris = pytz.timezone('Europe/Paris')
        maintenant = datetime.now(tz_paris)
        fin = maintenant + timedelta(days=15)
        
        for component in cal.walk():
            if component.name == "VEVENT":
                # ... (Logique identique de parsing et conversion de dates) ...
                dtstart_prop = component.get('dtstart')
                dtend_prop = component.get('dtend')
                if not dtstart_prop: continue
                
                dtstart = dtstart_prop.dt
                # Gestion de la fin d'événement (parfois manquante)
                if dtend_prop: dtend = dtend_prop.dt
                else: dtend = dtstart
                
                summary = str(component.get('summary')).replace('\\,', ',')

                if not isinstance(dtstart, datetime):
                    dtstart = datetime.combine(dtstart, datetime.min.time())
                    if not isinstance(dtend, datetime):
                        dtend = datetime.combine(dtend, datetime.min.time())
                    dtstart = tz_paris.localize(dtstart)
                    dtend = tz_paris.localize(dtend)
                else:
                    if not hasattr(dtstart, 'tzinfo') or dtstart.tzinfo is None:
                        dtstart = tz_paris.localize(dtstart)
                        dtend = tz_paris.localize(dtend)
                    else:
                        dtstart = dtstart.astimezone(tz_paris)
                        dtend = dtend.astimezone(tz_paris)

                # Filtre : Seulement les événements futurs sur 15 jours
                if dtend > maintenant and dtstart < fin:
                    liste_evenements.append({
                        "date_iso": dtstart.strftime("%Y-%m-%d"),
                        "jour_joli": dtstart.strftime("%A %d %B").capitalize(),
                        "horaire": f"{dtstart.strftime('%H:%M')} - {dtend.strftime('%H:%M')}",
                        "titre": summary,
                        "timestamp": dtstart.timestamp()
                    })
        # Tri chronologique important pour l'affichage
        liste_evenements.sort(key=lambda x: x['timestamp'])
        return liste_evenements
    except Exception as e:
        print(f"❌ Erreur planning {nom_fichier} : {e}")
        return []

# =========================================================
# 🚦 ROUTES FLASK (CONTROLLERS)
# =========================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Gère la page de connexion et l'authentification."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS_DB and USERS_DB[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Identifiants incorrects")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnecte l'utilisateur et le renvoie au login."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """
    PAGE D'ACCUEIL (Tableau de bord).
    Affiche la liste des salles avec leur statut en temps réel.
    Gère les filtres (Recherche, PC, Projecteur, Temps...).
    """
    if not os.path.exists(DOSSIER_CIBLE): return f"Erreur dossier ICS"
    tous_fichiers = os.listdir(DOSSIER_CIBLE)
    fichiers_ics = [f for f in tous_fichiers if f.lower().endswith('.ics')]
    
    # Récupération des paramètres GET (Filtres)
    q = request.args.get('q')
    f_pc = request.args.get('pc')
    f_proj = request.args.get('proj')
    f_etage = request.args.get('etage')
    f_aile = request.args.get('aile')
    f_duree = request.args.get('duree_min')
    f_heure_debut = request.args.get('heure_debut')
    f_heure_fin = request.args.get('heure_fin')
    
    # Préparation des objets datetime pour le filtrage temporel
    req_start, req_end = None, None
    tz_paris = pytz.timezone('Europe/Paris')
    now = datetime.now(tz_paris)
    
    if f_heure_debut and f_heure_fin:
        h_d, m_d = map(int, f_heure_debut.split(':'))
        h_f, m_f = map(int, f_heure_fin.split(':'))
        req_start = now.replace(hour=h_d, minute=m_d, second=0, microsecond=0)
        req_end = now.replace(hour=h_f, minute=m_f, second=0, microsecond=0)
        if req_end < req_start: req_end += timedelta(days=1)
    elif f_duree and f_duree.isdigit():
        req_start = now
        req_end = now + timedelta(minutes=int(f_duree))

    liste_salles = []
    
    # Boucle principale sur chaque fichier salle
    for f in fichiers_ics:
        nom_simple = f.replace('.ics', '').replace('.ICS', '')
        infos = get_infos_manuelles(nom_simple)
        etage, aile = detecter_etage_aile(nom_simple, infos)
        
        # Application des filtres
        keep = True
        if q and q.lower() not in nom_simple.lower(): keep = False
        if f_pc and not infos.get('pc'): keep = False
        if f_proj and not infos.get('projecteur'): keep = False
        if f_etage and f_etage != "" and str(etage) != f_etage: keep = False
        if f_aile and f_aile != "" and aile != f_aile: keep = False
        
        # Filtre de disponibilité complexe
        if keep and req_start and req_end:
            if not verifier_dispo_creneau(f, req_start, req_end): keep = False

        # Si la salle correspond aux critères, on calcule son statut
        if keep:
            status = get_salle_status(f)
            incidents = get_reports(nom_simple)
            infos['has_issue'] = (len(incidents) > 0)
            
            infos['etage_calc'] = etage
            infos['aile_calc'] = aile
            liste_salles.append({'nom': nom_simple, 'fichier': f, 'status': status, 'infos': infos})

    # Tri alphabétique par défaut
    liste_salles.sort(key=lambda x: x['nom'])
    
    return render_template('index.html', salles=liste_salles, 
                           q=q, f_pc=f_pc, f_proj=f_proj, f_etage=f_etage, f_aile=f_aile,
                           f_duree=f_duree, f_heure_debut=f_heure_debut, f_heure_fin=f_heure_fin)

@app.route('/salle/<nom_fichier>')
@login_required
def detail(nom_fichier):
    """Page de détail d'une salle : Status, Infos, Planning futur et Signalements."""
    nom_simple = nom_fichier.replace('.ics', '').replace('.ICS', '')
    etat = get_salle_status(nom_fichier)
    infos = get_infos_manuelles(nom_simple)
    planning = get_planning_etendu(nom_fichier)
    etage, aile = detecter_etage_aile(nom_simple, infos)
    incidents = get_reports(nom_simple)
    
    return render_template('detail.html', 
                           nom=nom_simple, etat=etat, infos=infos, 
                           planning=planning, etage_courant=etage, aile=aile,
                           incidents=incidents)

@app.route('/signaler/<nom_salle>', methods=['POST'])
def signaler(nom_salle):
    """Traitement du formulaire de signalement d'incident."""
    type_pb = request.form.get('type_probleme')
    description = request.form.get('description')
    if type_pb: add_report(nom_salle, type_pb, description)
        
    fichier_redir = f"{nom_salle}.ics"
    # Recherche du bon fichier .ics pour la redirection
    for f in os.listdir(DOSSIER_CIBLE):
        if nom_salle == f.replace('.ics', '').replace('.ICS', ''):
            fichier_redir = f
            break
    return redirect(url_for('detail', nom_fichier=fichier_redir))

# =========================================================
# 📺 ROUTE TV (MODE KIOSQUE)
# =========================================================
@app.route('/tv')
def tv_mode():
    """
    Mode Affichage Dynamique (Digital Signage).
    Cette route n'est PAS protégée par @login_required pour permettre
    l'affichage sur des écrans sans clavier/souris.
    """
    if not os.path.exists(DOSSIER_CIBLE): return "Erreur dossier"
    tous_fichiers = os.listdir(DOSSIER_CIBLE)
    fichiers_ics = [f for f in tous_fichiers if f.lower().endswith('.ics')]
    
    liste_salles = []
    
    for f in fichiers_ics:
        nom_simple = f.replace('.ics', '').replace('.ICS', '')
        infos = get_infos_manuelles(nom_simple)
        status = get_salle_status(f)
        etage, aile = detecter_etage_aile(nom_simple, infos)
        
        infos['etage_calc'] = etage
        infos['aile_calc'] = aile
        
        liste_salles.append({'nom': nom_simple, 'status': status, 'infos': infos})

    # TRI SPÉCIFIQUE TV :
    # 1. Les salles LIBRES en priorité (pour lecture rapide)
    # 2. Puis tri alphabétique
    liste_salles.sort(key=lambda x: (0 if x['status']['etat'] == 'LIBRE' else 1, x['nom']))
    
    return render_template('tv.html', salles=liste_salles)

if __name__ == '__main__':
    # Lancement du serveur en mode Debug pour le développement
    app.run(host='0.0.0.0', port=5001, debug=True)
# 🗺️ Maps Scraper - Scraper Google Maps pour entreprises tech en Suisse Romande

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Configuration VPS](#configuration-vps)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Base de données](#base-de-données)
- [Services et processus](#services-et-processus)
- [Sécurité](#sécurité)
- [Maintenance](#maintenance)
- [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

Application web complète de scraping Google Maps pour récupérer automatiquement les informations d'entreprises tech en Suisse Romande (canton de Neuchâtel en priorité).

### Fonctionnalités

- ✅ Scraping automatique Google Maps (nom, adresse, téléphone, site web, note, avis)
- ✅ Validation DNS des emails (rejet des emails fictifs)
- ✅ Extraction emails depuis les sites web des entreprises
- ✅ Rotation des User-Agents pour éviter la détection
- ✅ Système de checkpoint (reprise automatique après interruption)
- ✅ Interface web avec dashboard temps réel
- ✅ Filtres avancés (ville, présence site/email)
- ✅ Export CSV avec filtres appliqués
- ✅ Logs en temps réel du scraping
- ✅ Récupération automatique en cas d'erreur navigateur
- ✅ Base de données SQLite
- ✅ Authentication HTTP Basic
- ✅ Responsive (mobile, tablette, desktop)

---

## 🏗️ Architecture

### Architecture globale

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    VPS Ubuntu 25.04                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Nginx (port 80)                                     │  │
│  │  - Reverse proxy                                     │  │
│  │  - HTTP Basic Auth (.htpasswd)                      │  │
│  │  - Gestion SSL (si configuré)                       │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Gunicorn (127.0.0.1:5000)                          │  │
│  │  - 2 workers                                         │  │
│  │  - WSGI Server                                       │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│                     ▼                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Flask Application (backend/app.py)                  │  │
│  │  - API REST                                          │  │
│  │  - Gestion scraper                                   │  │
│  │  - Streaming logs                                    │  │
│  └──────┬────────────────────────────┬──────────────────┘  │
│         │                            │                      │
│         ▼                            ▼                      │
│  ┌─────────────┐            ┌──────────────────┐          │
│  │  Frontend   │            │  Backend         │          │
│  │  (HTML/CSS) │            │  scraper_suisse  │          │
│  │  /JS)       │            │  _romande.py     │          │
│  └─────────────┘            └────────┬─────────┘          │
│                                      │                      │
│                                      ▼                      │
│                             ┌──────────────────┐           │
│                             │  companies.db    │           │
│                             │  (SQLite)        │           │
│                             └──────────────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Flux de données

```
1. Utilisateur → Nginx (auth) → Gunicorn → Flask → Interface web
2. Clic "Démarrer" → Flask lance scraper_suisse_romande.py
3. Scraper → Google Maps → Extraction données → SQLite
4. Interface web → API Flask → Lecture SQLite → Affichage temps réel
```

---

## 🛠️ Stack technique

### Backend
- **Python 3.13** (compatible)
- **Flask 3.0.0** - Framework web
- **Gunicorn 21.2.0** - WSGI server
- **Playwright 1.48.0** - Automatisation navigateur (Firefox + Chromium)
- **BeautifulSoup4** - Parsing HTML
- **Pandas 2.2.0+** - Manipulation données
- **SQLite3** - Base de données
- **dnspython** - Validation DNS emails
- **email-validator** - Validation emails

### Frontend
- **HTML5/CSS3/JavaScript** (Vanilla, pas de framework)
- **Design responsive** (mobile-first)
- **Fetch API** pour les appels AJAX

### Infrastructure
- **Nginx** - Reverse proxy + authentification
- **Systemd** - Gestion des services
- **UFW** - Firewall
- **Git** - Versioning

### Serveur
- **OS** : Ubuntu 25.04 (Plucky)
- **Utilisateur** : `ubuntu`
- **Répertoire** : `/home/ubuntu/maps-scraper`

---

## ⚙️ Configuration VPS

### État actuel du VPS

#### Services actifs

```bash
# Service principal (web interface)
scraper-web.service
├─ Status: active (running)
├─ Port: 127.0.0.1:5000
├─ User: ubuntu
├─ WorkingDirectory: /home/ubuntu/maps-scraper/backend
└─ Command: gunicorn --bind 127.0.0.1:5000 app:app --workers 2
```

#### Ports ouverts (UFW)

| Port | Service | Description |
|------|---------|-------------|
| 22   | SSH     | Accès administrateur |
| 80   | HTTP    | Interface web (Nginx) |
| 443  | HTTPS   | SSL (si configuré) |

#### Structure fichiers VPS

```
/home/ubuntu/maps-scraper/
├── backend/
│   ├── app.py                      # API Flask
│   ├── scraper_suisse_romande.py  # Script scraping
│   ├── companies.db                # Base de données SQLite
│   ├── checkpoint.json             # Progression scraping
│   ├── intermediate_data.csv       # Données temporaires
│   ├── scraper.log                 # Logs du scraper
│   └── utils/
│       ├── clean_and_deduce_emails.py
│       └── verify_emails.py
├── frontend/
│   ├── index.html                  # Interface web
│   ├── style.css                   # Styles
│   └── script.js                   # Logique frontend
├── scripts/
│   ├── install.sh                  # Script installation VPS
│   └── change_password.py          # Utilitaire changement mot de passe
├── docs/
│   ├── INSTALL.md                  # Documentation installation
│   ├── UPDATE.md                   # Procédure mise à jour
│   └── CHANGE_PASSWORD.md          # Changer mot de passe admin
├── venv/                           # Environnement virtuel Python
├── requirements.txt                # Dépendances Python
├── .env                            # Variables d'environnement
├── .gitignore
└── README.md
```

#### Configuration Nginx

**Fichier** : `/etc/nginx/sites-available/scraper`

```nginx
server {
    listen 80;
    server_name _;

    # Authentification HTTP Basic
    auth_basic "Scraper Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Pour le streaming des logs
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
```

#### Configuration Systemd

**Fichier** : `/etc/systemd/system/scraper-web.service`

```ini
[Unit]
Description=Scraper Google Maps - Web Interface
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/maps-scraper/backend
Environment="PATH=/home/ubuntu/maps-scraper/venv/bin"
EnvironmentFile=/home/ubuntu/maps-scraper/.env
ExecStart=/home/ubuntu/maps-scraper/venv/bin/gunicorn --bind 127.0.0.1:5000 app:app --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Variables d'environnement (.env)

```bash
WEB_USERNAME=admin
WEB_PASSWORD=VotreMotDePasseIci
DATABASE_PATH=companies.db
FLASK_ENV=production
```

---

## 📦 Installation

### Installation initiale sur VPS

```bash
# 1. Se connecter au VPS
ssh ubuntu@<IP_VPS>

# 2. Cloner le projet
git clone https://github.com/votre-compte/maps-scraper.git
cd maps-scraper

# 3. Lancer l'installation automatique
sudo ./scripts/install.sh
```

Le script `install.sh` effectue :
- ✅ Mise à jour du système
- ✅ Installation dépendances système (libxml2, libxslt, pkg-config, etc.)
- ✅ Installation Python 3.13 + pip
- ✅ Création environnement virtuel
- ✅ Installation dépendances Python
- ✅ Installation Playwright (Firefox + Chromium)
- ✅ Configuration Nginx (reverse proxy + auth)
- ✅ Création service systemd
- ✅ Configuration firewall (UFW)
- ✅ Génération `.env` avec identifiants

### Installation en local (développement)

```bash
# 1. Cloner le projet
git clone https://github.com/votre-compte/maps-scraper.git
cd maps-scraper

# 2. Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Installer Playwright
playwright install firefox chromium

# 5. Créer le fichier .env
cp env.example .env
# Modifier .env avec vos identifiants

# 6. Lancer l'application
./start_local.sh
```

Accès : `http://localhost:8080`

---

## 🚀 Utilisation

### Accès à l'interface web

**URL** : `http://<IP_VPS>`

**Identifiants** : Ceux configurés dans `.env` lors de l'installation

### Fonctionnalités de l'interface

#### 1. Dashboard
- Statistiques temps réel
  - Total entreprises
  - Avec site web
  - Avec email
  - Dernière mise à jour
- Top 10 villes
- Contrôle du scraper (Démarrer/Arrêter)
- Statut et progression

#### 2. Filtres
- Par ville (dropdown)
- Avec site web (checkbox)
- Avec email (checkbox)
- Application en temps réel

#### 3. Liste des entreprises
- Tableau avec toutes les données
- Liens cliquables (site web, Maps)
- Tri par colonnes
- Export CSV avec filtres

#### 4. Logs en temps réel
- Affichage des logs du scraper
- Scroll automatique
- Couleurs selon type (success, error, warning, info)
- Bouton "Voir les logs"

### Commandes serveur

```bash
# Voir le statut du service
sudo systemctl status scraper-web

# Redémarrer le service
sudo systemctl restart scraper-web

# Arrêter le service
sudo systemctl stop scraper-web

# Démarrer le service
sudo systemctl start scraper-web

# Voir les logs en temps réel
sudo journalctl -u scraper-web -f

# Voir les logs du scraper
tail -f ~/maps-scraper/backend/scraper.log

# Vérifier si le scraper est actif
ps aux | grep scraper_suisse_romande.py
```

---

## 📊 Base de données

### Structure SQLite (companies.db)

```sql
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    maps_link TEXT UNIQUE,
    city TEXT,
    tag TEXT,                    -- Mot-clé de recherche
    address TEXT,
    phone TEXT,
    website TEXT,
    rating REAL,                 -- Note Google (0-5)
    reviews_count INTEGER,       -- Nombre d'avis
    email TEXT,                  -- Emails validés (séparés par virgule)
    social_links TEXT,           -- Liens sociaux (LinkedIn, etc.)
    status TEXT,                 -- 'Harvested', 'Enriched', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Accès direct à la BDD

```bash
cd ~/maps-scraper/backend
sqlite3 companies.db

# Commandes SQLite utiles
.tables                          # Lister les tables
.schema companies                # Voir la structure
SELECT COUNT(*) FROM companies;  # Nombre total
SELECT * FROM companies LIMIT 5; # Premiers résultats
.exit                            # Quitter
```

---

## 🔧 Services et processus

### Service web (scraper-web.service)

**Rôle** : Lance et maintient l'interface web Flask

**Gestion** :
```bash
sudo systemctl start scraper-web    # Démarrer
sudo systemctl stop scraper-web     # Arrêter
sudo systemctl restart scraper-web  # Redémarrer
sudo systemctl status scraper-web   # Statut
sudo systemctl enable scraper-web   # Auto-démarrage au boot
```

**Logs** :
```bash
sudo journalctl -u scraper-web -f   # Logs temps réel
sudo journalctl -u scraper-web -n 100  # 100 dernières lignes
```

### Processus de scraping

**Démarrage** : Via l'interface web (bouton "Démarrer")

**Script** : `backend/scraper_suisse_romande.py`

**Logs** : `backend/scraper.log`

**Caractéristiques** :
- Tourne en arrière-plan (subprocess)
- Indépendant du service web
- Continue même si vous fermez votre navigateur
- Peut être arrêté via l'interface web

**Vérification manuelle** :
```bash
# Voir si le scraper tourne
ps aux | grep scraper_suisse_romande.py

# Arrêter manuellement (si nécessaire)
pkill -f scraper_suisse_romande.py
```

---

## 🔐 Sécurité

### Authentification

**Type** : HTTP Basic Authentication (Nginx)

**Fichier** : `/etc/nginx/.htpasswd`

**Format** : `username:password_hash`

### Changer le mot de passe

**Méthode 1 : Script automatique**
```bash
cd ~/maps-scraper
python3 scripts/change_password.py
sudo systemctl restart scraper-web
```

**Méthode 2 : Manuel**
```bash
cd ~/maps-scraper
nano .env
# Modifier WEB_PASSWORD=NouveauMotDePasse
sudo htpasswd -c /etc/nginx/.htpasswd admin
sudo systemctl restart nginx
sudo systemctl restart scraper-web
```

### Firewall (UFW)

```bash
# Voir les règles actives
sudo ufw status

# Ouvrir un port (si besoin)
sudo ufw allow 81/tcp

# Fermer un port
sudo ufw delete allow 81/tcp
```

### Bonnes pratiques

- ✅ Ne jamais committer le fichier `.env`
- ✅ Utiliser des mots de passe forts (12+ caractères)
- ✅ Changer les identifiants par défaut
- ✅ Maintenir le système à jour (`apt update && apt upgrade`)
- ✅ Surveiller les logs régulièrement
- ⚠️ Ne pas exposer la BDD SQLite publiquement

---

## 🔄 Maintenance

### Mise à jour du code

**Sur votre machine locale** :
```bash
cd ~/test/maps-scrap
git add .
git commit -m "Description des changements"
git push origin main
```

**Sur le VPS** :
```bash
cd ~/maps-scraper
git pull origin main

# Si nouvelles dépendances
source venv/bin/activate
pip install -r requirements.txt

# Recharger systemd si service modifié
sudo systemctl daemon-reload

# Redémarrer le service
sudo systemctl restart scraper-web
```

📖 **Guide complet** : `docs/UPDATE.md`

### Sauvegarde de la base de données

```bash
# Créer une sauvegarde
cp ~/maps-scraper/backend/companies.db ~/companies_backup_$(date +%Y%m%d).db

# Télécharger la BDD en local (depuis votre machine)
scp ubuntu@<IP_VPS>:~/maps-scraper/backend/companies.db ./companies_local.db
```

### Nettoyage

```bash
# Supprimer les fichiers temporaires
cd ~/maps-scraper/backend
rm -f checkpoint.json intermediate_data.csv scraper.log

# Vider la BDD (⚠️ ATTENTION)
sqlite3 companies.db "DELETE FROM companies;"
```

---

## 🐛 Dépannage

### Problèmes courants

#### 1. Service ne démarre pas

```bash
# Voir les erreurs
sudo journalctl -u scraper-web -n 50

# Vérifier le port 5000
sudo lsof -i :5000

# Tester manuellement
cd ~/maps-scraper/backend
source ../venv/bin/activate
python app.py
```

#### 2. Erreur "Not Found" sur l'interface

**Cause** : Nginx ou Gunicorn mal configuré

**Solution** :
```bash
# Vérifier Nginx
sudo nginx -t
sudo systemctl restart nginx

# Vérifier le service
sudo systemctl status scraper-web
```

#### 3. Scraper ne démarre pas

**Vérifier** :
```bash
# Logs du scraper
tail -f ~/maps-scraper/backend/scraper.log

# Playwright installé ?
cd ~/maps-scraper
source venv/bin/activate
playwright install firefox chromium
```

#### 4. Erreur "Executable doesn't exist"

**Cause** : Navigateurs Playwright non installés

**Solution** :
```bash
cd ~/maps-scraper
source venv/bin/activate
playwright install firefox chromium
playwright install-deps firefox chromium  # Nécessite sudo
```

#### 5. Erreur d'authentification

**Solution** : Régénérer le `.htpasswd`
```bash
sudo htpasswd -c /etc/nginx/.htpasswd admin
# Entrer le même mot de passe que dans .env
sudo systemctl restart nginx
```

#### 6. Base de données corrompue

```bash
# Vérifier l'intégrité
sqlite3 ~/maps-scraper/backend/companies.db "PRAGMA integrity_check;"

# Recréer la BDD (⚠️ perte de données)
rm ~/maps-scraper/backend/companies.db
# Relancer le scraper pour recréer
```

---

## 📚 Documentation

- **Installation** : `docs/INSTALL.md`
- **Mise à jour** : `docs/UPDATE.md`
- **Changement mot de passe** : `docs/CHANGE_PASSWORD.md`
- **Structure projet** : `PROJECT_STRUCTURE.md`

---

## 🎯 Zones de scraping

### Canton de Neuchâtel (priorité)
- Neuchâtel, La Chaux-de-Fonds, Le Locle
- Val-de-Ruz, Val-de-Travers, Fleurier
- Cernier, Peseux, Colombier
- Marin-Epagnier, Saint-Blaise, Boudry, Cressier

### Villes proches (hors canton)
- Yverdon-les-Bains, Pontarlier, Morteau, Besançon

### Autres Suisse Romande
- Genève, Lausanne, Fribourg, Sion
- Nyon, Renens, Meyrin, Plan-les-Ouates
- Martigny, Vevey, Montreux
- Delémont, Porrentruy

---

## 🔍 Mots-clés de recherche

### Développement web & digital
- Agence Web, Développement logiciel, Conception de sites web
- Création site internet, Agence digitale, Web design
- Développeur web, Intégrateur web, UX Designer

### Développement spécialisé
- Full Stack, Frontend developer, Backend developer
- App development, Mobile app, Application mobile
- E-commerce, Site e-commerce, Boutique en ligne

### Software & SaaS
- Éditeur de logiciels, Software development, SaaS company
- Startup tech, Tech startup, Scale-up

### Sécurité & infrastructure
- Cybersécurité, Sécurité informatique, Consultant IT
- Consultant informatique, Services informatiques entreprises
- Cloud provider, DevOps, Infrastructure IT

### Marketing digital
- SEO, Référencement web, Marketing digital
- Social media management, Community manager

### Data & IA
- Data science, Intelligence artificielle, Machine Learning
- Big Data, Data analyst

---

## 📞 Support

Pour toute question ou problème :
1. Consulter les docs (`docs/`)
2. Vérifier les logs (`sudo journalctl -u scraper-web -f`)
3. Regarder dans le dépannage ci-dessus

---

## 📝 Licence

Projet privé - Tous droits réservés

---

## 🔮 Évolutions futures possibles

- [ ] Second bot d'enrichissement (LinkedIn, Pappers, etc.)
- [ ] Export Excel en plus du CSV
- [ ] Filtres avancés (par note Google, nombre d'avis)
- [ ] Notifications email en fin de scraping
- [ ] API REST publique
- [ ] Dashboard analytics avancé
- [ ] Gestion multi-utilisateurs
- [ ] Système de tags personnalisés
- [ ] Détection automatique des doublons
- [ ] Intégration CRM (HubSpot, Salesforce)

---

**Version** : 1.0.0  
**Dernière mise à jour** : Décembre 2024  
**Auteur** : Votre nom/société

# 🔧 Configuration Serveur VPS - Guide Complet

## 📋 Vue d'ensemble de l'architecture

```
Internet
   │
   ▼
[Firewall UFW] ← Ports 22, 80, 443 ouverts
   │
   ▼
[Nginx] ← Reverse Proxy + Authentification HTTP Basic
   │ (Port 80)
   ▼
[Gunicorn] ← Serveur WSGI Python (2 workers)
   │ (Port 5000, localhost uniquement)
   ▼
[Flask App] ← Application web (app.py)
   │
   ├─→ [SQLite DB] ← Base de données (companies.db)
   ├─→ [Scraper] ← Processus de scraping (scraper_suisse_romande.py)
   └─→ [Frontend] ← Interface web (HTML/CSS/JS)
```

---

## 🏗️ Architecture détaillée

### 1. **Firewall (UFW)** 🔥

**Rôle** : Protéger le serveur en filtrant les connexions

**Configuration** :
```bash
ufw enable                    # Activer le firewall
ufw allow 22/tcp             # SSH (connexion distante)
ufw allow 80/tcp             # HTTP (interface web)
ufw allow 443/tcp            # HTTPS (SSL/TLS)
# Tout le reste est BLOQUÉ par défaut
```

**Pourquoi** :
- Seuls les ports nécessaires sont ouverts
- Protection contre les attaques
- SSH reste accessible pour l'administration

---

### 2. **Nginx** 🌐

**Rôle** : Reverse proxy + authentification HTTP Basic

**Fichier** : `/etc/nginx/sites-available/scraper`

**Configuration** :
```nginx
server {
    listen 80;                    # Écoute sur le port HTTP
    server_name _;               # Accepte toutes les requêtes

    # Authentification HTTP Basic (1ère couche)
    auth_basic "Accès restreint";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        # Redirection vers Gunicorn (Flask)
        proxy_pass http://127.0.0.1:5000;
        
        # Headers pour préserver les infos client
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts longs (scraping peut prendre du temps)
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

**Pourquoi Nginx** :
- ✅ **Performance** : Gère mieux les connexions que Flask seul
- ✅ **Sécurité** : Authentification HTTP Basic avant Flask
- ✅ **SSL ready** : Facile d'ajouter HTTPS plus tard
- ✅ **Reverse proxy** : Cache, compression, etc.

**Authentification** :
- Fichier : `/etc/nginx/.htpasswd`
- Créé avec : `htpasswd -cb /etc/nginx/.htpasswd username password`
- Format : `username:$apr1$hash...` (mot de passe haché)

---

### 3. **Gunicorn** 🦄

**Rôle** : Serveur WSGI pour Flask (production)

**Commande** :
```bash
gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 600 app:app
```

**Paramètres** :
- `--bind 127.0.0.1:5000` : Écoute uniquement en localhost (sécurité)
- `--workers 2` : 2 processus parallèles (gère 2 requêtes simultanées)
- `--timeout 600` : Timeout de 10 minutes (pour les longues opérations)
- `app:app` : Module `app.py`, variable `app` (instance Flask)

**Pourquoi Gunicorn** :
- ✅ **Production-ready** : Plus stable que Flask dev server
- ✅ **Multi-workers** : Gère plusieurs requêtes en parallèle
- ✅ **Auto-restart** : Redémarre en cas de crash
- ✅ **Performance** : Optimisé pour la production

**Workers** :
- 2 workers = 2 processus Python indépendants
- Chaque worker peut gérer 1 requête à la fois
- Total : 2 requêtes simultanées max

---

### 4. **Service Systemd** ⚙️

**Rôle** : Démarrer/arrêter/redémarrer automatiquement l'application

**Fichier** : `/etc/systemd/system/scraper-web.service`

**Configuration** :
```ini
[Unit]
Description=Scraper Google Maps - Web Interface
After=network.target          # Démarrer après le réseau

[Service]
Type=simple                   # Processus simple
User=scraper                  # Exécuter en tant que cet utilisateur
WorkingDirectory=/home/scraper/maps-scraper/backend
Environment="PATH=/home/scraper/maps-scraper/venv/bin"
EnvironmentFile=/home/scraper/maps-scraper/.env
ExecStart=/home/scraper/maps-scraper/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 600 app:app
Restart=always                # Redémarrer si crash
RestartSec=10                 # Attendre 10s avant redémarrage

[Install]
WantedBy=multi-user.target    # Démarrer au boot
```

**Commandes** :
```bash
# Démarrer
sudo systemctl start scraper-web

# Arrêter
sudo systemctl stop scraper-web

# Redémarrer
sudo systemctl restart scraper-web

# Statut
sudo systemctl status scraper-web

# Activer au boot
sudo systemctl enable scraper-web

# Désactiver au boot
sudo systemctl disable scraper-web

# Logs en temps réel
sudo journalctl -u scraper-web -f
```

**Avantages** :
- ✅ **Démarrage automatique** au boot du serveur
- ✅ **Auto-restart** en cas de crash
- ✅ **Logs centralisés** (journalctl)
- ✅ **Gestion facile** (start/stop/restart)

---

### 5. **Utilisateur système** 👤

**Nom** : `scraper`

**Création** :
```bash
useradd -m -s /bin/bash scraper
```

**Pourquoi un utilisateur dédié** :
- ✅ **Sécurité** : Isolation de l'application
- ✅ **Permissions** : Limite les accès
- ✅ **Séparation** : Ne pollue pas le compte root
- ✅ **Best practice** : Standard en production

**Répertoire** : `/home/scraper/maps-scraper`

---

### 6. **Environnement virtuel Python** 🐍

**Répertoire** : `/home/scraper/maps-scraper/venv`

**Création** :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Pourquoi** :
- ✅ **Isolation** : Dépendances séparées du système
- ✅ **Versions** : Contrôle des versions Python/packages
- ✅ **Propreté** : Pas de conflits avec autres projets

**Contenu** :
- Python 3.x
- Flask, Gunicorn, Playwright
- Toutes les dépendances du projet

---

### 7. **Variables d'environnement** 🔐

**Fichier** : `/home/scraper/maps-scraper/.env`

**Contenu** :
```bash
WEB_USERNAME=admin
WEB_PASSWORD=changeme123
PORT=5000
DEBUG=False
```

**Utilisation** :
- Chargé par systemd (`EnvironmentFile`)
- Utilisé par Flask pour l'authentification
- **Sécurité** : Ne jamais commiter ce fichier (dans `.gitignore`)

---

### 8. **Base de données SQLite** 💾

**Fichier** : `/home/scraper/maps-scraper/backend/companies.db`

**Structure** :
```sql
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    maps_link TEXT UNIQUE,        -- Pas de doublons
    city TEXT,
    tag TEXT,
    address TEXT,
    phone TEXT,
    website TEXT,
    rating REAL,
    reviews_count INTEGER,
    email TEXT,
    social_links TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Avantages SQLite** :
- ✅ **Simple** : Pas de serveur séparé
- ✅ **Fiable** : Parfait pour ce cas d'usage
- ✅ **Portable** : Fichier unique, facile à sauvegarder
- ✅ **Performance** : Suffisant pour des milliers d'entrées

---

## 🔄 Flux d'une requête

### Exemple : Accès à l'interface web

```
1. Client → http://IP_VPS
   │
   ▼
2. Firewall (UFW) → Vérifie port 80 autorisé ✅
   │
   ▼
3. Nginx → Demande authentification HTTP Basic
   │
   ▼
4. Client → Envoie username:password
   │
   ▼
5. Nginx → Vérifie /etc/nginx/.htpasswd ✅
   │
   ▼
6. Nginx → Proxy vers http://127.0.0.1:5000
   │
   ▼
7. Gunicorn → Reçoit la requête (worker 1 ou 2)
   │
   ▼
8. Flask App → Traite la requête
   │
   ├─→ Si /api/companies → Interroge SQLite
   ├─→ Si /api/scraper/start → Lance subprocess
   └─→ Si / → Renvoie index.html
   │
   ▼
9. Réponse → Gunicorn → Nginx → Client
```

---

## 🔒 Sécurité

### Double authentification

**1. Nginx HTTP Basic Auth** :
- Fichier : `/etc/nginx/.htpasswd`
- Format : `username:$apr1$hash...`
- **Avantage** : Bloque avant même d'atteindre Flask

**2. Flask HTTPBasicAuth** :
- Code : `@auth.login_required`
- Vérifie : `users[username]` (hash Werkzeug)
- **Avantage** : Sécurité supplémentaire si Nginx est contourné

### Isolation réseau

- **Gunicorn** écoute uniquement sur `127.0.0.1:5000` (localhost)
- **Nginx** seul est exposé sur `0.0.0.0:80` (public)
- **Firewall** bloque tout sauf 22, 80, 443

### Permissions

- **Application** : Propriétaire `scraper:scraper`
- **Service** : Exécuté par utilisateur `scraper` (pas root)
- **Fichiers sensibles** : `.env` en 600 (lecture/écriture owner uniquement)

---

## 📊 Monitoring

### Logs

**Nginx** :
```bash
sudo tail -f /var/log/nginx/access.log    # Requêtes
sudo tail -f /var/log/nginx/error.log    # Erreurs
```

**Gunicorn/Flask** :
```bash
sudo journalctl -u scraper-web -f         # Logs temps réel
sudo journalctl -u scraper-web -n 100     # 100 dernières lignes
```

**Scraper** :
```bash
# Logs dans la base de données
sqlite3 companies.db "SELECT * FROM companies ORDER BY created_at DESC LIMIT 10;"
```

### Statut

**Vérifier que tout tourne** :
```bash
# Service systemd
sudo systemctl status scraper-web

# Nginx
sudo systemctl status nginx

# Processus Gunicorn
ps aux | grep gunicorn

# Ports ouverts
sudo netstat -tlnp | grep -E ':(80|5000)'
```

---

## 🚀 Déploiement

### Installation automatique

```bash
# Sur le VPS
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap
sudo ./scripts/install.sh
```

**Ce que fait le script** :
1. ✅ Met à jour le système
2. ✅ Installe Python, Node.js, Nginx, UFW
3. ✅ Crée l'utilisateur `scraper`
4. ✅ Copie les fichiers dans `/home/scraper/maps-scraper`
5. ✅ Crée l'environnement virtuel
6. ✅ Installe les dépendances
7. ✅ Configure Nginx
8. ✅ Crée le service systemd
9. ✅ Configure le firewall
10. ✅ Démarre tout automatiquement

### Mise à jour

```bash
cd /home/scraper/maps-scraper
git pull
sudo systemctl restart scraper-web
```

---

## 🔧 Personnalisation

### Changer le port

**Modifier** : `/home/scraper/maps-scraper/.env`
```bash
PORT=8080
```

**Modifier** : `/etc/systemd/system/scraper-web.service`
```ini
ExecStart=... --bind 127.0.0.1:8080 ...
```

**Modifier** : `/etc/nginx/sites-available/scraper`
```nginx
proxy_pass http://127.0.0.1:8080;
```

**Redémarrer** :
```bash
sudo systemctl daemon-reload
sudo systemctl restart scraper-web
sudo systemctl restart nginx
```

### Ajouter HTTPS (SSL)

```bash
# Installer certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtenir un certificat
sudo certbot --nginx -d scraper.votredomaine.com

# Renouvellement automatique
sudo systemctl enable certbot.timer
```

### Augmenter les workers Gunicorn

**Modifier** : `/etc/systemd/system/scraper-web.service`
```ini
ExecStart=... --workers 4 ...
```

**Redémarrer** :
```bash
sudo systemctl daemon-reload
sudo systemctl restart scraper-web
```

**Recommandation** : `workers = (2 × CPU cores) + 1`

---

## 📁 Structure des fichiers

```
/home/scraper/maps-scraper/
├── backend/
│   ├── app.py                    # Flask application
│   ├── scraper_suisse_romande.py # Scraper
│   ├── companies.db              # Base SQLite
│   └── checkpoint.json           # Progression
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── venv/                         # Environnement Python
├── .env                          # Variables d'environnement
└── scripts/
    ├── install.sh
    └── start.sh

/etc/nginx/
├── sites-available/scraper       # Config Nginx
└── .htpasswd                     # Authentification

/etc/systemd/system/
└── scraper-web.service           # Service systemd
```

---

## 🆘 Dépannage

### Le service ne démarre pas

```bash
# Voir les erreurs
sudo journalctl -u scraper-web -n 50

# Vérifier les permissions
sudo chown -R scraper:scraper /home/scraper/maps-scraper

# Vérifier le .env
cat /home/scraper/maps-scraper/.env
```

### Nginx ne fonctionne pas

```bash
# Tester la config
sudo nginx -t

# Voir les erreurs
sudo tail -f /var/log/nginx/error.log

# Redémarrer
sudo systemctl restart nginx
```

### Port déjà utilisé

```bash
# Voir qui utilise le port 5000
sudo lsof -i:5000

# Tuer le processus
sudo kill -9 PID
```

---

## 📚 Ressources

- **Nginx** : https://nginx.org/en/docs/
- **Gunicorn** : https://docs.gunicorn.org/
- **Systemd** : https://www.freedesktop.org/software/systemd/man/systemd.service.html
- **UFW** : https://help.ubuntu.com/community/UFW

---

**Cette configuration est prête pour la production ! 🚀**


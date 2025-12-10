# 🚀 Guide de Déploiement VPS

Guide complet pour déployer le scraper sur un VPS avec interface web accessible à distance.

## 📋 Prérequis

- **VPS** avec Ubuntu 20.04+ ou Debian 11+
- **2 GB RAM minimum** (4 GB recommandé)
- **20 GB espace disque**
- Accès **root** ou **sudo**

## 🎯 Installation en 3 étapes

### 1️⃣ Cloner le repository sur le VPS

**Tu peux cloner le projet n'importe où !** Le script d'installation va automatiquement copier les fichiers vers `/home/scraper/maps-scraper`.

```bash
# Connexion SSH au VPS (en tant que ubuntu ou root)
ssh ubuntu@VOTRE_IP_VPS

# Installation de git si nécessaire
sudo apt-get update && sudo apt-get install -y git

# Cloner le projet (n'importe où, par exemple dans /home/ubuntu)
cd ~
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap

# OU cloner dans /tmp, /opt, etc. - peu importe !
# Le script install.sh va copier vers /home/scraper/maps-scraper automatiquement
```

### 2️⃣ Lancer l'installation automatique

```bash
# Rendre le script exécutable
chmod +x scripts/install.sh

# Lancer l'installation (en tant que root)
sudo ./scripts/install.sh
```

Le script va :
- ✅ Installer Python 3, Node.js, Nginx
- ✅ Créer un utilisateur système `scraper`
- ✅ Installer toutes les dépendances
- ✅ Installer Playwright + Firefox
- ✅ Configurer Nginx (reverse proxy)
- ✅ Créer un service systemd
- ✅ Configurer le firewall
- ✅ Vous demander de créer un mot de passe

**Durée** : 5-10 minutes

### 3️⃣ Accéder à l'interface web

À la fin de l'installation, vous obtiendrez :

```
============================================
✅ Installation terminée !
============================================

📝 Informations de connexion:

   URL: http://XXX.XXX.XXX.XXX
   Nom d'utilisateur: admin
   Mot de passe: VOTRE_MOT_DE_PASSE

============================================
```

Ouvrez votre navigateur et accédez à l'URL indiquée !

## 🔒 Sécurité

### Double authentification
Le système utilise **2 couches de sécurité** :

1. **Authentification Nginx** (HTTP Basic Auth)
2. **Authentification Flask** (vérification dans l'application)

### Firewall configuré
- Port 22 (SSH) : Ouvert
- Port 80 (HTTP) : Ouvert
- Port 443 (HTTPS) : Ouvert
- Tout le reste : Fermé

### Recommandations
```bash
# Changer le port SSH (optionnel mais recommandé)
nano /etc/ssh/sshd_config
# Modifier: Port 2222
systemctl restart sshd

# Mettre à jour le firewall
ufw allow 2222/tcp
ufw delete allow 22/tcp
```

## 🛠️ Gestion du service

### Commandes principales

```bash
# Démarrer le service
sudo systemctl start scraper-web

# Arrêter le service
sudo systemctl stop scraper-web

# Redémarrer le service
sudo systemctl restart scraper-web

# Voir le statut
sudo systemctl status scraper-web

# Voir les logs en temps réel
sudo journalctl -u scraper-web -f
```

### Démarrage automatique

Le service démarre automatiquement au boot du VPS.

Pour désactiver :
```bash
sudo systemctl disable scraper-web
```

## 📊 Utilisation de l'interface web

### Tableau de bord
- **Statistiques** : Total entreprises, avec site web, avec email
- **Top 10 villes** : Graphique des villes les plus représentées
- **Contrôle scraper** : Démarrer/Arrêter le scraping
- **Filtres** : Ville, site web, email, recherche
- **Export CSV** : Télécharger les données

### Lancer un scraping

1. Cliquez sur **"▶️ Démarrer"** dans la section "Contrôle du Scraper"
2. Le scraper s'exécute en arrière-plan
3. La progression est visible sur le dashboard
4. Les données sont mises à jour en temps réel

### Exporter les données

1. Appliquer les filtres souhaités (ville, etc.)
2. Cliquer sur **"📥 Exporter CSV"**
3. Le fichier est téléchargé automatiquement

## 🗄️ Accès direct à la base de données

```bash
# Se connecter en tant que scraper
sudo su - scraper
cd /home/scraper/maps-scraper/backend

# Ouvrir la base SQLite
sqlite3 companies.db

# Exemples de requêtes SQL
SELECT COUNT(*) FROM companies;
SELECT * FROM companies WHERE city = 'Neuchâtel' LIMIT 10;
SELECT city, COUNT(*) FROM companies GROUP BY city;

# Quitter
.quit
```

## 🔄 Mise à jour du code

```bash
cd /home/scraper/maps-scraper
git pull
sudo systemctl restart scraper-web
```

## 📁 Structure des fichiers

```
/home/scraper/maps-scraper/
├── backend/
│   ├── app.py                    # API Flask
│   ├── scraper_suisse_romande.py # Scraper
│   ├── companies.db              # Base de données SQLite
│   ├── checkpoint.json           # Progression
│   └── intermediate_data.csv     # Données temporaires
├── frontend/
│   ├── index.html                # Interface web
│   ├── style.css                 # Styles
│   └── script.js                 # JavaScript
├── scripts/
│   ├── install.sh                # Installation
│   └── start.sh                  # Démarrage manuel
├── venv/                         # Environnement Python
└── .env                          # Variables d'environnement
```

## 🐛 Dépannage

### Le service ne démarre pas

```bash
# Voir les erreurs
sudo journalctl -u scraper-web -n 50

# Vérifier les permissions
sudo chown -R scraper:scraper /home/scraper/maps-scraper

# Redémarrer
sudo systemctl restart scraper-web
```

### Impossible d'accéder à l'interface web

```bash
# Vérifier que Nginx fonctionne
sudo systemctl status nginx

# Vérifier la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx

# Vérifier le firewall
sudo ufw status
```

### Le scraper ne trouve rien

```bash
# Vérifier que Playwright et Firefox sont installés
cd /home/scraper/maps-scraper
source venv/bin/activate
playwright install firefox
playwright install-deps firefox
```

### Réinitialiser complètement

```bash
# Supprimer les données
cd /home/scraper/maps-scraper/backend
rm companies.db checkpoint.json intermediate_data.csv

# Redémarrer le service
sudo systemctl restart scraper-web
```

## 🌐 Configurer un nom de domaine (optionnel)

### 1. Pointer le domaine vers votre VPS

Dans votre registrar DNS, créez un enregistrement A :
```
scraper.votredomaine.com  →  XXX.XXX.XXX.XXX
```

### 2. Modifier la configuration Nginx

```bash
sudo nano /etc/nginx/sites-available/scraper
```

Modifier la ligne `server_name` :
```nginx
server_name scraper.votredomaine.com;
```

### 3. Installer un certificat SSL (gratuit avec Let's Encrypt)

```bash
# Installer certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtenir un certificat
sudo certbot --nginx -d scraper.votredomaine.com

# Renouvellement automatique
sudo systemctl enable certbot.timer
```

Votre site sera accessible en HTTPS ! 🔒

## 💡 Conseils de performance

### Pour un gros volume de données

1. **Augmenter les workers Gunicorn** :
```bash
sudo nano /etc/systemd/system/scraper-web.service
# Modifier: --workers 4
sudo systemctl daemon-reload
sudo systemctl restart scraper-web
```

2. **Optimiser SQLite** :
```sql
-- Créer des index pour les requêtes fréquentes
CREATE INDEX idx_city ON companies(city);
CREATE INDEX idx_email ON companies(email);
CREATE INDEX idx_website ON companies(website);
```

3. **Configurer un cache Nginx** :
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m;
proxy_cache my_cache;
```

## 📞 Support

En cas de problème :
1. Vérifiez les logs : `sudo journalctl -u scraper-web -f`
2. Consultez la documentation : `README.md`
3. Testez localement : `./scripts/start.sh`

---

**Bon scraping ! 🕷️**


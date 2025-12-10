# ⚡ Quick Start - Déploiement VPS en 5 minutes

## 🎯 Pour déployer sur votre VPS

### 1. Connexion SSH à votre VPS
```bash
ssh root@VOTRE_IP_VPS
```

### 2. Installation automatique
```bash
# Installer git
apt-get update && apt-get install -y git

# Cloner le projet
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap

# Lancer l'installation (tout est automatique)
chmod +x scripts/install.sh
sudo ./scripts/install.sh
```

### 3. Connexion à l'interface

L'installation vous donnera l'URL et les identifiants :
```
URL: http://XXX.XXX.XXX.XXX
Username: admin
Password: VOTRE_MOT_DE_PASSE
```

Ouvrez votre navigateur et c'est parti ! 🚀

---

## 📋 Ce que fait le script d'installation

✅ Installe automatiquement :
- Python 3 + pip
- Node.js
- Nginx (serveur web)
- Playwright + Firefox
- Toutes les dépendances Python
- Service systemd (démarrage automatique)
- Firewall sécurisé (ufw)
- Base de données SQLite

✅ Configure automatiquement :
- Reverse proxy Nginx
- Authentification double (Nginx + Flask)
- Permissions utilisateur
- Service qui démarre au boot
- Ports firewall (22, 80, 443)

✅ Crée automatiquement :
- Utilisateur système `scraper`
- Base de données `companies.db`
- Fichier de configuration `.env`
- Mot de passe sécurisé (ou généré automatiquement)

**Durée totale : 5-10 minutes**

---

## 🎮 Utilisation rapide

### Depuis l'interface web

1. **Ouvrir** http://VOTRE_IP dans votre navigateur
2. **S'authentifier** avec admin/VOTRE_MOT_DE_PASSE
3. **Cliquer** sur "▶️ Démarrer" pour lancer le scraper
4. **Attendre** que les données se remplissent (visible en temps réel)
5. **Filtrer** par ville, email, site web
6. **Exporter** en CSV avec le bouton "📥 Exporter CSV"

### Commandes utiles

```bash
# Voir le statut du service
sudo systemctl status scraper-web

# Voir les logs en temps réel
sudo journalctl -u scraper-web -f

# Redémarrer le service
sudo systemctl restart scraper-web

# Arrêter le service
sudo systemctl stop scraper-web

# Accéder à la base de données
cd /home/scraper/maps-scraper/backend
sqlite3 companies.db
```

---

## 🔧 Personnalisation rapide

### Changer le mot de passe

```bash
cd /home/scraper/maps-scraper
nano .env

# Modifier :
WEB_PASSWORD=nouveau_mot_de_passe

# Redémarrer
sudo systemctl restart scraper-web
```

### Ajouter des villes

```bash
nano /home/scraper/maps-scraper/backend/scraper_suisse_romande.py

# Ligne ~20, ajouter vos villes dans CITIES = [...]
# Sauvegarder et quitter (Ctrl+X, Y, Enter)
```

### Exporter toutes les données

```bash
cd /home/scraper/maps-scraper/backend
sqlite3 companies.db ".mode csv" ".output export.csv" "SELECT * FROM companies;"
# Le fichier export.csv est créé
```

---

## ⚠️ Important

### Sécurité
- **Changez le mot de passe** après l'installation
- Le firewall est activé (seuls SSH et HTTP sont ouverts)
- Double authentification activée (Nginx + Flask)

### Performance
- Le scraper peut tourner pendant **8-12 heures** (toutes les combinaisons)
- Vous pouvez l'arrêter/reprendre à tout moment
- Les données sont sauvegardées en temps réel

### Légal
- Usage personnel/éducatif uniquement
- Respectez les CGU de Google Maps
- Respectez le RGPD et la LPD suisse

---

## 🆘 En cas de problème

### Le service ne démarre pas
```bash
sudo journalctl -u scraper-web -n 50
sudo systemctl restart scraper-web
```

### Impossible d'accéder à l'interface
```bash
sudo systemctl status nginx
sudo systemctl restart nginx
sudo ufw status
```

### Réinitialiser complètement
```bash
cd /home/scraper/maps-scraper/backend
rm companies.db checkpoint.json intermediate_data.csv
sudo systemctl restart scraper-web
```

---

## 📖 Documentation complète

- **README.md** : Guide utilisateur complet
- **DEPLOY.md** : Guide de déploiement détaillé
- **README_COMPLET.md** : Documentation technique

---

**Besoin d'aide ? Consultez DEPLOY.md pour plus de détails !**


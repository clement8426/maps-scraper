# 🚀 Installation rapide (VPS Ubuntu/Debian)

## Prérequis
- Accès root/sudo
- Ubuntu/Debian (25.04 compatible)
- Ports 80 (HTTP) et 22 (SSH) ouverts

## Installation en 3 commandes
```bash
git clone https://github.com/clement8426/maps-scraper.git
cd maps-scraper
sudo ./scripts/install.sh
```

L'URL d'accès et les identifiants sont affichés en fin d'installation.

## Ce que fait `install.sh`
- Met à jour le système + dépendances système (libxml2/libxslt)
- Installe Python (3.13 OK) et crée un venv
- Installe les dépendances Python + Playwright + navigateurs (Firefox, Chromium)
- Configure Nginx en reverse proxy + basic auth
- Crée le service systemd `scraper-web`
- Active UFW (ports 22/80/443)

## Notes importantes
- L'application tourne sous l'utilisateur **courant** (`$SUDO_USER`, ex: `ubuntu`).
- Les navigateurs Playwright sont installés dans `/home/$USER/.cache/ms-playwright`.
- Le service systemd écoute en local `127.0.0.1:5000` derrière Nginx (port 80).

## 🔐 Changer le mot de passe admin

Si votre mot de passe a été compromis ou si vous voulez le changer :

```bash
cd ~/maps-scraper
nano .env
# Modifiez WEB_PASSWORD=VotreNouveauMotDePasse123!
sudo systemctl restart scraper-web
```

📖 **Guide complet** : Voir `docs/CHANGE_PASSWORD.md`

## Commandes utiles
```bash
# Statut du service
sudo systemctl status scraper-web

# Logs backend
sudo journalctl -u scraper-web -f

# Redémarrer le service
sudo systemctl restart scraper-web
```

## Réinstallation propre (optionnel)
```bash
sudo systemctl stop scraper-web 2>/dev/null
sudo systemctl disable scraper-web 2>/dev/null
sudo rm -f /etc/systemd/system/scraper-web.service
sudo systemctl daemon-reload
sudo rm -f /etc/nginx/sites-available/scraper /etc/nginx/sites-enabled/scraper /etc/nginx/.htpasswd
sudo systemctl restart nginx
sudo rm -rf /home/$USER/maps-scraper
```

Puis relancer les 3 commandes d'installation.

## Dépannage Playwright
Si vous voyez `Executable doesn't exist ... playwright install` :
```bash
cd /home/$USER/maps-scraper
source venv/bin/activate
playwright install firefox chromium
playwright install-deps firefox chromium   # nécessite sudo
```

## Accès web
- URL : `http://<IP_VPS>`
- Identifiants : affichés en fin d'installation (ou dans `.env`)



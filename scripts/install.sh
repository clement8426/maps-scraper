#!/bin/bash

#############################################
# Script d'installation automatique
# Scraper Google Maps - Déploiement VPS
#############################################

set -e  # Arrêter en cas d'erreur

echo "============================================"
echo "🚀 Installation du Scraper Google Maps"
echo "============================================"
echo ""

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}❌ Ce script doit être exécuté en tant que root${NC}"
   echo "Utilisez: sudo ./install.sh"
   exit 1
fi

echo -e "${GREEN}✅ Exécution en tant que root${NC}"
echo ""

# 1. Mise à jour du système
echo "📦 Mise à jour du système..."
apt-get update -qq
apt-get upgrade -y -qq

# 2. Installation de Python 3 et pip
echo "🐍 Installation de Python 3 et pip..."
apt-get install -y python3 python3-pip python3-venv -qq

# 3. Installation de Node.js (pour certaines dépendances)
echo "📦 Installation de Node.js..."
apt-get install -y curl -qq
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null
    apt-get install -y nodejs -qq
fi

# 4. Installation de Nginx
echo "🌐 Installation de Nginx..."
apt-get install -y nginx -qq

# 5. Installation de ufw (firewall)
echo "🔥 Installation du firewall..."
apt-get install -y ufw -qq

# 6. Créer un utilisateur pour l'application (si n'existe pas)
if ! id "scraper" &>/dev/null; then
    echo "👤 Création de l'utilisateur 'scraper'..."
    useradd -m -s /bin/bash scraper
fi

# 7. Définir le répertoire de travail
APP_DIR="/home/scraper/maps-scraper"
echo "📁 Répertoire de l'application: $APP_DIR"

# Si le script est lancé depuis le repo cloné, copier les fichiers
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
if [ "$SCRIPT_DIR" != "$APP_DIR" ]; then
    echo "📋 Copie des fichiers vers $APP_DIR..."
    mkdir -p $APP_DIR
    cp -r $SCRIPT_DIR/* $APP_DIR/
fi

cd $APP_DIR

# 8. Créer l'environnement virtuel Python
echo "🐍 Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# 9. Installer les dépendances Python
echo "📦 Installation des dépendances Python..."
pip install --upgrade pip -qq
pip install -r requirements.txt -qq
pip install flask flask-httpauth gunicorn -qq

# 10. Installer Playwright et Firefox
echo "🎭 Installation de Playwright et Firefox..."
playwright install firefox
playwright install-deps firefox

# 11. Configuration des variables d'environnement
if [ ! -f .env ]; then
    echo "⚙️ Configuration des variables d'environnement..."
    read -p "Nom d'utilisateur pour l'interface web (défaut: admin): " web_username
    web_username=${web_username:-admin}
    
    read -sp "Mot de passe pour l'interface web: " web_password
    echo ""
    
    if [ -z "$web_password" ]; then
        web_password=$(openssl rand -base64 12)
        echo -e "${YELLOW}⚠️  Mot de passe généré automatiquement: $web_password${NC}"
        echo -e "${YELLOW}Notez-le bien !${NC}"
    fi
    
    cat > .env << EOF
WEB_USERNAME=$web_username
WEB_PASSWORD=$web_password
PORT=5000
DEBUG=False
EOF
    
    echo -e "${GREEN}✅ Fichier .env créé${NC}"
fi

# 12. Changer les permissions
echo "🔒 Configuration des permissions..."
chown -R scraper:scraper $APP_DIR
chmod +x scripts/*.sh

# 13. Configuration de Nginx
echo "🌐 Configuration de Nginx..."
cat > /etc/nginx/sites-available/scraper << 'EOF'
server {
    listen 80;
    server_name _;

    # Authentification HTTP Basic (double sécurité)
    auth_basic "Accès restreint";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts pour les longues requêtes
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
EOF

# Créer le fichier htpasswd pour Nginx
source $APP_DIR/.env
echo -e "${YELLOW}Configuration de l'authentification Nginx...${NC}"
apt-get install -y apache2-utils -qq
htpasswd -cb /etc/nginx/.htpasswd $WEB_USERNAME $WEB_PASSWORD

# Activer le site
ln -sf /etc/nginx/sites-available/scraper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 14. Créer un service systemd
echo "⚙️ Création du service systemd..."
cat > /etc/systemd/system/scraper-web.service << EOF
[Unit]
Description=Scraper Google Maps - Web Interface
After=network.target

[Service]
Type=simple
User=scraper
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 600 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable scraper-web
systemctl start scraper-web

# 15. Configuration du firewall
echo "🔥 Configuration du firewall..."
ufw --force enable
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS (si SSL plus tard)
ufw status

# 16. Afficher les informations de connexion
echo ""
echo "============================================"
echo -e "${GREEN}✅ Installation terminée !${NC}"
echo "============================================"
echo ""
echo "📝 Informations de connexion:"
echo ""
SERVER_IP=$(hostname -I | awk '{print $1}')
echo -e "   URL: ${GREEN}http://$SERVER_IP${NC}"
echo -e "   Nom d'utilisateur: ${GREEN}$WEB_USERNAME${NC}"
echo -e "   Mot de passe: ${GREEN}$WEB_PASSWORD${NC}"
echo ""
echo "🔧 Commandes utiles:"
echo ""
echo "   Vérifier le statut:"
echo "     sudo systemctl status scraper-web"
echo ""
echo "   Voir les logs:"
echo "     sudo journalctl -u scraper-web -f"
echo ""
echo "   Redémarrer le service:"
echo "     sudo systemctl restart scraper-web"
echo ""
echo "   Accéder à la base de données:"
echo "     cd $APP_DIR/backend && sqlite3 companies.db"
echo ""
echo "============================================"
echo ""


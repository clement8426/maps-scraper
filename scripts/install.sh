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

# 2. Installation des dépendances système (pour compilation Python)
echo "🔧 Installation des dépendances système..."
apt-get install -y pkg-config libatlas-base-dev libblas-dev liblapack-dev gfortran python3-dev \
    libxml2-dev libxslt1-dev zlib1g-dev -qq

# 3. Installation de Python 3 et pip
echo "🐍 Installation de Python 3 et pip..."
apt-get install -y python3 python3-pip python3-venv -qq

# Vérifier la version de Python
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
UBUNTU_VERSION=$(lsb_release -cs 2>/dev/null || echo "unknown")
echo "Version Python détectée: $PYTHON_VERSION"
echo "Ubuntu version: $UBUNTU_VERSION"

if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo -e "${YELLOW}⚠️  Python 3.13 détecté.${NC}"
    
    # Vérifier si on peut installer Python 3.11 depuis le PPA
    if [[ "$UBUNTU_VERSION" == "jammy" || "$UBUNTU_VERSION" == "noble" ]]; then
        echo "Installation de Python 3.11 depuis deadsnakes PPA..."
        apt-get install -y software-properties-common -qq
        add-apt-repository -y ppa:deadsnakes/ppa
        apt-get update -qq
        apt-get install -y python3.11 python3.11-venv python3.11-dev -qq
        PYTHON_CMD="python3.11"
        echo -e "${GREEN}✅ Python 3.11 installé${NC}"
    else
        # Ubuntu trop récent (plucky, etc.) - utiliser Python 3.13 avec Pandas 2.2+
        echo -e "${YELLOW}⚠️  Ubuntu $UBUNTU_VERSION - PPA deadsnakes non disponible${NC}"
        echo -e "${YELLOW}Utilisation de Python 3.13 avec Pandas 2.2+ (compatible)${NC}"
        PYTHON_CMD="python3"
    fi
else
    PYTHON_CMD="python3"
fi

# 4. Installation de Node.js (pour certaines dépendances)
echo "📦 Installation de Node.js..."
apt-get install -y curl -qq
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null
    apt-get install -y nodejs -qq
fi

# 5. Installation de Nginx
echo "🌐 Installation de Nginx..."
apt-get install -y nginx -qq

# 6. Installation de ufw (firewall)
echo "🔥 Installation du firewall..."
apt-get install -y ufw -qq

# 7. Définir l'utilisateur et le répertoire de travail
TARGET_USER=${SUDO_USER:-$USER}
APP_DIR="/home/$TARGET_USER/maps-scraper"
echo "👤 Utilisateur cible: $TARGET_USER"
echo "📁 Répertoire de l'application: $APP_DIR"

# Si le script est lancé depuis le repo cloné, copier les fichiers
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
if [ "$SCRIPT_DIR" != "$APP_DIR" ]; then
    echo "📋 Copie des fichiers vers $APP_DIR..."
    mkdir -p $APP_DIR
    cp -r $SCRIPT_DIR/* $APP_DIR/
fi

cd $APP_DIR

# 9. Créer l'environnement virtuel Python
echo "🐍 Création de l'environnement virtuel..."
if [ -d "$APP_DIR/venv" ]; then
    echo -e "${YELLOW}⚠️  Le venv existe déjà, suppression...${NC}"
    rm -rf "$APP_DIR/venv"
fi
${PYTHON_CMD:-python3} -m venv "$APP_DIR/venv"
if [ ! -d "$APP_DIR/venv" ]; then
    echo -e "${RED}❌ Erreur lors de la création du venv !${NC}"
    exit 1
fi
source "$APP_DIR/venv/bin/activate"
echo -e "${GREEN}✅ Environnement virtuel créé dans $APP_DIR/venv avec ${PYTHON_CMD:-python3}${NC}"

# 10. Installer les dépendances Python
echo "📦 Installation des dépendances Python..."
pip install --upgrade pip -qq
pip install -r requirements.txt -qq
pip install flask flask-httpauth gunicorn -qq

# 11. Installer Playwright et ses navigateurs
echo "🎭 Installation de Playwright et des navigateurs (firefox + chromium)..."
# Installer les dépendances système (une seule fois, en root)
$APP_DIR/venv/bin/python -m playwright install-deps firefox chromium || true
# Installer les navigateurs pour l'utilisateur cible (cache dans /home/$TARGET_USER/.cache)
runuser -u "$TARGET_USER" -- bash -c "cd \"$APP_DIR\" && \"$APP_DIR/venv/bin/python\" -m playwright install firefox chromium"

# 12. Configuration des variables d'environnement
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

# 13. Changer les permissions
echo "🔒 Configuration des permissions..."
chown -R $TARGET_USER:$TARGET_USER $APP_DIR
chmod +x scripts/*.sh

# 14. Configuration de Nginx
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

# 15. Créer un service systemd
echo "⚙️ Création du service systemd..."
cat > /etc/systemd/system/scraper-web.service << EOF
[Unit]
Description=Scraper Google Maps - Web Interface
After=network.target

[Service]
Type=simple
User=$TARGET_USER
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

# 16. Configuration du firewall
echo "🔥 Configuration du firewall..."
ufw --force enable
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS (si SSL plus tard)
ufw status

# 17. Afficher les informations de connexion
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


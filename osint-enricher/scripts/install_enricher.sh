#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="osint-enricher"
USER_NAME="${SUDO_USER:-ubuntu}"
PORT="${PORT:-5001}"
NGINX_PORT="${NGINX_PORT:-81}"

echo "=== Installation OSINT Enricher ==="
echo "User: $USER_NAME"
echo "App:  $APP_DIR"

if [[ $EUID -ne 0 ]]; then
  echo "Veuillez lancer avec sudo"
  exit 1
fi

apt-get update
apt-get install -y python3-venv python3-dev build-essential \
  whatweb pdfgrep whois curl git golang-go

# Installer theHarvester via pip (global)
pip3 install theHarvester --break-system-packages || python3 -m pip install theHarvester

# Installer subfinder (Go)
if ! command -v subfinder &> /dev/null; then
  go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
  # Ajouter au PATH si nécessaire
  if [[ -f "/home/${USER_NAME}/go/bin/subfinder" ]]; then
    ln -sf "/home/${USER_NAME}/go/bin/subfinder" /usr/local/bin/subfinder || true
  fi
fi

# Installer amass (Go)
if ! command -v amass &> /dev/null; then
  go install -v github.com/owasp-amass/amass/v4/...@master
  # Ajouter au PATH si nécessaire
  if [[ -f "/home/${USER_NAME}/go/bin/amass" ]]; then
    ln -sf "/home/${USER_NAME}/go/bin/amass" /usr/local/bin/amass || true
  fi
fi

cd "$APP_DIR"

# Créer le .env dans le répertoire de l'app
if [[ ! -f .env ]]; then
  cat > .env <<EOF
WEB_USERNAME=enricher
WEB_PASSWORD=change_me_123!
DATABASE_PATH=/home/${USER_NAME}/maps-scraper/backend/companies.db
EOF
  chown "${USER_NAME}:${USER_NAME}" .env
  echo "✅ Fichier .env créé dans $APP_DIR/.env"
  echo "⚠️  Pensez à changer WEB_PASSWORD dans .env"
else
  echo "ℹ️  Fichier .env existe déjà"
fi

if [[ -d venv ]]; then rm -rf venv; fi
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cat >/etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=OSINT Enricher - Flask
After=network.target

[Service]
Type=notify
User=${USER_NAME}
Group=${USER_NAME}
WorkingDirectory=${APP_DIR}/backend
Environment="PATH=${APP_DIR}/venv/bin"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn --bind 127.0.0.1:${PORT} app:app --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/nginx/sites-available/${SERVICE_NAME} <<EOF
server {
    listen ${NGINX_PORT};
    server_name _;

    auth_basic "OSINT Enricher";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/${SERVICE_NAME}
nginx -t
systemctl restart nginx

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

echo ""
echo "=== Installation terminée ==="
echo ""
echo "📁 Fichier .env créé dans : $APP_DIR/.env"
echo "🔐 Identifiants par défaut :"
echo "   Username: enricher"
echo "   Password: change_me_123!"
echo "⚠️  Changez le mot de passe dans $APP_DIR/.env"
echo ""
echo "🌐 Accès web :"
echo "   Enrichissement : http://<IP>:$NGINX_PORT/enrich"
echo "   Exploration BDD: http://<IP>:$NGINX_PORT/db"
echo ""
echo "📊 Statut du service :"
systemctl status ${SERVICE_NAME} --no-pager -l
echo ""
echo "📝 Commandes utiles :"
echo "   sudo systemctl status ${SERVICE_NAME}"
echo "   sudo systemctl restart ${SERVICE_NAME}"
echo "   sudo journalctl -u ${SERVICE_NAME} -f"


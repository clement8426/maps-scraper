#!/bin/bash
# Script pour corriger l'erreur 502 et la lenteur

set -e

# Variables
APP_DIR="/home/ubuntu/maps-scraper/osint-enricher"

echo "=== Correction erreur 502 et lenteur ==="
echo ""

# 1. Arrêter le service
echo "1. Arrêt du service..."
sudo systemctl stop osint-enricher
sleep 2

# 2. Tuer les processus zombies
echo "2. Nettoyage des processus..."
sudo pkill -f "gunicorn.*5001" 2>/dev/null || true
sleep 1

# 3. Vérifier la configuration nginx et augmenter les timeouts
echo "3. Mise à jour configuration nginx..."
NGINX_CONFIG="/etc/nginx/sites-available/osint-enricher"

if [ -f "$NGINX_CONFIG" ]; then
    # Sauvegarder l'ancienne config
    sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Créer une nouvelle config avec timeouts augmentés
    sudo tee "$NGINX_CONFIG" > /dev/null <<'EOF'
server {
    listen 81;
    server_name _;

    auth_basic "OSINT Enricher";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Désactiver le buffering pour SSE
        proxy_buffering off;
        proxy_cache off;
        
        # Timeouts augmentés pour SSE et longues requêtes
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        
        # Headers pour SSE
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
EOF
    
    # Tester la configuration
    if sudo nginx -t; then
        echo "✅ Configuration nginx valide"
        sudo systemctl reload nginx
        echo "✅ Nginx rechargé"
    else
        echo "❌ Erreur dans la configuration nginx"
        sudo mv "${NGINX_CONFIG}.backup"* "$NGINX_CONFIG" 2>/dev/null || true
        exit 1
    fi
else
    echo "⚠️  Fichier nginx non trouvé: $NGINX_CONFIG"
fi

# 4. Vérifier le service systemd (s'assurer qu'il utilise 1 worker + timeout augmenté)
echo "4. Vérification service systemd..."
SERVICE_FILE="/etc/systemd/system/osint-enricher.service"

if [ -f "$SERVICE_FILE" ]; then
    # Sauvegarder l'ancienne config
    sudo cp "$SERVICE_FILE" "${SERVICE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Vérifier si --workers 1 et --timeout sont présents
    HAS_WORKERS=$(grep -q "--workers 1" "$SERVICE_FILE" && echo "yes" || echo "no")
    HAS_TIMEOUT=$(grep -q "--timeout" "$SERVICE_FILE" && echo "yes" || echo "no")
    
    if [ "$HAS_WORKERS" = "no" ] || [ "$HAS_TIMEOUT" = "no" ]; then
        echo "  → Modification pour utiliser 1 worker + timeout 600s"
        # Remplacer la ligne ExecStart
        sudo sed -i 's|ExecStart=.*gunicorn.*|ExecStart='${APP_DIR}'/venv/bin/gunicorn --bind 127.0.0.1:5001 app:app --workers 1 --timeout 600 --keep-alive 5|g' "$SERVICE_FILE"
        sudo systemctl daemon-reload
        echo "✅ Service modifié (1 worker, timeout 600s)"
    else
        echo "✅ Service déjà configuré correctement"
    fi
else
    echo "⚠️  Fichier service non trouvé: $SERVICE_FILE"
fi

# 5. Redémarrer le service
echo "5. Démarrage du service..."
sudo systemctl start osint-enricher
sleep 3

# 6. Vérifier le statut
echo "6. Vérification du statut..."
if sudo systemctl is-active --quiet osint-enricher; then
    echo "✅ Service démarré avec succès"
else
    echo "❌ Le service n'a pas démarré !"
    echo ""
    echo "Logs d'erreur:"
    sudo journalctl -u osint-enricher -n 20 --no-pager
    exit 1
fi

# 7. Test de connexion
echo "7. Test de connexion..."
sleep 2
if timeout 3 curl -s http://127.0.0.1:5001/health > /dev/null 2>&1; then
    echo "✅ Port 5001 répond"
else
    echo "⚠️  Port 5001 ne répond pas encore (peut prendre quelques secondes)"
fi

echo ""
echo "=== Correction terminée ==="
echo ""
echo "📊 Statut:"
sudo systemctl status osint-enricher --no-pager -l | head -10
echo ""
echo "📋 Vérifications:"
echo "  - Service actif: sudo systemctl is-active osint-enricher"
echo "  - Port 5001: curl http://127.0.0.1:5001/health"
echo "  - Logs: sudo journalctl -u osint-enricher -f"


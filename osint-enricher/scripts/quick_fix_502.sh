#!/bin/bash
# Fix rapide pour l'erreur 502 - Augmente le timeout Gunicorn

echo "🔧 Fix rapide : Augmentation timeout Gunicorn..."

SERVICE_FILE="/etc/systemd/system/osint-enricher.service"

if [ -f "$SERVICE_FILE" ]; then
    # Sauvegarder
    sudo cp "$SERVICE_FILE" "${SERVICE_FILE}.backup"
    
    # Modifier la ligne ExecStart pour ajouter --timeout 600
    sudo sed -i 's|ExecStart=.*gunicorn.*app:app|ExecStart=/home/ubuntu/maps-scraper/osint-enricher/venv/bin/gunicorn --bind 127.0.0.1:5001 app:app --workers 1 --timeout 600 --keep-alive 5|g' "$SERVICE_FILE"
    
    # Recharger et redémarrer
    sudo systemctl daemon-reload
    sudo systemctl restart osint-enricher
    
    echo "✅ Timeout Gunicorn augmenté à 600s"
    echo "✅ Service redémarré"
    
    sleep 3
    sudo systemctl status osint-enricher --no-pager -l | head -15
else
    echo "❌ Fichier service non trouvé: $SERVICE_FILE"
    exit 1
fi


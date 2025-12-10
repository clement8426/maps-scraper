#!/bin/bash

#############################################
# Script de démarrage manuel
# (Alternative au service systemd)
#############################################

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$APP_DIR/backend"

# Charger l'environnement virtuel
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
else
    echo "❌ Environnement virtuel non trouvé !"
    echo "Lancez d'abord: python3 -m venv venv"
    exit 1
fi

# Charger les variables d'environnement
if [ -f ../.env ]; then
    export $(cat ../.env | xargs)
fi

echo "🚀 Démarrage du serveur web..."
echo "📍 URL: http://localhost:${PORT:-5000}"
echo "👤 User: ${WEB_USERNAME:-admin}"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""

# Démarrer avec Gunicorn (production)
if command -v gunicorn &> /dev/null; then
    gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 600 app:app
else
    # Fallback sur Flask development server
    python app.py
fi


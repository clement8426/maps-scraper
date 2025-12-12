#!/bin/bash
# Script pour redémarrer le service osint-enricher de manière sécurisée

set -e

echo "=== Redémarrage sécurisé du service osint-enricher ==="
echo ""

# Aller dans le répertoire osint-enricher
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR/.." || { echo "❌ Erreur: Impossible d'aller dans le répertoire osint-enricher"; exit 1; }

echo "📁 Répertoire: $(pwd)"
echo ""

# 1. Vérifier la syntaxe Python
echo "1. Vérification syntaxe Python..."
cd backend
if ! python3 -m py_compile app.py pipeline.py 2>&1; then
    echo "❌ Erreur de syntaxe Python détectée !"
    echo "Corrigez les erreurs avant de redémarrer."
    exit 1
fi
echo "✅ Syntaxe Python: OK"
echo ""

# 2. Vérifier les imports
echo "2. Vérification des imports..."
if ! python3 -c "import app; import pipeline" 2>&1; then
    echo "❌ Erreur d'import détectée !"
    python3 -c "import app; import pipeline" 2>&1
    exit 1
fi
echo "✅ Imports: OK"
echo ""

# 3. Arrêter le service
echo "3. Arrêt du service..."
sudo systemctl stop osint-enricher || echo "⚠️ Service déjà arrêté"
sleep 2

# 4. Vérifier qu'il n'y a pas de processus zombie
echo "4. Nettoyage des processus..."
sudo pkill -f "gunicorn.*osint-enricher" 2>/dev/null || true
sleep 1

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

# 7. Vérifier que le port est en écoute
echo "7. Vérification du port 5001..."
sleep 2
if sudo netstat -tlnp 2>/dev/null | grep -q ":5001"; then
    echo "✅ Port 5001 en écoute"
else
    echo "⚠️ Port 5001 non détecté (peut prendre quelques secondes)"
fi

echo ""
echo "=== Redémarrage terminé ==="
echo ""
echo "📊 Statut:"
sudo systemctl status osint-enricher --no-pager -l | head -10
echo ""
echo "📋 Logs en temps réel:"
echo "  sudo journalctl -u osint-enricher -f"


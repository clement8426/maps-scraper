#!/bin/bash
# Fix: Réduire à 1 worker pour éviter les états désynchronisés

echo "🔧 Fix: Passage à 1 seul worker Gunicorn..."

# Modifier le service pour n'avoir qu'1 worker
sudo sed -i 's/--workers [0-9]*/--workers 1/' /etc/systemd/system/osint-enricher.service

# Recharger et redémarrer
sudo systemctl daemon-reload
sudo systemctl restart osint-enricher

echo "✅ Fait ! Le statut ne devrait plus switcher."
echo ""
echo "Vérification du service..."
sudo systemctl status osint-enricher --no-pager


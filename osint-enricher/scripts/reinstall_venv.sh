#!/bin/bash
# Script pour réinstaller complètement le venv

set -e

echo "🔄 Réinstallation complète du venv..."

cd "$(dirname "$0")/.." || exit 1

# Sauvegarder le chemin actuel
CURRENT_DIR=$(pwd)

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "requirements.txt" ]; then
    echo "❌ Erreur: requirements.txt introuvable. Êtes-vous dans le bon répertoire ?"
    exit 1
fi

# Supprimer l'ancien venv
echo "🗑️  Suppression de l'ancien venv..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "   ✅ Ancien venv supprimé"
fi

# Créer un nouveau venv
echo "📦 Création d'un nouveau venv..."
python3 -m venv venv

# Activer le venv
echo "🔌 Activation du venv..."
source venv/bin/activate

# Mettre à jour pip
echo "⬆️  Mise à jour de pip..."
pip install --upgrade pip --quiet

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo ""
echo "✅ Venv réinstallé avec succès !"
echo ""
echo "📋 Dépendances installées :"
pip list | grep -E "(beautifulsoup4|PyPDF2|selenium|requests|flask|gunicorn)" || echo "   (certaines dépendances peuvent ne pas être listées)"

echo ""
echo "🚀 Redémarrez le service avec :"
echo "   sudo systemctl restart osint-enricher"
echo ""
echo "📊 Vérifiez les logs avec :"
echo "   sudo journalctl -u osint-enricher -f"


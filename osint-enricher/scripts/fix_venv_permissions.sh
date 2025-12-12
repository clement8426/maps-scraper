#!/bin/bash
# Script pour corriger les permissions du venv et installer les dépendances

set -e

echo "🔧 Correction des permissions du venv..."

cd "$(dirname "$0")/.." || exit 1

# Vérifier si le venv existe
if [ ! -d "venv" ]; then
    echo "❌ Le venv n'existe pas. Création d'un nouveau venv..."
    python3 -m venv venv
fi

# Corriger les permissions
echo "📝 Correction des permissions..."
chmod -R u+w venv/ 2>/dev/null || true

# Activer le venv
echo "🔌 Activation du venv..."
source venv/bin/activate

# Mettre à jour pip
echo "⬆️  Mise à jour de pip..."
pip install --upgrade pip --quiet

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "✅ Dépendances installées avec succès !"
echo ""
echo "📋 Dépendances installées :"
pip list | grep -E "(beautifulsoup4|PyPDF2|selenium|requests)"

echo ""
echo "🚀 Redémarrez le service avec :"
echo "   sudo systemctl restart osint-enricher"


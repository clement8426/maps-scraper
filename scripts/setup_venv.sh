#!/bin/bash

#############################################
# Script de création de l'environnement virtuel
# À utiliser si install.sh n'a pas été lancé
#############################################

set -e

echo "============================================"
echo "🐍 Création de l'environnement virtuel"
echo "============================================"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Déterminer le répertoire du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$APP_DIR"

echo "📁 Répertoire: $APP_DIR"
echo ""

# Vérifier que Python 3 est installé
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé !${NC}"
    echo "Installez-le avec: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

# Vérifier que python3-venv est installé
if ! python3 -c "import venv" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  python3-venv n'est pas installé${NC}"
    echo "Installation..."
    sudo apt-get update -qq
    sudo apt-get install -y python3-venv -qq
fi

# Créer le venv s'il n'existe pas
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Le répertoire venv existe déjà${NC}"
    read -p "Voulez-vous le supprimer et le recréer ? (o/N): " response
    if [[ "$response" =~ ^[Oo]$ ]]; then
        echo "🗑️  Suppression de l'ancien venv..."
        rm -rf venv
    else
        echo "✅ Utilisation du venv existant"
    fi
fi

if [ ! -d "venv" ]; then
    echo "🐍 Création de l'environnement virtuel..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Environnement virtuel créé${NC}"
fi

# Activer le venv
echo "🔄 Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
echo "📦 Mise à jour de pip..."
pip install --upgrade pip -q

# Installer les dépendances
if [ -f "requirements.txt" ]; then
    echo "📦 Installation des dépendances Python..."
    pip install -r requirements.txt -q
    echo -e "${GREEN}✅ Dépendances installées${NC}"
else
    echo -e "${RED}❌ Fichier requirements.txt non trouvé !${NC}"
    exit 1
fi

# Installer les dépendances supplémentaires
echo "📦 Installation des dépendances supplémentaires..."
pip install flask flask-httpauth gunicorn -q

# Installer Playwright et Firefox
echo "🎭 Installation de Playwright et Firefox..."
playwright install firefox
playwright install-deps firefox

echo ""
echo "============================================"
echo -e "${GREEN}✅ Environnement virtuel prêt !${NC}"
echo "============================================"
echo ""
echo "Pour activer le venv manuellement:"
echo "  source venv/bin/activate"
echo ""
echo "Pour démarrer le serveur:"
echo "  ./scripts/start.sh"
echo ""


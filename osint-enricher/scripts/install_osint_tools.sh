#!/usr/bin/env bash
set -uo pipefail

echo "=== Installation des outils OSINT manquants ==="
echo ""

# 1. theHarvester
echo "📦 Installation de theHarvester..."
if ! command -v theHarvester &> /dev/null; then
  # Installer via pipx pour isolation
  if command -v pipx &> /dev/null; then
    pipx install theHarvester
  else
    # Sinon via pip avec --break-system-packages
    pip3 install theHarvester --break-system-packages || pip3 install theHarvester --user
  fi
  
  # Trouver et lier l'exécutable
  THEHARVESTER_PATH=$(find /usr/local /home -name theHarvester -type f 2>/dev/null | head -1)
  if [[ -n "$THEHARVESTER_PATH" ]]; then
    sudo ln -sf "$THEHARVESTER_PATH" /usr/local/bin/theHarvester
    echo "  ✅ theHarvester installé: $THEHARVESTER_PATH"
  else
    echo "  ⚠️  theHarvester installé mais exécutable non trouvé"
  fi
else
  echo "  ✅ theHarvester déjà disponible"
fi

# 2. subfinder (via releases GitHub)
echo ""
echo "📦 Installation de subfinder..."
if ! command -v subfinder &> /dev/null; then
  cd /tmp
  SUBFINDER_VERSION="v2.6.6"
  wget -q "https://github.com/projectdiscovery/subfinder/releases/download/${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION#v}_linux_amd64.zip" -O subfinder.zip
  
  if [[ $? -eq 0 ]]; then
    unzip -q subfinder.zip
    sudo mv subfinder /usr/local/bin/
    sudo chmod +x /usr/local/bin/subfinder
    rm -f subfinder.zip LICENSE.md README.md
    echo "  ✅ subfinder installé"
  else
    echo "  ⚠️  Échec téléchargement subfinder"
  fi
else
  echo "  ✅ subfinder déjà disponible"
fi

# 3. amass (via releases GitHub)
echo ""
echo "📦 Installation de amass..."
if ! command -v amass &> /dev/null; then
  cd /tmp
  AMASS_VERSION="v4.2.0"
  wget -q "https://github.com/owasp-amass/amass/releases/download/${AMASS_VERSION}/amass_Linux_amd64.zip" -O amass.zip
  
  if [[ $? -eq 0 ]]; then
    unzip -q amass.zip
    sudo mv amass_Linux_amd64/amass /usr/local/bin/
    sudo chmod +x /usr/local/bin/amass
    rm -rf amass.zip amass_Linux_amd64/
    echo "  ✅ amass installé"
  else
    echo "  ⚠️  Échec téléchargement amass"
  fi
else
  echo "  ✅ amass déjà disponible"
fi

echo ""
echo "=== Vérification finale ==="
for tool in theHarvester subfinder amass; do
  if command -v "$tool" &> /dev/null; then
    echo "✅ $tool → $(which $tool)"
  else
    echo "❌ $tool → NON TROUVÉ"
  fi
done

echo ""
echo "✅ Installation terminée !"
echo "⚠️  N'oubliez pas de redémarrer le service:"
echo "   sudo systemctl restart osint-enricher"


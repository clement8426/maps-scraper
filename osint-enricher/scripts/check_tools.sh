#!/usr/bin/env bash
# Script de diagnostic pour vérifier les outils OSINT

echo "=== Vérification des outils OSINT ==="
echo ""

TOOLS=(curl whatweb theHarvester subfinder amass whois pdfgrep)

for tool in "${TOOLS[@]}"; do
  if command -v "$tool" &> /dev/null; then
    path=$(which "$tool")
    echo "✅ $tool → $path"
  else
    echo "❌ $tool → NON TROUVÉ"
  fi
done

echo ""
echo "=== PATH actuel ==="
echo "$PATH"
echo ""

echo "=== Variables d'environnement service systemd ==="
if systemctl show osint-enricher -p Environment &> /dev/null; then
  systemctl show osint-enricher -p Environment
else
  echo "⚠️  Service osint-enricher non trouvé"
fi

echo ""
echo "=== Go binaries (si installés) ==="
if [[ -d "/home/ubuntu/go/bin" ]]; then
  ls -la /home/ubuntu/go/bin/ 2>/dev/null || echo "Répertoire vide"
else
  echo "Répertoire Go non trouvé"
fi


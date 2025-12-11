#!/usr/bin/env bash
# Script pour nettoyer complètement et recommencer l'enrichissement

set -e

echo "🧹 Nettoyage complet de l'enrichissement OSINT"
echo ""

# Chemin de la BDD
DB_PATH="${1:-$HOME/maps-scraper/backend/companies.db}"

if [[ ! -f "$DB_PATH" ]]; then
  echo "❌ Base de données non trouvée : $DB_PATH"
  exit 1
fi

# 1. Nettoyer les logs
echo "1️⃣ Nettoyage des logs..."
bash "$(dirname "$0")/clear_logs.sh" backend/pipeline.log --yes

# 2. Réinitialiser les statuts OSINT
echo ""
echo "2️⃣ Réinitialisation des statuts OSINT..."
python3 "$(dirname "$0")/reset_osint.py" "$DB_PATH" --yes

# 3. Nettoyer les tech_stack existants
echo ""
echo "3️⃣ Nettoyage des données tech_stack..."
python3 "$(dirname "$0")/clean_tech_stack.py" "$DB_PATH"

# 4. Redémarrer le service
echo ""
echo "4️⃣ Redémarrage du service..."
sudo systemctl restart osint-enricher

echo ""
echo "✅ Nettoyage terminé !"
echo ""
echo "🚀 Vous pouvez maintenant :"
echo "   1. Aller sur http://57.131.35.91:81/enrich"
echo "   2. Cocher 'Mode illimité' pour enrichir toute la base"
echo "   3. Cliquer sur 'Démarrer'"
echo ""
echo "📊 Suivre les logs : sudo journalctl -u osint-enricher -f"


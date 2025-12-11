#!/usr/bin/env bash
# Script pour nettoyer les anciens logs du pipeline

LOG_FILE="${1:-backend/pipeline.log}"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "❌ Fichier de log non trouvé : $LOG_FILE"
  exit 1
fi

echo "📝 Fichier de log : $LOG_FILE"
echo "📊 Taille actuelle : $(du -h "$LOG_FILE" | cut -f1)"
echo "📄 Lignes actuelles : $(wc -l < "$LOG_FILE")"
echo ""

read -p "⚠️  Voulez-vous vider le fichier de log ? (oui/non) : " response
if [[ "$response" =~ ^(oui|o|yes|y)$ ]]; then
  > "$LOG_FILE"
  echo "✅ Fichier de log vidé"
else
  echo "❌ Annulé"
fi


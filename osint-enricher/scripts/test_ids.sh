#!/bin/bash

# Script pour tester les IDs dans la base de données
# Usage: ./test_ids.sh

DB_PATH="../companies.db"

if [ ! -f "$DB_PATH" ]; then
    echo "❌ Base de données introuvable: $DB_PATH"
    exit 1
fi

echo "=========================================="
echo "🔍 Diagnostic des IDs dans la base de données"
echo "=========================================="
echo ""

echo "1️⃣ Plage d'IDs (min/max)"
sqlite3 "$DB_PATH" "SELECT MIN(id) as premier_id, MAX(id) as dernier_id, COUNT(*) as total FROM companies;"
echo ""

echo "2️⃣ Statuts OSINT"
sqlite3 "$DB_PATH" "SELECT osint_status, COUNT(*) as nombre FROM companies GROUP BY osint_status;"
echo ""

echo "3️⃣ Premières entreprises à enrichir (ORDER BY id ASC)"
sqlite3 "$DB_PATH" <<SQL
.mode column
.headers on
SELECT id, company_name, city, osint_status
FROM companies
WHERE (osint_status IS NULL OR osint_status NOT IN ('Done','Skipped'))
  AND website IS NOT NULL
  AND website <> ''
ORDER BY id ASC
LIMIT 10;
SQL
echo ""

echo "4️⃣ Vérification ID spécifique (41971, 41972, 42490)"
for id in 41971 41972 42490; do
    echo "ID $id:"
    sqlite3 "$DB_PATH" "SELECT id, company_name, city, osint_status FROM companies WHERE id = $id;"
done
echo ""

echo "✅ Diagnostic terminé"


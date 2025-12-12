#!/bin/bash
# Script pour diagnostiquer le service osint-enricher

echo "=== Diagnostic du service osint-enricher ==="
echo ""

# 1. Vérifier le statut du service
echo "1. Statut du service:"
sudo systemctl status osint-enricher --no-pager -l | head -20
echo ""

# 2. Vérifier les logs récents
echo "2. Logs récents (dernières 30 lignes):"
sudo journalctl -u osint-enricher -n 30 --no-pager
echo ""

# 3. Vérifier si le port est en écoute
echo "3. Port 5001 (gunicorn):"
sudo netstat -tlnp | grep 5001 || echo "❌ Port 5001 non en écoute"
echo ""

# 4. Vérifier les processus gunicorn
echo "4. Processus gunicorn:"
ps aux | grep gunicorn | grep -v grep || echo "❌ Aucun processus gunicorn"
echo ""

# 5. Tester la syntaxe Python
echo "5. Vérification syntaxe Python:"
cd "$(dirname "$0")/.."
python3 -m py_compile backend/app.py && echo "✅ app.py: OK" || echo "❌ app.py: Erreur de syntaxe"
python3 -m py_compile backend/pipeline.py && echo "✅ pipeline.py: OK" || echo "❌ pipeline.py: Erreur de syntaxe"
echo ""

# 6. Vérifier les imports
echo "6. Test des imports:"
cd backend
python3 -c "import app; print('✅ Imports app.py: OK')" 2>&1 || echo "❌ Erreur imports app.py"
python3 -c "import pipeline; print('✅ Imports pipeline.py: OK')" 2>&1 || echo "❌ Erreur imports pipeline.py"
echo ""

# 7. Vérifier la configuration nginx
echo "7. Configuration nginx (osint-enricher):"
sudo nginx -t 2>&1 | grep -A 5 "osint-enricher" || echo "Vérifiez manuellement: sudo cat /etc/nginx/sites-enabled/osint-enricher"
echo ""

echo "=== Fin du diagnostic ==="
echo ""
echo "Pour redémarrer le service:"
echo "  sudo systemctl restart osint-enricher"
echo ""
echo "Pour suivre les logs en temps réel:"
echo "  sudo journalctl -u osint-enricher -f"


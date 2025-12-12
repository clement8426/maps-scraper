#!/bin/bash
# Script pour diagnostiquer l'erreur 502 et la lenteur

echo "=== Diagnostic 502 Bad Gateway et lenteur ==="
echo ""

# 1. Statut du service
echo "1. Statut du service osint-enricher:"
sudo systemctl status osint-enricher --no-pager -l | head -15
echo ""

# 2. Logs récents avec erreurs
echo "2. Logs récents (dernières 50 lignes, avec erreurs):"
sudo journalctl -u osint-enricher -n 50 --no-pager | grep -E "(ERROR|error|Exception|Traceback|502|timeout)" || echo "Aucune erreur récente"
echo ""

# 3. Vérifier si le port 5001 répond
echo "3. Test de connexion au port 5001:"
timeout 2 curl -s http://127.0.0.1:5001/health 2>&1 | head -5 || echo "❌ Port 5001 ne répond pas"
echo ""

# 4. Processus gunicorn
echo "4. Processus gunicorn osint-enricher:"
ps aux | grep "gunicorn.*5001" | grep -v grep || echo "❌ Aucun processus gunicorn sur port 5001"
echo ""

# 5. Utilisation CPU/Mémoire
echo "5. Utilisation ressources (top 5 processus Python):"
ps aux | grep python | grep -E "(gunicorn|osint)" | head -5
echo ""

# 6. Vérifier les connexions au port 5001
echo "6. Connexions au port 5001:"
sudo ss -tlnp | grep 5001 || echo "❌ Port 5001 non en écoute"
echo ""

# 7. Logs nginx (erreurs récentes)
echo "7. Logs nginx (erreurs récentes):"
sudo tail -20 /var/log/nginx/error.log 2>/dev/null | grep -E "(502|upstream|timeout|osint)" || echo "Pas d'erreurs nginx récentes"
echo ""

# 8. Configuration nginx pour osint-enricher
echo "8. Configuration nginx osint-enricher:"
sudo cat /etc/nginx/sites-enabled/osint-enricher 2>/dev/null | head -30 || echo "Fichier non trouvé"
echo ""

# 9. Test de charge sur le port 5001
echo "9. Test de réponse (3 requêtes):"
for i in {1..3}; do
    echo -n "  Requête $i: "
    time timeout 5 curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/health 2>&1 || echo "timeout"
    echo ""
done

echo ""
echo "=== Fin du diagnostic ==="
echo ""
echo "Solutions possibles:"
echo "  1. Redémarrer le service: sudo systemctl restart osint-enricher"
echo "  2. Vérifier les logs: sudo journalctl -u osint-enricher -f"
echo "  3. Vérifier nginx: sudo nginx -t && sudo systemctl reload nginx"


#!/bin/bash

#############################################
# Démarrage rapide en local
#############################################

echo "🚀 Démarrage du serveur en local..."
echo ""

# Vérifier qu'on est dans le bon dossier
if [ ! -f "backend/app.py" ]; then
    echo "❌ Erreur : Lancez ce script depuis la racine du projet"
    exit 1
fi

# Vérifier le fichier .env
if [ ! -f ".env" ]; then
    echo "📝 Création du fichier .env..."
    cp env.example .env
    echo "⚠️  Modifiez .env si besoin (username/password)"
    echo ""
fi

# Charger les variables (en ignorant les commentaires)
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Tuer le processus sur le port si existant
PORT_TO_USE=${PORT:-5000}
echo "🔍 Vérification du port $PORT_TO_USE..."

# Essayer de tuer le processus plusieurs fois
for i in {1..3}; do
    if lsof -ti:$PORT_TO_USE > /dev/null 2>&1; then
        echo "⚠️  Port $PORT_TO_USE occupé (tentative $i/3), arrêt du processus..."
        lsof -ti:$PORT_TO_USE | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo "✅ Port $PORT_TO_USE disponible"
        break
    fi
done

# Si toujours occupé, suggérer un autre port
if lsof -ti:$PORT_TO_USE > /dev/null 2>&1; then
    echo "❌ Port $PORT_TO_USE toujours occupé (probablement AirPlay Receiver)"
    echo "💡 Utilisation du port 8080 à la place..."
    export PORT=8080
    PORT_TO_USE=8080
fi
echo ""

# Aller dans backend
cd backend

echo "============================================"
echo "✅ Serveur prêt !"
echo "============================================"
echo ""
echo "📍 URL : http://localhost:${PORT:-5000}"
echo "👤 Username : ${WEB_USERNAME:-admin}"
echo "🔑 Password : ${WEB_PASSWORD:-test123}"
echo ""
echo "============================================"
echo ""
echo "💡 Astuce : Ouvrez http://localhost:${PORT:-5000} dans votre navigateur"
echo ""
echo "⏹️  Pour arrêter : Ctrl + C"
echo ""

# Démarrer le serveur
python app.py


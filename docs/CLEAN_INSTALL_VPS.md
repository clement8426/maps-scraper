# 🧹 Nettoyage complet et réinstallation VPS

## 🔴 Script de nettoyage complet

Copie-colle ce bloc complet sur ton VPS :

```bash
#!/bin/bash

echo "============================================"
echo "🧹 NETTOYAGE COMPLET DU VPS"
echo "============================================"
echo ""

# 1. Arrêter le service s'il existe
echo "🛑 Arrêt du service scraper-web..."
sudo systemctl stop scraper-web 2>/dev/null || true
sudo systemctl disable scraper-web 2>/dev/null || true

# 2. Supprimer le service systemd
echo "🗑️  Suppression du service systemd..."
sudo rm -f /etc/systemd/system/scraper-web.service
sudo systemctl daemon-reload

# 3. Supprimer la configuration Nginx
echo "🗑️  Suppression de la configuration Nginx..."
sudo rm -f /etc/nginx/sites-available/scraper
sudo rm -f /etc/nginx/sites-enabled/scraper
sudo rm -f /etc/nginx/.htpasswd
sudo systemctl restart nginx 2>/dev/null || true

# 4. Supprimer l'utilisateur scraper et ses fichiers
echo "🗑️  Suppression de l'utilisateur scraper..."
sudo pkill -u scraper 2>/dev/null || true
sudo userdel -r scraper 2>/dev/null || true
sudo rm -rf /home/scraper

# 5. Supprimer le repo cloné
echo "🗑️  Suppression du repo cloné..."
cd ~
sudo rm -rf maps-scraper

# 6. Supprimer le PPA deadsnakes s'il existe
echo "🗑️  Suppression du PPA deadsnakes..."
sudo rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-*.list
sudo rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-*.sources

# 7. Nettoyer apt
echo "🧹 Nettoyage apt..."
sudo apt-get clean
sudo apt-get update

echo ""
echo "============================================"
echo "✅ NETTOYAGE TERMINÉ"
echo "============================================"
echo ""
echo "📝 Prochaines étapes :"
echo "   1. git clone https://github.com/clement8426/maps-scraper.git"
echo "   2. cd maps-scraper"
echo "   3. sudo ./scripts/install.sh"
echo ""
```

## 🚀 Installation complète (après nettoyage)

Après avoir lancé le script de nettoyage ci-dessus, lance :

```bash
# Cloner le repo (avec les dernières modifications)
git clone https://github.com/clement8426/maps-scraper.git
cd maps-scraper

# Lancer l'installation
sudo ./scripts/install.sh
```

## 📋 Version ultra-courte (tout en une commande)

Si tu veux vraiment TOUT en une seule commande :

```bash
sudo systemctl stop scraper-web 2>/dev/null; \
sudo systemctl disable scraper-web 2>/dev/null; \
sudo rm -f /etc/systemd/system/scraper-web.service; \
sudo systemctl daemon-reload; \
sudo rm -f /etc/nginx/sites-available/scraper /etc/nginx/sites-enabled/scraper /etc/nginx/.htpasswd; \
sudo systemctl restart nginx 2>/dev/null; \
sudo pkill -u scraper 2>/dev/null; \
sudo userdel -r scraper 2>/dev/null; \
sudo rm -rf /home/scraper; \
cd ~ && sudo rm -rf maps-scraper; \
sudo rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-*; \
sudo apt-get update; \
git clone https://github.com/clement8426/maps-scraper.git; \
cd maps-scraper; \
sudo ./scripts/install.sh
```

---

**Copie-colle simplement le script complet ou la version ultra-courte !** 🚀


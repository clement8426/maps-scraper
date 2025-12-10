# 🕷️ Scraper Google Maps - Suisse Romande

**Système complet de scraping avec interface web** pour extraire et gérer les données d'entreprises tech depuis Google Maps.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## ⚡ Quick Start

### Sur VPS (Recommandé)

```bash
# 1. Cloner le projet
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap

# 2. Installer (tout automatique)
sudo ./scripts/install.sh

# 3. Ouvrir l'interface web
# URL affichée en fin d'installation
```

**⏱️ Temps : 5-10 minutes**

### En local (Développement)

```bash
# 1. Cloner et installer
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap
pip install -r requirements.txt
playwright install firefox

# 2. Configuration
cp env.example .env
nano .env  # Modifier USERNAME et PASSWORD

# 3. Lancer
cd backend
python app.py
# Ouvrir http://localhost:5000
```

---

## 📁 Structure du projet

```
maps-scrap/
├── backend/              # Backend Flask + Scraper
│   ├── app.py           # API REST
│   ├── scraper_suisse_romande.py  # Scraper principal
│   └── utils/           # Utilitaires (validation emails, etc.)
├── frontend/            # Interface web
│   ├── index.html      # Dashboard
│   ├── style.css       # Design moderne
│   └── script.js       # Interactivité
├── scripts/             # Scripts d'installation
│   ├── install.sh      # Installation VPS (automatique)
│   └── start.sh        # Démarrage manuel
├── docs/                # Documentation
│   ├── DEPLOY.md       # Guide déploiement VPS
│   └── QUICKSTART.md   # Guide rapide
├── tests/               # Tests et outils de debug
└── requirements.txt     # Dépendances Python
```

---

## ✨ Fonctionnalités

### 🎯 Scraping
- **25 villes** (Canton de Neuchâtel + Suisse Romande)
- **40 mots-clés** tech (Web, SaaS, DevOps, Data, IA...)
- **Extraction** : nom, adresse, téléphone, site, email, note, avis
- **Anti-détection** : user-agents rotatifs, délais aléatoires
- **Reprise automatique** après interruption

### 🌐 Interface Web
- **Dashboard temps réel** avec statistiques
- **Filtres avancés** (ville, email, site web)
- **Contrôle du scraper** (démarrer/arrêter)
- **Export CSV** avec filtres
- **Graphiques** (top villes)

### 💾 Stockage
- **SQLite** (base de données embarquée)
- **Export CSV** à la demande
- **Sauvegarde automatique**

### 🔒 Sécurité
- **Double authentification** (Nginx + Flask)
- **Firewall configuré** automatiquement
- **HTTPS ready** (certificat Let's Encrypt)

### ✅ Validation
- **Emails vérifiés** par DNS (MX records)
- **Suppression des emails fictifs**
- **Nettoyage automatique**

---

## 🗺️ Zones géographiques

### Canton de Neuchâtel (priorité)
Neuchâtel, La Chaux-de-Fonds, Le Locle, Val-de-Ruz, Val-de-Travers, Fleurier, Cernier, Peseux, Colombier, Marin-Epagnier, Saint-Blaise, Boudry, Cressier

### Villes proches
Yverdon-les-Bains, Pontarlier, Morteau, Besançon

### Suisse Romande
Genève, Lausanne, Fribourg, Sion, Nyon, Renens, Meyrin, Vevey, Montreux, Delémont, Porrentruy

**Total : 1000 combinaisons possibles** (25 villes × 40 mots-clés)

---

## 📊 Résultats attendus

- **Volume** : 10 000 - 50 000 entreprises
- **Temps** : 8-12h pour tout scraper
- **Qualité** : Emails validés DNS, données publiques uniquement

---

## 🛠️ Commandes utiles

```bash
# Service systemd
sudo systemctl status scraper-web
sudo systemctl restart scraper-web
sudo journalctl -u scraper-web -f

# Base de données
cd backend && sqlite3 companies.db
SELECT * FROM companies WHERE city = 'Neuchâtel' LIMIT 10;

# Mise à jour
git pull
sudo systemctl restart scraper-web
```

---

## 📖 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Démarrage rapide (5 min)
- **[DEPLOY.md](docs/DEPLOY.md)** - Guide de déploiement complet
- **[API Documentation](#api-endpoints)** - Endpoints REST

---

## 🔌 API Endpoints

```
GET  /                      # Dashboard HTML
GET  /api/companies         # Liste des entreprises (avec filtres)
GET  /api/stats            # Statistiques globales
GET  /api/cities           # Liste des villes
GET  /api/scraper/status   # Statut du scraper
POST /api/scraper/start    # Démarrer le scraper
POST /api/scraper/stop     # Arrêter le scraper
GET  /api/export/csv       # Exporter en CSV
```

### Exemples

```bash
# Obtenir les statistiques
curl -u admin:password http://localhost:5000/api/stats

# Filtrer par ville
curl -u admin:password "http://localhost:5000/api/companies?city=Neuchâtel"

# Entreprises avec email uniquement
curl -u admin:password "http://localhost:5000/api/companies?has_email=true"
```

---

## ⚙️ Configuration

### Variables d'environnement (.env)

```bash
WEB_USERNAME=admin          # Nom d'utilisateur interface web
WEB_PASSWORD=votre_mdp      # Mot de passe
PORT=5000                   # Port du serveur
DEBUG=False                 # Mode debug (False en production)
```

### Personnaliser les recherches

Modifier `backend/scraper_suisse_romande.py` :

```python
# Ajouter des villes (ligne ~20)
CITIES = [
    "Neuchâtel", "Le Locle",
    "Votre Ville",  # Ajoutez ici
]

# Ajouter des mots-clés (ligne ~35)
KEYWORDS = [
    "Agence Web", "Startup",
    "Votre Keyword",  # Ajoutez ici
]
```

---

## 🐛 Dépannage

### Le service ne démarre pas
```bash
sudo journalctl -u scraper-web -n 50
sudo systemctl restart scraper-web
```

### Impossible d'accéder à l'interface
```bash
sudo systemctl status nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Le scraper ne trouve rien
```bash
cd /home/scraper/maps-scraper
source venv/bin/activate
playwright install firefox
playwright install-deps firefox
```

### Réinitialiser les données
```bash
cd /home/scraper/maps-scraper/backend
rm companies.db checkpoint.json intermediate_data.csv
sudo systemctl restart scraper-web
```

---

## ⚠️ Avertissements légaux

- **Usage personnel/éducatif uniquement**
- Respectez les CGU de Google Maps
- Respectez le RGPD et la LPD suisse
- Données publiques uniquement
- Ne pas utiliser à des fins commerciales sans autorisation

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -m 'Ajout fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

---

## 📝 Licence

Ce projet est fourni à des fins éducatives. Utilisez-le de manière responsable.

---

## 🆘 Support

- 📖 [Documentation complète](docs/)
- 🐛 [Issues GitHub](https://github.com/VOTRE_USERNAME/maps-scrap/issues)
- 💬 [Discussions](https://github.com/VOTRE_USERNAME/maps-scrap/discussions)

---

**Fait avec ❤️ pour le canton de Neuchâtel et la Suisse Romande**

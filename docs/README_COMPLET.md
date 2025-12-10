# 🕷️ Scraper Google Maps - Suisse Romande

**Système complet de scraping avec interface web** pour extraire et gérer les données d'entreprises tech depuis Google Maps.

## ✨ Caractéristiques principales

### 🎯 Scraping automatisé
- **25 villes** (focus canton de Neuchâtel + Suisse Romande)
- **40 mots-clés tech** (Web, Software, SaaS, DevOps, Data, etc.)
- **1000 combinaisons possibles**
- Extraction : nom, adresse, téléphone, site web, email, note, avis

### 🌐 Interface web moderne
- **Dashboard en temps réel**
- **Filtres avancés** (ville, site web, email)
- **Contrôle du scraper** (démarrage/arrêt)
- **Export CSV** avec filtres
- **Statistiques visuelles**

### 🔒 Sécurité
- **Double authentification** (Nginx + Flask)
- **Firewall configuré**
- **Mots de passe chiffrés**
- **HTTPS ready**

### 💾 Stockage
- **SQLite** (base de données embarquée)
- **CSV** (export facile)
- **Sauvegarde automatique** (reprise après interruption)

### 🛡️ Anti-détection
- **11 User-Agents rotatifs**
- **Délais aléatoires**
- **Navigation naturelle**
- **Firefox headless**

### ✅ Validation intelligente
- **Emails vérifiés par DNS** (MX records)
- **Suppression des emails fictifs**
- **Nettoyage automatique**

## 🚀 Installation

### Développement local

```bash
# Cloner le repo
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap

# Installer les dépendances
pip install -r requirements.txt
playwright install firefox

# Copier l'exemple de configuration
cp env.example .env

# Modifier .env avec vos identifiants
nano .env

# Lancer le serveur
cd backend && python app.py
```

Accédez à http://localhost:5000

### Déploiement VPS (Production)

```bash
# Sur le VPS (Ubuntu/Debian)
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap
sudo ./scripts/install.sh
```

**C'est tout !** Le script configure automatiquement :
- Python, Nginx, Playwright
- Service systemd
- Firewall
- Certificats

Voir [DEPLOY.md](DEPLOY.md) pour plus de détails.

## 📁 Structure du projet

```
maps-scrap/
├── backend/
│   ├── app.py                      # API Flask
│   ├── scraper_suisse_romande.py   # Scraper principal
│   ├── companies.db                # Base SQLite
│   └── checkpoint.json             # Progression
├── frontend/
│   ├── index.html                  # Dashboard
│   ├── style.css                   # Styles
│   └── script.js                   # JavaScript
├── scripts/
│   ├── install.sh                  # Installation VPS
│   └── start.sh                    # Démarrage manuel
├── requirements.txt                # Dépendances Python
├── README.md                       # Guide utilisateur
└── DEPLOY.md                       # Guide déploiement
```

## 🎮 Utilisation

### Via l'interface web

1. **Ouvrir** l'interface : http://VOTRE_IP
2. **S'authentifier** avec vos identifiants
3. **Démarrer le scraper** : cliquer sur "▶️ Démarrer"
4. **Filtrer** les résultats par ville, email, site web
5. **Exporter** en CSV

### Via ligne de commande

```bash
# Lancer le scraper en CLI
cd backend
python scraper_suisse_romande.py

# Requêtes SQL directes
sqlite3 companies.db
SELECT * FROM companies WHERE city = 'Neuchâtel' AND email IS NOT NULL;
```

## 📊 API Endpoints

```
GET  /                          # Dashboard
GET  /api/companies             # Liste des entreprises (+ filtres)
GET  /api/stats                 # Statistiques
GET  /api/cities                # Liste des villes
GET  /api/scraper/status        # Statut du scraper
POST /api/scraper/start         # Démarrer le scraper
POST /api/scraper/stop          # Arrêter le scraper
GET  /api/export/csv            # Exporter en CSV
```

## ⚙️ Configuration

### Variables d'environnement (.env)

```bash
WEB_USERNAME=admin              # Nom d'utilisateur web
WEB_PASSWORD=votre_mdp          # Mot de passe web
PORT=5000                       # Port du serveur
DEBUG=False                     # Mode debug
```

### Personnaliser les recherches

Modifier `backend/scraper_suisse_romande.py` :

```python
# Ajouter des villes
CITIES = [
    "Neuchâtel", "Le Locle", "La Chaux-de-Fonds",
    # Ajoutez vos villes ici
]

# Ajouter des mots-clés
KEYWORDS = [
    "Agence Web", "Développement logiciel",
    # Ajoutez vos keywords ici
]
```

## 🔧 Maintenance

### Logs

```bash
# Logs du service
sudo journalctl -u scraper-web -f

# Logs Nginx
sudo tail -f /var/log/nginx/error.log
```

### Backup

```bash
# Sauvegarder la base de données
cp backend/companies.db ~/backup_$(date +%Y%m%d).db

# Restaurer
cp ~/backup_YYYYMMDD.db backend/companies.db
```

### Mise à jour

```bash
git pull
sudo systemctl restart scraper-web
```

## 🐛 Dépannage

Voir [DEPLOY.md - Section Dépannage](DEPLOY.md#-dépannage)

## 📈 Performance

- **Vitesse** : ~10-50 entreprises par recherche
- **Durée** : 8-12h pour toutes les combinaisons
- **Volume** : 10 000 - 50 000 entreprises potentielles

## ⚠️ Avertissements légaux

- **Usage personnel/éducatif uniquement**
- Respectez les CGU de Google Maps
- Respectez le RGPD et la LPD suisse
- Ne pas utiliser à des fins commerciales sans autorisation
- Données publiques uniquement

## 🤝 Contribution

Pour contribuer :
1. Fork le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -m 'Ajout fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est fourni à des fins éducatives. Utilisez-le de manière responsable.

## 🆘 Support

- 📖 Documentation : README.md + DEPLOY.md
- 🐛 Issues : GitHub Issues
- 💬 Questions : Créer une discussion

---

**Fait avec ❤️ pour le canton de Neuchâtel et la Suisse Romande**


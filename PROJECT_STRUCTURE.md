# 📁 Structure du projet

## 🌳 Arborescence

```
maps-scrap/
│
├── 📄 README.md              # Documentation principale (COMMENCEZ ICI)
├── 📄 requirements.txt       # Dépendances Python
├── 📄 env.example            # Exemple de configuration
├── 📄 .gitignore             # Fichiers ignorés par Git
│
├── 📂 backend/               # Backend Flask + Scraper
│   ├── app.py                    # API REST (interface web)
│   ├── scraper_suisse_romande.py # Scraper principal
│   ├── companies.db              # Base de données SQLite (générée)
│   ├── checkpoint.json           # Point de reprise (généré)
│   └── utils/                    # Utilitaires
│       ├── __init__.py
│       ├── clean_and_deduce_emails.py
│       └── verify_emails.py
│
├── 📂 frontend/              # Interface web
│   ├── index.html                # Dashboard HTML
│   ├── style.css                 # Styles CSS
│   └── script.js                 # JavaScript (AJAX, filtres)
│
├── 📂 scripts/               # Scripts d'installation et démarrage
│   ├── install.sh                # Installation VPS (automatique)
│   └── start.sh                  # Démarrage manuel
│
├── 📂 docs/                  # Documentation complète
│   ├── QUICKSTART.md             # Démarrage rapide (5 min)
│   ├── DEPLOY.md                 # Guide déploiement VPS
│   └── README_COMPLET.md         # Documentation technique
│
├── 📂 tests/                 # Tests et outils de debug
│   ├── test_enrichment.py        # Test extraction données
│   ├── test_firefox.py           # Test navigateur
│   ├── test_curl.py              # Test requêtes HTTP
│   └── inspect_maps_html.py      # Inspection HTML
│
└── 📂 config/                # Configurations (Nginx, etc.)

```

## 🎯 Rôle de chaque dossier

### 📂 `backend/`
**Cœur de l'application**
- `app.py` : Serveur Flask avec API REST
- `scraper_suisse_romande.py` : Logique de scraping
- `utils/` : Fonctions utilitaires (validation emails, etc.)
- **Fichiers générés** : `companies.db`, `checkpoint.json`, `*.csv`

### 📂 `frontend/`
**Interface utilisateur**
- Dashboard web moderne
- Visualisation des données en temps réel
- Filtres et exports
- Contrôle du scraper

### 📂 `scripts/`
**Automatisation**
- `install.sh` : Installation complète sur VPS (1 commande)
- `start.sh` : Démarrage manuel du serveur

### 📂 `docs/`
**Guides et documentation**
- `QUICKSTART.md` : Démarrage en 5 minutes
- `DEPLOY.md` : Guide complet pour VPS
- `README_COMPLET.md` : Documentation technique détaillée

### 📂 `tests/`
**Outils de test et debug**
- Tests unitaires
- Outils d'inspection HTML
- Tests de compatibilité navigateur

### 📂 `config/`
**Fichiers de configuration**
- Configuration Nginx
- Variables d'environnement
- Certificats SSL (si utilisés)

## 🚀 Par où commencer ?

### 1️⃣ Pour déployer sur VPS
```bash
1. Lire : README.md
2. Suivre : docs/QUICKSTART.md
3. Exécuter : sudo ./scripts/install.sh
```

### 2️⃣ Pour développer en local
```bash
1. Lire : README.md
2. Installer : pip install -r requirements.txt
3. Configurer : cp env.example .env
4. Lancer : cd backend && python app.py
```

### 3️⃣ Pour comprendre le code
```bash
1. Lire : docs/README_COMPLET.md
2. Explorer : backend/scraper_suisse_romande.py
3. Tester : tests/test_enrichment.py
```

## 📝 Fichiers à la racine (minimum)

- ✅ `README.md` - Point d'entrée
- ✅ `requirements.txt` - Dépendances
- ✅ `env.example` - Configuration
- ✅ `.gitignore` - Exclusions Git

**Tout le reste est organisé dans des dossiers thématiques !**

## 🔄 Fichiers générés (ignorés par Git)

Ces fichiers sont créés automatiquement lors de l'exécution :

```
backend/
├── companies.db           # Base de données SQLite
├── checkpoint.json        # Progression du scraper
├── intermediate_data.csv  # Données temporaires
└── base_tech_suisse.csv   # Export final

venv/                      # Environnement virtuel Python
__pycache__/              # Cache Python
ms-playwright/            # Binaires Playwright
.env                      # Configuration (secrets)
```

## 🎨 Philosophie de l'organisation

1. **Séparation claire** : Backend / Frontend / Scripts / Docs
2. **Un fichier, un rôle** : Chaque fichier a une responsabilité unique
3. **Documentation proche du code** : docs/ centralisé
4. **Tests isolés** : tests/ séparé du code production
5. **Racine minimaliste** : Seulement les fichiers essentiels

---

**Navigation rapide** : [README](README.md) | [Quick Start](docs/QUICKSTART.md) | [Deploy](docs/DEPLOY.md)


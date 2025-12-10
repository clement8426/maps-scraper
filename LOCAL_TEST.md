# 🧪 Test en local (avant VPS)

Guide pour tester l'interface web sur votre machine locale.

## ⚡ Installation rapide

### 1. Installer les dépendances

```bash
cd /Users/soleadmaci9/test/maps-scrap

# Installer les dépendances Python
pip install -r requirements.txt

# Installer Flask et Gunicorn
pip install flask flask-httpauth gunicorn

# Installer Playwright + Firefox
playwright install firefox
```

### 2. Configurer l'environnement

```bash
# Créer le fichier .env
cp env.example .env

# Éditer avec vos identifiants
nano .env
```

Dans `.env`, modifier :
```bash
WEB_USERNAME=admin
WEB_PASSWORD=test123      # Changez ce mot de passe
PORT=5000
DEBUG=True                # True pour le dev local
```

### 3. Lancer le serveur

```bash
cd backend
python app.py
```

Vous devriez voir :
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 4. Ouvrir dans le navigateur

Ouvrez : **http://localhost:5000**

Authentification :
- **Username** : `admin`
- **Password** : `test123` (ou celui que vous avez mis dans .env)

## 🎮 Test des fonctionnalités

### ✅ Vérifier le dashboard
- Les statistiques s'affichent (même à 0)
- Les filtres sont présents
- Le bouton "Démarrer" est visible

### ✅ Lancer un test de scraping

1. Cliquez sur **"▶️ Démarrer"**
2. Attendez quelques secondes
3. Vérifiez que :
   - Le statut passe à "En cours"
   - Les entreprises apparaissent dans le tableau
   - Les statistiques se mettent à jour

### ✅ Tester les filtres

1. Sélectionnez une ville dans le filtre
2. Cliquez sur **"Appliquer"**
3. Vérifiez que le tableau se filtre

### ✅ Tester l'export

1. Appliquez un filtre (ex: Neuchâtel)
2. Cliquez sur **"📥 Exporter CSV"**
3. Vérifiez que le fichier se télécharge

## 🐛 En cas de problème

### Erreur : "Module not found"

```bash
pip install -r requirements.txt
pip install flask flask-httpauth gunicorn
```

### Erreur : "Playwright not found"

```bash
playwright install firefox
playwright install-deps firefox
```

### Erreur : "Port 5000 already in use"

```bash
# Option 1 : Changer le port dans .env
PORT=8080

# Option 2 : Tuer le processus sur le port 5000
lsof -ti:5000 | xargs kill -9
```

### Le scraper ne démarre pas

```bash
# Vérifier que Firefox est installé
playwright install firefox

# Tester le scraper en CLI
cd backend
python scraper_suisse_romande.py
```

### Impossible de se connecter

```bash
# Vérifier le .env
cat .env

# Vérifier que le serveur tourne
lsof -i:5000
```

## 🔄 Arrêter le serveur

```bash
# Dans le terminal où le serveur tourne
Ctrl + C
```

## 📊 Vérifier la base de données

```bash
cd backend

# Ouvrir la base SQLite
sqlite3 companies.db

# Compter les entreprises
SELECT COUNT(*) FROM companies;

# Voir les 10 dernières
SELECT company_name, city FROM companies LIMIT 10;

# Quitter
.quit
```

## 🚀 Une fois validé en local

Si tout fonctionne en local, vous êtes prêt pour le VPS :

1. Pushez votre code sur GitHub
2. Suivez **docs/QUICKSTART.md** pour le déploiement VPS
3. Lancez `./scripts/install.sh` sur le VPS

## 💡 Astuces

### Mode debug activé

En local, gardez `DEBUG=True` dans `.env` :
- Rechargement automatique du code
- Messages d'erreur détaillés
- Logs complets dans le terminal

### Tester sans scraper

Si vous voulez juste tester l'interface sans lancer le scraper :
1. Lancez uniquement le serveur : `python app.py`
2. L'interface s'affiche même sans données
3. Les statistiques affichent 0

### Utiliser un autre navigateur

Par défaut, le scraper utilise Firefox. Pour tester avec Chromium :

```python
# Dans backend/scraper_suisse_romande.py, ligne 39
BROWSER_TYPE = "chromium"  # Au lieu de "firefox"
```

Puis :
```bash
playwright install chromium
```

## 📝 Checklist de test

Avant de déployer sur le VPS, vérifiez :

- [ ] Le serveur démarre sans erreur
- [ ] L'interface web s'affiche
- [ ] L'authentification fonctionne
- [ ] Le dashboard affiche les statistiques
- [ ] Le scraper peut démarrer/s'arrêter
- [ ] Les filtres fonctionnent
- [ ] L'export CSV fonctionne
- [ ] La base de données se remplit

**Si tout est ✅, vous êtes prêt pour le VPS !**

---

**Navigation** : [README](../README.md) | [Structure](../PROJECT_STRUCTURE.md) | [Deploy VPS](docs/QUICKSTART.md)


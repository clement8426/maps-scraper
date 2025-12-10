# 🔍 Diagnostic du Scraper

## ✅ Vérifications à faire sur le VPS

### 1. Vérifier que le service tourne

```bash
sudo systemctl status scraper-web
```

**Doit afficher** : `active (running)`

### 2. Vérifier les logs du service

```bash
sudo journalctl -u scraper-web -n 50 --no-pager
```

Cherche les erreurs en rouge.

### 3. Vérifier si le scraper démarre vraiment

```bash
# Voir les processus Python
ps aux | grep scraper_suisse_romande

# Voir tous les processus Python
ps aux | grep python
```

### 4. Tester manuellement le démarrage du scraper

```bash
# Se connecter en tant que scraper
sudo su - scraper

# Aller dans le répertoire
cd /home/scraper/maps-scraper/backend

# Activer le venv
source ../venv/bin/activate

# Tester le scraper directement
python scraper_suisse_romande.py
```

**Si ça plante**, tu verras l'erreur exacte.

### 5. Vérifier les permissions

```bash
# Vérifier les permissions du répertoire
ls -la /home/scraper/maps-scraper/backend/

# Vérifier que le fichier scraper existe
ls -la /home/scraper/maps-scraper/backend/scraper_suisse_romande.py
```

### 6. Vérifier le Python du venv

```bash
# Vérifier que le venv existe
ls -la /home/scraper/maps-scraper/venv/bin/python

# Tester le Python
/home/scraper/maps-scraper/venv/bin/python --version
```

### 7. Vérifier les logs en temps réel

```bash
# Logs du service
sudo journalctl -u scraper-web -f

# Dans un autre terminal, lancer le scraper depuis l'interface web
# Tu verras les erreurs en direct
```

## 🐛 Erreurs courantes

### Erreur : "No such file or directory"

**Cause** : Le fichier `scraper_suisse_romande.py` n'existe pas ou le chemin est incorrect.

**Solution** :
```bash
# Vérifier que le fichier existe
ls -la /home/scraper/maps-scraper/backend/scraper_suisse_romande.py

# Si absent, copier depuis le repo
cd ~/maps-scraper
sudo cp backend/scraper_suisse_romande.py /home/scraper/maps-scraper/backend/
sudo chown scraper:scraper /home/scraper/maps-scraper/backend/scraper_suisse_romande.py
```

### Erreur : "ModuleNotFoundError"

**Cause** : Les dépendances ne sont pas installées dans le venv.

**Solution** :
```bash
sudo su - scraper
cd /home/scraper/maps-scraper
source venv/bin/activate
pip install -r requirements.txt
```

### Erreur : "Permission denied"

**Cause** : L'utilisateur `scraper` n'a pas les permissions.

**Solution** :
```bash
sudo chown -R scraper:scraper /home/scraper/maps-scraper
```

## 🔧 Commandes de diagnostic rapide

```bash
# Tout vérifier d'un coup
echo "=== Service ===" && \
sudo systemctl status scraper-web --no-pager -l && \
echo -e "\n=== Processus scraper ===" && \
ps aux | grep scraper_suisse_romande && \
echo -e "\n=== Fichier scraper ===" && \
ls -la /home/scraper/maps-scraper/backend/scraper_suisse_romande.py && \
echo -e "\n=== Python venv ===" && \
ls -la /home/scraper/maps-scraper/venv/bin/python && \
echo -e "\n=== Derniers logs ===" && \
sudo journalctl -u scraper-web -n 20 --no-pager
```

## 📝 Après diagnostic

Une fois que tu as identifié l'erreur, partage-la et je t'aiderai à la corriger !


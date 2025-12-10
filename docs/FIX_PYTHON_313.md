# 🔧 Problème Python 3.13 et Pandas

## ⚠️ Le problème

Tu as Python 3.13 sur ton VPS, mais **Pandas 2.1.3 n'est pas compatible avec Python 3.13**.

L'erreur :
```
error: too few arguments to function '_PyLong_AsByteArray'
```

Cela signifie que Pandas 2.1.3 essaie de compiler avec Python 3.13, mais l'API C de Python a changé.

## ✅ Solutions (choisir une)

### Solution 1 : Installer Python 3.11 (recommandé)

Le script `install.sh` a été modifié pour détecter Python 3.13 et installer Python 3.11 automatiquement.

**Sur le VPS, relance simplement :**

```bash
cd ~/maps-scraper
sudo ./scripts/install.sh
```

Le script va maintenant :
1. Détecter Python 3.13
2. Installer Python 3.11 depuis le PPA deadsnakes
3. Créer le venv avec Python 3.11
4. Installer toutes les dépendances

### Solution 2 : Mettre à jour Pandas manuellement

Si tu veux garder Python 3.13, utilise Pandas 2.2.0+ qui est compatible :

```bash
cd ~/maps-scraper

# Pousser les modifications
git pull origin main  # (après avoir poussé le nouveau requirements.txt)

# Supprimer le venv existant (s'il existe)
sudo rm -rf /home/scraper/maps-scraper/venv

# Relancer l'installation
sudo ./scripts/install.sh
```

### Solution 3 : Installation manuelle avec Python 3.11

```bash
# Installer Python 3.11
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Aller dans le répertoire de l'app
cd /home/scraper/maps-scraper

# Supprimer le venv existant
sudo rm -rf venv

# Créer un nouveau venv avec Python 3.11
sudo -u scraper python3.11 -m venv venv

# Activer le venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
pip install flask flask-httpauth gunicorn

# Installer Playwright
playwright install firefox
playwright install-deps firefox
```

## 🔍 Vérifier la version de Python

```bash
# Version Python système
python3 --version

# Version Python du venv
source /home/scraper/maps-scraper/venv/bin/activate
python --version
```

## 📝 Pourquoi ce problème ?

- **Python 3.13** est sorti en octobre 2024
- **Pandas 2.1.3** utilise Cython 0.29.37 (ancienne version)
- L'API C de Python 3.13 a changé (`_PyLong_AsByteArray` a un nouveau paramètre)
- **Pandas 2.2.0+** ou **Python 3.11** résolvent le problème

## 🚀 Après la correction

Une fois Python 3.11 installé et le venv recréé, l'installation devrait se terminer sans erreur :

```
✅ Environnement virtuel créé dans /home/scraper/maps-scraper/venv avec python3.11
📦 Installation des dépendances Python...
✅ Toutes les dépendances installées
```

---

**Le script install.sh a été mis à jour pour gérer automatiquement ce problème ! 🎉**


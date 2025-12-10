# 🔧 Ubuntu 25.04 (Plucky) - Python 3.13

## ⚠️ Le problème

Tu as **Ubuntu 25.04 "plucky"** qui est trop récent pour le PPA deadsnakes.

Erreur :
```
E: The repository 'https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu plucky Release' does not have a Release file.
```

Le PPA deadsnakes ne supporte que :
- Ubuntu 22.04 (jammy)
- Ubuntu 24.04 (noble)

## ✅ Solution : Utiliser Python 3.13 avec Pandas 2.2+

Bonne nouvelle : **j'ai mis à jour `requirements.txt`** pour utiliser Pandas 2.2.0+, qui est **compatible avec Python 3.13**.

### Étapes sur ton VPS

```bash
cd ~/maps-scraper

# Récupérer la dernière version (avec requirements.txt mis à jour)
git pull origin main

# Relancer l'installation
sudo ./scripts/install.sh
```

Le script va maintenant :
1. Détecter Python 3.13 ✅
2. Détecter Ubuntu plucky ✅
3. **Utiliser Python 3.13 directement** (au lieu d'essayer d'installer Python 3.11)
4. Installer Pandas 2.2+ qui est compatible avec Python 3.13 ✅

## 🎯 Pourquoi ça marche maintenant ?

Avant :
- `requirements.txt` : `pandas==2.1.3` ❌ (incompatible Python 3.13)

Après :
- `requirements.txt` : `pandas>=2.2.0` ✅ (compatible Python 3.13)

Pandas 2.2.0 a été mis à jour pour supporter Python 3.13.

## 📝 Vérification après installation

```bash
# Vérifier Python
source /home/scraper/maps-scraper/venv/bin/activate
python --version
# Devrait afficher : Python 3.13.x

# Vérifier Pandas
python -c "import pandas; print(pandas.__version__)"
# Devrait afficher : 2.2.x ou plus récent
```

## 🚀 Alternative : Installer Python 3.11 manuellement (optionnel)

Si tu veux vraiment Python 3.11, tu peux l'installer depuis les sources :

```bash
# Installer les dépendances de compilation
sudo apt-get update
sudo apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev

# Télécharger et compiler Python 3.11
cd /tmp
wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz
tar -xf Python-3.11.8.tgz
cd Python-3.11.8
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall

# Vérifier
python3.11 --version
```

Mais **ce n'est pas nécessaire** ! Python 3.13 + Pandas 2.2+ fonctionne parfaitement.

---

**TL;DR : Lance `git pull && sudo ./scripts/install.sh` et tout fonctionnera avec Python 3.13 ! 🎉**


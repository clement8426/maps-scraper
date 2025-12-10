# 🐍 Python 3.13 - Compatibilité des packages

## ⚠️ Problèmes avec Python 3.13

Python 3.13 a changé l'API C interne, ce qui casse certains packages anciens :

### Packages incompatibles (anciennes versions)

- ❌ `pandas==2.1.3` → erreur `_PyLong_AsByteArray`
- ❌ `lxml==4.9.3` → erreur `_PyInterpreterState_GetConfig`, `_PyDict_SetItem_KnownHash`

### Packages compatibles (versions mises à jour)

- ✅ `pandas>=2.2.0` → Compatible Python 3.13
- ✅ `lxml>=5.0.0` → Compatible Python 3.13

## 📝 Modifications apportées

### requirements.txt (avant)

```txt
pandas==2.1.3
lxml==4.9.3
```

### requirements.txt (après)

```txt
pandas>=2.2.0  # Compatible Python 3.13
lxml>=5.0.0    # Compatible Python 3.13 (4.9.3 ne l'est pas)
```

## 🔍 Erreurs typiques avec Python 3.13

### Pandas 2.1.3 + Python 3.13

```
error: too few arguments to function '_PyLong_AsByteArray'
```

**Fix** : `pandas>=2.2.0`

### lxml 4.9.3 + Python 3.13

```
error: implicit declaration of function '_PyInterpreterState_GetConfig'
error: implicit declaration of function '_PyDict_SetItem_KnownHash'
error: too few arguments to function '_PyLong_AsByteArray'
```

**Fix** : `lxml>=5.0.0`

## ✅ Dépendances système nécessaires

Même avec les bonnes versions, il faut les dépendances de compilation :

```bash
sudo apt-get install -y \
    pkg-config \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev
```

Ces dépendances sont déjà incluses dans `scripts/install.sh`.

## 🚀 Versions recommandées (Python 3.13)

```txt
playwright==1.40.0
beautifulsoup4==4.12.2
pandas>=2.2.0
requests==2.31.0
dnspython==2.4.2
email-validator==2.1.0
lxml>=5.0.0
flask==3.0.0
flask-httpauth==4.8.0
gunicorn==21.2.0
```

## 📊 Tableau de compatibilité

| Package | Version ancienne | Python 3.13 | Version compatible | Status |
|---------|------------------|-------------|-------------------|--------|
| pandas | 2.1.3 | ❌ | >=2.2.0 | ✅ |
| lxml | 4.9.3 | ❌ | >=5.0.0 | ✅ |
| playwright | 1.40.0 | ✅ | - | ✅ |
| beautifulsoup4 | 4.12.2 | ✅ | - | ✅ |
| flask | 3.0.0 | ✅ | - | ✅ |

## 🎯 Conclusion

Pour utiliser Python 3.13 sur Ubuntu 25.04, il suffit de :

1. ✅ Utiliser `pandas>=2.2.0` au lieu de `2.1.3`
2. ✅ Utiliser `lxml>=5.0.0` au lieu de `4.9.3`
3. ✅ Installer les dépendances système (déjà dans `install.sh`)

**Le script `install.sh` est maintenant compatible Python 3.13 ! 🎉**


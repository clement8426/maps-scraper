# 📍 Où cloner le projet sur le VPS ?

## 🎯 Réponse courte

**Tu peux cloner le projet n'importe où !** Le script `install.sh` va automatiquement :
1. Créer l'utilisateur `scraper` (s'il n'existe pas)
2. Copier tous les fichiers vers `/home/scraper/maps-scraper`
3. Installer tout là-bas

## 📂 Structure Linux standard

```
/
├── home/          ← Répertoire pour les utilisateurs
│   ├── ubuntu/    ← Ton utilisateur actuel
│   └── scraper/   ← Utilisateur créé par install.sh
│       └── maps-scraper/  ← Où l'app sera installée
├── root/          ← Utilisateur root
├── tmp/           ← Fichiers temporaires
└── opt/           ← Logiciels optionnels
```

## ✅ Où cloner ? (tous fonctionnent)

### Option 1 : Dans ton répertoire home (recommandé)
```bash
cd ~
# ou
cd /home/ubuntu
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap
sudo ./scripts/install.sh
```

### Option 2 : Dans /tmp (temporaire)
```bash
cd /tmp
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap
sudo ./scripts/install.sh
```

### Option 3 : Dans /opt (logiciels)
```bash
cd /opt
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap
sudo ./scripts/install.sh
```

### Option 4 : Dans /root (si tu es root)
```bash
cd /root
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap
./scripts/install.sh  # Pas besoin de sudo si root
```

## 🔄 Ce que fait install.sh

Quand tu lances `sudo ./scripts/install.sh`, le script :

1. **Détecte où tu es** : `SCRIPT_DIR=$(pwd)`
2. **Définit où installer** : `APP_DIR="/home/scraper/maps-scraper"`
3. **Si différent** : Copie tout vers `/home/scraper/maps-scraper`
4. **Crée le venv** : Dans `/home/scraper/maps-scraper/venv`
5. **Installe tout** : Dans `/home/scraper/maps-scraper`

## 🎯 Pourquoi `/home/scraper/maps-scraper` ?

- **Sécurité** : Utilisateur dédié `scraper` (pas root, pas ubuntu)
- **Isolation** : L'app ne pollue pas ton compte ubuntu
- **Standard** : Convention Linux pour les applications utilisateur
- **Permissions** : Facile à gérer les permissions

## 📝 Exemple complet

```bash
# 1. Connexion au VPS
ssh ubuntu@VOTRE_IP

# 2. Cloner (n'importe où)
cd ~
git clone https://github.com/VOTRE_USERNAME/maps-scrap.git
cd maps-scrap

# 3. Lancer l'installation
sudo ./scripts/install.sh

# Le script va :
# - Créer /home/scraper/maps-scraper
# - Copier les fichiers là-bas
# - Créer le venv
# - Installer tout
# - Configurer Nginx, systemd, etc.

# 4. Après l'installation, l'app est dans :
# /home/scraper/maps-scraper/
```

## 🔍 Vérifier après installation

```bash
# Voir où l'app est installée
ls -la /home/scraper/maps-scraper/

# Voir le venv
ls -la /home/scraper/maps-scraper/venv/

# Voir le service systemd
sudo systemctl status scraper-web
```

## ❓ FAQ

**Q : Je dois supprimer le repo cloné après installation ?**  
R : Non, tu peux le garder ou le supprimer. L'app tourne depuis `/home/scraper/maps-scraper/`.

**Q : Je peux installer ailleurs que `/home/scraper/maps-scraper` ?**  
R : Oui, mais il faut modifier le script `install.sh` (ligne 67 : `APP_DIR=...`).

**Q : Pourquoi pas dans `/home/ubuntu/maps-scraper` ?**  
R : C'est possible, mais moins sécurisé. L'utilisateur dédié `scraper` isole l'application.

---

**En résumé : Clone où tu veux, le script s'occupe du reste ! 🚀**


# Résolution des problèmes OSINT Enricher

## Problème : "No such file or directory" pour tous les outils

### Cause
Les outils OSINT (curl, whatweb, theHarvester, etc.) ne sont pas installés ou pas dans le PATH du service systemd.

### Solution

#### 1. Vérifier les outils installés

```bash
cd ~/maps-scraper/osint-enricher
bash scripts/check_tools.sh
```

Si des outils sont manquants (❌), vous devez les installer ou corriger le PATH.

#### 2. Réinstaller les outils et corriger le service

```bash
cd ~/maps-scraper
git pull
cd osint-enricher
sudo ./scripts/install_enricher.sh
```

Ce script va :
- Installer les dépendances système (curl, whatweb, whois, etc.)
- Installer theHarvester via pip
- Installer subfinder et amass via Go
- Corriger le PATH dans le service systemd

#### 3. Vérifier que le service démarre correctement

```bash
sudo systemctl status osint-enricher
```

Si le service est actif mais que les outils ne fonctionnent toujours pas, vérifier le PATH :

```bash
systemctl show osint-enricher -p Environment
```

Le PATH doit contenir :
- `/usr/local/bin`
- `/usr/bin`
- `/bin`
- `/home/ubuntu/go/bin` (pour subfinder/amass)

#### 4. Tester manuellement un outil

```bash
# En tant qu'utilisateur ubuntu
su - ubuntu
which curl
which whatweb
which theHarvester
```

Si `which` trouve l'outil mais le service ne peut pas l'utiliser, c'est un problème de PATH systemd.

#### 5. Redémarrer le service après correction

```bash
sudo systemctl daemon-reload
sudo systemctl restart osint-enricher
```

#### 6. Consulter les logs

Les nouveaux logs indiqueront quels outils sont disponibles :

```bash
sudo journalctl -u osint-enricher -f
```

Vous devriez voir au démarrage du pipeline :

```
Outils disponibles: curl, whatweb, whois
⚠️  Outils manquants: theHarvester, subfinder, amass
```

---

## Outils optionnels vs. essentiels

### Essentiels (gratuits et faciles à installer)
- `curl` - Appels HTTP (apt)
- `whatweb` - Identification de technologies (apt)
- `whois` - Informations domaine (apt)

### Optionnels (plus complexes)
- `theHarvester` - Collecte emails (pip)
- `subfinder` - Énumération sous-domaines (Go)
- `amass` - Énumération avancée (Go)

Le pipeline fonctionne même si certains outils optionnels sont absents. Il marquera simplement les données comme `NULL` au lieu de faire échouer l'enrichissement.

---

## Installation manuelle des outils Go

Si subfinder/amass ne s'installent pas via le script :

```bash
# Installer Go si nécessaire
sudo apt install golang-go

# Configurer GOPATH
export GOPATH=/home/ubuntu/go
export PATH=$PATH:$GOPATH/bin

# Installer subfinder
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Installer amass
go install -v github.com/owasp-amass/amass/v4/...@master

# Lien symbolique pour accès système
sudo ln -sf /home/ubuntu/go/bin/subfinder /usr/local/bin/subfinder
sudo ln -sf /home/ubuntu/go/bin/amass /usr/local/bin/amass
```

Ensuite, redémarrer le service.


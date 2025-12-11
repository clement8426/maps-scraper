# 🔄 Mettre à jour le projet sur le VPS

## Processus de mise à jour

### 1. Sur votre machine locale (push vers GitHub)
```bash
cd /Users/soleadmaci9/test/maps-scrap  # ou votre chemin local
git add .
git commit -m "Amélioration: réduction des arrêts du scraper"
git push origin main  # ou master selon votre branche
```

### 2. Sur le VPS (pull et redémarrage)

Connectez-vous en SSH :
```bash
ssh ubuntu@vps-7da9f2a0.vps.ovh.net  # ou votre IP/domaine
```

Puis exécutez :
```bash
cd ~/maps-scraper
git pull origin main  # ou master

# Si de nouvelles dépendances ont été ajoutées
source venv/bin/activate
pip install -r requirements.txt

# Si vous voyez un warning "unit file changed", recharger systemd d'abord
sudo systemctl daemon-reload

# Redémarrer le service pour prendre en compte les changements
sudo systemctl restart scraper-web

# Vérifier que tout fonctionne
sudo systemctl status scraper-web
```

## Commandes utiles

### Voir les logs en temps réel
```bash
sudo journalctl -u scraper-web -f
```

### Voir les logs du scraper (activité scraping)
```bash
tail -f ~/maps-scraper/backend/scraper.log
```

### Redémarrer le service
```bash
sudo systemctl restart scraper-web
```

### Arrêter le service
```bash
sudo systemctl stop scraper-web
```

### Démarrer le service
```bash
sudo systemctl start scraper-web
```

### Vérifier le statut
```bash
sudo systemctl status scraper-web
```

## ⚠️ Si le scraper est en cours d'exécution

Si le scraper est en train de scraper, **ne le redémarrez pas** ! Attendez qu'il termine ou arrêtez-le d'abord via l'interface web.

Pour vérifier si le scraper est en cours :
```bash
ps aux | grep scraper_suisse_romande.py
```

Si vous voyez un processus, le scraper est actif.

## 🔄 Workflow complet recommandé

1. **Développement local** : Testez vos modifications
2. **Commit et push** : `git add . && git commit -m "..." && git push`
3. **SSH sur le VPS** : `ssh ubuntu@vps-7da9f2a0.vps.ovh.net`
4. **Pull** : `cd ~/maps-scraper && git pull`
5. **Mise à jour dépendances** (si nécessaire) : `source venv/bin/activate && pip install -r requirements.txt`
6. **Recharger systemd** (si warning) : `sudo systemctl daemon-reload`
7. **Redémarrage** : `sudo systemctl restart scraper-web`
8. **Vérification** : `sudo systemctl status scraper-web`

## 📝 Note importante

Le service `scraper-web` gère :
- Le backend Flask (interface web)
- Le scraper (lancé via l'interface web)

Quand vous redémarrez le service, seul le backend Flask redémarre. Le scraper doit être relancé via l'interface web si nécessaire.


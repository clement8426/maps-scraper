# 🔐 Changer le mot de passe admin

## Méthode 1 : Via le fichier .env (Recommandé)

1. **Connectez-vous au VPS** :
   ```bash
   ssh ubuntu@votre-vps-ip
   ```

2. **Éditez le fichier `.env`** :
   ```bash
   cd ~/maps-scraper
   nano .env
   ```

3. **Modifiez la ligne `WEB_PASSWORD`** :
   ```env
   WEB_USERNAME=admin
   WEB_PASSWORD=VotreNouveauMotDePasse123!
   PORT=5000
   DEBUG=False
   ```

4. **Sauvegardez** (Ctrl+O, Enter, Ctrl+X dans nano)

5. **Redémarrez le service** :
   ```bash
   sudo systemctl restart scraper-web
   ```

6. **Vérifiez que ça fonctionne** :
   ```bash
   sudo systemctl status scraper-web
   ```

## Méthode 2 : Via le script Python (local)

1. **Sur votre machine locale**, générez un hash :
   ```bash
   cd /Users/soleadmaci9/test/maps-scrap
   python3 scripts/change_password.py MonNouveauMotDePasse123!
   ```

2. **Copiez le hash généré** et utilisez-le dans le fichier `.env` (méthode 1)

## 🔒 Bonnes pratiques

- ✅ Utilisez un mot de passe fort (minimum 12 caractères)
- ✅ Mélangez majuscules, minuscules, chiffres et symboles
- ✅ Ne partagez jamais votre mot de passe
- ✅ Changez-le régulièrement
- ✅ Utilisez un gestionnaire de mots de passe (1Password, Bitwarden, etc.)

## ⚠️ Si vous avez oublié le mot de passe

Si vous avez perdu l'accès, vous pouvez :

1. **Arrêter le service** :
   ```bash
   sudo systemctl stop scraper-web
   ```

2. **Modifier directement le fichier `.env`** :
   ```bash
   nano ~/maps-scraper/.env
   ```

3. **Redémarrer le service** :
   ```bash
   sudo systemctl start scraper-web
   ```

## 🛡️ Sécurité supplémentaire

Pour renforcer la sécurité, vous pouvez aussi :

1. **Changer le nom d'utilisateur** dans `.env` :
   ```env
   WEB_USERNAME=mon_nom_utilisateur_unique
   ```

2. **Utiliser un mot de passe très long** (20+ caractères)

3. **Restreindre l'accès IP** via Nginx (voir `docs/INSTALL.md`)


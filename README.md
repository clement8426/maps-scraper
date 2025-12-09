# 🚀 Scraper Google Maps - Suisse Romande (Mode Guérilla)

Pipeline d'extraction et d'enrichissement de données d'entreprises tech en Suisse Romande **sans API payante**.

## ⚠️ Avertissements Importants

**Ce script est fourni à des fins éducatives et de recherche uniquement.**

- ⚠️ **Respectez les conditions d'utilisation de Google Maps**
- ⚠️ **Respectez le `robots.txt` des sites web visités**
- ⚠️ **Ne surchargez pas les serveurs** (délais intégrés)
- ⚠️ **Vérifiez la légalité** de l'utilisation dans votre juridiction
- ⚠️ **Les emails récupérés** doivent respecter le RGPD et les lois anti-spam

## 📋 Prérequis

- Python 3.8+
- Navigateur Chromium (installé via Playwright)

## 🛠️ Installation

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Installer les navigateurs Playwright (Firefox recommandé)
playwright install firefox
# OU pour Chromium
playwright install chromium

# Tester que Playwright fonctionne
python test_playwright.py

# Tester avec Google Maps (Firefox recommandé)
python test_firefox.py
```

**⚠️ Note importante :**
- **Firefox est recommandé** car il semble mieux fonctionner avec Google Maps
- Le script utilise Firefox par défaut (configurable dans `scraper_suisse_romande.py`)
- Google Maps peut rediriger vers une page de consentement - le script la gère automatiquement

## 🎯 Architecture

Le système se compose de 3 phases :

1. **Harvester (Moissonneur)** : Parcourt Google Maps par secteurs géographiques
2. **Enricher (Enrichisseur)** : Récupère les sites web depuis les fiches Maps
3. **Miner (Mineur)** : Visite les sites web pour extraire emails et liens sociaux

## 🚀 Utilisation

### Étape 1 : Lancer le scraper principal

```bash
python scraper_suisse_romande.py
```

**Fonctionnalités :**
- ✅ Sauvegarde incrémentale (peut être interrompu et relancé)
- ✅ Gestion des sites React/SPA avec Playwright
- ✅ Délais aléatoires pour simuler un comportement humain
- ✅ Rotation des User-Agents
- ✅ Gestion des erreurs et timeouts

**Fichiers générés :**
- `base_tech_suisse.csv` : Résultat final
- `intermediate_data.csv` : Sauvegarde intermédiaire (supprimé à la fin)
- `checkpoint.json` : Checkpoint pour reprendre (supprimé à la fin)

### Étape 2 : Vérifier les emails (Optionnel mais recommandé)

Avant d'envoyer des emails marketing, vérifiez que les domaines sont valides :

```bash
python verify_emails.py base_tech_suisse.csv
```

Cela ajoute une colonne `Email_Valid` au CSV.

### Étape 3 : Nettoyer et enrichir les données

```bash
python clean_and_deduce_emails.py base_tech_suisse.csv
```

**Fonctionnalités :**
- Nettoie les URLs et extrait les domaines
- Identifie les emails génériques (info@, contact@, etc.)
- Déduit des emails possibles à partir des noms d'entreprises
- Filtre les lignes incomplètes

## 📊 Structure des Données

Le CSV final contient :

| Colonne | Description |
|---------|-------------|
| `Company` | Nom de l'entreprise |
| `Maps_Link` | Lien vers la fiche Google Maps |
| `City` | Ville |
| `Tag` | Mot-clé de recherche utilisé |
| `Website` | Site web de l'entreprise |
| `Email` | Emails trouvés (peut être multiple, séparés par virgule) |
| `Social_Links` | Liens vers réseaux sociaux |
| `Status` | Statut du scraping |

## ⚙️ Configuration

Modifiez les constantes dans `scraper_suisse_romande.py` :

```python
CITIES = ["Genève", "Lausanne", ...]  # Villes à scraper
KEYWORDS = ["Agence Web", ...]         # Mots-clés de recherche
MIN_DELAY = 1.5                        # Délai minimum entre actions
MAX_DELAY = 4.0                        # Délai maximum entre actions
```

## 🛡️ Protection Anti-Ban

Le script inclut plusieurs mécanismes pour éviter les blocages :

- ✅ Délais aléatoires entre chaque action
- ✅ Rotation des User-Agents
- ✅ Simulation d'un comportement humain (scroll, pauses)
- ✅ Gestion des cookies Google
- ✅ Timeouts adaptatifs

**Si vous êtes bloqué :**
- Augmentez les délais (`MIN_DELAY`, `MAX_DELAY`)
- Utilisez un VPN ou changez d'IP
- Réduisez le nombre de villes/mots-clés par session

## 🐛 Dépannage

### Le navigateur plante (SEGV_MAPERR, segmentation fault)

- Problème connu avec certaines versions de Playwright/Chromium sur macOS
- **Solutions** :
  1. Le script utilise Firefox par défaut maintenant (meilleure compatibilité)
  2. Le script utilise `headless=True` par défaut (évite les problèmes d'affichage)
  3. Si vous voulez utiliser Chromium : modifiez `BROWSER_TYPE = "chromium"` dans le script
  4. Réinstallez Playwright si nécessaire : `playwright install firefox --force`

### Page de consentement Google

- Google Maps peut rediriger vers `consent.google.com`
- **Solution** : Le script gère automatiquement cette page en acceptant les cookies/conditions
- Si le problème persiste, essayez de visiter Google Maps manuellement dans un navigateur pour accepter les conditions une fois

### Le script plante après quelques résultats

- Google a peut-être détecté le bot
- **Solution** : Augmentez les délais (`MIN_DELAY`, `MAX_DELAY`), réduisez le nombre de recherches par session

### Pas d'emails trouvés sur les sites

- Certains sites sont en React/Vue.js et nécessitent JavaScript
- **Solution** : Le script utilise déjà Playwright pour gérer cela, mais certains sites peuvent avoir des protections anti-bot

### Erreur "Timeout" fréquente

- Connexion lente ou site bloquant
- **Solution** : Augmentez les timeouts dans le code ou vérifiez votre connexion

### Erreur "Target page, context or browser has been closed"

- Le navigateur a planté ou a été fermé
- **Solution** : Le script sauvegarde automatiquement les données récupérées. Relancez-le, il reprendra où il s'est arrêté grâce aux checkpoints

## 📝 Notes Importantes

1. **Emails génériques** : La plupart des emails trouvés seront génériques (`info@`, `contact@`). Pour des emails personnels, il faudra :
   - Rechercher manuellement sur LinkedIn
   - Utiliser des outils de déduction d'email (comme le script `clean_and_deduce_emails.py`)

2. **Faux positifs** : Certains résultats peuvent ne pas être des entreprises tech (ex: boutiques de réparation). Un tri manuel peut être nécessaire.

3. **Limites Google Maps** : Google Maps limite à ~120 résultats par recherche. Le script utilise le scroll infini pour maximiser les résultats.

## 🔒 Sécurité et Conformité

- ✅ Vérifiez toujours les emails avec `verify_emails.py` avant envoi
- ✅ Respectez le RGPD pour les emails marketing
- ✅ Utilisez un service d'email transactionnel avec bonne réputation
- ✅ Ne spammez pas : limitez le nombre d'emails par jour

## 📄 Licence

Ce code est fourni "tel quel" sans garantie. Utilisez-le à vos propres risques.

## 🤝 Contribution

Améliorations suggérées :
- Gestion des CAPTCHAs
- Support de proxies rotatifs
- Export vers d'autres formats (JSON, SQLite)
- Interface web pour monitoring

# maps-scraper

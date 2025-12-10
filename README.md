# 🚀 Scraper Google Maps - Suisse Romande (Mode Guérilla)

Scraper automatisé pour extraire et enrichir les données d'entreprises tech depuis Google Maps, avec focus sur le **canton de Neuchâtel** et la Suisse Romande.

## 🎯 Fonctionnalités

### Phase 1: Harvesting (Récolte)
- Recherche automatisée sur Google Maps
- Extraction des noms et liens Maps
- Gestion automatique des cookies

### Phase 2: Enrichissement
- **Adresse complète**
- **Téléphone**
- **Site web**
- **Note Google** (étoiles)
- **Nombre d'avis**

### Phase 3: Mining (Fouille)
- **Extraction d'emails** depuis les sites web
- **Validation DNS** des emails (suppression des emails fictifs)
- **Liens réseaux sociaux** (LinkedIn, Facebook, Twitter, Instagram)

### Bonus
- **Base de données SQLite** (`companies.db`)
- **Sauvegarde incrémentale** (reprend après interruption)
- **Anti-détection** avancé (user-agents rotatifs, delays aléatoires)

## 📍 Zones géographiques couvertes

### Priorité: Canton de Neuchâtel
- Neuchâtel
- La Chaux-de-Fonds
- Le Locle
- Val-de-Ruz
- Val-de-Travers
- Fleurier
- Cernier
- Peseux
- Colombier
- Marin-Epagnier
- Saint-Blaise
- Boudry
- Cressier

### Villes proches (hors canton)
- Yverdon-les-Bains
- Pontarlier
- Morteau
- Besançon

### Autres villes Suisse Romande
- Genève, Lausanne, Fribourg, Sion, Nyon, Renens, Meyrin, Vevey, Montreux, Delémont, Porrentruy

## 🔍 Mots-clés recherchés

**40+ mots-clés** couvrant:
- Développement web & digital (Agence Web, Web design, UX Designer, etc.)
- Développement spécialisé (Full Stack, Frontend, Backend, Mobile app, E-commerce)
- Software & SaaS (Startup tech, SaaS company, Scale-up)
- Sécurité & infrastructure (Cybersécurité, Cloud provider, DevOps)
- Marketing digital (SEO, Marketing digital, Social media)
- Data & IA (Data science, Machine Learning, Big Data)

## 🛠️ Installation

### 1. Prérequis
```bash
Python 3.8+
```

### 2. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 3. Installation de Playwright
```bash
# Firefox (recommandé)
playwright install firefox

# Ou Chromium
playwright install chromium
```

## 🚀 Utilisation

### Lancement simple
```bash
python scraper_suisse_romande.py
```

Le script va :
1. Créer/ouvrir la base de données SQLite `companies.db`
2. Pour chaque combinaison ville × mot-clé :
   - Rechercher sur Google Maps
   - Enrichir les fiches (adresse, téléphone, site, note, avis)
   - Extraire les emails depuis les sites web
   - **Valider les emails** (DNS MX records)
   - Sauvegarder dans CSV + SQLite

### Reprise après interruption
Le script sauvegarde automatiquement sa progression dans `checkpoint.json`. En cas d'interruption (Ctrl+C, crash), relancez simplement :
```bash
python scraper_suisse_romande.py
```
Il reprendra là où il s'était arrêté.

### Repartir de zéro
```bash
rm checkpoint.json intermediate_data.csv companies.db
python scraper_suisse_romande.py
```

## 📂 Fichiers générés

- **`base_tech_suisse.csv`** : Fichier final avec toutes les données
- **`intermediate_data.csv`** : Données intermédiaires (sauvegarde automatique)
- **`companies.db`** : Base de données SQLite
- **`checkpoint.json`** : Point de reprise

## 🗄️ Base de données SQLite

La base `companies.db` contient une table `companies` avec tous les champs :
```sql
SELECT * FROM companies WHERE city = 'Neuchâtel' AND email IS NOT NULL;
```

Requête exemple pour exporter :
```bash
sqlite3 companies.db ".mode csv" ".output neuchatel_companies.csv" \
  "SELECT * FROM companies WHERE city = 'Neuchâtel' ORDER BY rating DESC;"
```

## ✅ Validation des emails

Le script **valide automatiquement** tous les emails extraits :
1. Format valide (regex)
2. Domaine valide
3. **DNS MX records** (vérification que le serveur mail existe)
4. Suppression des emails génériques/fictifs (noreply@, test@, etc.)

Seuls les emails **validés** sont sauvegardés.

## ⚙️ Configuration

Modifiez les constantes dans `scraper_suisse_romande.py` :

```python
# Navigateur : "firefox" (recommandé) ou "chromium"
BROWSER_TYPE = "firefox"

# Délais pour simuler un humain
MIN_DELAY = 1.5
MAX_DELAY = 4.0

# Ajouter/retirer des villes
CITIES = [...]

# Ajouter/retirer des mots-clés
KEYWORDS = [...]
```

## 🛡️ Anti-détection

- **11 User-Agents différents** (Chrome, Firefox, Safari, Edge)
- Rotation automatique à chaque recherche
- Délais aléatoires entre actions
- Navigation naturelle (Google.com → Google Maps)
- Gestion automatique des cookies
- Masquage des signaux d'automatisation

## ⚠️ Avertissements

1. **Légalité** : Ce script est à usage personnel/éducatif. Assurez-vous de respecter les CGU de Google et la législation sur la protection des données (RGPD, LPD suisse).
2. **Rate limiting** : Le script intègre des délais pour éviter le blocage, mais Google peut quand même bloquer en cas d'usage intensif.
3. **Données publiques** : Seules les données publiques accessibles sur Google Maps sont extraites.

## 📊 Statistiques

Avec la configuration actuelle :
- **25 villes** × **40 mots-clés** = **1000 recherches possibles**
- Environ **10-50 entreprises par recherche**
- Durée estimée : **8-12 heures** (avec tous les mots-clés et villes)

## 🐛 Dépannage

### Le navigateur crash
- Essayez Firefox au lieu de Chromium : `BROWSER_TYPE = "firefox"`
- Installez Firefox : `playwright install firefox`

### Timeout lors de l'enrichissement
- Certains sites sont lents ou bloquent les scrapers
- Les erreurs sont gérées automatiquement (le script continue)

### Aucun email trouvé
- Beaucoup de sites n'affichent pas d'emails
- Certains utilisent des formulaires de contact uniquement
- Les emails trouvés sont validés (DNS), donc certains sont rejetés

### Base de données corrompue
```bash
rm companies.db
python scraper_suisse_romande.py
```

## 📝 Licence

Ce projet est fourni à des fins éducatives. Utilisez-le de manière responsable.

## 🤝 Contribution

Pour ajouter des villes ou mots-clés, modifiez directement les listes `CITIES` et `KEYWORDS` dans le fichier principal.

---

**Bon scraping ! 🕷️**

# Les 11 Méthodes OSINT Complètes 🚀

*Date : 12 décembre 2025*

## 📋 Vue d'ensemble

Le pipeline d'enrichissement OSINT utilise maintenant **11 méthodes complètes** inspirées du script local de l'utilisateur, pour collecter le maximum d'informations sur chaque entreprise.

---

## ✅ Méthodes implémentées

### 1. **theHarvester** ✅
**Fonction :** Collecte d'emails via 4 sources fiables
- Sources : `bing`, `duckduckgo`, `yahoo`, `brave`
- Parsing JSON propre avec fallback texte
- Filtrage avancé (exclusion noreply, abuse@, etc.)
- **Résultat :** Emails du domaine

**Code :** `run_email_tools()`

---

### 2. **Web Scraping (About/Team/Contact)** ✅
**Fonction :** Scrape les pages web pour trouver emails et noms d'employés
- Pages testées : `/`, `/about`, `/about-us`, `/team`, `/contact`, `/staff`, `/employees`, `/people`, `/equipe`, `/a-propos`
- Extraction emails via regex
- Extraction noms depuis balises `h1-h4`, `strong`, `b`, et attributs `data-name`
- **Résultat :** Emails + noms d'employés

**Code :** `run_web_scraping()`

**Dépendances :** `requests`, `beautifulsoup4`

---

### 3. **Extraction PDF** ✅
**Fonction :** Télécharge et parse les PDFs trouvés sur le site
- Détection automatique des liens PDF sur la page principale
- Limite : 5 PDFs, 5 pages par PDF
- Extraction emails et noms depuis le texte des PDFs
- **Résultat :** Emails + noms d'employés depuis PDFs

**Code :** `run_pdf_extraction()`

**Dépendances :** `requests`, `beautifulsoup4`, `PyPDF2`

---

### 4. **Google Dorks** ✅
**Fonction :** Recherches Google ciblées pour trouver emails et employés
- Utilise Selenium/Firefox en mode headless (si disponible)
- Fallback sur `requests` si Selenium non disponible
- Dorks utilisés :
  - `site:domain "@domain"`
  - `site:domain "email" OR "contact"`
  - `"company_name" "@domain"`
- **Résultat :** Emails + noms d'employés depuis résultats Google

**Code :** `run_google_dorks()`

**Dépendances :** `selenium` (optionnel), `requests`, `beautifulsoup4`

---

### 5. **Subdomain Scraping manuel** ✅
**Fonction :** Teste les sous-domaines communs pour trouver des emails
- Sous-domaines testés : `www`, `mail`, `webmail`, `blog`, `news`, `newsletter`, `contact`, `about`, `team`, `careers`, `jobs`
- Scrape chaque sous-domaine pour extraire les emails
- **Résultat :** Emails trouvés sur les sous-domaines

**Code :** `run_subdomain_scraping()`

**Dépendances :** `requests`, `beautifulsoup4`

---

### 6. **Subfinder** ✅
**Fonction :** Découverte automatique de sous-domaines
- Utilise l'outil `subfinder` en ligne de commande
- Sources : toutes les sources passives disponibles
- Timeout : 180s
- **Résultat :** Liste de sous-domaines (jusqu'à 100)

**Code :** `run_subfinder()`

**Dépendances :** `subfinder` (outil système)

---

### 7. **Wayback Machine** ✅
**Fonction :** Archives historiques du site
- Interroge Internet Archive via API CDX
- Limite : 50 URLs, filtrées à 20 uniques
- Nettoyage : suppression trailing slashes, préférence HTTPS
- **Résultat :** URLs historiques archivées

**Code :** `run_wayback()`

**Dépendances :** `curl` (outil système)

---

### 8. **WHOIS Enhanced** ✅
**Fonction :** Extraction emails et noms depuis WHOIS
- Utilise l'outil `whois` en ligne de commande
- Extraction emails via regex
- Extraction noms depuis `Registrant Name`, `Admin Name`, `Tech Name`
- Filtrage : garde seulement les lignes importantes (registrar, dates, name servers, status, organization)
- **Résultat :** Emails + noms + données WHOIS brutes (30 lignes max)

**Code :** `run_whois_enhanced()`

**Dépendances :** `whois` (outil système)

---

### 9. **Réseaux sociaux** ✅
**Fonction :** Scrape les pages de réseaux sociaux mentionnées
- Support : LinkedIn, Facebook, Twitter/X
- Utilise les liens depuis la colonne `social_links` de la BDD
- Limite : 3 liens sociaux
- Extraction emails et noms depuis les métadonnées
- **Résultat :** Emails + noms d'employés depuis réseaux sociaux

**Code :** `run_social_media_scraping()`

**Dépendances :** `requests`, `beautifulsoup4`

---

### 10. **Commentaires HTML** ✅
**Fonction :** Extraction emails depuis commentaires HTML et attributs
- Parse les commentaires HTML (`<!-- ... -->`)
- Parse les attributs `data-*` et `aria-*`
- Extraction emails via regex
- **Résultat :** Emails trouvés dans le code source

**Code :** `run_html_comments()`

**Dépendances :** `requests`, `beautifulsoup4` (optionnel)

---

### 11. **GitHub Scraping** ✅
**Fonction :** Recherche dans les repositories GitHub
- Recherche par nom de domaine
- Parse les résultats de recherche
- Parse les README des repositories (limite : 3 repos)
- Extraction emails depuis le texte
- **Résultat :** Emails trouvés sur GitHub

**Code :** `run_github_scraping()`

**Dépendances :** `requests`, `beautifulsoup4`

---

### 12. **Robots.txt/Sitemap** ✅
**Fonction :** Parse robots.txt et sitemap pour trouver des pages cachées
- Parse `/robots.txt` pour trouver les sitemaps
- Limite : 2 sitemaps, 10 URLs par sitemap
- Scrape les pages contenant `about`, `team`, `contact`, `staff`
- Extraction emails depuis ces pages
- **Résultat :** Emails trouvés sur des pages cachées

**Code :** `run_robots_sitemap()`

**Dépendances :** `requests`, `beautifulsoup4`

---

## 📊 Colonnes BDD ajoutées

| Colonne | Type | Description |
|---------|------|-------------|
| `osint_employees` | TEXT | Noms d'employés trouvés (toutes sources) |
| `osint_html_comments` | TEXT | Emails depuis commentaires HTML |
| `osint_github_data` | TEXT | Données GitHub (emails) |
| `osint_social_data` | TEXT | Données réseaux sociaux (résumé) |

---

## 🔄 Fusion intelligente des données

### Emails
Tous les emails trouvés par les différentes méthodes sont **fusionnés automatiquement** dans `emails_osint` :
- theHarvester
- Web Scraping
- Extraction PDF
- Google Dorks
- Subdomain Scraping
- WHOIS Enhanced
- Réseaux sociaux
- Commentaires HTML
- GitHub Scraping
- Robots.txt/Sitemap

**Déduplication automatique** : les emails en double sont supprimés.

### Noms d'employés
Tous les noms trouvés sont collectés dans `osint_employees` :
- Web Scraping
- Extraction PDF
- Google Dorks
- WHOIS Enhanced
- Réseaux sociaux

---

## 📦 Dépendances Python

### Obligatoires
```bash
pip install requests beautifulsoup4 PyPDF2
```

### Optionnelles
```bash
pip install selenium  # Pour Google Dorks avec navigateur
```

### Outils système requis
- `curl` (pour Wayback Machine)
- `whatweb` (pour tech stack)
- `theHarvester` (pour emails)
- `subfinder` (pour sous-domaines)
- `whois` (pour infos domaine)

---

## 🚀 Déploiement sur le VPS

### 1. Installer les dépendances Python

```bash
cd ~/maps-scraper/osint-enricher
source venv/bin/activate  # Si vous utilisez un venv
pip install -r requirements.txt
```

### 2. Installer Selenium (optionnel, pour Google Dorks)

```bash
# Installer Firefox et geckodriver
sudo apt-get update
sudo apt-get install -y firefox-esr

# Télécharger geckodriver
wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz
tar -xzf geckodriver-v0.33.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/
sudo chmod +x /usr/local/bin/geckodriver
```

### 3. Mettre à jour le code

```bash
cd ~/maps-scraper
git pull
```

### 4. Redémarrer le service

```bash
sudo systemctl restart osint-enricher
```

### 5. Vérifier les logs

```bash
sudo journalctl -u osint-enricher -f
```

---

## 📈 Performance

### Temps d'exécution estimé par entreprise

| Méthode | Temps moyen |
|---------|-------------|
| WhatWeb | 2-5s |
| theHarvester | 30-60s (4 sources × 90s max) |
| Web Scraping | 10-20s (10 pages) |
| Extraction PDF | 15-30s (5 PDFs) |
| Google Dorks | 20-40s (3 dorks) |
| Subdomain Scraping | 10-15s (11 subdomains) |
| Subfinder | 15-30s |
| WHOIS | 2-5s |
| Wayback | 3-8s |
| Réseaux sociaux | 10-20s (3 liens) |
| Commentaires HTML | 2-5s |
| GitHub Scraping | 10-20s |
| Robots.txt/Sitemap | 10-20s |

**Total estimé :** 2-5 minutes par entreprise (selon les données disponibles)

---

## 🎯 Résultat attendu

### Exemple de logs

```
[2025-12-11 14:21:21] 🔄 Enrichissement #1/50
[2025-12-11 14:21:21] 📌 ID: 12345 | Entreprise: Example Corp
[2025-12-11 14:21:21] 🌐 Site: https://example.com
[2025-12-11 14:21:23]   ✅ WhatWeb: 5 tech(s)
[2025-12-11 14:21:53]   ✅ theHarvester: 3 email(s) valide(s) pour example.com
[2025-12-11 14:22:13]   ✅ Web Scraping: 2 email(s), 5 employé(s)
[2025-12-11 14:22:28]   ✅ Extraction PDF: 1 email(s), 2 employé(s)
[2025-12-11 14:22:48]   ✅ Google Dorks: 1 email(s), 0 employé(s)
[2025-12-11 14:22:58]   ✅ Subdomain Scraping: 1 email(s)
[2025-12-11 14:23:13]   ✅ Subfinder: 15 sous-domaine(s) unique(s)
[2025-12-11 14:23:15]   ✅ WHOIS Enhanced: 2 email(s), 1 nom(s)
[2025-12-11 14:23:18]   ✅ Wayback: 10 URLs uniques
[2025-12-11 14:23:28]   ✅ Réseaux sociaux: 0 email(s), 2 employé(s)
[2025-12-11 14:23:30]   ✅ Commentaires HTML: 1 email(s)
[2025-12-11 14:23:40]   ✅ GitHub Scraping: 0 email(s)
[2025-12-11 14:23:50]   ✅ Robots.txt/Sitemap: 0 email(s)
[2025-12-11 14:23:50] 💾 Sauvegarde en BDD...
[2025-12-11 14:23:50]    ✅ SAUVEGARDE RÉUSSIE pour ID 12345
[2025-12-11 14:23:50] ✅ ID 12345 - Example Corp terminé et sauvegardé en BDD
```

### Données sauvegardées

- **emails_osint** : `contact@example.com, info@example.com, admin@example.com, ...` (fusion de toutes les sources)
- **osint_employees** : `John Doe, Jane Smith, ...` (tous les noms trouvés)
- **osint_html_comments** : `hidden@example.com` (emails depuis commentaires)
- **osint_github_data** : `dev@example.com` (emails GitHub)
- **osint_social_data** : `Emails: 0, Employés: 2` (résumé réseaux sociaux)

---

## 🔧 Gestion des erreurs

### Dépendances manquantes

Si une dépendance est manquante, la méthode correspondante est **silencieusement ignorée** :
- `REQUESTS_AVAILABLE = False` → Web Scraping, PDF, etc. désactivés
- `BS4_AVAILABLE = False` → Parsing HTML désactivé
- `PDF_AVAILABLE = False` → Extraction PDF désactivée
- `SELENIUM_AVAILABLE = False` → Google Dorks utilise `requests` (moins efficace)

### Timeouts

Chaque méthode a un timeout approprié :
- Requêtes web : 10-15s
- theHarvester : 90s par source
- Subfinder : 180s global
- WHOIS : 30s

### Rate limiting

Des délais sont ajoutés entre les requêtes pour éviter le rate limiting :
- Entre pages web : 1s
- Entre sources theHarvester : 1s
- Entre Google Dorks : 5s
- Entre réseaux sociaux : 2s

---

## 📝 Notes techniques

### Fusion des emails

Les emails sont collectés dans des `set()` Python pour éviter les doublons, puis fusionnés dans une seule chaîne séparée par des virgules.

### Extraction de noms

Les noms sont détectés via regex : `^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$`
- 2-3 mots
- Première lettre en majuscule
- Longueur : 3-50 caractères

### Filtrage des emails

Exclusion automatique des emails génériques :
- `noreply`, `no-reply`, `donotreply`
- `abuse@`, `postmaster@`, `hostmaster@`, `webmaster@`
- Domaines de test : `example.com`, `test.com`, etc.

---

## 🎉 Résumé

**11 méthodes OSINT complètes** sont maintenant intégrées dans le pipeline d'enrichissement, permettant de collecter :
- ✅ **Emails** depuis 10 sources différentes
- ✅ **Noms d'employés** depuis 5 sources différentes
- ✅ **Sous-domaines** via 2 méthodes
- ✅ **Technologies web** via WhatWeb
- ✅ **Archives historiques** via Wayback Machine
- ✅ **Infos domaine** via WHOIS

**Résultat :** Enrichissement OSINT **complet et exhaustif** pour chaque entreprise ! 🚀


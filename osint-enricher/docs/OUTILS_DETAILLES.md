# 🛠️ Guide détaillé des outils OSINT

## Table des matières
1. [WhatWeb](#1-whatweb---détection-de-technologies-web)
2. [theHarvester](#2-theharvester---recherche-demails-et-dinformations)
3. [Subfinder](#3-subfinder---énumération-de-sous-domaines)
4. [Amass](#4-amass---mapping-de-réseau-avancé)
5. [WHOIS](#5-whois---informations-denregistrement-de-domaine)
6. [Wayback Machine (curl)](#6-wayback-machine---historique-de-sites-web)

---

## 1. WhatWeb - Détection de technologies web

### 🎯 Objectif
Identifier les technologies utilisées par un site web (CMS, serveurs, frameworks, plugins, etc.)

### 📖 Comment ça marche ?

WhatWeb analyse :
1. **Les en-têtes HTTP** du serveur
2. **Le code HTML** de la page
3. **Les cookies** envoyés
4. **Les fichiers JavaScript/CSS** chargés
5. **Les patterns spécifiques** à chaque technologie

### 🔧 Commande utilisée
```bash
whatweb example.com --log-verbose=- --no-errors
```

**Options :**
- `--log-verbose=-` : Affiche tous les détails sur la sortie standard
- `--no-errors` : N'affiche pas les erreurs de connexion

### 📊 Ce qui est détecté

#### Technologies CMS :
- **WordPress** : Détecté via `/wp-content/`, `/wp-includes/`, meta generator
- **Drupal** : Via `Drupal.settings`, fichiers spécifiques
- **Joomla** : Via `/components/`, `/modules/`
- **Shopify** : Via domaines `.myshopify.com`, scripts spécifiques

#### Plugins WordPress :
- **Yoast SEO** : Via `<!-- This site is optimized with the Yoast SEO plugin -->`
- **WooCommerce** : Via classes CSS `.woocommerce`, scripts
- **Elementor** : Via classes `.elementor-`, scripts

#### Serveurs web :
- **Apache** : Via en-tête `Server: Apache/2.4.41`
- **Nginx** : Via en-tête `Server: nginx/1.18.0`
- **LiteSpeed** : Via en-tête `Server: LiteSpeed`
- **IIS** : Via en-tête `Server: Microsoft-IIS/10.0`

#### Frameworks JavaScript :
- **React** : Via `react.development.js`, `__REACT_DEVTOOLS_GLOBAL_HOOK__`
- **Vue.js** : Via `Vue.config`, attributs `v-` dans le HTML
- **Angular** : Via `ng-version`, attributs `ng-`

#### Autres infos :
- **IP du serveur** : Résolution DNS
- **Pays d'hébergement** : Via base de données GeoIP
- **Certificat SSL** : Via handshake HTTPS
- **jQuery** : Via `jQuery.fn.jquery`, version détectée

### 💡 Exemple de sortie brute
```
http://example.com [200 OK] 
  Apache[2.4.41], 
  Country[FRANCE][FR], 
  HTML5, 
  HTTPServer[Ubuntu Linux][Apache/2.4.41 (Ubuntu)], 
  IP[51.77.165.6], 
  JQuery[3.6.0], 
  MetaGenerator[WordPress 6.2], 
  Script[text/javascript], 
  Title[Mon site], 
  UncommonHeaders[x-powered-by], 
  WordPress[6.2], 
  X-Powered-By[PHP/8.1.2]
```

### 🎨 Notre traitement
On extrait et structure :
```
WordPress | WP 6.2 | Server: Apache/2.4.41 | jQuery 3.6.0 | IP: 51.77.165.6 | Pays: FR
```

### ⏱️ Performance
- **Timeout** : 30 secondes
- **Vitesse** : ~2-5 secondes par domaine
- **Fiabilité** : ~95% de précision

---

## 2. theHarvester - Recherche d'emails et d'informations

### 🎯 Objectif
Collecter des emails, sous-domaines, noms, et IPs associés à un domaine via des sources publiques (moteurs de recherche, réseaux sociaux, etc.)

### 📖 Comment ça marche ?

theHarvester utilise des **scrapers** pour chaque source :

#### Sources utilisées avec `-b all` :

1. **Google** : 
   - Requêtes : `site:example.com email` ou `@example.com`
   - Parse les résultats HTML
   - Extrait les emails visibles

2. **Bing** :
   - Même principe que Google
   - API Bing Search si configurée

3. **LinkedIn** :
   - Recherche de profils d'employés
   - Extrait les emails au format `prenom.nom@example.com`

4. **Hunter.io** :
   - API de recherche d'emails
   - Base de données publique d'emails

5. **Shodan** :
   - Moteur de recherche pour appareils connectés
   - Trouve les serveurs du domaine

6. **Baidu** :
   - Moteur de recherche chinois
   - Utile pour domaines asiatiques

7. **DuckDuckGo** :
   - Moteur de recherche respectueux de la vie privée
   - Pas de limite de taux

8. **Yahoo** :
   - Ancien mais toujours utile
   - Résultats différents de Google/Bing

9. **Certspotter** :
   - Certificats SSL publics (Certificate Transparency)
   - Trouve les sous-domaines via les certificats

10. **Crtsh** :
    - Base de données de certificats SSL
    - Très efficace pour les sous-domaines

11. **DNSdumpster** :
    - Mapping DNS
    - Trouve sous-domaines et IPs

12. **Virustotal** :
    - Historique de scans de sécurité
    - Révèle sous-domaines et IPs

### 🔧 Commande utilisée
```bash
theHarvester -d example.com -b all -l 500
```

**Options :**
- `-d example.com` : Domaine cible
- `-b all` : Utilise toutes les sources disponibles
- `-l 500` : Limite de 500 résultats par source

### 📊 Ce qui est collecté

#### Emails :
```
contact@example.com
info@example.com
admin@example.com
john.doe@example.com
support@subdomain.example.com
```

#### Sous-domaines :
```
www.example.com
mail.example.com
api.example.com
staging.example.com
```

#### Noms de personnes :
```
John Doe (CEO)
Jane Smith (CTO)
```

#### IPs :
```
51.77.165.6
192.168.1.1
```

### 💡 Exemple de sortie brute
```
[*] Target: example.com

[*] Searching in Google:
	Searching 0 results.
	Searching 100 results.
	Searching 200 results.

[*] Emails found:
------------------
contact@example.com
info@example.com
admin@example.com

[*] Hosts found:
------------------
www.example.com:51.77.165.6
mail.example.com:51.77.165.7
api.example.com:51.77.165.8

[*] IPs found:
------------------
51.77.165.6
51.77.165.7
51.77.165.8
```

### 🎨 Notre traitement
On extrait avec regex :
```python
emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", result)
# Filtre pour ne garder que le domaine cible
domain_emails = [e for e in emails if "example.com" in e.lower()]
```

Résultat final :
```
contact@example.com, info@example.com, admin@example.com
```

### ⏱️ Performance
- **Timeout** : 5 minutes (300s)
- **Vitesse** : ~30-60 secondes par domaine (dépend des sources)
- **Fiabilité** : ~80% (certaines sources peuvent être bloquées)

### ⚠️ Limitations
- **Rate limiting** : Google/Bing peuvent bloquer après trop de requêtes
- **Captchas** : Certaines sources nécessitent une résolution manuelle
- **APIs** : Certaines sources nécessitent des clés API (Hunter.io, Shodan)

---

## 3. Subfinder - Énumération de sous-domaines

### 🎯 Objectif
Découvrir tous les sous-domaines d'un domaine principal (ex: `mail.example.com`, `api.example.com`)

### 📖 Comment ça marche ?

Subfinder interroge **plusieurs sources passives** (pas de brute-force DNS) :

#### Sources utilisées avec `-all` :

1. **Certificats SSL (Certificate Transparency)** :
   - **crt.sh** : Base de données publique de certificats
   - **Certspotter** : Monitoring de certificats
   - Quand un certificat SSL est émis, il est enregistré publiquement
   - Exemple : Certificat pour `*.example.com` révèle tous les sous-domaines

2. **Moteurs de recherche** :
   - **Google** : `site:example.com`
   - **Bing** : `domain:example.com`
   - **Yahoo** : Recherche de sous-domaines indexés

3. **Services DNS** :
   - **Shodan** : Scan de serveurs DNS
   - **DNSdumpster** : Mapping DNS complet
   - **SecurityTrails** : Historique DNS

4. **Répertoires web** :
   - **VirusTotal** : Sous-domaines détectés lors de scans
   - **ThreatCrowd** : Base de données de menaces
   - **AlienVault OTX** : Open Threat Exchange

5. **Archives** :
   - **Wayback Machine** : Historique de sous-domaines
   - **CommonCrawl** : Archive du web

6. **Autres sources** :
   - **GitHub** : Code source contenant des sous-domaines
   - **Pastebin** : Fuites de configuration
   - **RapidDNS** : Base DNS
   - **BufferOver** : Agrégateur DNS

### 🔧 Commande utilisée
```bash
subfinder -d example.com -silent -all -timeout 60
```

**Options :**
- `-d example.com` : Domaine cible
- `-silent` : N'affiche pas le banner (sortie propre)
- `-all` : Utilise toutes les sources disponibles
- `-timeout 60` : Timeout de 60s par source

### 📊 Ce qui est découvert

#### Sous-domaines fonctionnels :
```
www.example.com
mail.example.com
webmail.example.com
ftp.example.com
api.example.com
staging.example.com
dev.example.com
```

#### Sous-domaines d'infrastructure :
```
ns1.example.com (Name Server)
mx1.example.com (Mail Server)
vpn.example.com (VPN)
remote.example.com (Remote Access)
```

#### Sous-domaines de services :
```
shop.example.com
blog.example.com
support.example.com
status.example.com
```

### 💡 Exemple de sortie brute
```
www.example.com
mail.example.com
ftp.example.com
api.example.com
staging.example.com
old.example.com
test.example.com
dev.example.com
admin.example.com
```

### 🎨 Notre traitement
```python
subs = [line.strip() for line in result.splitlines() if line.strip()]
unique_subs = sorted(set(subs))  # Dédupliquer et trier
```

Résultat final (limité à 100) :
```
admin.example.com, api.example.com, dev.example.com, ftp.example.com, mail.example.com...
```

### ⏱️ Performance
- **Timeout** : 3 minutes (180s global)
- **Vitesse** : ~15-30 secondes par domaine
- **Fiabilité** : ~90% (sources passives très fiables)

### 🔍 Pourquoi c'est utile ?
Les sous-domaines révèlent :
- **Infrastructure technique** : serveurs mail, FTP, VPN
- **Environnements de développement** : staging, dev, test
- **Services oubliés** : anciens sous-domaines non sécurisés
- **Surface d'attaque** : plus de sous-domaines = plus de points d'entrée potentiels

---

## 4. Amass - Mapping de réseau avancé

### 🎯 Objectif
Découverte de sous-domaines **encore plus approfondie** que Subfinder, avec mapping de réseau

### 📖 Comment ça marche ?

Amass utilise **3 techniques** :

#### 1. Énumération passive (comme Subfinder) :
- Certificats SSL
- Moteurs de recherche
- APIs diverses
- Archives web

#### 2. Énumération active (requêtes DNS) :
- **Zone transfers** : Tente de récupérer toute la zone DNS
- **Résolution DNS** : Vérifie l'existence des sous-domaines trouvés
- **Reverse DNS** : Trouve les domaines associés à une IP

#### 3. Brute-force intelligent :
- **Wordlists** : Liste de sous-domaines communs
- **Permutations** : Génère des variations (api-dev, api-staging, etc.)
- **Altérations** : Teste des variantes

### 🔧 Commande utilisée
```bash
amass enum -d example.com -passive
```

**Options :**
- `enum` : Mode énumération
- `-d example.com` : Domaine cible
- `-passive` : Utilise uniquement les sources passives (pas de requêtes directes)

### 📊 Ce qui est découvert

Tout ce que Subfinder trouve, **plus** :

#### Sous-domaines profonds :
```
internal.api.example.com
v2.staging.dev.example.com
legacy.old.backup.example.com
```

#### Relations DNS :
```
example.com -> 51.77.165.6
mail.example.com -> 51.77.165.7
api.example.com -> CNAME -> aws-lb-123.elb.amazonaws.com
```

#### Infrastructure cloud :
```
example.s3.amazonaws.com
example.azurewebsites.net
example.herokuapp.com
```

### 💡 Exemple de sortie brute
```
[Certspotter] www.example.com
[Crtsh] mail.example.com
[DNSdumpster] api.example.com
[Google] blog.example.com
[VirusTotal] staging.example.com
[Active DNS] internal.example.com
```

### ⏱️ Performance
- **Timeout** : Variable (peut être très long)
- **Vitesse** : ~1-5 minutes par domaine
- **Fiabilité** : ~95% (le plus complet)

### ⚠️ Note
Amass est plus lent mais plus exhaustif que Subfinder. Dans notre pipeline, il est disponible mais optionnel.

---

## 5. WHOIS - Informations d'enregistrement de domaine

### 🎯 Objectif
Obtenir les informations publiques d'enregistrement d'un nom de domaine

### 📖 Comment ça marche ?

WHOIS est un **protocole de requête/réponse** (port 43) :

1. **Client** envoie une requête : `example.com`
2. **Serveur WHOIS** (du registrar) répond avec les informations publiques

#### Hiérarchie WHOIS :

```
IANA (Internet Assigned Numbers Authority)
  ↓
TLD Registry (.com, .fr, .org)
  ↓
Registrar (OVH, GoDaddy, Namecheap)
  ↓
Registrant (Propriétaire du domaine)
```

### 🔧 Commande utilisée
```bash
whois example.com
```

Pas d'options nécessaires, la commande est simple !

### 📊 Informations collectées

#### 1. **Registrar** (Bureau d'enregistrement) :
```
Registrar: OVH sas
Registrar URL: https://www.ovh.com
Registrar WHOIS Server: whois.ovh.com
```

#### 2. **Dates importantes** :
```
Creation Date: 2015-03-15T10:30:00Z
Registry Expiry Date: 2025-03-15T10:30:00Z
Updated Date: 2024-01-10T15:45:00Z
```
→ Permet de savoir :
- L'âge du domaine (crédibilité)
- Quand il expire (risque de perte)
- Dernière modification

#### 3. **Name Servers** (Serveurs DNS) :
```
Name Server: ns1.ovh.net
Name Server: dns1.ovh.net
```
→ Révèle l'hébergeur DNS

#### 4. **Status** (Statut du domaine) :
```
Domain Status: clientTransferProhibited
Domain Status: clientDeleteProhibited
Domain Status: clientUpdateProhibited
```
→ Protections activées (verrouillage)

#### 5. **Organisation** (si pas de protection WHOIS) :
```
Registrant Organization: ACME Corporation
Registrant State/Province: Paris
Registrant Country: FR
```

#### 6. **Contacts** (souvent masqués) :
```
Admin Email: admin@example.com
Tech Email: tech@example.com
```

### 💡 Exemple de sortie brute
```
Domain Name: EXAMPLE.COM
Registry Domain ID: 2138514_DOMAIN_COM-VRSN
Registrar WHOIS Server: whois.ovh.com
Registrar URL: http://www.ovh.com
Updated Date: 2024-01-10T15:45:32Z
Creation Date: 2015-03-15T10:30:15Z
Registry Expiry Date: 2025-03-15T10:30:15Z
Registrar: OVH sas
Registrar IANA ID: 433
Registrar Abuse Contact Email: abuse@ovh.net
Registrar Abuse Contact Phone: +33.972101007
Domain Status: clientDeleteProhibited https://icann.org/epp#clientDeleteProhibited
Domain Status: clientTransferProhibited https://icann.org/epp#clientTransferProhibited
Name Server: NS1.OVH.NET
Name Server: DNS1.OVH.NET
DNSSEC: unsigned
URL of the ICANN Whois Inaccuracy Complaint Form: https://www.icann.org/wicf/
```

### 🎨 Notre traitement
On extrait **uniquement les lignes importantes** :
```
Registrar: OVH sas
Creation Date: 2015-03-15T10:30:15Z
Registry Expiry Date: 2025-03-15T10:30:15Z
Updated Date: 2024-01-10T15:45:32Z
Name Server: NS1.OVH.NET
Name Server: DNS1.OVH.NET
Domain Status: clientDeleteProhibited
Domain Status: clientTransferProhibited
```

### ⏱️ Performance
- **Timeout** : 30 secondes
- **Vitesse** : ~2-5 secondes par domaine
- **Fiabilité** : ~100% (protocole standardisé)

### 🔍 Utilité pour l'OSINT

#### 1. **Identifier l'hébergeur** :
- Name Servers → OVH, Cloudflare, AWS ?
- Registrar → Où le domaine a été acheté

#### 2. **Évaluer la crédibilité** :
- Domaine récent (< 6 mois) = suspect
- Domaine ancien (> 5 ans) = établi

#### 3. **Trouver des connexions** :
- Même registrar que d'autres domaines suspects
- Même organisation = même propriétaire

#### 4. **Planifier un contact** :
- Date d'expiration proche = moment idéal pour racheter
- Emails de contact (admin, tech)

---

## 6. Wayback Machine - Historique de sites web

### 🎯 Objectif
Trouver les anciennes versions d'un site web et découvrir des URLs oubliées

### 📖 Comment ça marche ?

La **Wayback Machine** (Internet Archive) est un projet qui archive le web depuis 1996 :

1. **Crawlers** (robots) visitent les sites web régulièrement
2. **Snapshots** (captures) sont sauvegardées avec date/heure
3. **CDX Server** indexe toutes les URLs archivées

On interroge le **CDX API** :

```
https://web.archive.org/cdx/search
  ?url=example.com          # Domaine à rechercher
  &output=txt               # Format texte
  &fl=original              # Ne retourner que les URLs originales
  &filter=statuscode:200    # Seulement les pages réussies (200 OK)
  &limit=50                 # Limiter à 50 résultats
```

### 🔧 Commande utilisée
```bash
curl -s "https://web.archive.org/cdx/search?url=example.com&output=txt&fl=original&filter=statuscode:200&limit=50"
```

**Options curl :**
- `-s` : Silent (pas de barre de progression)

**Options CDX API :**
- `url=example.com` : Domaine cible
- `output=txt` : Format texte (1 URL par ligne)
- `fl=original` : Field List = URL originale uniquement
- `filter=statuscode:200` : Seulement les pages qui ont réussi
- `limit=50` : Maximum 50 URLs

### 📊 Ce qui est découvert

#### URLs publiques :
```
https://example.com
https://example.com/
https://example.com/about
https://example.com/contact
https://example.com/products
https://example.com/blog
```

#### URLs oubliées :
```
https://example.com/admin
https://example.com/old-admin
https://example.com/backup
https://example.com/test
https://example.com/.git/config
```

#### Anciennes pages :
```
https://example.com/promotion-2020
https://example.com/news/article-old
https://example.com/legacy/app
```

### 💡 Exemple de sortie brute
```
https://example.com
https://example.com/
https://example.com/index.html
https://example.com/about.html
https://example.com/contact.php
https://example.com/products/item1
https://example.com/products/item2
https://example.com/blog/post1
https://example.com/blog/post2
https://example.com/old-site/
https://example.com/admin/login
```

### 🎨 Notre traitement
On déduplique et nettoie :
```python
# Enlever trailing slash
normalized = url.rstrip('/')

# Préférer HTTPS
if 'http://' in url:
    url = url.replace('http://', 'https://')

# Dédupliquer
unique_urls = list(set(urls))
```

Résultat final (20 URLs uniques) :
```
https://example.com, https://example.com/about, https://example.com/contact...
```

### ⏱️ Performance
- **Timeout** : 20 secondes
- **Vitesse** : ~3-8 secondes par domaine
- **Fiabilité** : ~85% (dépend si le site a été archivé)

### 🔍 Utilité pour l'OSINT

#### 1. **Découvrir des pages cachées** :
- `/admin`, `/backup`, `/test`
- Fichiers de configuration exposés

#### 2. **Analyser l'évolution** :
- Comment le site a changé au fil du temps
- Anciennes technologies utilisées

#### 3. **Retrouver du contenu supprimé** :
- Anciennes pages de produits
- Articles de blog effacés
- Anciens emails de contact

#### 4. **Identifier des vulnérabilités** :
- Anciennes versions de CMS non patchées
- Chemins d'administration connus

---

## 🔄 Pipeline complet - Exemple concret

Prenons **`agence107.com`** comme exemple :

### Étape 1 : WhatWeb
```bash
whatweb agence107.com --log-verbose=- --no-errors
```
**Résultat :**
```
WordPress | Server: LiteSpeed | IP: 51.77.165.6 | Pays: GB
```
→ Site WordPress hébergé sur LiteSpeed au Royaume-Uni

### Étape 2 : theHarvester
```bash
theHarvester -d agence107.com -b all -l 500
```
**Résultat :**
```
contact@agence107.com
info@agence107.com
```
→ 2 emails trouvés

### Étape 3 : Subfinder
```bash
subfinder -d agence107.com -silent -all -timeout 60
```
**Résultat :**
```
www.agence107.com
mail.agence107.com
ftp.agence107.com
api.agence107.com
```
→ 4 sous-domaines découverts

### Étape 4 : WHOIS
```bash
whois agence107.com
```
**Résultat :**
```
Registrar: OVH sas
Creation Date: 2018-05-10
Expiry Date: 2025-05-10
Name Server: ns1.ovh.net
```
→ Domaine de 6 ans, chez OVH

### Étape 5 : Wayback Machine
```bash
curl -s "https://web.archive.org/cdx/search?url=agence107.com&output=txt&fl=original&filter=statuscode:200&limit=50"
```
**Résultat :**
```
https://agence107.com
https://agence107.com/services
https://agence107.com/contact
```
→ 3 URLs archivées

### 📊 Résultat final en BDD
```sql
UPDATE companies SET
  tech_stack = 'WordPress | Server: LiteSpeed | IP: 51.77.165.6 | Pays: GB',
  emails_osint = 'contact@agence107.com, info@agence107.com',
  subdomains = 'www.agence107.com, mail.agence107.com, ftp.agence107.com, api.agence107.com',
  whois_raw = 'Registrar: OVH sas\nCreation Date: 2018-05-10...',
  wayback_urls = 'https://agence107.com, https://agence107.com/services, https://agence107.com/contact',
  osint_status = 'Done',
  osint_updated_at = '2025-12-11T14:21:47+01:00'
WHERE company_name = 'AGENCE 107';
```

---

## 📈 Comparaison des outils

| Outil | Vitesse | Fiabilité | Données collectées | Difficulté |
|-------|---------|-----------|-------------------|------------|
| **WhatWeb** | ⚡⚡⚡ Rapide | 95% | Technologies web | Facile |
| **theHarvester** | ⚡⚡ Moyen | 80% | Emails, sous-domaines | Moyen |
| **Subfinder** | ⚡⚡⚡ Rapide | 90% | Sous-domaines | Facile |
| **Amass** | ⚡ Lent | 95% | Sous-domaines + mapping | Avancé |
| **WHOIS** | ⚡⚡⚡ Rapide | 100% | Infos domaine | Facile |
| **Wayback** | ⚡⚡ Moyen | 85% | URLs historiques | Facile |

---

## 🎯 Quand utiliser quel outil ?

### Pour trouver des emails :
1. **theHarvester** en premier (exhaustif)
2. **WHOIS** en complément (emails admin/tech)

### Pour trouver des sous-domaines :
1. **Subfinder** (rapide et fiable)
2. **Amass** si besoin de plus (plus lent)
3. **theHarvester** en complément

### Pour identifier les technologies :
1. **WhatWeb** (rapide et complet)
2. **Wappalyzer** (extension navigateur) en complément manuel

### Pour des infos d'hébergement :
1. **WHOIS** (registrar, name servers)
2. **WhatWeb** (IP, pays)

### Pour l'historique :
1. **Wayback Machine** (archives publiques)

---

## 🛡️ Aspects légaux et éthiques

### ✅ Légal (OSINT passif) :
- Consulter des informations **publiques**
- Utiliser des APIs **publiques**
- Rechercher dans des bases de données **ouvertes**

### ⚠️ Zone grise :
- Scraping intensif (rate limiting)
- Brute-force DNS (peut être détecté)

### ❌ Illégal :
- Exploitation de vulnérabilités trouvées
- Accès non autorisé à des systèmes
- Utilisation malveillante des données

### 📜 Règle d'or :
> **Si c'est public et accessible sans authentification, c'est OK pour l'OSINT.**

---

## 📚 Ressources supplémentaires

### Documentation officielle :
- **WhatWeb** : https://github.com/urbanadventurer/WhatWeb
- **theHarvester** : https://github.com/laramies/theHarvester
- **Subfinder** : https://github.com/projectdiscovery/subfinder
- **Amass** : https://github.com/OWASP/Amass

### Tutoriels :
- **OSINT Framework** : https://osintframework.com/
- **Awesome OSINT** : https://github.com/jivoi/awesome-osint

---

**Dernière mise à jour** : 2025-12-11
**Version** : 1.0


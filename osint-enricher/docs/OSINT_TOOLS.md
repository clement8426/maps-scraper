# 🔍 Outils OSINT - Guide Complet

Ce document explique les outils d'Open Source Intelligence (OSINT) utilisés pour enrichir votre base de données d'entreprises.

---

## 🌐 WhatWeb - Identification des Technologies

### Ce qu'il fait
WhatWeb identifie les technologies utilisées par un site web en analysant sa structure HTML, ses en-têtes HTTP et ses réponses.

### Informations collectées
- **CMS** : WordPress, Drupal, Joomla, etc.
- **Serveur web** : Apache, Nginx, IIS, Cloudflare
- **Frameworks** : React, Vue.js, Angular, Bootstrap
- **Langages** : PHP, ASP.NET, Ruby, Python
- **Outils** : Google Analytics, jQuery, Font Awesome
- **Pays d'hébergement** et adresse IP

### Exemple de résultat
```
Server: Apache | WordPress 6.2 | jQuery 3.7.1 | Pays: CH | IP: 128.65.195.18
```

### Utilité
- Savoir si le site est récent (technologies modernes)
- Identifier les vulnérabilités potentielles (versions obsolètes)
- Comprendre le niveau technique de l'entreprise

---

## 🔍 Subfinder - Découverte de Sous-domaines

### Ce qu'il fait
Subfinder découvre tous les sous-domaines associés à un domaine principal en utilisant des sources publiques (certificats SSL, DNS, archives web).

### Informations collectées
- `api.example.com` - API publique
- `mail.example.com` - Serveur email
- `dev.example.com` - Environnement de développement
- `blog.example.com` - Blog de l'entreprise
- `staging.example.com` - Environnement de test

### Exemple de résultat
```
www.example.com, api.example.com, mail.example.com, cdn.example.com
```

### Utilité
- Découvrir des services cachés (APIs, portails internes)
- Identifier des environnements de test mal sécurisés
- Cartographier l'infrastructure de l'entreprise

---

## 🎯 Amass - Reconnaissance Avancée

### Ce qu'il fait
Amass est un outil de cartographie réseau qui combine plusieurs techniques pour découvrir l'infrastructure d'une organisation.

### Informations collectées
- Sous-domaines avancés
- Réseau AS (Autonomous System)
- Adresses IP associées
- Relations DNS complexes
- Infrastructure cloud (AWS, Azure, etc.)

### Exemple de résultat
```
Sous-domaines: 15 découverts
AS: AS16509 (Amazon)
Infrastructure: AWS, Cloudflare
```

### Utilité
- Cartographie complète de l'infrastructure
- Identification des fournisseurs cloud
- Découverte de relations avec d'autres domaines

---

## 📋 WHOIS - Informations d'Enregistrement

### Ce qu'il fait
WHOIS interroge les bases de données d'enregistrement de domaines pour obtenir des informations officielles.

### Informations collectées
- **Propriétaire** : Nom, organisation (parfois masqué)
- **Contact** : Email administratif (souvent protégé)
- **Dates** :
  - Date de création du domaine
  - Date d'expiration
  - Dernière mise à jour
- **Registrar** : Bureau d'enregistrement (GoDaddy, OVH, etc.)
- **Serveurs DNS** : Serveurs de noms utilisés

### Exemple de résultat
```
Domain: example.com
Created: 2015-03-12
Expires: 2025-03-12
Registrar: OVH
Name Servers: ns1.ovh.net, ns2.ovh.net
```

### Utilité
- Vérifier la légitimité d'un site (ancienneté)
- Identifier le registrar pour d'éventuelles démarches
- Estimer la maturité de l'entreprise

---

## 📦 Wayback Machine - Archives Web

### Ce qu'il fait
Interroge l'API d'archive.org pour récupérer les URLs archivées d'un site web.

### Informations collectées
- Anciennes versions du site
- Pages supprimées
- Changements de contenu au fil du temps
- Historique des modifications

### Exemple de résultat
```
20 URLs archivées entre 2016 et 2024:
- https://example.com/ (53 captures)
- https://example.com/about (12 captures)
- https://example.com/contact (8 captures)
```

### Utilité
- Voir l'évolution de l'entreprise
- Récupérer des informations supprimées
- Identifier des services abandonnés
- Trouver d'anciennes pages de contact

---

## 🚀 Utilisation dans le Pipeline

### Ordre d'exécution
1. **WhatWeb** → Identification rapide des technologies
2. **Subfinder** → Découverte de sous-domaines
3. **Amass** → Cartographie avancée
4. **WHOIS** → Informations d'enregistrement
5. **Wayback** → Archives historiques

### Timing
- **1 entreprise** : 20-40 secondes
- **50 entreprises** : ~25 minutes
- **358 entreprises** : 2-4 heures

### Données stockées
Toutes les informations sont stockées dans `companies.db` avec horodatage.

---

## 💡 Conseils d'Utilisation

### Mode Illimité
- Enrichit toute la base de données
- Peut prendre plusieurs heures
- Progression sauvegardée automatiquement
- Arrêt possible à tout moment

### Filtrage
- **Par ville** : Concentrer sur une région
- **Avec site web** : Ignorer les entreprises sans site
- **Limite** : Contrôler le nombre d'entreprises à traiter

### Surveillance
- Logs en temps réel sur `/enrich`
- Compteur de progression
- Statut pour chaque entreprise (Done/Pending/Skipped)

---

## 🔒 Conformité et Éthique

### Sources Publiques
Tous les outils utilisent **uniquement des sources publiques** :
- Archives web publiques
- Certificats SSL publics
- Enregistrements DNS publics
- Bases WHOIS officielles

### Respect des Limites
- Pas de force brute
- Respect des délais entre requêtes
- Pas d'exploitation de vulnérabilités
- Collecte d'informations publiques uniquement

### Usage Légitime
Ces outils sont conçus pour :
- Recherche commerciale légitime
- Cartographie de votre propre infrastructure
- Sécurité et conformité
- Due diligence commerciale

---

## 📚 Ressources

- **WhatWeb** : https://github.com/urbanadventurer/WhatWeb
- **Subfinder** : https://github.com/projectdiscovery/subfinder
- **Amass** : https://github.com/owasp-amass/amass
- **WHOIS** : Standard IETF RFC 3912
- **Wayback Machine** : https://archive.org/web/


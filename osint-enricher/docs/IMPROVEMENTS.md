# 🚀 Améliorations OSINT Pipeline

## Résumé des optimisations apportées

### 1. 📧 theHarvester - Scan email amélioré

**Avant :**
```bash
theHarvester -d example.com -b all
# Timeout court, extraction basique
```

**Maintenant :**
```bash
theHarvester -d example.com -b all -l 500
# Toutes les sources (google, bing, linkedin, etc.)
# Limite de 500 résultats par source
# Timeout de 5 minutes (300s)
# Extraction exhaustive avec regex
# Filtrage intelligent des emails du domaine
```

**Résultats :**
- ✅ Plus d'emails trouvés grâce à la limite élevée
- ✅ Timeout généreux pour les gros domaines
- ✅ Filtrage des sous-domaines (ex: `contact@subdomain.example.com`)
- ✅ Logs détaillés : nombre d'emails total vs. domaine cible

---

### 2. 🔍 Subfinder - Scan sous-domaines optimisé

**Avant :**
```bash
subfinder -d example.com -silent
# Sources par défaut uniquement
```

**Maintenant :**
```bash
subfinder -d example.com -silent -all -timeout 60
# Toutes les sources disponibles
# Timeout de 60s par source
# Timeout global de 3 minutes
# Déduplication et tri automatique
# Limite à 100 sous-domaines
```

**Résultats :**
- ✅ Plus de sous-domaines découverts
- ✅ Déduplication automatique
- ✅ Tri alphabétique
- ✅ Logs clairs avec nombre de résultats uniques

---

### 3. 🌐 WhatWeb - Détection technologique avancée

**Améliorations :**
- Détection de **WordPress** avec version
- Détection de **plugins** : Yoast SEO, WooCommerce, Elementor
- Détection de **frameworks JS** : React, Vue.js, Angular
- Extraction de **serveur web**, **IP**, **pays**
- Utilise `--log-verbose` pour plus d'infos
- Nettoyage des codes ANSI
- Format de sortie structuré : `WordPress | WP 6.2 | Yoast SEO | Server: LiteSpeed | IP: 51.77.165.6 | Pays: GB`

**Résultats :**
- ✅ Infos comparables à Wappalyzer
- ✅ Limite à 8 technologies principales
- ✅ Affichage lisible et structuré

---

### 4. 📝 WHOIS - Extraction intelligente

**Améliorations :**
- Extraction des **lignes importantes** uniquement :
  - Registrar
  - Dates (création, expiration, mise à jour)
  - Name servers
  - Status
  - Organisation/Registrant
- Limite à 30 lignes importantes (au lieu de tout)
- Validation : au moins 50 caractères pour être considéré valide
- Timeout de 30s
- Gestion des codes de retour non-zéro

**Résultats :**
- ✅ Données WHOIS compactes et pertinentes
- ✅ Pas de pollution avec des infos inutiles
- ✅ Logs informatifs

---

### 5. 🕐 Wayback Machine - Déduplication URLs

**Améliorations :**
- Recherche de **50 URLs** (au lieu de 20)
- **Déduplication** : enlève les trailing slashes (`/`)
- **Préférence HTTPS** : `https://example.com` plutôt que `http://example.com`
- **Normalisation** : minuscules, sans slash final
- Limite finale à **20 URLs uniques**

**Résultats :**
- ✅ Pas de doublons dans la BDD
- ✅ URLs propres et uniques
- ✅ Préférence pour HTTPS

---

### 6. 🐛 Debug et logs améliorés

**Nouveau système de logs :**
```
[2025-12-11 13:30:00] 🔍 theHarvester: scan de example.com (toutes sources, limit=500)...
[2025-12-11 13:35:00] ✅ theHarvester: 5 email(s) du domaine example.com
[2025-12-11 13:35:10] 🔍 Subfinder: scan de example.com (toutes sources)...
[2025-12-11 13:36:00] ✅ Subfinder: 15 sous-domaine(s) unique(s)
[2025-12-11 13:36:10] ✅ WHOIS: 12 info(s) extraite(s)
[2025-12-11 13:36:15] ✅ Wayback: 8 URLs uniques
[2025-12-11 13:36:15] → Mise à jour BDD pour example.com
[2025-12-11 13:36:15]    [DEBUG] Champs à mettre à jour: {'tech_stack': 'WordPress | Server: LiteSpeed...', ...}
[2025-12-11 13:36:15]    [DEBUG] SQL: UPDATE companies SET ... WHERE id = 123
[2025-12-11 13:36:15]    [DEBUG] 1 ligne(s) mise(s) à jour dans /path/to/companies.db
[2025-12-11 13:36:15] ✅ example.com terminé
```

**Résultats :**
- ✅ Logs clairs et informatifs
- ✅ Émojis pour meilleure lisibilité
- ✅ Debug SQL pour vérifier les écritures en BDD
- ✅ Compteurs précis

---

### 7. 🗄️ Script de diagnostic BDD

**Nouveau script : `check_osint_data.py`**

```bash
python3 scripts/check_osint_data.py /path/to/companies.db
```

**Affiche :**
- ✅ Vérification des colonnes OSINT
- ✅ Statistiques : total, enrichi, avec tech, avec emails, etc.
- ✅ Dernières mises à jour avec détails
- ✅ Exemples de données enrichies

---

## 📊 Comparaison Avant/Après

| Métrique | Avant | Après |
|----------|-------|-------|
| **theHarvester timeout** | 40s | 300s (5 min) |
| **theHarvester limit** | défaut | 500/source |
| **Subfinder sources** | défaut | toutes (-all) |
| **Subfinder timeout** | 40s | 180s (3 min) |
| **WhatWeb infos** | brutes | structurées |
| **WHOIS données** | tout (4000 car) | lignes importantes (30 lignes) |
| **Wayback URLs** | 20 avec doublons | 20 uniques sans doublons |
| **Logs** | basiques | détaillés + debug |

---

## 🚀 Utilisation sur le VPS

```bash
cd ~/maps-scraper
git pull

cd osint-enricher

# Vérifier la BDD avant
python3 scripts/check_osint_data.py ~/maps-scraper/backend/companies.db

# Redémarrer avec les nouvelles améliorations
sudo systemctl restart osint-enricher

# Suivre les logs
tail -f backend/pipeline.log

# Vérifier la BDD après quelques enrichissements
python3 scripts/check_osint_data.py ~/maps-scraper/backend/companies.db
```

---

## 📝 Notes

- **Patience** : avec les timeouts augmentés, chaque enrichissement prend plus de temps mais donne de meilleurs résultats
- **Qualité > Vitesse** : on privilégie l'exhaustivité des données
- **Logs** : suivez les logs en temps réel pour voir la progression
- **Debug** : les logs `[DEBUG]` vous disent exactement ce qui est écrit en BDD

---

## 🎯 Prochaines améliorations possibles

1. **Amass** : ajouter des options avancées
2. **Rate limiting** : délai configurable entre domaines
3. **Retry** : réessayer en cas d'échec
4. **API keys** : support des clés API pour theHarvester (plus de résultats)
5. **Rapports** : génération de rapports HTML/PDF

---

**Date de mise à jour** : 2025-12-11
**Version** : 2.0


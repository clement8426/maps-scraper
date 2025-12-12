# Améliorations de theHarvester 🚀

*Date : 12 décembre 2025*

## 📋 Contexte

L'utilisateur a développé un script OSINT local performant avec une excellente configuration de theHarvester. Cette configuration a été intégrée dans le pipeline d'enrichissement du VPS.

---

## ✅ Améliorations apportées

### 1. **Sources fiables uniquement**

**Avant :**
```python
sources = "bing,duckduckgo,yahoo,baidu,crtsh,certspotter,hackertarget,rapiddns,subdomaincenter,urlscan"
# 10 sources, dont certaines lentes ou peu fiables
```

**Maintenant :**
```python
sources_list = ['bing', 'duckduckgo', 'yahoo', 'brave']
# 4 sources fiables et rapides
```

**Avantage :** Réduit les timeouts et améliore la fiabilité

---

### 2. **Parsing JSON propre**

**Avant :**
```python
# Parse uniquement la sortie texte
result = subprocess.run(cmd, capture_output=True)
emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", result.stdout)
```

**Maintenant :**
```python
# Génère un fichier JSON structuré
cmd = ["theHarvester", "-d", domain, "-b", source, "-l", "100", "-f", temp_json_path]

# Parse le JSON (méthode propre)
with open(temp_json_path + '.json', 'r') as f:
    json_data = json.load(f)
    emails = json_data.get('emails', [])

# Fallback sur parsing texte si JSON échoue
```

**Avantage :** 
- Extraction plus fiable et structurée
- Moins de faux positifs
- Fallback intelligent

---

### 3. **Filtrage avancé des emails**

**Avant :**
```python
# Filtrage basique par domaine
domain_emails = [e for e in all_emails if domain in e.lower()]
```

**Maintenant :**
```python
# Patterns d'emails à exclure
excluded_patterns = [
    'noreply', 'no-reply', 'donotreply', 'no_reply',
    'example.com', 'test.com', 'sample.com', 'domain.com',
    'abuse@', 'postmaster@', 'hostmaster@', 'webmaster@'
]

# Filtrage avancé
for email in all_emails:
    email_lower = email.lower()
    email_domain = email_lower.split('@')[1]
    
    # Vérifie le domaine (avec variations)
    is_domain_email = any(var in email_domain for var in domain_variations)
    
    # Exclut les emails génériques
    if not any(pattern in email_lower for pattern in excluded_patterns):
        # Validation stricte
        if len(email_lower) > 5 and '.' in email_domain:
            valid_emails.append(email_lower)
```

**Avantage :** 
- Exclusion des emails techniques et génériques
- Validation stricte (longueur, format)
- Emails de meilleure qualité

---

### 4. **Timeout optimisé**

**Avant :**
```python
timeout = 300  # 5 minutes pour toutes les sources
```

**Maintenant :**
```python
timeout = 90  # 90 secondes PAR source
# Total : 4 sources × 90s = 6 minutes max
```

**Avantage :** 
- Évite les blocages sur une source lente
- Timeout individuel par source
- Plus réactif en cas d'erreur

---

### 5. **Nettoyage automatique**

**Avant :**
```python
# Pas de nettoyage des fichiers temporaires
```

**Maintenant :**
```python
# Nettoie les fichiers temporaires
os.unlink(temp_json_path)
if os.path.exists(temp_json_path + '.json'):
    os.unlink(temp_json_path + '.json')
if os.path.exists(temp_json_path + '.xml'):
    os.unlink(temp_json_path + '.xml')
```

**Avantage :** Pas de pollution du système de fichiers

---

### 6. **Statistiques détaillées**

**Avant :**
```
✅ theHarvester: OK
```

**Maintenant :**
```
🔍 theHarvester: scan de example.com (4 sources fiables, limit=100)...
✅ theHarvester: 5 email(s) valide(s) pour example.com
```

ou

```
ℹ️  theHarvester: 12 email(s) trouvé(s), 0 valide après filtrage
```

**Avantage :** Visibilité sur le processus de filtrage

---

## 📊 Comparaison des performances

| Métrique | Avant | Maintenant |
|----------|-------|------------|
| **Sources** | 10 | 4 (fiables) |
| **Timeout** | 300s global | 90s × 4 sources |
| **Parsing** | Texte | JSON + fallback texte |
| **Filtrage** | Basique | Avancé (exclusions) |
| **Validation** | Aucune | Stricte (longueur, format) |
| **Nettoyage** | ❌ | ✅ |
| **Logs** | Basiques | Détaillés |

---

## 🚀 Déploiement sur le VPS

```bash
cd ~/maps-scraper
git pull

# Redémarrer le service
sudo systemctl restart osint-enricher

# Suivre les logs
sudo journalctl -u osint-enricher -f
```

---

## 🔍 Résultat attendu

### Exemple avec `agence107.com` :

**Avant :**
```
[14:21:47] 🔍 theHarvester: scan de agence107.com (10 sources, limit=500)...
[14:21:47] ℹ️  theHarvester: scan terminé (aucun email trouvé)
```

**Maintenant :**
```
[14:21:47] 🔍 theHarvester: scan de agence107.com (4 sources fiables, limit=100)...
[14:22:15] ✅ theHarvester: 3 email(s) valide(s) pour agence107.com
```

ou si aucun email valide :

```
[14:21:47] 🔍 theHarvester: scan de agence107.com (4 sources fiables, limit=100)...
[14:22:15] ℹ️  theHarvester: 8 email(s) trouvé(s), 0 valide après filtrage
```

---

## 📝 Notes techniques

### Fichiers temporaires créés

theHarvester génère 3 fichiers temporaires :
- `/tmp/tmpXXXXXX` (base)
- `/tmp/tmpXXXXXX.json` (résultats structurés)
- `/tmp/tmpXXXXXX.xml` (résultats XML, non utilisé)

Tous sont automatiquement nettoyés après chaque scan.

### Délai entre sources

Un délai de 1 seconde est ajouté entre chaque source pour éviter le rate limiting :
```python
time.sleep(1)  # Petit délai entre les sources
```

### Gestion des erreurs

Trois types d'erreurs sont gérées :
1. **Timeout** : Passe à la source suivante
2. **JSON invalide** : Fallback sur parsing texte
3. **Erreur générale** : Loggée et passe à la suite

---

## 🎯 Résumé

**Objectif :** Collecter plus d'emails valides, plus rapidement, avec moins de faux positifs

**Résultat :**
- ✅ Meilleure qualité des emails collectés
- ✅ Temps de scan optimisé (4 sources rapides)
- ✅ Logs plus informatifs
- ✅ Parsing plus fiable (JSON + fallback)
- ✅ Nettoyage automatique

**Inspiré du script local de l'utilisateur, adapté au pipeline VPS.**


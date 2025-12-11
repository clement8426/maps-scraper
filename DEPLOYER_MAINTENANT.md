# 🚀 DÉPLOYER SUR LE VPS - MAINTENANT

## ✅ Ce qui a été fait

### 1. **Logs OSINT améliorés** 📋
- Affichage de l'ID à chaque étape
- Diagnostic détaillé si ID introuvable
- Logs plus clairs et structurés

### 2. **Scripts de diagnostic SQL** 🔍
- `osint-enricher/scripts/debug_ids.sql` - Requêtes SQL pour comprendre
- `osint-enricher/scripts/test_ids.sh` - Script automatique de diagnostic

### 3. **Toutes les colonnes dans /db** 📊
- Téléphone, note, avis, adresse, lien Maps, tag, réseaux sociaux
- Mapping SQL corrigé

---

## 🎯 COMMANDES À EXÉCUTER SUR LE VPS

### Étape 1 : Se connecter
```bash
ssh ubuntu@57.131.35.91
```

### Étape 2 : Mettre à jour le code
```bash
cd ~/maps-scraper
git pull
```

### Étape 3 : Redémarrer l'enrichisseur OSINT
```bash
sudo systemctl restart osint-enricher
```

### Étape 4 : Suivre les nouveaux logs en temps réel
```bash
# Les nouveaux logs vont maintenant afficher :
# - 📊 IDs récupérés au début
# - 📌 ID + Entreprise pour chaque enrichissement
# - 💾 ID au moment de la sauvegarde
# - 🔍 Diagnostic si ID introuvable

sudo journalctl -u osint-enricher -f
```

---

## 🔍 DIAGNOSTIQUER LE PROBLÈME DES IDs

### Requête SQL sur le VPS
```bash
cd ~/maps-scraper
sqlite3 companies.db << 'EOF'
-- Voir les IDs min/max
SELECT MIN(id) as min, MAX(id) as max, COUNT(*) as total FROM companies;

-- Voir les 10 entreprises à enrichir
SELECT id, company_name, city, osint_status
FROM companies
WHERE (osint_status IS NULL OR osint_status NOT IN ('Done','Skipped'))
  AND website IS NOT NULL AND website <> ''
ORDER BY id ASC
LIMIT 10;

-- Vérifier si les IDs problématiques existent
SELECT id, company_name, osint_status FROM companies WHERE id IN (41971, 41972, 42490);
EOF
```

### Ou utiliser le script automatique
```bash
cd ~/maps-scraper/osint-enricher/scripts
./test_ids.sh
```

---

## 📋 EXEMPLE DE NOUVEAUX LOGS

### ❌ AVANT (impossible de comprendre)
```
Enrichissement #4/105 - Vision Publicité (https://visionpublicite.ch)
→ Sauvegarde en BDD pour Vision Publicité...
❌ ERREUR: ID 41971 introuvable dans la BDD !
```

### ✅ MAINTENANT (super clair)
```
============================================================
🚀 Pipeline OSINT démarré
📋 Paramètres: city=La Chaux-de-Fonds, limit=50, require_website=True
✅ 50 cible(s) trouvée(s)
📊 IDs à enrichir: 100, 101, 102, 103, 104... (+45 autres)
============================================================
🔄 Enrichissement #1/50
📌 ID: 100 | Entreprise: Vision Publicité
🌐 Site: https://visionpublicite.ch
============================================================
✅ WhatWeb: 3 tech(s)
🔍 theHarvester: scan de visionpublicite.ch...
✅ Subfinder: 2 sous-domaine(s)

💾 Sauvegarde en BDD...
   ID: 100 | Entreprise: Vision Publicité
   📝 4/6 champs avec données
   🔍 Vérification de l'existence de l'ID 100...
   ✅ ID 100 existe bien: 'Vision Publicité'
   ✅ SAUVEGARDE RÉUSSIE pour ID 100
✅ ID 100 - Vision Publicité terminé et sauvegardé en BDD
```

### Si l'ID est introuvable (avec diagnostic)
```
💾 Sauvegarde en BDD...
   ID: 41971 | Entreprise: Vision Publicité
   🔍 Vérification de l'existence de l'ID 41971...
   ❌ ERREUR CRITIQUE: ID 41971 INTROUVABLE dans la BDD !
   💡 L'entreprise a peut-être été supprimée pendant l'enrichissement
   📊 BDD actuelle: 38500 entreprises, IDs de 1 à 38500
```

---

## 🎯 CE QUE TU VAS DÉCOUVRIR

Après le déploiement et le redémarrage, tu vas voir dans les logs :

1. **Les IDs récupérés** au début du pipeline
2. **L'ID exact** de chaque entreprise enrichie
3. **L'ID au moment de la sauvegarde**
4. **Si un ID est introuvable** : diagnostic complet avec la plage d'IDs dans la BDD

Ça va te permettre de comprendre **exactement** ce qui se passe et pourquoi certains IDs ne sont pas trouvés.

---

## 🚨 SI LE PROBLÈME PERSISTE

Si après le déploiement tu vois encore `❌ ID XXXXX INTROUVABLE`, fais-moi un screenshot des logs complets, notamment :
- La ligne `📊 IDs à enrichir: ...`
- Le diagnostic `📊 BDD actuelle: ...`

Je pourrai alors comprendre d'où vient le décalage entre les IDs sélectionnés et ceux qui existent réellement.


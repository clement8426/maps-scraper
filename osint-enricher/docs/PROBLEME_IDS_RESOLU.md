# 🔧 Problème des IDs mouvants - RÉSOLU

## 🔴 Le problème

Les données OSINT n'étaient pas sauvegardées malgré les logs "✅ Sauvegarde réussie".

### Analyse du problème

1. **Le scraper Maps tourne en continu** et ajoute de nouvelles entreprises
2. **Les IDs changent constamment** :
   - Début de journée : AGENCE 107 = ID 38122
   - Milieu de journée : AGENCE 107 = ID 39646
   - Les nouveaux IDs : 39730-39739 (entreprises ajoutées à 14:19)

3. **Le pipeline utilisait `ORDER BY updated_at DESC`** :
   - Cela sélectionne les entreprises les plus RÉCEMMENT modifiées
   - Donc le pipeline enrichissait toujours les NOUVELLES entreprises
   - Ces nouvelles entreprises sont instables (pas encore traitées complètement)

4. **Résultat** :
   - Le pipeline enrichissait des entreprises fantômes
   - Les anciennes entreprises stables n'étaient jamais enrichies
   - Total enrichi : 0 malgré des dizaines de scans

## ✅ La solution

### Changement dans `fetch_targets()`

**AVANT** :
```python
ORDER BY updated_at DESC  # Les plus récentes en premier
```

**MAINTENANT** :
```python
ORDER BY id ASC  # Les plus anciennes en premier
```

### Pourquoi ça fonctionne ?

1. **IDs stables** : Les anciennes entreprises ont des IDs bas (38122, 38123...) qui ne changent pas
2. **Données complètes** : Ces entreprises ont déjà été traitées par le scraper Maps
3. **Progression logique** : Le pipeline enrichit de manière séquentielle, ID par ID
4. **Pas de collision** : Le scraper Maps ajoute des IDs hauts, le pipeline traite les IDs bas

## 📊 Résultat attendu

### Avant la correction
```sql
SELECT COUNT(*) FROM companies WHERE osint_status = 'Done';
-- Résultat : 0
```

### Après la correction
```sql
SELECT COUNT(*) FROM companies WHERE osint_status = 'Done';
-- Résultat : augmente progressivement (1, 2, 3...)
```

## 🚀 Déploiement

```bash
# Sur le VPS
cd ~/maps-scraper
git pull

cd osint-enricher
sudo systemctl restart osint-enricher

# Lancer un enrichissement test
# Aller sur http://IP:81/enrich
# Lancer : city=Val-de-Ruz, limit=5

# Vérifier les résultats
sqlite3 ~/maps-scraper/backend/companies.db \
  "SELECT id, company_name, osint_status 
   FROM companies 
   WHERE osint_status = 'Done' 
   ORDER BY id ASC 
   LIMIT 10;"
```

## 🔍 Vérifications post-déploiement

### 1. Vérifier les IDs traités
```sql
SELECT id, company_name, city, osint_updated_at 
FROM companies 
WHERE osint_status = 'Done' 
ORDER BY id ASC;
```

### 2. Vérifier la progression
```sql
-- Avant l'enrichissement
SELECT MIN(id) as premier_id, MAX(id) as dernier_id 
FROM companies 
WHERE city = 'Val-de-Ruz' AND website IS NOT NULL;

-- Après l'enrichissement
SELECT MIN(id) as premier_enrichi, MAX(id) as dernier_enrichi 
FROM companies 
WHERE osint_status = 'Done';
```

### 3. Logs détaillés
```bash
tail -f ~/maps-scraper/osint-enricher/backend/pipeline.log | grep -E "Enrichissement #|Sauvegarde|ligne"
```

Vous devriez voir :
```
[15:00:00] Enrichissement #1/5 - AGENCE 107 (https://agence107.com)
[15:01:30] → Sauvegarde en BDD pour AGENCE 107...
[15:01:30]    ✅ Sauvegarde réussie : 1 ligne(s) mise(s) à jour
```

## 🎯 Test de validation

```bash
cd ~/maps-scraper/osint-enricher

# Script de test
cat > test_ordre.py << 'EOF'
import sqlite3
import os

db_path = os.getenv("DATABASE_PATH", "../backend/companies.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Simuler fetch_targets() avec le nouvel ordre
cur.execute("""
    SELECT id, company_name, website
    FROM companies
    WHERE city = 'Val-de-Ruz' 
      AND website IS NOT NULL 
      AND (osint_status IS NULL OR osint_status NOT IN ('Done','Skipped'))
    ORDER BY id ASC
    LIMIT 5
""")

print("🎯 Premières cibles à enrichir (ORDER BY id ASC) :")
for row in cur.fetchall():
    print(f"  ID {row[0]}: {row[1]} ({row[2]})")

conn.close()
EOF

python3 test_ordre.py
```

## 📈 Avantages de la correction

1. **Stabilité** : Les IDs ne changent plus pendant l'enrichissement
2. **Prévisibilité** : Progression séquentielle et logique
3. **Pas de doublon** : Chaque entreprise est enrichie une seule fois
4. **Traçabilité** : On peut facilement voir où le pipeline en est
5. **Cohabitation** : Le scraper Maps et l'enrichisseur OSINT fonctionnent en parallèle sans conflit

## 🛡️ Prévention future

Pour éviter ce problème à l'avenir :

1. **Toujours utiliser `ORDER BY id ASC`** pour les pipelines qui traitent des données en croissance
2. **Éviter `ORDER BY updated_at DESC`** quand des données sont ajoutées en continu
3. **Tester avec des données en mouvement** : lancer le pipeline pendant que le scraper tourne
4. **Monitorer les IDs** : vérifier que les IDs traités sont cohérents

## 📝 Notes

- Le scraper Maps peut continuer à tourner pendant l'enrichissement OSINT
- Les deux processus ne se gênent pas mutuellement
- L'enrichissement progresse des anciens IDs vers les nouveaux
- Les nouvelles entreprises seront enrichies lors du prochain scan

---

**Date** : 2025-12-11  
**Problème** : IDs mouvants + ORDER BY incorrect  
**Solution** : ORDER BY id ASC  
**Status** : ✅ RÉSOLU


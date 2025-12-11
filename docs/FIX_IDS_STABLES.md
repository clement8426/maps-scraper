# 🔧 FIX CRITIQUE : IDs Stables

## ⚠️ Problème découvert

Le scraper Google Maps utilisait `INSERT OR REPLACE` qui **supprimait et recréait** les entreprises, générant de nouveaux IDs à chaque scan.

### Impact
```
Scan 1 : ID 41971 | Vision Publicité | https://visionpublicite.ch
         ↓ Enrichissement OSINT en cours (2-3 min)...
Scan 2 : ID 46604 | Vision Publicité | https://visionpublicite.ch  ← NOUVEL ID !
         ↓ 
Erreur : ❌ ID 41971 introuvable dans la BDD !
```

**Résultat** : L'enrichisseur OSINT ne pouvait jamais sauvegarder car les IDs changeaient pendant le traitement.

---

## ✅ Solution implémentée

### Avant (`INSERT OR REPLACE`)
```python
INSERT OR REPLACE INTO companies (...)
```
- ❌ Supprime l'ancienne ligne
- ❌ Crée une nouvelle ligne avec nouvel ID
- ❌ Perd les données OSINT enrichies
- ❌ Empêche l'enrichisseur de fonctionner

### Après (`SELECT → UPDATE ou INSERT`)
```python
# Vérifier si existe
SELECT id FROM companies WHERE maps_link = ?

if exists:
    # UPDATE : Préserve l'ID et les données OSINT
    UPDATE companies SET ... WHERE maps_link = ?
else:
    # INSERT : Nouvelle entreprise
    INSERT INTO companies (...)
```

**Avantages** :
- ✅ Les IDs ne changent **JAMAIS**
- ✅ Les données OSINT sont **préservées**
- ✅ L'enrichisseur peut sauvegarder sans erreur
- ✅ Mise à jour seulement des infos Google Maps (nom, adresse, téléphone, etc.)

---

## 🚀 Déploiement

```bash
ssh ubuntu@57.131.35.91

cd ~/maps-scraper
git pull

# Redémarrer le scraper
sudo systemctl restart maps-scraper

# Redémarrer l'enrichisseur
sudo systemctl restart osint-enricher
```

---

## 🧪 Test de vérification

Après le déploiement, attends 5-10 minutes puis vérifie que les IDs ne changent plus :

```bash
# Noter les IDs actuels
sqlite3 ~/maps-scraper/backend/companies.db \
  "SELECT MIN(id), MAX(id), COUNT(*) FROM companies;"

# Attendre 10 minutes (le scraper rescanne)
sleep 600

# Vérifier que les IDs n'ont pas changé
sqlite3 ~/maps-scraper/backend/companies.db \
  "SELECT MIN(id), MAX(id), COUNT(*) FROM companies;"
```

**Résultat attendu** : MIN(id) et MAX(id) doivent rester stables. Seul COUNT(*) peut augmenter (nouvelles entreprises).

---

## 📊 Impact sur l'enrichissement OSINT

Maintenant que les IDs sont stables :

1. ✅ Le pipeline récupère des IDs valides
2. ✅ Les IDs existent toujours pendant l'enrichissement (2-3 min)
3. ✅ La sauvegarde réussit
4. ✅ Les données OSINT restent en BDD même après un rescan Google Maps

**Plus d'erreur "ID introuvable" !** 🎉


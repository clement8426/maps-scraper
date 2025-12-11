# 🚀 Déploiement des corrections

## ✅ Modifications apportées

### 1. **Anti-clignotement OSINT** (`osint-enricher/frontend/script.js`)
- Cache du dernier statut avec confirmation avant changement
- Évite les changements d'état intempestifs entre "En cours" et "Arrêté"

### 2. **Toutes les colonnes BDD** (`osint-enricher/backend/app.py`)
- Ajout de toutes les colonnes de la table `companies` dans `/db`
- Mapping correct des index pour afficher : téléphone, note, avis, adresse, lien Maps, tag, réseaux sociaux
- Ordre SQL corrigé pour correspondre à la structure réelle de la table

### 3. **Fix header mobile** (`frontend/index.html`, `frontend/script.js`, `frontend/style.css`)
- Bouton "Déconnexion" supprimé
- Bouton "Actualiser" fonctionnel (recharge stats + entreprises + statut)
- Layout responsive en colonne sur mobile

---

## 🔧 Déploiement sur le VPS

### Étape 1 : Arrêter les services
```bash
ssh ubuntu@57.131.35.91

# Arrêter les deux services
sudo systemctl stop maps-scraper
sudo systemctl stop osint-enricher
```

### Étape 2 : Mettre à jour le code
```bash
cd ~/maps-scraper
git pull
```

### Étape 3 : Redémarrer les services
```bash
# Redémarrer le scraper principal
sudo systemctl start maps-scraper
sudo systemctl status maps-scraper

# Redémarrer l'enrichisseur OSINT
sudo systemctl start osint-enricher
sudo systemctl status osint-enricher
```

### Étape 4 : Vérifier les logs
```bash
# Logs du scraper
sudo journalctl -u maps-scraper -f

# Logs de l'enrichisseur
sudo journalctl -u osint-enricher -f
```

---

## ⚠️ Problème "Race to IDs" résolu

Le problème où les IDs changeaient a été résolu avec :
```python
ORDER BY id ASC  # Au lieu de ORDER BY updated_at DESC
```

Cela garantit que le pipeline traite les **entreprises les plus anciennes en premier** (IDs stables), pas les plus récentes (IDs qui changent car le scraper continue d'ajouter des données).

---

## 🧪 Tester après déploiement

1. **Page principale** : `http://57.131.35.91:5000`
   - ✅ Bouton "Actualiser" fonctionne
   - ✅ Header en colonne sur mobile
   - ✅ Pas de bouton "Déconnexion"

2. **Page OSINT** : `http://57.131.35.91:81/enrich`
   - ✅ Statut ne clignote plus
   - ✅ "En cours" reste stable pendant l'enrichissement
   - ✅ Les IDs sont corrects (pas d'erreur "ID introuvable")

3. **Page BDD** : `http://57.131.35.91:81/db`
   - ✅ Toutes les colonnes affichées (téléphone, note, avis, etc.)
   - ✅ Lien Google Maps cliquable
   - ✅ Données complètes visibles au clic

---

## 📊 Résultat attendu

**Logs OSINT sans erreurs** :
```
[2025-12-11 16:10:00] Enrichissement #1/105 - noxup (https://noxup.ch)
[2025-12-11 16:10:05] ✅ Sauvegarde réussie : 1 ligne(s) mise(s) à jour
[2025-12-11 16:10:05] ✅ noxup terminé et sauvegardé en BDD
```

**Plus d'erreurs** :
```
❌ ERREUR: ID 41971 introuvable dans la BDD !  ← Cette erreur ne devrait plus apparaître
```


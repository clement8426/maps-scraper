# Synchronisation de la progression : Comprendre "2/50 (4%)" vs "#3/50"

*Date : 12 décembre 2025*

## ❓ La question

**Observation :**
- Sur l'interface `/enrich` : "Progression : 2/50 (4%)"
- Dans les logs serveur : "🔄 Enrichissement #3/50"

**Question :** Pourquoi les deux ne sont pas synchronisés ?

---

## ✅ Réponse : C'EST NORMAL !

Les deux métriques représentent **deux choses différentes** :

### 📊 Métrique 1 : Progression (interface)

```
Progression : 2/50 (4%)
```

**Signification :** 
- **2 entreprises ont été TERMINÉES et SAUVEGARDÉES** dans la base de données
- C'est le champ `processed` dans le statut
- Mis à jour **APRÈS** la sauvegarde de chaque entreprise

**Code backend (`pipeline.py`) :**
```python
# Après avoir traité et sauvegardé l'entreprise
self.status["processed"] += 1  # Incrémente après sauvegarde
```

---

### 🔄 Métrique 2 : Enrichissement en cours (logs)

```
🔄 Enrichissement #3/50
```

**Signification :**
- **L'entreprise #3 est EN COURS de traitement**
- C'est le message de statut
- Mis à jour **AVANT** de commencer le traitement

**Code backend (`pipeline.py`) :**
```python
# Avant de traiter l'entreprise
log(f"🔄 Enrichissement #{idx+1}/{total}")
self.status["message"] = f"Enrichissement {idx+1}/{total}"

# ... traitement de l'entreprise ...

# Après traitement et sauvegarde
self.status["processed"] += 1  # Maintenant processed = 3
```

---

## 📈 Timeline détaillée

Voici ce qui se passe exactement :

```
Temps    | Processed | Message             | État
---------|-----------|---------------------|------------------
T0       | 0         | "Démarrage..."      | Initialisation
T1       | 0         | "Enrichissement 1/50" | 🔄 Traitement #1
T2       | 1         | "Enrichissement 1/50" | ✅ #1 terminé
T3       | 1         | "Enrichissement 2/50" | 🔄 Traitement #2
T4       | 2         | "Enrichissement 2/50" | ✅ #2 terminé
T5       | 2         | "Enrichissement 3/50" | 🔄 Traitement #3  ← ICI
T6       | 3         | "Enrichissement 3/50" | ✅ #3 terminé
...
```

**À T5 (pendant que #3 est en cours) :**
- Interface : `Progression : 2/50 (4%)` ← 2 entreprises terminées
- Logs : `Enrichissement #3/50` ← entreprise en cours

---

## 🎯 Les deux métriques sont utiles !

### Métrique "Processed" (2/50)
✅ Montre le **progrès réel** (données sauvegardées en BDD)
✅ Utile pour le **pourcentage d'avancement**
✅ Fiable pour savoir **combien d'entreprises sont prêtes**

### Métrique "Message" (#3/50)
✅ Montre **quelle entreprise est en train d'être traitée**
✅ Utile pour **suivre en temps réel**
✅ Permet de voir **l'activité en cours**

---

## 💡 Options d'amélioration

Voici 3 options pour clarifier l'affichage :

### **Option A : Synchroniser sur l'entreprise en cours**

**Avant :**
```
Statut : 🔄 En cours
Progression : 2/50 (4%)
```

**Après :**
```
Statut : 🔄 En cours
En traitement : #3/50 (6%)
Terminées : 2/50 (4%)
```

**Code frontend (`script.js`) :**
```javascript
// Extraire le numéro depuis le message
const match = st.message.match(/Enrichissement (\d+)\/(\d+)/);
if (match) {
  const current = match[1];
  const total = match[2];
  progressEl.textContent = `En traitement : #${current}/${total}`;
}
progressEl.textContent += ` | Terminées : ${st.processed}/${st.total}`;
```

---

### **Option B : Affichage unifié sur "processed"**

**Avant :**
```
Statut : 🔄 En cours
Progression : 2/50 (4%)
```

**Après :**
```
Statut : 🔄 En cours
Progression : 3/50 (6%) - En traitement
```

**Code backend (`pipeline.py`) :**
```python
# Mettre à jour processed AVANT le traitement
self.status["processed"] = idx + 1  # Incrémente avant traitement
log(f"🔄 Enrichissement #{idx+1}/{total}")
# ... traitement ...
```

**Inconvénient :** Le pourcentage peut être trompeur (entreprise pas encore terminée)

---

### **Option C : Affichage en deux lignes**

**Avant :**
```
Statut : 🔄 En cours
Progression : 2/50 (4%)
```

**Après :**
```
Statut : 🔄 En cours - Traitement de #3/50
Progression : 2 entreprises terminées et sauvegardées (4%)
```

**Code frontend (`script.js`) :**
```javascript
// Extraire le numéro depuis le message
const match = st.message.match(/Enrichissement (\d+)\/(\d+)/);
if (match && st.running) {
  statusEl.textContent = `🔄 En cours - Traitement de #${match[1]}/${match[2]}`;
}

// Progression séparée
progressEl.textContent = `${st.processed} entreprises terminées et sauvegardées (${percentage}%)`;
```

---

## 🎨 Ma recommandation : **Option A**

C'est la plus claire et informatif :

```
╔════════════════════════════════════════════╗
║  Statut : 🔄 En cours                      ║
║  ─────────────────────────────────────────║
║  En traitement : #3/50 (6%)               ║
║  Terminées : 2/50 (4%)                    ║
║  ─────────────────────────────────────────║
║  Dernière entreprise : SBA Concept         ║
╚════════════════════════════════════════════╝
```

**Avantages :**
✅ Montre clairement les **deux métriques**
✅ Facile à comprendre
✅ Pas de confusion
✅ Pas de changement backend nécessaire

---

## 🚀 Implémentation (Option A)

### Changements à faire dans `script.js` :

```javascript
async function refreshStatus() {
  const st = await api.status();
  
  // Mise à jour du statut
  if (st.running) {
    // Extraire le numéro depuis le message
    const match = st.message.match(/Enrichissement (\d+)\/(\d+)/);
    if (match) {
      const current = match[1];
      const currentPercent = Math.round((current / st.total) * 100);
      progressEl.textContent = `En traitement : #${current}/${st.total} (${currentPercent}%)`;
    }
    
    // Ajouter la ligne "Terminées"
    if (st.processed > 0) {
      const completedPercent = Math.round((st.processed / st.total) * 100);
      progressEl.textContent += ` | Terminées : ${st.processed}/${st.total} (${completedPercent}%)`;
    }
  } else {
    // Si arrêté ou terminé
    const percentage = Math.round((st.processed / st.total) * 100);
    progressEl.textContent = `${st.processed}/${st.total} (${percentage}%)`;
  }
}
```

---

## 📝 Résumé

**Question :** Pourquoi "2/50" sur l'interface et "#3/50" dans les logs ?

**Réponse :** 
- `2/50` = 2 entreprises **TERMINÉES** et **SAUVEGARDÉES** ✅
- `#3/50` = Entreprise **EN COURS** de traitement 🔄

**Les deux sont corrects et utiles !**

**Solution recommandée :** Afficher les deux métriques clairement séparées (Option A)

---

Veux-tu que j'implémente l'**Option A** maintenant ? 🤔


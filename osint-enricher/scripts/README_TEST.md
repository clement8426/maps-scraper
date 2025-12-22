# Script de Test Enrichissement OSINT

## Utilisation

Le script `test_enrichment_debug.py` permet de tester l'enrichissement OSINT directement depuis la ligne de commande avec des logs détaillés.

### Commande de base

```bash
cd ~/maps-scraper/osint-enricher
source venv/bin/activate
python3 scripts/test_enrichment_debug.py
```

### Options disponibles

```bash
# Tester avec 1 seule entreprise (rapide pour debug)
python3 scripts/test_enrichment_debug.py --limit 1

# Tester avec 2 entreprises
python3 scripts/test_enrichment_debug.py --limit 2

# Tester pour une ville spécifique
python3 scripts/test_enrichment_debug.py --city "Genève" --limit 5

# Tester sans exiger de site web
python3 scripts/test_enrichment_debug.py --no-require-website --limit 3

# Spécifier un chemin de BDD personnalisé
python3 scripts/test_enrichment_debug.py --db /chemin/vers/companies.db --limit 2
```

### Exemples d'utilisation

**Test rapide (1 entreprise) :**
```bash
python3 scripts/test_enrichment_debug.py --limit 1
```

**Test complet pour Genève (5 entreprises) :**
```bash
python3 scripts/test_enrichment_debug.py --city "Genève" --limit 5
```

**Test sans site web requis :**
```bash
python3 scripts/test_enrichment_debug.py --no-require-website --limit 3
```

## Ce que le script affiche

1. **Statut initial** : Configuration et paramètres
2. **Logs en temps réel** : Tous les logs du pipeline (identique à l'interface web)
3. **Statut périodique** : Mise à jour toutes les 2 secondes
4. **Résumé final** : 
   - Temps total d'exécution
   - Nombre d'entreprises traitées
   - Vérification dans la BDD
   - Dernières entreprises enrichies avec leurs données

## Avantages par rapport à l'interface web

- ✅ Logs complets dans le terminal (pas de limite de buffer)
- ✅ Pas de problème de connexion SSE
- ✅ Affichage direct des erreurs Python
- ✅ Vérification finale automatique dans la BDD
- ✅ Plus facile pour le debugging

## Dépannage

Si le script ne trouve pas la BDD :
```bash
# Vérifier le chemin par défaut
ls -la ~/maps-scraper/backend/companies.db

# Ou spécifier le chemin explicitement
python3 scripts/test_enrichment_debug.py --db ~/maps-scraper/backend/companies.db
```

Si les imports échouent :
```bash
# S'assurer d'être dans le bon répertoire et d'avoir activé le venv
cd ~/maps-scraper/osint-enricher
source venv/bin/activate
pip install -r requirements.txt
```


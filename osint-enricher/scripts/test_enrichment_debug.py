#!/usr/bin/env python3
"""
Script de test pour l'enrichissement OSINT avec logs détaillés
Usage: python3 test_enrichment_debug.py [--limit N] [--city VILLE]
"""

import os
import sys
import time
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from pipeline import OsintPipeline

# Chemin par défaut de la BDD
DEFAULT_DB = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "backend", "companies.db"
))

def print_status(status, prefix="📊"):
    """Affiche le statut de manière lisible"""
    print(f"\n{prefix} STATUT ACTUEL:")
    print(f"   Running: {status.get('running', False)}")
    print(f"   Processed: {status.get('processed', 0)}/{status.get('total', 0)}")
    print(f"   Message: {status.get('message', 'N/A')}")
    if status.get('current'):
        curr = status['current']
        print(f"   Current: ID={curr.get('id')}, Company={curr.get('company')}")
    if status.get('started_at'):
        print(f"   Started: {status.get('started_at')}")
    if status.get('finished_at'):
        print(f"   Finished: {status.get('finished_at')}")
    print()

def main():
    parser = argparse.ArgumentParser(description='Test enrichissement OSINT avec logs détaillés')
    parser.add_argument('--limit', type=int, default=2, help='Nombre d\'entreprises à enrichir (défaut: 2)')
    parser.add_argument('--city', type=str, default=None, help='Filtrer par ville')
    parser.add_argument('--require-website', action='store_true', default=True, help='Exiger un site web (défaut: True)')
    parser.add_argument('--no-require-website', dest='require_website', action='store_false', help='Ne pas exiger un site web')
    parser.add_argument('--db', type=str, default=None, help='Chemin vers la BDD (défaut: auto-détecté)')
    
    args = parser.parse_args()
    
    # Déterminer le chemin de la BDD
    db_path = args.db or os.getenv("DATABASE_PATH", DEFAULT_DB)
    
    if not os.path.exists(db_path):
        print(f"❌ ERREUR: Base de données introuvable: {db_path}")
        print(f"💡 Vérifiez le chemin ou utilisez --db pour spécifier la BDD")
        sys.exit(1)
    
    print("=" * 80)
    print("🧪 TEST ENRICHISSEMENT OSINT - MODE DEBUG")
    print("=" * 80)
    print(f"📁 BDD: {db_path}")
    print(f"📊 Paramètres:")
    print(f"   - Limit: {args.limit}")
    print(f"   - City: {args.city or 'Toutes'}")
    print(f"   - Require website: {args.require_website}")
    print("=" * 80)
    print()
    
    # Statut partagé pour suivre la progression
    status = {
        "running": False,
        "processed": 0,
        "total": 0,
        "current": None,
        "message": "Initialisation..."
    }
    
    # Flag d'arrêt
    stop_flag = False
    
    # Créer le pipeline
    print("🔧 Initialisation du pipeline...")
    try:
        pipeline = OsintPipeline(
            db_path=db_path,
            status_ref=status,
            stop_flag_ref=lambda: stop_flag,
            logs_queue_ref=None  # Pas de queue pour ce test, on utilise print directement
        )
        print("✅ Pipeline initialisé")
        print()
    except Exception as e:
        print(f"❌ ERREUR lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Afficher le statut initial
    print_status(status, "🚀")
    
    # Lancer l'enrichissement
    print("▶️  Démarrage de l'enrichissement...")
    print("=" * 80)
    print()
    
    start_time = time.time()
    
    try:
        # Lancer dans un thread pour pouvoir surveiller le statut
        import threading
        
        def run_pipeline():
            try:
                pipeline.run(
                    city=args.city,
                    limit=args.limit,
                    require_website=args.require_website
                )
            except Exception as e:
                print(f"\n❌ ERREUR dans le pipeline: {e}")
                import traceback
                traceback.print_exc()
                status["running"] = False
                status["message"] = f"Erreur: {str(e)[:100]}"
        
        thread = threading.Thread(target=run_pipeline, daemon=False)
        thread.start()
        
        # Surveiller le statut toutes les 2 secondes
        last_processed = -1
        while thread.is_alive():
            time.sleep(2)
            
            # Afficher le statut si quelque chose a changé
            if status.get("processed", 0) != last_processed:
                print_status(status, "🔄")
                last_processed = status.get("processed", 0)
            
            # Afficher un heartbeat toutes les 10 secondes
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(f"⏱️  Temps écoulé: {int(elapsed)}s | Processed: {status.get('processed', 0)}/{status.get('total', 0)}")
        
        # Attendre la fin du thread
        thread.join(timeout=1)
        
        elapsed = time.time() - start_time
        
        print()
        print("=" * 80)
        print("✅ ENRICHISSEMENT TERMINÉ")
        print("=" * 80)
        print_status(status, "📊 FINAL")
        print(f"⏱️  Temps total: {int(elapsed)}s ({elapsed/60:.1f} minutes)")
        print()
        
        # Vérifier le résultat final
        if status.get("processed", 0) == status.get("total", 0) and status.get("total", 0) > 0:
            print("✅ SUCCÈS: Toutes les entreprises ont été traitées")
        elif status.get("total", 0) == 0:
            print("⚠️  ATTENTION: Aucune entreprise trouvée avec ces filtres")
        else:
            print(f"⚠️  ATTENTION: Seulement {status.get('processed', 0)}/{status.get('total', 0)} entreprises traitées")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Arrêt demandé par l'utilisateur (Ctrl+C)")
        stop_flag = True
        status["message"] = "Arrêt demandé"
        print_status(status, "⏸️")
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("📋 Vérification finale dans la BDD...")
    print("=" * 80)
    
    # Vérifier les entreprises enrichies
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Compter les entreprises enrichies
        cur.execute("SELECT COUNT(*) FROM companies WHERE osint_status = 'Done'")
        done_count = cur.fetchone()[0]
        
        # Compter les entreprises avec emails OSINT
        cur.execute("SELECT COUNT(*) FROM companies WHERE emails_osint IS NOT NULL AND emails_osint != ''")
        emails_count = cur.fetchone()[0]
        
        # Afficher les dernières entreprises enrichies
        cur.execute("""
            SELECT id, company_name, osint_status, osint_updated_at, 
                   emails_osint, tech_stack
            FROM companies 
            WHERE osint_status = 'Done'
            ORDER BY osint_updated_at DESC
            LIMIT 5
        """)
        recent = cur.fetchall()
        
        print(f"✅ Entreprises enrichies (osint_status='Done'): {done_count}")
        print(f"📧 Entreprises avec emails OSINT: {emails_count}")
        print()
        print("📋 Dernières entreprises enrichies:")
        for row in recent:
            print(f"   ID {row[0]}: {row[1]}")
            print(f"      Status: {row[2]}")
            print(f"      Updated: {row[3]}")
            if row[4]:
                emails = row[4].split(',')[:3]  # Afficher max 3 emails
                print(f"      Emails: {', '.join(emails)}{'...' if len(row[4].split(',')) > 3 else ''}")
            if row[5]:
                print(f"      Tech: {row[5][:100]}...")
            print()
        
        conn.close()
    except Exception as e:
        print(f"⚠️  Erreur lors de la vérification BDD: {e}")
    
    print("=" * 80)
    print("✅ Test terminé")
    print("=" * 80)

if __name__ == "__main__":
    main()


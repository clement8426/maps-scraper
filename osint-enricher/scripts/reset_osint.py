#!/usr/bin/env python3
"""
Script pour réinitialiser tous les statuts OSINT et recommencer l'enrichissement
"""
import sqlite3
import sys

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../backend/companies.db"
    
    print(f"🔄 Réinitialisation des statuts OSINT : {db_path}")
    print("")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Compter les entrées actuelles
    cur.execute("SELECT COUNT(*) FROM companies WHERE osint_status = 'Done'")
    done_count = cur.fetchone()[0]
    
    print(f"📊 Statistiques actuelles :")
    print(f"   - Entrées enrichies (Done) : {done_count}")
    
    # Demander confirmation
    response = input("\n⚠️  Voulez-vous réinitialiser TOUS les statuts OSINT ? (oui/non) : ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Annulé")
        return
    
    # Réinitialiser les statuts et données OSINT
    cur.execute("""
        UPDATE companies 
        SET osint_status = NULL,
            osint_updated_at = NULL,
            tech_stack = NULL,
            emails_osint = NULL,
            pdf_emails = NULL,
            subdomains = NULL,
            whois_raw = NULL,
            wayback_urls = NULL
        WHERE osint_status IS NOT NULL
    """)
    
    conn.commit()
    affected = cur.rowcount
    conn.close()
    
    print(f"\n✅ {affected} entrées réinitialisées")
    print(f"✅ Vous pouvez maintenant relancer l'enrichissement depuis /enrich")
    print(f"\n💡 Les données du scraper principal (company_name, city, website, email) sont préservées.")

if __name__ == "__main__":
    main()


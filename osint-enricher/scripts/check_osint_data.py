#!/usr/bin/env python3
"""
Script pour vérifier les données OSINT dans la BDD
"""
import sqlite3
import sys
import os

def check_osint_data(db_path):
    """Vérifie les données OSINT dans la BDD"""
    print(f"🔍 Vérification de la BDD : {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Fichier introuvable : {db_path}")
        return
    
    print(f"✅ Fichier trouvé : {os.path.getsize(db_path)} octets")
    print("")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Vérifier les colonnes
    cur.execute("PRAGMA table_info(companies)")
    columns = [row[1] for row in cur.fetchall()]
    osint_cols = ['tech_stack', 'emails_osint', 'pdf_emails', 'subdomains', 'whois_raw', 'wayback_urls', 'osint_status', 'osint_updated_at']
    
    print("📋 Colonnes OSINT :")
    for col in osint_cols:
        if col in columns:
            print(f"  ✅ {col}")
        else:
            print(f"  ❌ {col} - MANQUANTE !")
    print("")
    
    # Statistiques
    cur.execute("SELECT COUNT(*) FROM companies")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM companies WHERE osint_status = 'Done'")
    enriched = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM companies WHERE tech_stack IS NOT NULL AND tech_stack != ''")
    with_tech = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM companies WHERE emails_osint IS NOT NULL AND emails_osint != ''")
    with_emails_osint = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM companies WHERE subdomains IS NOT NULL AND subdomains != ''")
    with_subdomains = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM companies WHERE wayback_urls IS NOT NULL AND wayback_urls != ''")
    with_wayback = cur.fetchone()[0]
    
    print("📊 Statistiques :")
    print(f"  Total d'entreprises : {total}")
    print(f"  Status 'Done' : {enriched}")
    print(f"  Avec tech_stack : {with_tech}")
    print(f"  Avec emails_osint : {with_emails_osint}")
    print(f"  Avec subdomains : {with_subdomains}")
    print(f"  Avec wayback_urls : {with_wayback}")
    print("")
    
    # Dernières mises à jour
    cur.execute("""
        SELECT company_name, osint_status, osint_updated_at, 
               LENGTH(tech_stack) as tech_len,
               LENGTH(emails_osint) as emails_len,
               LENGTH(subdomains) as subs_len,
               LENGTH(wayback_urls) as wayback_len
        FROM companies 
        WHERE osint_updated_at IS NOT NULL 
        ORDER BY osint_updated_at DESC 
        LIMIT 10
    """)
    rows = cur.fetchall()
    
    if rows:
        print("🕐 Dernières mises à jour OSINT :")
        for row in rows:
            name, status, updated, tech_len, emails_len, subs_len, wayback_len = row
            print(f"  • {name}")
            print(f"    Status: {status} | MAJ: {updated}")
            print(f"    Tech: {tech_len or 0} car | Emails: {emails_len or 0} car | Subs: {subs_len or 0} car | Wayback: {wayback_len or 0} car")
            print("")
    else:
        print("⚠️  Aucune mise à jour OSINT trouvée !")
    
    # Exemple de données
    cur.execute("""
        SELECT company_name, tech_stack, emails_osint, subdomains, wayback_urls
        FROM companies 
        WHERE tech_stack IS NOT NULL AND tech_stack != ''
        LIMIT 3
    """)
    rows = cur.fetchall()
    
    if rows:
        print("📄 Exemples de données OSINT :")
        for row in rows:
            name, tech, emails, subs, wayback = row
            print(f"\n  🏢 {name}")
            if tech:
                print(f"    Tech: {tech[:100]}{'...' if len(tech) > 100 else ''}")
            if emails:
                print(f"    Emails: {emails}")
            if subs:
                subs_list = subs.split(',')[:3]
                print(f"    Subs: {', '.join(subs_list)}{'...' if len(subs.split(',')) > 3 else ''}")
            if wayback:
                wayback_list = wayback.split(',')[:2]
                print(f"    Wayback: {', '.join(wayback_list)}{'...' if len(wayback.split(',')) > 2 else ''}")
    
    conn.close()

def main():
    # Détecter le chemin de la BDD
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Chemin par défaut
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, "..", "..", "backend", "companies.db")
        db_path = os.path.abspath(db_path)
    
    check_osint_data(db_path)

if __name__ == "__main__":
    main()


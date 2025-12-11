#!/usr/bin/env python3
"""
Script pour nettoyer les doublons dans wayback_urls
"""
import sqlite3
import sys

def clean_wayback_urls(urls_string):
    """Nettoie et déduplique les URLs Wayback"""
    if not urls_string:
        return None
    
    # Séparer par virgules
    urls = [u.strip() for u in urls_string.split(',') if u.strip()]
    
    if not urls:
        return None
    
    # Dédupliquer
    cleaned = []
    seen = set()
    
    for url in urls:
        # Normaliser (enlever trailing slash, minuscules)
        normalized = url.rstrip('/').lower()
        if normalized not in seen:
            seen.add(normalized)
            # Préférer https
            if url.startswith('https://'):
                cleaned.append(url.rstrip('/'))
            elif url.startswith('http://'):
                https_version = url.replace('http://', 'https://').rstrip('/')
                if https_version.lower() not in seen:
                    cleaned.append(https_version)
    
    # Limiter à 20 URLs uniques
    unique = list(dict.fromkeys(cleaned))[:20]
    
    return ", ".join(unique) if unique else None

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../backend/companies.db"
    
    print(f"🧹 Nettoyage des doublons Wayback URLs : {db_path}")
    print("")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Récupérer toutes les entrées avec wayback_urls
    cur.execute("SELECT id, company_name, wayback_urls FROM companies WHERE wayback_urls IS NOT NULL AND wayback_urls != ''")
    rows = cur.fetchall()
    
    print(f"Entrées à traiter : {len(rows)}")
    
    cleaned = 0
    for row_id, company_name, wayback_urls in rows:
        cleaned_urls = clean_wayback_urls(wayback_urls)
        if cleaned_urls != wayback_urls:
            print(f"  ✅ {company_name}: {len(wayback_urls.split(','))} → {len(cleaned_urls.split(','))} URLs")
            cur.execute("UPDATE companies SET wayback_urls = ? WHERE id = ?", (cleaned_urls, row_id))
            cleaned += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ {cleaned}/{len(rows)} entrées nettoyées")

if __name__ == "__main__":
    main()


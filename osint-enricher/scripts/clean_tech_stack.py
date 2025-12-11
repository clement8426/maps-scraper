#!/usr/bin/env python3
"""
Script pour nettoyer et formater les tech_stack de manière plus lisible
"""
import sqlite3
import re
import sys

def clean_tech_stack(text):
    """Nettoie et formate tech_stack pour le rendre plus lisible"""
    if not text:
        return text
    
    # Supprimer les codes ANSI
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    cleaned = ansi_escape.sub('', text)
    
    # Supprimer les URLs répétées et les status HTTP redondants
    lines = cleaned.split(';')
    unique_info = []
    seen_urls = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Extraire l'URL
        url_match = re.match(r'^(https?://[^\s]+)\s+\[', line)
        if url_match:
            url = url_match.group(1)
            if url in seen_urls:
                continue  # Skip duplicate URLs
            seen_urls.add(url)
        
        # Nettoyer les informations inutiles
        # Garder seulement les infos importantes
        important_parts = []
        
        # Extraire le serveur web
        if 'HTTPServer' in line:
            server = re.search(r'HTTPServer\[([^\]]+)\]', line)
            if server:
                important_parts.append(f"Server: {server.group(1)}")
        
        # Extraire les technologies
        if 'WordPress' in line:
            important_parts.append('WordPress')
        if 'JQuery' in line:
            jquery = re.search(r'JQuery\[([^\]]+)\]', line)
            if jquery:
                important_parts.append(f"jQuery {jquery.group(1)}")
        
        # Frameworks et CMS
        for tech in ['React', 'Vue', 'Angular', 'Drupal', 'Joomla', 'Magento', 'Shopify']:
            if tech in line:
                important_parts.append(tech)
        
        # IP et pays
        if 'IP[' in line:
            ip = re.search(r'IP\[([^\]]+)\]', line)
            if ip:
                important_parts.append(f"IP: {ip.group(1)}")
        
        if 'Country' in line:
            country = re.search(r'Country\[([^\]]+)\]\[([^\]]+)\]', line)
            if country:
                important_parts.append(f"Pays: {country.group(2)}")
        
        if important_parts:
            unique_info.append(' | '.join(important_parts))
    
    # Joindre et limiter la longueur
    result = ' • '.join(unique_info[:3])  # Max 3 entrées
    return result[:500] if result else None

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../backend/companies.db"
    
    print(f"Nettoyage avancé de tech_stack : {db_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Récupérer toutes les entrées avec tech_stack
    cur.execute("SELECT id, company_name, tech_stack FROM companies WHERE tech_stack IS NOT NULL AND tech_stack != ''")
    rows = cur.fetchall()
    
    print(f"Entrées à traiter : {len(rows)}")
    
    cleaned = 0
    for row_id, company_name, tech_stack in rows:
        cleaned_stack = clean_tech_stack(tech_stack)
        if cleaned_stack != tech_stack:
            print(f"  ✅ {company_name}: {cleaned_stack[:80]}...")
            cur.execute("UPDATE companies SET tech_stack = ? WHERE id = ?", (cleaned_stack, row_id))
            cleaned += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ {cleaned}/{len(rows)} entrées nettoyées et formatées")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Script pour nettoyer les codes ANSI dans la colonne tech_stack
"""
import sqlite3
import re
import sys

def clean_ansi_codes(text):
    """Supprime les codes ANSI d'une chaîne"""
    if not text:
        return text
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../backend/companies.db"
    
    print(f"Nettoyage de la base de données : {db_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Compter les entrées avec codes ANSI
    cur.execute("SELECT COUNT(*) FROM companies WHERE tech_stack LIKE '%[0m%' OR tech_stack LIKE '%[1m%'")
    dirty_count = cur.fetchone()[0]
    print(f"Entrées à nettoyer : {dirty_count}")
    
    if dirty_count == 0:
        print("Rien à nettoyer !")
        return
    
    # Récupérer toutes les entrées avec tech_stack
    cur.execute("SELECT id, tech_stack FROM companies WHERE tech_stack IS NOT NULL AND tech_stack != ''")
    rows = cur.fetchall()
    
    cleaned = 0
    for row_id, tech_stack in rows:
        cleaned_stack = clean_ansi_codes(tech_stack)
        if cleaned_stack != tech_stack:
            # Limiter à 500 caractères
            cleaned_stack = cleaned_stack[:500]
            cur.execute("UPDATE companies SET tech_stack = ? WHERE id = ?", (cleaned_stack, row_id))
            cleaned += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ {cleaned} entrées nettoyées")

if __name__ == "__main__":
    main()


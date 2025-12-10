#!/usr/bin/env python3
"""
Script pour changer le mot de passe admin
Usage: python3 change_password.py <nouveau_mot_de_passe>
"""

import sys
import os
from werkzeug.security import generate_password_hash

def change_password(new_password, username="admin"):
    """Génère un hash pour le nouveau mot de passe"""
    password_hash = generate_password_hash(new_password)
    
    print(f"✅ Hash généré pour l'utilisateur '{username}':")
    print(f"   {password_hash}")
    print()
    print("📝 Pour changer le mot de passe sur le VPS:")
    print("   1. Éditez le fichier .env:")
    print("      nano ~/maps-scraper/.env")
    print()
    print(f"   2. Remplacez WEB_PASSWORD par:")
    print(f"      WEB_PASSWORD={new_password}")
    print()
    print("   3. Redémarrez le service:")
    print("      sudo systemctl restart scraper-web")
    print()
    print("⚠️  OU utilisez directement ce hash dans le code (non recommandé):")
    print(f"   {username}: {password_hash}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python3 change_password.py <nouveau_mot_de_passe>")
        print()
        print("Exemple:")
        print("  python3 change_password.py MonNouveauMotDePasse123!")
        sys.exit(1)
    
    new_password = sys.argv[1]
    
    if len(new_password) < 8:
        print("⚠️  Attention: Le mot de passe fait moins de 8 caractères.")
        response = input("Continuer quand même? (o/N): ")
        if response.lower() != 'o':
            print("❌ Annulé.")
            sys.exit(1)
    
    change_password(new_password)


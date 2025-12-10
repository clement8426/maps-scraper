"""
Script de vérification DNS pour valider les emails avant envoi
Vérifie que les domaines ont des records MX valides
"""

import pandas as pd
import dns.resolver
import socket
from urllib.parse import urlparse
import time
import os

def extract_domain_from_email(email):
    """Extrait le domaine d'un email"""
    if not email or pd.isna(email):
        return None
    if '@' in str(email):
        return str(email).split('@')[1].strip()
    return None

def check_mx_record(domain):
    """Vérifie si le domaine a des records MX valides"""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return len(mx_records) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return False
    except Exception as e:
        print(f"  ⚠️  Erreur DNS pour {domain}: {e}")
        return False

def verify_emails_in_csv(csv_file, output_file=None):
    """
    Vérifie les emails dans le CSV et ajoute une colonne 'Email_Valid'
    
    Args:
        csv_file: Chemin vers le CSV d'entrée
        output_file: Chemin vers le CSV de sortie (optionnel, remplace l'entrée si None)
    """
    print("=" * 60)
    print("🔍 VÉRIFICATION DNS DES EMAILS")
    print("=" * 60)
    
    df = pd.read_csv(csv_file)
    
    if 'Email' not in df.columns:
        print("❌ Colonne 'Email' introuvable dans le CSV")
        return
    
    print(f"📊 {len(df)} lignes à vérifier\n")
    
    email_valid = []
    domains_checked = {}  # Cache pour éviter de vérifier plusieurs fois le même domaine
    
    for index, row in df.iterrows():
        email = row.get('Email')
        
        if pd.isna(email) or not email:
            email_valid.append(False)
            continue
        
        # Gérer les emails multiples (séparés par virgule)
        emails_list = [e.strip() for e in str(email).split(',')]
        valid_emails = []
        
        for e in emails_list:
            domain = extract_domain_from_email(e)
            
            if not domain:
                continue
            
            # Utiliser le cache
            if domain in domains_checked:
                is_valid = domains_checked[domain]
            else:
                is_valid = check_mx_record(domain)
                domains_checked[domain] = is_valid
                time.sleep(0.1)  # Pause pour ne pas surcharger les serveurs DNS
            
            if is_valid:
                valid_emails.append(e)
        
        email_valid.append(len(valid_emails) > 0)
        
        if (index + 1) % 10 == 0:
            print(f"  ✅ {index + 1}/{len(df)} vérifiés...")
    
    df['Email_Valid'] = email_valid
    
    # Statistiques
    total_valid = sum(email_valid)
    print(f"\n📊 Résultats:")
    print(f"   ✅ Emails valides: {total_valid}/{len(df)} ({total_valid/len(df)*100:.1f}%)")
    print(f"   ❌ Emails invalides: {len(df) - total_valid}")
    
    # Sauvegarde
    output = output_file if output_file else csv_file
    df.to_csv(output, index=False)
    print(f"\n💾 Fichier sauvegardé: {output}")
    
    # Afficher les domaines invalides pour debug
    invalid_domains = set()
    for index, row in df.iterrows():
        if not email_valid[index] and pd.notna(row.get('Email')):
            email = str(row.get('Email'))
            for e in email.split(','):
                domain = extract_domain_from_email(e)
                if domain and domain not in domains_checked.get(domain, True):
                    invalid_domains.add(domain)
    
    if invalid_domains:
        print(f"\n⚠️  Domaines sans MX valide: {', '.join(sorted(invalid_domains))}")

if __name__ == "__main__":
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else "base_tech_suisse.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"❌ Fichier introuvable: {input_file}")
        sys.exit(1)
    
    verify_emails_in_csv(input_file, output_file)


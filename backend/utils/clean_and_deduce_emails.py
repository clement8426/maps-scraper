"""
Script de nettoyage et déduction d'emails
- Nettoie les données du CSV
- Tente de déduire des emails à partir des domaines trouvés
- Filtre les emails génériques
"""

import pandas as pd
import re
from urllib.parse import urlparse

def extract_domain_from_url(url):
    """Extrait le domaine d'une URL"""
    if not url or pd.isna(url):
        return None
    try:
        parsed = urlparse(str(url))
        domain = parsed.netloc or parsed.path
        # Enlever www.
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None

def is_generic_email(email):
    """Vérifie si l'email est générique (info@, contact@, etc.)"""
    if not email:
        return True
    
    generic_patterns = [
        r'^info@',
        r'^contact@',
        r'^admin@',
        r'^hello@',
        r'^support@',
        r'^noreply@',
        r'^no-reply@',
        r'^sales@',
        r'^marketing@',
        r'^webmaster@',
        r'^postmaster@',
        r'^abuse@',
        r'^privacy@',
        r'^legal@'
    ]
    
    email_lower = str(email).lower()
    return any(re.match(pattern, email_lower) for pattern in generic_patterns)

def clean_company_name(name):
    """Nettoie le nom de l'entreprise pour déduire un email"""
    if not name or pd.isna(name):
        return None
    
    # Enlever les caractères spéciaux
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
    # Enlever les mots communs
    stop_words = ['sarl', 'sa', 'gmbh', 'ltd', 'inc', 'llc', 'ag', 'sàrl']
    words = cleaned.lower().split()
    words = [w for w in words if w not in stop_words]
    
    return ' '.join(words)

def deduce_possible_emails(company_name, domain):
    """Déduit des emails possibles à partir du nom de l'entreprise et du domaine"""
    if not domain:
        return []
    
    possible_emails = []
    cleaned_name = clean_company_name(company_name)
    
    if not cleaned_name:
        return []
    
    # Formats courants
    formats = [
        # Format simple: nom@domaine
        cleaned_name.replace(' ', '').lower(),
        # Format avec tirets: nom-entreprise@domaine
        cleaned_name.replace(' ', '-').lower(),
        # Format avec points: nom.entreprise@domaine
        cleaned_name.replace(' ', '.').lower(),
        # Première lettre de chaque mot
        ''.join([w[0] for w in cleaned_name.split() if w]).lower(),
    ]
    
    for fmt in formats:
        if fmt:
            email = f"{fmt}@{domain}"
            possible_emails.append(email)
    
    return list(set(possible_emails))  # Dédupliquer

def clean_and_enrich_csv(csv_file, output_file=None):
    """
    Nettoie et enrichit le CSV
    
    Args:
        csv_file: Chemin vers le CSV d'entrée
        output_file: Chemin vers le CSV de sortie (optionnel)
    """
    print("=" * 60)
    print("🧹 NETTOYAGE ET ENRICHISSEMENT DES DONNÉES")
    print("=" * 60)
    
    df = pd.read_csv(csv_file)
    
    print(f"📊 Lignes initiales: {len(df)}\n")
    
    # 1. Nettoyer les URLs de sites web
    if 'Website' in df.columns:
        print("🌐 Nettoyage des URLs...")
        df['Domain'] = df['Website'].apply(extract_domain_from_url)
        print(f"   ✅ Domaines extraits: {df['Domain'].notna().sum()}")
    
    # 2. Identifier les emails génériques
    if 'Email' in df.columns:
        print("\n📧 Analyse des emails...")
        df['Is_Generic_Email'] = df['Email'].apply(is_generic_email)
        generic_count = df['Is_Generic_Email'].sum()
        print(f"   ⚠️  Emails génériques: {generic_count}/{df['Email'].notna().sum()}")
    
    # 3. Déduire des emails possibles pour les entreprises sans email
    if 'Domain' in df.columns and 'Company' in df.columns:
        print("\n🔮 Déduction d'emails possibles...")
        deduced_emails = []
        
        for index, row in df.iterrows():
            if pd.isna(row.get('Email')) and pd.notna(row.get('Domain')):
                possible = deduce_possible_emails(row.get('Company'), row.get('Domain'))
                deduced_emails.append(', '.join(possible) if possible else None)
            else:
                deduced_emails.append(None)
        
        df['Deduced_Emails'] = deduced_emails
        deduced_count = df['Deduced_Emails'].notna().sum()
        print(f"   💡 Emails déduits: {deduced_count}")
    
    # 4. Filtrer les lignes sans site web ni email
    print("\n🗑️  Filtrage des lignes incomplètes...")
    initial_count = len(df)
    
    # Garder seulement les lignes avec au moins un site web OU un email
    df_filtered = df[
        df['Website'].notna() | 
        df['Email'].notna() | 
        df['Deduced_Emails'].notna()
    ].copy()
    
    removed = initial_count - len(df_filtered)
    print(f"   ✅ Lignes conservées: {len(df_filtered)}")
    print(f"   ❌ Lignes supprimées: {removed}")
    
    # 5. Statistiques finales
    print("\n" + "=" * 60)
    print("📊 STATISTIQUES FINALES")
    print("=" * 60)
    print(f"   Total entreprises: {len(df_filtered)}")
    print(f"   Avec site web: {df_filtered['Website'].notna().sum()}")
    print(f"   Avec email: {df_filtered['Email'].notna().sum()}")
    print(f"   Avec email déduit: {df_filtered['Deduced_Emails'].notna().sum()}")
    print(f"   Emails génériques: {df_filtered['Is_Generic_Email'].sum()}")
    
    # Sauvegarde
    output = output_file if output_file else csv_file.replace('.csv', '_cleaned.csv')
    df_filtered.to_csv(output, index=False)
    print(f"\n💾 Fichier sauvegardé: {output}")
    
    return df_filtered

if __name__ == "__main__":
    import sys
    import os
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else "base_tech_suisse.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ Fichier introuvable: {input_file}")
        sys.exit(1)
    
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    clean_and_enrich_csv(input_file, output_file)



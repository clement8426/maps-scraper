"""
Test de la fonction d'enrichissement seule
"""

from scraper_suisse_romande import enrich_maps_details
from playwright.sync_api import sync_playwright
import time

def test_enrichment():
    """Test l'enrichissement d'une seule fiche"""
    test_url = "https://www.google.com/maps/place/Agence+Web+Gen%C3%A8ve+%E2%AD%90+Cr%C3%A9ation+de+site+web,+SEO+%26+marketing+digital/data=!4m7!3m6!1s0xa0474ce3f342f843:0xd847038d59573114!8m2!3d46.1905111!4d6.1387503!16s%2Fg%2F11rvfz06qx!19sChIJQ_hC8-NMR6ARFDFXWY0DR9g?authuser=0&hl=fr&rclk=1"
    
    print("=" * 60)
    print("🧪 TEST DE L'ENRICHISSEMENT")
    print("=" * 60)
    print(f"\nURL test: {test_url}\n")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='fr-CH',
            timezone_id='Europe/Zurich'
        )
        page = context.new_page()
        
        print("📍 Appel de enrich_maps_details()...\n")
        
        details = enrich_maps_details(page, test_url)
        
        print("📊 RÉSULTATS:")
        print("=" * 60)
        print(f"📍 Adresse: {details.get('Address') or '❌ Non trouvée'}")
        print(f"📞 Téléphone: {details.get('Phone') or '❌ Non trouvé'}")
        print(f"🌐 Site web: {details.get('Website') or '❌ Non trouvé'}")
        print(f"⭐ Note: {details.get('Rating') or '❌ Non trouvée'}")
        print(f"💬 Avis: {details.get('Reviews_Count') or '❌ Non trouvé'}")
        print(f"🕐 Horaires: {details.get('Opening_Hours') or '❌ Non trouvés'}")
        print("=" * 60)
        
        # Vérifier ce qui a été trouvé
        found = sum(1 for v in details.values() if v)
        print(f"\n✅ {found}/6 informations trouvées")
        
        browser.close()
        
        if found == 0:
            print("\n⚠️  Aucune information trouvée - il y a un problème avec l'extraction")
        elif found < 3:
            print(f"\n⚠️  Seulement {found} informations trouvées - l'extraction peut être améliorée")
        else:
            print(f"\n✅ {found} informations trouvées - l'extraction fonctionne !")

if __name__ == "__main__":
    test_enrichment()


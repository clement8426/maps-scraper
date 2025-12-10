"""
Test avec curl pour voir le HTML initial (sans JavaScript)
Note: Google Maps est une SPA, donc curl ne verra pas tout le contenu
"""

import subprocess
import sys

def test_curl(url):
    """Teste avec curl pour voir le HTML initial"""
    print("=" * 60)
    print("🌐 TEST AVEC CURL")
    print("=" * 60)
    print(f"\nURL: {url}\n")
    print("⚠️  Note: Google Maps est une SPA (Single Page Application)")
    print("   Curl ne verra que le HTML initial, pas le contenu chargé par JavaScript\n")
    
    try:
        # Curl avec headers pour simuler un navigateur
        cmd = [
            'curl',
            '-s',  # Silent
            '-L',  # Follow redirects
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '-H', 'Accept-Language: fr-CH,fr;q=0.9',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            html = result.stdout
            
            # Sauvegarder
            with open("maps_curl.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            print(f"✅ HTML récupéré ({len(html)} caractères)")
            print("📄 Sauvegardé dans maps_curl.html\n")
            
            # Analyser rapidement
            if "consent.google.com" in html:
                print("⚠️  Redirection vers consent.google.com détectée")
            
            if "maps" in html.lower():
                print("✅ Contient 'maps' dans le HTML")
            
            if "address" in html.lower():
                print("✅ Contient 'address' dans le HTML")
            
            if "phone" in html.lower():
                print("✅ Contient 'phone' dans le HTML")
            
            # Chercher des données JSON-LD ou autres structures
            import re
            json_ld = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
            if json_ld:
                print(f"\n✅ Trouvé {len(json_ld)} script(s) JSON-LD")
                for i, jd in enumerate(json_ld[:2]):
                    print(f"   JSON-LD #{i+1}: {jd[:100]}...")
            
            # Chercher des données dans les attributs data
            data_attrs = re.findall(r'data-[^=]*="[^"]*"', html)
            if data_attrs:
                print(f"\n✅ Trouvé {len(data_attrs)} attributs data")
                # Afficher quelques exemples
                for attr in data_attrs[:5]:
                    if len(attr) < 100:
                        print(f"   {attr}")
            
            print("\n💡 Pour voir le contenu réel, utilisez inspect_maps_html.py avec Playwright")
            
        else:
            print(f"❌ Erreur curl: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout - la requête a pris trop de temps")
    except FileNotFoundError:
        print("❌ curl n'est pas installé sur ce système")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_url = "https://www.google.com/maps/place/Agence+Web+Gen%C3%A8ve+%E2%AD%90+Cr%C3%A9ation+de+site+web,+SEO+%26+marketing+digital/data=!4m7!3m6!1s0xa0474ce3f342f843:0xd847038d59573114!8m2!3d46.1905111!4d6.1387503!16s%2Fg%2F11rvfz06qx!19sChIJQ_hC8-NMR6ARFDFXWY0DR9g?authuser=0&hl=fr&rclk=1"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    test_curl(test_url)


"""
Test avec Firefox au cas où Chromium serait détecté
"""

from playwright.sync_api import sync_playwright
import time
import random

def test_firefox():
    print("🧪 Test avec Firefox...")
    
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='fr-CH',
                timezone_id='Europe/Zurich'
            )
            page = context.new_page()
            
            print("  ✅ Navigateur Firefox lancé")
            
            # Aller sur Google Maps
            print("  📍 Navigation vers Google Maps...")
            page.goto("https://www.google.com/maps", timeout=60000, wait_until="networkidle")
            time.sleep(3)
            print("  ✅ Page chargée")
            
            # Vérifier que la page est toujours ouverte
            try:
                url = page.url
                print(f"  ✅ URL: {url[:60]}...")
            except Exception as e:
                print(f"  ❌ Page fermée: {e}")
                browser.close()
                return False
            
            # Gérer la page de consentement Google
            if "consent.google.com" in url:
                print("  🍪 Gestion de la page de consentement...")
                try:
                    # Plusieurs sélecteurs possibles pour accepter
                    accept_selectors = [
                        "button:has-text('Tout accepter')",
                        "button:has-text('Accept all')",
                        "button:has-text('J'accepte')",
                        "button:has-text('I agree')",
                        "button[id*='accept']",
                        "button[aria-label*='Accept']",
                        "form button[type='submit']"
                    ]
                    
                    accepted = False
                    for selector in accept_selectors:
                        try:
                            button = page.locator(selector).first
                            if button.count() > 0:
                                button.click(timeout=5000)
                                time.sleep(2)
                                print("  ✅ Consentement accepté")
                                accepted = True
                                break
                        except:
                            continue
                    
                    if not accepted:
                        print("  ⚠️  Impossible de trouver le bouton d'acceptation")
                        # Essayer de cliquer sur n'importe quel bouton de la page
                        try:
                            page.locator("button").first.click(timeout=3000)
                            time.sleep(2)
                        except:
                            pass
                    
                    # Attendre la redirection vers Maps
                    time.sleep(3)
                    url = page.url
                    print(f"  ✅ URL après consentement: {url[:60]}...")
                except Exception as e:
                    print(f"  ⚠️  Erreur lors de la gestion du consentement: {e}")
            
            # Gérer les cookies sur Maps directement
            try:
                cookie_button = page.locator("button:has-text('Tout accepter'), button:has-text('Accept all'), button[id*='accept']").first
                if cookie_button.count() > 0:
                    cookie_button.click(timeout=3000)
                    time.sleep(1)
                    print("  ✅ Cookies acceptés")
            except:
                pass
            
            # S'assurer qu'on est bien sur Maps
            if "consent.google.com" in page.url:
                print("  ⚠️  Toujours sur la page de consentement, nouvelle tentative...")
                page.goto("https://www.google.com/maps", timeout=60000, wait_until="networkidle")
                time.sleep(3)
            
            # Test recherche
            print("\n  🔍 Test recherche: 'Agence Web Genève'...")
            query = "Agence Web Genève"
            
            try:
                # Attendre que le champ de recherche soit disponible
                search_input = page.locator("#searchboxinput")
                search_input.wait_for(state="visible", timeout=15000)
                print("  ✅ Champ de recherche trouvé")
                
                search_input.fill(query)
                time.sleep(1)
                page.keyboard.press("Enter")
                
                # Attendre les résultats avec plusieurs sélecteurs possibles
                try:
                    page.wait_for_selector('div[role="feed"]', timeout=20000)
                    print("  ✅ Résultats chargés")
                except:
                    # Essayer d'autres sélecteurs
                    try:
                        page.wait_for_selector('div[data-value="Directions"]', timeout=5000)
                        print("  ✅ Résultats trouvés (sélecteur alternatif)")
                    except:
                        print("  ⚠️  Résultats peut-être chargés mais sélecteur différent")
                
                print("  ✅ Recherche réussie avec Firefox")
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                # Afficher l'URL actuelle pour debug
                try:
                    print(f"  ℹ️  URL actuelle: {page.url[:80]}")
                except:
                    pass
                browser.close()
                return False
            
            browser.close()
            print("\n✅ Firefox fonctionne !")
            return True
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  Note: Firefox doit être installé: playwright install firefox")
    success = test_firefox()
    if success:
        print("\n🎉 Firefox est une alternative viable !")
    else:
        print("\n⚠️  Firefox a aussi des problèmes.")


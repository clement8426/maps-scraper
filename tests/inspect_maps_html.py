"""
Script pour inspecter le HTML réel d'une fiche Google Maps
et identifier la structure exacte pour l'extraction
"""

from playwright.sync_api import sync_playwright
import time
import json

def inspect_maps_page(maps_url):
    """Inspecte une fiche Google Maps et sauvegarde le HTML"""
    print(f"🔍 Inspection de: {maps_url}\n")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='fr-CH',
            timezone_id='Europe/Zurich'
        )
        page = context.new_page()
        
        try:
            # Aller sur la page
            print("📍 Navigation vers la fiche Maps...")
            page.goto(maps_url, timeout=30000, wait_until="networkidle")
            time.sleep(3)
            
            # Gérer le consentement
            if "consent.google.com" in page.url:
                print("🍪 Gestion du consentement...")
                try:
                    button = page.locator("button:has-text('Tout accepter'), button:has-text('Accept all')").first
                    if button.count() > 0:
                        button.click(timeout=3000)
                        time.sleep(2)
                        page.goto(maps_url, timeout=30000, wait_until="networkidle")
                        time.sleep(3)
                except:
                    pass
            
            # Sauvegarder le HTML complet
            html_content = page.content()
            with open("maps_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("✅ HTML sauvegardé dans maps_page.html")
            
            # Extraire le texte visible
            try:
                body_text = page.locator('body').inner_text()
                with open("maps_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(body_text)
                print("✅ Texte visible sauvegardé dans maps_page_text.txt")
            except:
                pass
            
            # Chercher des éléments spécifiques avec plusieurs méthodes
            print("\n🔎 Recherche d'informations...\n")
            
            # 1. ADRESSE
            print("📍 ADRESSE:")
            address_found = False
            address_selectors = [
                'button[data-item-id="address"]',
                '[data-item-id="address"]',
                'button[data-value="Address"]',
                'a[href*="maps/dir"]',
            ]
            
            for selector in address_selectors:
                try:
                    elems = page.locator(selector).all()
                    for i, elem in enumerate(elems[:3]):  # Limiter à 3
                        try:
                            text = elem.inner_text()
                            aria = elem.get_attribute("aria-label") or ""
                            href = elem.get_attribute("href") or ""
                            if text and len(text) > 5:
                                print(f"  [{selector}] #{i}: {text[:80]}")
                                if 'Rue' in text or 'Avenue' in text or 'Genève' in text:
                                    print(f"    ⭐ POTENTIEL: {text}")
                                    address_found = True
                        except:
                            pass
                except:
                    pass
            
            if not address_found:
                print("  ⚠️  Aucune adresse trouvée avec les sélecteurs")
            
            # 2. TÉLÉPHONE
            print("\n📞 TÉLÉPHONE:")
            phone_found = False
            phone_selectors = [
                'a[href^="tel:"]',
                'button[data-item-id*="phone"]',
                '[data-item-id*="phone"]',
            ]
            
            for selector in phone_selectors:
                try:
                    elems = page.locator(selector).all()
                    for i, elem in enumerate(elems[:3]):
                        try:
                            text = elem.inner_text()
                            href = elem.get_attribute("href") or ""
                            if href.startswith("tel:"):
                                print(f"  [{selector}] #{i}: {href}")
                                phone_found = True
                            elif text and ('+41' in text or '022' in text):
                                print(f"  [{selector}] #{i}: {text[:50]}")
                                phone_found = True
                        except:
                            pass
                except:
                    pass
            
            if not phone_found:
                print("  ⚠️  Aucun téléphone trouvé avec les sélecteurs")
            
            # 3. SITE WEB
            print("\n🌐 SITE WEB:")
            website_found = False
            website_selectors = [
                'a[data-item-id="authority"]',
                'a[href^="http"]:has-text("Site web")',
                'a[href^="http"]:has-text("Website")',
            ]
            
            for selector in website_selectors:
                try:
                    elems = page.locator(selector).all()
                    for i, elem in enumerate(elems[:5]):
                        try:
                            href = elem.get_attribute("href") or ""
                            text = elem.inner_text()
                            if href and href.startswith("http") and "google.com" not in href:
                                print(f"  [{selector}] #{i}: {href}")
                                print(f"    Texte: {text[:50]}")
                                website_found = True
                        except:
                            pass
                except:
                    pass
            
            if not website_found:
                print("  ⚠️  Aucun site web trouvé avec les sélecteurs")
            
            # 4. NOTE
            print("\n⭐ NOTE:")
            rating_found = False
            rating_selectors = [
                'span[aria-label*="étoiles"]',
                'span[aria-label*="stars"]',
                'div[aria-label*="étoiles"]',
            ]
            
            for selector in rating_selectors:
                try:
                    elems = page.locator(selector).all()
                    for i, elem in enumerate(elems[:3]):
                        try:
                            aria = elem.get_attribute("aria-label") or ""
                            text = elem.inner_text()
                            if aria:
                                print(f"  [{selector}] #{i}: aria-label = {aria[:80]}")
                                rating_found = True
                            elif text:
                                print(f"  [{selector}] #{i}: text = {text[:50]}")
                        except:
                            pass
                except:
                    pass
            
            if not rating_found:
                print("  ⚠️  Aucune note trouvée avec les sélecteurs")
            
            # 5. AVIS
            print("\n💬 AVIS:")
            reviews_found = False
            reviews_selectors = [
                'button[data-value="Reviews"]',
                'span:has-text("avis")',
                'span:has-text("reviews")',
            ]
            
            for selector in reviews_selectors:
                try:
                    elems = page.locator(selector).all()
                    for i, elem in enumerate(elems[:3]):
                        try:
                            text = elem.inner_text()
                            if text and ('avis' in text.lower() or 'review' in text.lower()):
                                print(f"  [{selector}] #{i}: {text[:50]}")
                                reviews_found = True
                        except:
                            pass
                except:
                    pass
            
            if not reviews_found:
                print("  ⚠️  Aucun avis trouvé avec les sélecteurs")
            
            # 6. HORAIRES
            print("\n🕐 HORAIRES:")
            hours_found = False
            hours_selectors = [
                'div[data-value="Hours"]',
                'button[data-value="Hours"]',
                'div:has-text("Ouvert")',
            ]
            
            for selector in hours_selectors:
                try:
                    elems = page.locator(selector).all()
                    for i, elem in enumerate(elems[:3]):
                        try:
                            text = elem.inner_text()
                            if text and ('Ouvert' in text or 'Fermé' in text or 'lundi' in text.lower()):
                                print(f"  [{selector}] #{i}: {text[:100]}")
                                hours_found = True
                        except:
                            pass
                except:
                    pass
            
            if not hours_found:
                print("  ⚠️  Aucun horaire trouvé avec les sélecteurs")
            
            # Analyser le texte de la page pour trouver des patterns
            print("\n🔍 ANALYSE DU TEXTE (patterns):")
            body_text = page.locator('body').inner_text()
            
            # Chercher adresse
            import re
            address_pattern = r'Rue\s+[A-Za-zÀ-ÿ\s]+\s+\d+[,\s]+\d{4}\s+Genève'
            match = re.search(address_pattern, body_text, re.IGNORECASE)
            if match:
                print(f"  📍 Adresse trouvée: {match.group(0)}")
            
            # Chercher téléphone
            phone_pattern = r'\+41\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}'
            match = re.search(phone_pattern, body_text)
            if match:
                print(f"  📞 Téléphone trouvé: {match.group(0)}")
            
            # Chercher note
            rating_pattern = r'(\d+[.,]\d+)\s*(?:étoiles|stars)'
            match = re.search(rating_pattern, body_text, re.IGNORECASE)
            if match:
                print(f"  ⭐ Note trouvée: {match.group(1)}")
            
            # Chercher avis
            reviews_pattern = r'(\d+[\s,.]?\d*)\s*(?:avis|reviews)'
            match = re.search(reviews_pattern, body_text, re.IGNORECASE)
            if match:
                print(f"  💬 Avis trouvés: {match.group(1)}")
            
            browser.close()
            print("\n✅ Inspection terminée!")
            print("📄 Fichiers créés:")
            print("   - maps_page.html (HTML complet)")
            print("   - maps_page_text.txt (Texte visible)")
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            browser.close()

if __name__ == "__main__":
    # Utiliser une URL du CSV
    test_url = "https://www.google.com/maps/place/Agence+Web+Gen%C3%A8ve+%E2%AD%90+Cr%C3%A9ation+de+site+web,+SEO+%26+marketing+digital/data=!4m7!3m6!1s0xa0474ce3f342f843:0xd847038d59573114!8m2!3d46.1905111!4d6.1387503!16s%2Fg%2F11rvfz06qx!19sChIJQ_hC8-NMR6ARFDFXWY0DR9g?authuser=0&hl=fr&rclk=1"
    
    print("=" * 60)
    print("🔍 INSPECTION D'UNE FICHE GOOGLE MAPS")
    print("=" * 60)
    print()
    
    inspect_maps_page(test_url)


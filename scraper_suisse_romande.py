"""
Scraper Google Maps pour entreprises tech en Suisse Romande
Mode "Guérilla" - Sans API payante
"""

import time
import re
import random
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
CITIES = [
    "Genève", "Lausanne", "Yverdon-les-Bains", "Neuchâtel", 
    "Fribourg", "Sion", "Nyon", "Renens", "La Chaux-de-Fonds", 
    "Meyrin", "Plan-les-Ouates", "Martigny"
]

KEYWORDS = [
    "Agence Web", "Développement logiciel", "Conception de sites web", 
    "Full Stack", "Éditeur de logiciels", "Startup", "SaaS company", 
    "App development", "Cybersécurité", "Sécurité informatique", 
    "Consultant informatique", "Services informatiques entreprises", 
    "Cloud provider"
]

OUTPUT_FILE = "base_tech_suisse.csv"
CHECKPOINT_FILE = "checkpoint.json"
INTERMEDIATE_FILE = "intermediate_data.csv"

# Navigateur à utiliser: "chromium" ou "firefox"
# Firefox semble mieux fonctionner avec Google Maps
BROWSER_TYPE = "firefox"  # Changez en "chromium" si vous préférez

# Délais aléatoires pour simuler un humain
MIN_DELAY = 1.5
MAX_DELAY = 4.0
MIN_PAGE_DELAY = 0.5
MAX_PAGE_DELAY = 2.0

# User agents rotatifs
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def random_delay(min_sec=MIN_DELAY, max_sec=MAX_DELAY):
    """Délai aléatoire pour simuler un comportement humain"""
    time.sleep(random.uniform(min_sec, max_sec))

def load_checkpoint():
    """Charge le checkpoint pour reprendre où on s'est arrêté"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"last_city": None, "last_keyword": None, "completed_combinations": []}

def save_checkpoint(city, keyword, completed):
    """Sauvegarde le checkpoint"""
    checkpoint = {
        "last_city": city,
        "last_keyword": keyword,
        "completed_combinations": completed,
        "timestamp": datetime.now().isoformat()
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def load_intermediate_data():
    """Charge les données intermédiaires si elles existent"""
    if os.path.exists(INTERMEDIATE_FILE):
        return pd.read_csv(INTERMEDIATE_FILE)
    return pd.DataFrame()

def save_intermediate_data(df):
    """Sauvegarde les données intermédiaires"""
    df.to_csv(INTERMEDIATE_FILE, index=False)

# --- PARTIE 1 : GOOGLE MAPS HARVESTER ---
def scrape_gmaps_urls(search_term, city, page, browser, context):
    """Récupère les Noms et Sites Web depuis Google Maps"""
    leads = []
    
    print(f"--- Recherche : {search_term} à {city} ---")
    
    try:
        # Aller sur Google Maps avec une approche plus discrète
        try:
            # D'abord aller sur Google.com pour paraître plus naturel
            page.goto("https://www.google.com", timeout=60000, wait_until="domcontentloaded")
            random_delay(2, 4)
            
            # Puis aller sur Maps
            page.goto("https://www.google.com/maps", timeout=60000, wait_until="networkidle")
            random_delay(3, 5)
            
            # Vérifier que la page est toujours ouverte
            try:
                _ = page.url
            except:
                print("  ❌ Page fermée après chargement")
                return leads
        except Exception as nav_error:
            # Si la navigation échoue, recréer la page
            print(f"  ⚠️  Erreur navigation: {nav_error}")
            try:
                page.close()
            except:
                pass
            try:
                page = context.new_page()
                page.goto("https://www.google.com/maps", timeout=60000, wait_until="networkidle")
                random_delay(2, 3)
            except:
                print("  ❌ Impossible de recréer la page")
                return leads
        
        # Gérer la page de consentement Google si présente
        try:
            current_url = page.url
            if "consent.google.com" in current_url:
                print("  🍪 Gestion de la page de consentement...")
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
                            random_delay(2, 3)
                            print("  ✅ Consentement accepté")
                            accepted = True
                            break
                    except:
                        continue
                
                if not accepted:
                    # Essayer de cliquer sur le premier bouton
                    try:
                        page.locator("button").first.click(timeout=3000)
                        random_delay(2, 3)
                    except:
                        pass
                
                # Attendre la redirection
                random_delay(2, 3)
                current_url = page.url
                if "consent.google.com" in current_url:
                    print("  ⚠️  Toujours sur consentement, nouvelle tentative...")
                    page.goto("https://www.google.com/maps", timeout=60000, wait_until="networkidle")
                    random_delay(2, 3)
        except Exception as e:
            print(f"  ⚠️  Erreur gestion consentement: {e}")
        
        # Gestion cookies sur Maps directement
        try:
            cookie_button = page.locator("button:has-text('Tout accepter'), button:has-text('Accept all'), button[id*='accept']").first
            if cookie_button.count() > 0:
                cookie_button.click(timeout=3000)
                random_delay(1, 2)
        except:
            pass

        # Recherche avec vérifications
        query = f"{search_term} {city}"
        try:
            # Vérifier que la page est toujours ouverte
            try:
                _ = page.url
            except:
                print("  ❌ Page fermée avant la recherche")
                return leads
            
            # Attendre que le champ de recherche soit disponible
            search_input = page.locator("#searchboxinput")
            search_input.wait_for(state="visible", timeout=10000)
            
            # Remplir le champ avec des délais pour simuler un humain
            search_input.click()
            random_delay(0.5, 1)
            search_input.fill(query, timeout=5000)
            random_delay(0.5, 1.5)
            page.keyboard.press("Enter")
        except Exception as search_error:
            error_str = str(search_error).lower()
            if "closed" in error_str or "target" in error_str:
                print(f"  ❌ Page fermée pendant la recherche: {search_error}")
                return leads
            print(f"  ⚠️  Erreur lors de la recherche: {search_error}")
            return leads
        
        # Attendre le chargement de la liste
        try:
            page.wait_for_selector('div[role="feed"]', timeout=20000)
        except PlaywrightTimeout:
            print(f"  ⚠️  Timeout: Pas de résultats pour {query}")
            return leads
        except Exception as e:
            print(f"  ⚠️  Erreur lors de l'attente: {e}")
            return leads
        
        random_delay(2, 3)
        
        # Scroll infini pour charger tous les résultats
        feed_selector = 'div[role="feed"]'
        last_height = 0
        max_scrolls = 25
        scroll_attempts = 0
        
        for i in range(max_scrolls):
            try:
                # Vérifier que la page est toujours ouverte
                try:
                    _ = page.url
                except:
                    print(f"  ⚠️  Page fermée pendant le scroll")
                    break
                
                # Scroll dans le feed
                try:
                    page.evaluate(f'''
                        const feed = document.querySelector("{feed_selector}");
                        if (feed) {{
                            feed.scrollTo(0, feed.scrollHeight);
                        }}
                    ''')
                except Exception as eval_error:
                    if "closed" in str(eval_error).lower():
                        print(f"  ⚠️  Page fermée: {eval_error}")
                        break
                    # Continuer si c'est juste une erreur de sélecteur
                    continue
                
                random_delay(1.5, 2.5)
                
                try:
                    new_height = page.evaluate(f'''
                        const feed = document.querySelector("{feed_selector}");
                        return feed ? feed.scrollHeight : 0;
                    ''')
                except Exception as eval_error:
                    if "closed" in str(eval_error).lower():
                        print(f"  ⚠️  Page fermée: {eval_error}")
                        break
                    new_height = last_height  # Utiliser la dernière hauteur connue
                
                if new_height == last_height:
                    scroll_attempts += 1
                    if scroll_attempts >= 3:
                        break
                else:
                    scroll_attempts = 0
                    
                last_height = new_height
            except Exception as e:
                error_str = str(e).lower()
                if "closed" in error_str or "target" in error_str:
                    print(f"  ⚠️  Page fermée lors du scroll: {e}")
                    break
                print(f"  ⚠️  Erreur lors du scroll: {e}")
                # Continuer au lieu de break pour être plus résilient
                continue

        # Extraction des résultats
        # Plusieurs sélecteurs possibles selon la version de Google Maps
        selectors = [
            'a[href*="/maps/place/"]',
            '.hfpxzc',
            '[data-value="Directions"]',
            'div[role="article"] a'
        ]
        
        results = []
        for selector in selectors:
            try:
                # Vérifier que la page est toujours ouverte
                _ = page.url
                found = page.locator(selector).all()
                if len(found) > 0:
                    results = found
                    break
            except Exception as e:
                if "closed" in str(e).lower() or "target" in str(e).lower():
                    print(f"  ⚠️  Page fermée lors de l'extraction: {e}")
                    return leads
                continue
        
        print(f"  -> {len(results)} entreprises trouvées")
        
        # Extraire les noms et liens Maps
        seen_names = set()
        for res in results[:120]:  # Limite Google Maps
            try:
                # Essayer plusieurs méthodes pour obtenir le nom
                name = None
                try:
                    name = res.get_attribute("aria-label")
                except:
                    pass
                
                if not name:
                    try:
                        name = res.inner_text()
                    except:
                        pass
                
                if not name or name in seen_names:
                    continue
                    
                seen_names.add(name)
                
                # Obtenir le lien Maps
                maps_link = None
                try:
                    href = res.get_attribute("href")
                    if href and "/maps/place/" in href:
                        if not href.startswith("http"):
                            maps_link = f"https://www.google.com{href}"
                        else:
                            maps_link = href
                except:
                    pass
                
                if maps_link:
                    leads.append({
                        "Company": name,
                        "Maps_Link": maps_link,
                        "City": city,
                        "Tag": search_term,
                        "Address": None,
                        "Phone": None,
                        "Website": None,
                        "Rating": None,
                        "Reviews_Count": None,
                        "Opening_Hours": None,
                        "Email": None,
                        "Social_Links": None,
                        "Status": "Harvested"
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"  ❌ Erreur sur {city} - {search_term}: {e}")
        
    return leads

# --- PARTIE 2 : ENRICHISSEUR (Récupère toutes les infos depuis la fiche Maps) ---
def enrich_maps_details(page, maps_link):
    """
    Visite la fiche Maps pour extraire toutes les informations :
    - Adresse complète
    - Téléphone
    - Site web
    - Note Google (étoiles)
    - Nombre d'avis
    - Horaires d'ouverture
    """
    if not maps_link:
        return {
            "Address": None,
            "Phone": None,
            "Website": None,
            "Rating": None,
            "Reviews_Count": None,
            "Opening_Hours": None
        }
    
    result = {
        "Address": None,
        "Phone": None,
        "Website": None,
        "Rating": None,
        "Reviews_Count": None,
        "Opening_Hours": None
    }
    
    try:
        page.goto(maps_link, timeout=20000, wait_until="networkidle")
        random_delay(2, 3)
        
        # Gérer le consentement si présent
        try:
            if "consent.google.com" in page.url:
                accept_selectors = [
                    "button:has-text('Tout accepter')",
                    "button:has-text('Accept all')",
                    "button[id*='accept']"
                ]
                for selector in accept_selectors:
                    try:
                        button = page.locator(selector).first
                        if button.count() > 0:
                            button.click(timeout=3000)
                            random_delay(2, 3)
                            break
                    except:
                        continue
        except:
            pass
        
        # 1. ADRESSE COMPLÈTE
        try:
            address_selectors = [
                'button[data-item-id="address"]',
                '[data-item-id="address"]',
                'button:has-text("Rue"), button:has-text("Avenue"), button:has-text("Chemin")',
                'div[data-value="Address"]',
                'span[data-value="Address"]'
            ]
            
            for selector in address_selectors:
                try:
                    address_elem = page.locator(selector).first
                    if address_elem.count() > 0:
                        address_text = address_elem.inner_text()
                        if address_text and len(address_text) > 5:
                            result["Address"] = address_text.strip()
                            break
                except:
                    continue
            
            # Fallback: chercher dans le contenu de la page
            if not result["Address"]:
                try:
                    # Chercher un texte qui ressemble à une adresse
                    page_content = page.content()
                    soup = BeautifulSoup(page_content, 'html.parser')
                    # Chercher des patterns d'adresse
                    for elem in soup.find_all(['button', 'div', 'span']):
                        text = elem.get_text()
                        if text and ('Rue' in text or 'Avenue' in text or 'Chemin' in text) and 'Genève' in text:
                            if len(text) < 100:  # Éviter les textes trop longs
                                result["Address"] = text.strip()
                                break
                except:
                    pass
        except Exception as e:
            pass
        
        # 2. TÉLÉPHONE
        try:
            phone_selectors = [
                'button[data-item-id*="phone"]',
                '[data-item-id*="phone"]',
                'button:has-text("+41")',
                'a[href^="tel:"]',
                'span:has-text("+41")'
            ]
            
            for selector in phone_selectors:
                try:
                    phone_elem = page.locator(selector).first
                    if phone_elem.count() > 0:
                        phone_text = phone_elem.inner_text()
                        # Extraire le numéro de téléphone
                        phone_match = re.search(r'\+?41\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}', phone_text)
                        if phone_match:
                            result["Phone"] = phone_match.group(0).strip()
                            break
                        elif phone_text and ('+41' in phone_text or '022' in phone_text):
                            # Nettoyer le texte
                            phone_clean = re.sub(r'[^\d\+\s]', '', phone_text)
                            if len(phone_clean) > 8:
                                result["Phone"] = phone_clean.strip()
                                break
                except:
                    continue
        except Exception as e:
            pass
        
        # 3. SITE WEB
        try:
            website_selectors = [
                'a[data-item-id="authority"]',
                'a[href^="http"]:has-text("Site web")',
                'a[href^="http"]:has-text("Website")',
                'a[data-value="Website"]',
                'a:has([aria-label*="Site web"])',
                'a:has([aria-label*="Website"])'
            ]
            
            for selector in website_selectors:
                try:
                    website_link = page.locator(selector).first
                    if website_link.count() > 0:
                        href = website_link.get_attribute("href")
                        if href and not any(x in href for x in ["google.com", "maps.google.com", "plus.google.com"]):
                            if href.startswith("http"):
                                result["Website"] = href
                                break
                except:
                    continue
            
            # Fallback: chercher tous les liens http/https qui ne sont pas Google
            if not result["Website"]:
                try:
                    all_links = page.locator('a[href^="http"]').all()
                    for link in all_links[:10]:  # Limiter pour performance
                        href = link.get_attribute("href")
                        if href and not any(x in href for x in ["google.com", "maps.google.com", "plus.google.com", "facebook.com", "twitter.com"]):
                            result["Website"] = href
                            break
                except:
                    pass
        except Exception as e:
            pass
        
        # 4. NOTE GOOGLE (RATING)
        try:
            rating_selectors = [
                'span[aria-label*="étoiles"]',
                'span[aria-label*="stars"]',
                'div[aria-label*="étoiles"]',
                'div[aria-label*="stars"]',
                '[data-value="Rating"]',
                'span.F7nice',
                'div.F7nice'
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = page.locator(selector).first
                    if rating_elem.count() > 0:
                        rating_text = rating_elem.get_attribute("aria-label") or rating_elem.inner_text()
                        if rating_text:
                            # Extraire le nombre (ex: "4.5" depuis "4,5 étoiles" ou "4.5 stars")
                            rating_match = re.search(r'(\d+[.,]\d+|\d+)', rating_text.replace(',', '.'))
                            if rating_match:
                                result["Rating"] = rating_match.group(1).replace(',', '.')
                                break
                except:
                    continue
        except Exception as e:
            pass
        
        # 5. NOMBRE D'AVIS
        try:
            reviews_selectors = [
                'button[data-value="Reviews"]',
                'span:has-text("avis")',
                'span:has-text("reviews")',
                '[data-value="Reviews"]',
                'div[aria-label*="avis"]',
                'div[aria-label*="reviews"]'
            ]
            
            for selector in reviews_selectors:
                try:
                    reviews_elem = page.locator(selector).first
                    if reviews_elem.count() > 0:
                        reviews_text = reviews_elem.inner_text() or reviews_elem.get_attribute("aria-label") or ""
                        # Extraire le nombre
                        reviews_match = re.search(r'(\d+[\s,.]?\d*)', reviews_text.replace(' ', '').replace(',', ''))
                        if reviews_match:
                            result["Reviews_Count"] = reviews_match.group(1)
                            break
                except:
                    continue
        except Exception as e:
            pass
        
        # 6. HORAIRES D'OUVERTURE
        try:
            hours_selectors = [
                'div[data-value="Hours"]',
                'button[data-value="Hours"]',
                'div:has-text("Ouvert")',
                'div:has-text("Fermé")',
                '[data-item-id="hours"]'
            ]
            
            hours_text_parts = []
            for selector in hours_selectors:
                try:
                    hours_elem = page.locator(selector).first
                    if hours_elem.count() > 0:
                        hours_text = hours_elem.inner_text()
                        if hours_text and ('Ouvert' in hours_text or 'Fermé' in hours_text or 'lundi' in hours_text.lower() or 'monday' in hours_text.lower()):
                            hours_text_parts.append(hours_text.strip())
                except:
                    continue
            
            if hours_text_parts:
                # Prendre le premier texte d'horaires trouvé
                result["Opening_Hours"] = hours_text_parts[0]
        except Exception as e:
            pass
            
    except Exception as e:
        print(f"    ⚠️  Erreur lors de l'enrichissement: {e}")
    
    return result

# --- PARTIE 3 : MINER (Scrape le site de l'entreprise avec Playwright pour gérer React/SPA) ---
def enrich_company_data_playwright(page, website_url):
    """Enrichit les données en visitant le site avec Playwright (gère React/SPA)"""
    if not website_url:
        return None, None, None
    
    emails = set()
    social_links = []
    
    try:
        # Visiter le site
        page.goto(website_url, timeout=15000, wait_until="networkidle")
        random_delay(2, 3)
        
        # Attendre que le contenu se charge (important pour React/SPA)
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Extraire le contenu HTML
        html_content = page.content()
        
        # Regex pour emails
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        new_emails = set(re.findall(email_pattern, html_content))
        emails.update(new_emails)
        
        # Extraire les liens sociaux depuis le HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        social_domains = ['linkedin.com', 'twitter.com', 'x.com', 'facebook.com', 
                         'instagram.com', 'github.com', 'youtube.com']
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(website_url, href)
            
            for domain in social_domains:
                if domain in href.lower():
                    if full_url not in social_links:
                        social_links.append(full_url)
        
        # Chercher les pages Contact/About/Team
        contact_keywords = ['contact', 'about', 'team', 'equipe', 'nous', 'about-us']
        contact_links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            text = a.get_text().lower()
            
            if any(keyword in href or keyword in text for keyword in contact_keywords):
                full_url = urljoin(website_url, a['href'])
                if full_url not in contact_links and full_url != website_url:
                    contact_links.append(full_url)
        
        # Visiter max 2 pages de contact
        for link in contact_links[:2]:
            try:
                page.goto(link, timeout=10000, wait_until="networkidle")
                random_delay(1, 2)
                
                contact_html = page.content()
                contact_emails = set(re.findall(email_pattern, contact_html))
                emails.update(contact_emails)
                
                # Mettre à jour les liens sociaux
                contact_soup = BeautifulSoup(contact_html, 'html.parser')
                for a in contact_soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(website_url, href)
                    for domain in social_domains:
                        if domain in href.lower() and full_url not in social_links:
                            social_links.append(full_url)
                            
            except Exception as e:
                continue
        
        # Filtrer les emails "poubelle"
        clean_emails = [
            e for e in emails 
            if not any(x in e.lower() for x in [
                '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp',
                'sentry', 'wix', 'example.com', 'test@', 'noreply',
                'no-reply', 'donotreply', 'privacy', 'legal'
            ])
        ]
        
        return ", ".join(clean_emails) if clean_emails else None, \
               ", ".join(social_links) if social_links else None, \
               "Success"
        
    except Exception as e:
        print(f"    ⚠️  Erreur lors du scraping de {website_url}: {e}")
        return None, None, "Error"

# --- EXÉCUTION PRINCIPALE ---
def main():
    print("=" * 60)
    print("🚀 SCRAPER SUISSE ROMANDE - MODE GUÉRILLA")
    print("=" * 60)
    
    # Charger les données existantes
    existing_df = load_intermediate_data()
    checkpoint = load_checkpoint()
    
    all_data = existing_df.to_dict('records') if not existing_df.empty else []
    completed_combos = checkpoint.get("completed_combinations", [])
    
    print(f"📊 Données existantes: {len(all_data)} entreprises")
    print(f"✅ Combinaisons complétées: {len(completed_combos)}")
    
    try:
        with sync_playwright() as p:
            # Lancer le navigateur (Firefox par défaut car mieux détecté)
            try:
                if BROWSER_TYPE == "firefox":
                    browser = p.firefox.launch(headless=True)
                    print("  🌐 Utilisation de Firefox")
                else:
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-web-security',
                            '--disable-features=IsolateOrigins,site-per-process',
                            '--disable-site-isolation-trials'
                        ]
                    )
                    print("  🌐 Utilisation de Chromium")
            except Exception as e:
                print(f"⚠️  Erreur lors du lancement du navigateur: {e}")
                print("   Tentative avec Firefox...")
                try:
                    browser = p.firefox.launch(headless=True)
                    print("  🌐 Basculement vers Firefox")
                except:
                    print("   Tentative avec Chromium minimal...")
                    browser = p.chromium.launch(headless=True)
            
            try:
                if BROWSER_TYPE == "firefox":
                    # Firefox a des options différentes
                    context = browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        locale='fr-CH',
                        timezone_id='Europe/Zurich',
                        geolocation={'latitude': 46.2044, 'longitude': 6.1432},  # Genève
                        permissions=['geolocation']
                    )
                else:
                    # Chromium avec options anti-détection
                    context = browser.new_context(
                        user_agent=random.choice(USER_AGENTS),
                        viewport={'width': 1920, 'height': 1080},
                        locale='fr-CH',
                        timezone_id='Europe/Zurich',
                        permissions=['geolocation'],
                        geolocation={'latitude': 46.2044, 'longitude': 6.1432},  # Genève
                        color_scheme='light'
                    )
                    
                    # Scripts anti-détection (Chromium seulement)
                    context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        window.chrome = {
                            runtime: {}
                        };
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['fr-CH', 'fr', 'en']
                        });
                    """)
                
                page = context.new_page()
                
                # Écouter les événements de fermeture pour debug
                def on_close():
                    print("  ⚠️  Page fermée par événement")
                page.on("close", on_close)
                
                print("\n" + "=" * 60)
                print("📡 PHASE 1: HARVESTING GOOGLE MAPS")
                print("=" * 60)
                
                for city in CITIES:
                    for keyword in KEYWORDS:
                        combo = f"{city}_{keyword}"
                        
                        # Skip si déjà fait
                        if combo in completed_combos:
                            print(f"⏭️  Déjà fait: {city} - {keyword}")
                            continue
                        
                        try:
                            # Vérifier que le navigateur est toujours ouvert
                            try:
                                _ = browser.is_connected()
                            except:
                                print("  ❌ Navigateur fermé, impossible de continuer")
                                raise Exception("Browser closed")
                            
                            # Créer une nouvelle page pour chaque recherche pour éviter les problèmes de session
                            try:
                                if page:
                                    try:
                                        _ = page.url  # Vérifier si la page est toujours ouverte
                                    except:
                                        page = None
                            except:
                                page = None
                            
                            if not page:
                                print("  ⚠️  Création d'une nouvelle page...")
                                try:
                                    page = context.new_page()
                                except:
                                    print("  ⚠️  Contexte fermé, recréation...")
                                    context = browser.new_context(
                                        user_agent=random.choice(USER_AGENTS),
                                        viewport={'width': 1920, 'height': 1080},
                                        locale='fr-CH',
                                        timezone_id='Europe/Zurich'
                                    )
                                    page = context.new_page()
                            
                            extracted = scrape_gmaps_urls(keyword, city, page, browser, context)
                            all_data.extend(extracted)
                            
                            # Sauvegarder après chaque combinaison
                            if extracted:
                                df_temp = pd.DataFrame(all_data)
                                save_intermediate_data(df_temp)
                            
                            completed_combos.append(combo)
                            save_checkpoint(city, keyword, completed_combos)
                            
                            print(f"  ✅ {len(extracted)} entreprises ajoutées")
                            random_delay(3, 6)  # Pause importante entre recherches
                        except Exception as e:
                            error_msg = str(e)
                            print(f"  ⚠️  Erreur sur {city} - {keyword}: {error_msg}")
                            
                            # Si le navigateur est fermé, on ne peut pas continuer
                            if "closed" in error_msg.lower() or "browser" in error_msg.lower():
                                print("  ❌ Navigateur fermé, arrêt du scraping")
                                raise
                            
                            # Continuer avec la prochaine combinaison pour les autres erreurs
                            continue
                
                # Nettoyer les doublons
                df = pd.DataFrame(all_data)
                if not df.empty:
                    df = df.drop_duplicates(subset=['Company'], keep='first')
                    print(f"\n📊 Total après nettoyage: {len(df)} entreprises uniques")
                else:
                    print("\n⚠️  Aucune donnée récupérée. Vérifiez votre connexion et les sélecteurs.")
                    return
                
                # 2. ENRICHISSEMENT DES DONNÉES MAPS (Adresse, Téléphone, Site web, Note, Avis, Horaires)
                print("\n" + "=" * 60)
                print("🌐 PHASE 2: ENRICHISSEMENT DES FICHES MAPS")
                print("=" * 60)
                
                addresses = []
                phones = []
                websites = []
                ratings = []
                reviews_counts = []
                opening_hours = []
                
                for index, row in df.iterrows():
                    # Vérifier si on a déjà les données
                    has_data = (pd.notna(row.get('Address')) or pd.notna(row.get('Phone')) or 
                               pd.notna(row.get('Website')) or pd.notna(row.get('Rating')))
                    
                    if not has_data:
                        try:
                            print(f"  🔍 {row['Company']} ({index+1}/{len(df)})")
                            
                            # Vérifier que la page est toujours ouverte
                            try:
                                _ = page.url
                            except:
                                print("    ⚠️  Page fermée, recréation...")
                                page = context.new_page()
                            
                            details = enrich_maps_details(page, row.get('Maps_Link'))
                            
                            addresses.append(details.get('Address'))
                            phones.append(details.get('Phone'))
                            websites.append(details.get('Website'))
                            ratings.append(details.get('Rating'))
                            reviews_counts.append(details.get('Reviews_Count'))
                            opening_hours.append(details.get('Opening_Hours'))
                            
                            random_delay(MIN_PAGE_DELAY, MAX_PAGE_DELAY)
                        except Exception as e:
                            print(f"    ⚠️  Erreur: {e}")
                            addresses.append(row.get('Address') if 'Address' in row else None)
                            phones.append(row.get('Phone') if 'Phone' in row else None)
                            websites.append(row.get('Website') if 'Website' in row else None)
                            ratings.append(row.get('Rating') if 'Rating' in row else None)
                            reviews_counts.append(row.get('Reviews_Count') if 'Reviews_Count' in row else None)
                            opening_hours.append(row.get('Opening_Hours') if 'Opening_Hours' in row else None)
                    else:
                        # Utiliser les données existantes
                        addresses.append(row.get('Address'))
                        phones.append(row.get('Phone'))
                        websites.append(row.get('Website'))
                        ratings.append(row.get('Rating'))
                        reviews_counts.append(row.get('Reviews_Count'))
                        opening_hours.append(row.get('Opening_Hours'))
                
                df['Address'] = addresses
                df['Phone'] = phones
                df['Website'] = websites
                df['Rating'] = ratings
                df['Reviews_Count'] = reviews_counts
                df['Opening_Hours'] = opening_hours
                save_intermediate_data(df)
                
                # 3. MINING (Emails et liens sociaux)
                print("\n" + "=" * 60)
                print("⛏️  PHASE 3: MINING (Emails & Réseaux sociaux)")
                print("=" * 60)
                
                final_emails = []
                final_socials = []
                final_status = []
                
                for index, row in df.iterrows():
                    website = row.get('Website')
                    
                    if pd.notna(website) and website:
                        try:
                            print(f"  🔎 Scraping: {row['Company']} ({index+1}/{len(df)})")
                            emails, socials, status = enrich_company_data_playwright(page, website)
                            final_emails.append(emails)
                            final_socials.append(socials)
                            final_status.append(status)
                            random_delay(2, 4)  # Pause entre sites
                        except Exception as e:
                            print(f"    ⚠️  Erreur: {e}")
                            final_emails.append(None)
                            final_socials.append(None)
                            final_status.append("Error")
                    else:
                        final_emails.append(None)
                        final_socials.append(None)
                        final_status.append("No Website")
                
                df['Email'] = final_emails
                df['Social_Links'] = final_socials
                df['Status'] = final_status
                
                # Sauvegarde finale
                df.to_csv(OUTPUT_FILE, index=False)
                print("\n" + "=" * 60)
                print(f"✅ TERMINÉ ! Fichier sauvegardé: {OUTPUT_FILE}")
                print(f"📊 Total: {len(df)} entreprises")
                print(f"📍 Avec adresse: {df['Address'].notna().sum()}")
                print(f"📞 Avec téléphone: {df['Phone'].notna().sum()}")
                print(f"🌐 Avec site web: {df['Website'].notna().sum()}")
                print(f"⭐ Avec note: {df['Rating'].notna().sum()}")
                print(f"💬 Avec avis: {df['Reviews_Count'].notna().sum()}")
                print(f"🕐 Avec horaires: {df['Opening_Hours'].notna().sum()}")
                print(f"📧 Avec email: {df['Email'].notna().sum()}")
                print("=" * 60)
                
            except Exception as browser_error:
                print(f"\n⚠️  Erreur navigateur: {browser_error}")
                print("   Sauvegarde des données récupérées jusqu'ici...")
                # Sauvegarder ce qu'on a récupéré
                if 'df' in locals() and not df.empty:
                    df.to_csv(OUTPUT_FILE, index=False)
                    print(f"   ✅ Données sauvegardées dans {OUTPUT_FILE}")
                raise
            finally:
                try:
                    browser.close()
                except:
                    pass
    
    except Exception as e:
        print(f"\n❌ Erreur fatale dans le navigateur: {e}")
        # Sauvegarder les données récupérées
        if 'all_data' in locals() and all_data:
            df_temp = pd.DataFrame(all_data)
            if not df_temp.empty:
                df_temp.to_csv(OUTPUT_FILE, index=False)
                print(f"   ✅ Données partielles sauvegardées dans {OUTPUT_FILE}")
        raise
    
    # Nettoyer les fichiers temporaires (seulement si tout s'est bien passé)
    if os.path.exists(OUTPUT_FILE):
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        if os.path.exists(INTERMEDIATE_FILE):
            os.remove(INTERMEDIATE_FILE)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur. Les données intermédiaires sont sauvegardées.")
        print(f"   Relancez le script pour reprendre où vous vous êtes arrêté.")
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        print(f"   Les données intermédiaires sont sauvegardées dans {INTERMEDIATE_FILE}")


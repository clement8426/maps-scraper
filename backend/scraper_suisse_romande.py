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
import sqlite3
import dns.resolver
from email_validator import validate_email, EmailNotValidError
import sys

# Forcer le flush des print() pour voir les logs en temps réel
def print_flush(*args, **kwargs):
    """Print avec flush automatique"""
    print(*args, **kwargs)
    sys.stdout.flush()

# --- CONFIGURATION ---
# Villes du canton de Neuchâtel et alentours (priorité)
CITIES = [
    # Canton de Neuchâtel
    "Neuchâtel", "La Chaux-de-Fonds", "Le Locle", "Val-de-Ruz", 
    "Val-de-Travers", "Fleurier", "Cernier", "Peseux", "Colombier", 
    "Marin-Epagnier", "Saint-Blaise", "Boudry", "Cressier",
    # Villes proches hors canton
    "Yverdon-les-Bains", "Pontarlier", "Morteau", "Besançon",
    # Autres villes Suisse Romande (existantes)
    "Genève", "Lausanne", "Fribourg", "Sion", "Nyon", "Renens", 
    "Meyrin", "Plan-les-Ouates", "Martigny", "Vevey", "Montreux",
    "Delémont", "Porrentruy"
]

KEYWORDS = [
    # Développement web & digital
    "Agence Web", "Développement logiciel", "Conception de sites web", 
    "Création site internet", "Agence digitale", "Web design",
    "Développeur web", "Intégrateur web", "UX Designer",
    # Développement spécialisé
    "Full Stack", "Frontend developer", "Backend developer",
    "App development", "Mobile app", "Application mobile",
    "E-commerce", "Site e-commerce", "Boutique en ligne",
    # Software & SaaS
    "Éditeur de logiciels", "Software development", "SaaS company", 
    "Startup tech", "Tech startup", "Scale-up",
    # Sécurité & infrastructure
    "Cybersécurité", "Sécurité informatique", "Consultant IT",
    "Consultant informatique", "Services informatiques entreprises", 
    "Cloud provider", "DevOps", "Infrastructure IT",
    # Marketing digital
    "SEO", "Référencement web", "Marketing digital",
    "Social media management", "Community manager",
    # Data & IA
    "Data science", "Intelligence artificielle", "Machine Learning",
    "Big Data", "Data analyst"
]

OUTPUT_FILE = "base_tech_suisse.csv"
CHECKPOINT_FILE = "checkpoint.json"
INTERMEDIATE_FILE = "intermediate_data.csv"
DATABASE_FILE = "companies.db"

# Navigateur à utiliser: "chromium" ou "firefox"
# Firefox semble mieux fonctionner avec Google Maps
BROWSER_TYPE = "firefox"  # Changez en "chromium" si vous préférez

# Délais aléatoires pour simuler un humain
MIN_DELAY = 2.0
MAX_DELAY = 5.0
MIN_PAGE_DELAY = 1.0
MAX_PAGE_DELAY = 3.0

# Configuration de retry
MAX_RETRIES = 3
RETRY_DELAY = 5  # secondes entre les retries

# User agents rotatifs (plus de variété)
USER_AGENTS = [
    # Chrome Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    # Chrome macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    # Chrome Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # Firefox Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    # Firefox macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13.5; rv:120.0) Gecko/20100101 Firefox/120.0',
    # Safari macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    # Edge Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]

def random_delay(min_sec=MIN_DELAY, max_sec=MAX_DELAY):
    """Délai aléatoire pour simuler un comportement humain"""
    time.sleep(random.uniform(min_sec, max_sec))

def retry_with_backoff(func, max_retries=MAX_RETRIES, delay=RETRY_DELAY, *args, **kwargs):
    """Exécute une fonction avec retry automatique en cas d'échec"""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Dernière tentative, on propage l'erreur
            error_str = str(e).lower()
            if "closed" in error_str or "target" in error_str or "browser" in error_str:
                # Erreur critique, on ne retry pas
                raise
            print(f"    ⚠️  Tentative {attempt + 1}/{max_retries} échouée: {e}")
            print(f"    ⏳ Nouvelle tentative dans {delay} secondes...")
            time.sleep(delay)
            delay *= 1.5  # Backoff exponentiel
    return None

def is_browser_alive(browser, context, page):
    """Vérifie si le navigateur, contexte et page sont toujours actifs"""
    try:
        if browser and not browser.is_connected():
            return False, None, None, None
        if context and context.pages:
            if page and page.url:
                return True, browser, context, page
        return True, browser, context, None
    except:
        return False, None, None, None

def recreate_browser_context_internal(p, browser=None):
    """Recrée le navigateur et le contexte en cas de problème (fonction interne)"""
    try:
        if browser:
            try:
                browser.close()
            except:
                pass
    except:
        pass
    
    try:
        if BROWSER_TYPE == "firefox":
            browser = p.firefox.launch(headless=True)
        else:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
        
        if BROWSER_TYPE == "firefox":
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='fr-CH',
                timezone_id='Europe/Zurich',
                geolocation={'latitude': 46.2044, 'longitude': 6.1432},
                permissions=['geolocation']
            )
        else:
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080},
                locale='fr-CH',
                timezone_id='Europe/Zurich',
                permissions=['geolocation'],
                geolocation={'latitude': 46.2044, 'longitude': 6.1432},
                color_scheme='light'
            )
            
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
        print("  ✅ Navigateur et contexte recréés avec succès")
        return browser, context, page
    except Exception as e:
        print(f"  ❌ Erreur lors de la recréation: {e}")
        raise

def check_google_block(page):
    """Vérifie si Google a bloqué le bot"""
    try:
        url = page.url
        content = page.content()
        
        # Signes de blocage
        block_indicators = [
            "unusual traffic",
            "automated queries",
            "captcha",
            "robot",
            "verify you're not a robot",
            "not a robot"
        ]
        
        content_lower = content.lower()
        for indicator in block_indicators:
            if indicator in content_lower:
                print(f"  ⚠️  Blocage Google détecté: {indicator}")
                return True
        
        # Vérifier l'URL
        if "sorry" in url.lower() or "captcha" in url.lower():
            print(f"  ⚠️  Page de blocage détectée: {url}")
            return True
            
        return False
    except:
        return False

def init_database():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            maps_link TEXT UNIQUE,
            city TEXT,
            tag TEXT,
            address TEXT,
            phone TEXT,
            website TEXT,
            rating REAL,
            reviews_count INTEGER,
            email TEXT,
            social_links TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Base de données initialisée: {DATABASE_FILE}")

def save_to_database(df):
    """Sauvegarde les données dans la base SQLite (avec UPDATE pour préserver les IDs)"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        try:
            maps_link = row.get('Maps_Link')
            
            # Vérifier si l'entreprise existe déjà
            cursor.execute('SELECT id FROM companies WHERE maps_link = ?', (maps_link,))
            existing = cursor.fetchone()
            
            if existing:
                # UPDATE : Met à jour sans changer l'ID (préserve les données OSINT)
                cursor.execute('''
                    UPDATE companies 
                    SET company_name = ?, city = ?, tag = ?, address = ?, phone = ?,
                        website = ?, rating = ?, reviews_count = ?, email = ?, 
                        social_links = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE maps_link = ?
                ''', (
                    row.get('Company'),
                    row.get('City'),
                    row.get('Tag'),
                    row.get('Address'),
                    row.get('Phone'),
                    row.get('Website'),
                    row.get('Rating'),
                    row.get('Reviews_Count'),
                    row.get('Email'),
                    row.get('Social_Links'),
                    row.get('Status'),
                    maps_link
                ))
            else:
                # INSERT : Nouvelle entreprise
                cursor.execute('''
                    INSERT INTO companies 
                    (company_name, maps_link, city, tag, address, phone, website, 
                     rating, reviews_count, email, social_links, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    row.get('Company'),
                    maps_link,
                    row.get('City'),
                    row.get('Tag'),
                    row.get('Address'),
                    row.get('Phone'),
                    row.get('Website'),
                    row.get('Rating'),
                    row.get('Reviews_Count'),
                    row.get('Email'),
                    row.get('Social_Links'),
                    row.get('Status')
                ))
        except Exception as e:
            print(f"    ⚠️  Erreur BDD: {e}")
    
    conn.commit()
    conn.close()

def verify_email_dns(email):
    """Vérifie si un email est valide via DNS MX records"""
    if not email or '@' not in email:
        return False
    
    # Emails génériques à exclure
    generic_emails = [
        'example.com', 'test.com', 'demo.com', 'sample.com',
        'noreply', 'no-reply', 'donotreply', 'info@example',
        'contact@example', 'admin@example'
    ]
    
    email_lower = email.lower()
    if any(generic in email_lower for generic in generic_emails):
        return False
    
    try:
        # Validation basique du format
        valid = validate_email(email, check_deliverability=False)
        domain = valid.domain
        
        # Vérification DNS MX
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return False
        except Exception:
            # Si erreur DNS, on garde l'email quand même
            return True
            
    except EmailNotValidError:
        return False
    except Exception:
        return False
    
    return False

def clean_emails(emails_string):
    """Nettoie et valide les emails"""
    if not emails_string or pd.isna(emails_string):
        return None
    
    emails = [e.strip() for e in str(emails_string).split(',')]
    valid_emails = []
    
    for email in emails:
        if verify_email_dns(email):
            valid_emails.append(email)
        else:
            print(f"    ❌ Email invalide/fictif rejeté: {email}")
    
    return ', '.join(valid_emails) if valid_emails else None

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
        df = pd.read_csv(INTERMEDIATE_FILE)
        # Remplacer les chaînes vides par NaN pour faciliter la détection
        df = df.replace('', pd.NA)
        return df
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
            page.goto("https://www.google.com", timeout=90000, wait_until="domcontentloaded")
            random_delay(2, 4)
            
            # Puis aller sur Maps
            page.goto("https://www.google.com/maps", timeout=90000, wait_until="networkidle")
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
                page.goto("https://www.google.com/maps", timeout=90000, wait_until="networkidle")
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
                    page.goto("https://www.google.com/maps", timeout=90000, wait_until="networkidle")
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
            page.wait_for_selector('div[role="feed"]', timeout=30000)
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
            "Reviews_Count": None
        }
    
    result = {
            "Address": None,
            "Phone": None,
            "Website": None,
            "Rating": None,
            "Reviews_Count": None
        }
    
    try:
        page.goto(maps_link, timeout=30000, wait_until="networkidle")
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
        
        # Attendre que la page soit complètement chargée
        try:
            page.wait_for_load_state("networkidle", timeout=25000)
        except:
            pass
        
        random_delay(2, 3)
        
        # Extraire le texte visible de la page (plus fiable que le HTML minifié)
        page_text = ""
        try:
            # Méthode 1: inner_text via locator
            page_text = page.locator('body').inner_text(timeout=5000)
        except:
            try:
                # Méthode 2: evaluate JavaScript
                page_text = page.evaluate("document.body.innerText")
            except:
                try:
                    # Méthode 3: via BeautifulSoup
                    html_content = page.content()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    page_text = soup.get_text()
                except:
                    page_text = ""
        
        # Debug: sauvegarder le texte si vide ou pour debug
        if not page_text or len(page_text) < 100:
            print(f"    ⚠️  Texte de la page trop court ({len(page_text)} caractères), tentative alternative...")
            try:
                # Essayer d'attendre plus longtemps
                page.wait_for_load_state("networkidle", timeout=30000)
                random_delay(3, 5)
                page_text = page.locator('body').inner_text(timeout=15000)
            except:
                pass
        
        # Extraire aussi le HTML pour BeautifulSoup
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Debug: vérifier que le texte contient des infos utiles
        if page_text:
            has_address = 'Rue' in page_text or 'Avenue' in page_text or 'Genève' in page_text
            has_phone = '+41' in page_text or '022' in page_text
            has_website = '.ch' in page_text or '.com' in page_text
            if not (has_address or has_phone or has_website):
                print(f"    ⚠️  Le texte extrait ne semble pas contenir les infos attendues")
                print(f"    ℹ️  Longueur du texte: {len(page_text)} caractères")
                print(f"    ℹ️  Premiers 200 caractères: {page_text[:200]}")
        
        # 1. ADRESSE COMPLÈTE - Basé sur le texte visible (plus fiable)
        try:
            if not page_text:
                print(f"    ⚠️  Pas de texte à analyser pour l'adresse")
            else:
                # Pattern observé dans maps_page_text.txt ligne 47: "Rue Caroline 23, 1227 Genève, Suisse"
                address_patterns = [
                    r'(?:Rue|Avenue|Chemin|Route|Place|Boulevard)\s+[A-Za-zÀ-ÿ\s\-]+\s+\d+[,\s]+\d{4}\s+Genève[,\s]+Suisse?',
                    r'(?:Rue|Avenue|Chemin|Route|Place|Boulevard)\s+[A-Za-zÀ-ÿ\s\-]+\s+\d+[,\s]+\d{4}\s+Genève',
                    r'\d+[,\s]+(?:Rue|Avenue|Chemin|Route|Place|Boulevard)\s+[A-Za-zÀ-ÿ\s\-]+[,\s]+\d{4}\s+Genève',
                ]
                
                for pattern in address_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        addr = match.group(0).strip()
                        # Vérifier que c'est une vraie adresse (contient un code postal)
                        if re.search(r'\d{4}', addr) and ('Genève' in addr or 'Suisse' in addr or 'Lausanne' in addr):
                            result["Address"] = addr
                            break
                
                # Fallback: chercher ligne par ligne dans le texte (MÉTHODE PRINCIPALE)
                if not result["Address"]:
                    lines = page_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Pattern simple: contient un type de rue + numéro + code postal + ville
                        if (any(x in line for x in ['Rue', 'Avenue', 'Chemin', 'Route', 'Place', 'Boulevard']) and
                            re.search(r'\d+', line) and  # Contient un numéro
                            re.search(r'\d{4}', line) and  # Contient un code postal
                            any(x in line for x in ['Genève', 'Lausanne', 'Suisse', 'Yverdon', 'Neuchâtel', 'Fribourg', 'Sion', 'Nyon'])):
                            if 15 < len(line) < 150:
                                result["Address"] = line
                                break
        except Exception as e:
            print(f"    ⚠️  Erreur extraction adresse: {e}")
        
        # 2. TÉLÉPHONE - Pattern observé ligne 60: "+41 22 501 76 86"
        try:
            if page_text:
                # Pattern suisse: +41 XX XXX XX XX
                phone_patterns = [
                    r'\+41\s\d{2}\s\d{3}\s\d{2}\s\d{2}',  # Avec espaces exacts: "+41 22 501 76 86"
                    r'\+41\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',  # Espaces optionnels
                    r'0\d{2}\s\d{3}\s\d{2}\s\d{2}',  # Format local avec espaces
                    r'0\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',  # Format local espaces optionnels
                ]
                
                for pattern in phone_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        phone = match.group(0).strip()
                        # Nettoyer les espaces multiples
                        phone = re.sub(r'\s+', ' ', phone)
                        result["Phone"] = phone
                        break
            
            # Chercher dans les liens tel:
            if not result["Phone"]:
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if href.startswith('tel:'):
                        phone = href.replace('tel:', '').strip()
                        if '+41' in phone or phone.startswith('0'):
                            result["Phone"] = phone
                            break
        except Exception as e:
            pass
        
        # 3. SITE WEB - Pattern observé ligne 53: "creation-site-internet-suisse.ch"
        try:
            if page_text:
                # Chercher les domaines dans le texte ligne par ligne (éviter les emails)
                lines = page_text.split('\n')
                for line in lines:
                    line = line.strip()
                    # Ignorer les lignes qui contiennent @ (emails) ou qui sont trop courtes
                    if '@' not in line and '.' in line and len(line) > 5:
                        # Chercher un domaine valide (format: domaine.ch ou domaine.com)
                        # Pattern plus simple et direct
                        domain_match = re.search(r'([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.(?:ch|com|net|org|fr|io|co)[a-zA-Z]*)', line)
                        if domain_match:
                            domain = domain_match.group(1)
                            # Vérifier que ce n'est pas un domaine Google ou social
                            if not any(x in domain.lower() for x in ['google', 'facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'maps']):
                                result["Website"] = f"https://{domain}" if not domain.startswith('http') else domain
                                break
            
            # Chercher dans les liens href (méthode principale)
            if not result["Website"]:
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if href.startswith('http') and not any(x in href.lower() for x in [
                        "google.com", "maps.google.com", "plus.google.com", 
                        "facebook.com", "twitter.com", "x.com", "linkedin.com",
                        "instagram.com", "youtube.com"
                    ]):
                        result["Website"] = href
                        break
        except Exception as e:
            pass
        
        # 4. NOTE GOOGLE (RATING) - Pattern observé ligne 28: "5,0"
        try:
            if page_text:
                # Chercher un nombre avec virgule ou point (format suisse: "5,0" ou format US: "5.0")
                # Format observé: "5,0" ou "5.0" souvent suivi de "(30)" pour les avis
                rating_patterns = [
                    r'(\d+[.,]\d+)\s*\(',  # "5,0 (" ou "5.0 ("
                    r'^(\d+[.,]\d+)\s*$',   # Ligne complète avec juste la note
                    r'(\d+[.,]\d+)\s*$',   # Fin de ligne
                ]
                
                lines = page_text.split('\n')
                for line in lines:
                    line = line.strip()
                    # Chercher un pattern de note (nombre entre 0 et 5)
                    for pattern in rating_patterns:
                        match = re.search(pattern, line)
                        if match:
                            rating = match.group(1).replace(',', '.')
                            try:
                                rating_float = float(rating)
                                if 0 <= rating_float <= 5:
                                    result["Rating"] = rating
                                    break
                            except:
                                pass
                    if result["Rating"]:
                        break
        except Exception as e:
            pass
        
        # 5. NOMBRE D'AVIS - Pattern observé ligne 29: "(30)" ou ligne 97: "30 avis"
        try:
            if page_text:
                # Chercher "(30)" ou "30 avis" dans le texte
                reviews_patterns = [
                    r'\((\d+)\)',  # "(30)" - format le plus commun
                    r'(\d+)\s+avis',  # "30 avis"
                    r'(\d+)\s+reviews',  # "30 reviews"
                ]
                
                for pattern in reviews_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        reviews = match.group(1)
                        if reviews.isdigit():
                            result["Reviews_Count"] = reviews
                            break
                
                # Chercher dans les lignes du texte (méthode alternative)
                if not result["Reviews_Count"]:
                    lines = page_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if 'avis' in line.lower() or 'review' in line.lower():
                            reviews_match = re.search(r'(\d+)', line)
                            if reviews_match:
                                result["Reviews_Count"] = reviews_match.group(1)
                                break
        except Exception as e:
            pass
        
        # 6. HORAIRES D'OUVERTURE - Pattern observé ligne 50: "Ouvert 24h/24"
        try:
            # Chercher "Ouvert" ou "Fermé" dans le texte
            hours_patterns = [
                r'Ouvert\s+24h/24',
                r'Ouvert\s+\d{2}h\s*-\s*\d{2}h',
                r'Fermé',
            ]
            
            hours_found = []
            
            # Chercher dans les lignes du texte
            lines = page_text.split('\n')
            for line in lines:
                line = line.strip()
                if 'Ouvert' in line or 'Fermé' in line or '24h' in line:
                    if 5 < len(line) < 100:
                        hours_found.append(line)
            
            # Si on trouve "Ouvert 24h/24", c'est souvent la seule info
            if hours_found:
                # Prendre la première occurrence pertinente
                for h in hours_found:
                    if 'Ouvert' in h or 'Fermé' in h:
                        result["Opening_Hours"] = h
                        break
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
        page.goto(website_url, timeout=25000, wait_until="networkidle")
        random_delay(2, 3)
        
        # Attendre que le contenu se charge (important pour React/SPA)
        page.wait_for_load_state("networkidle", timeout=15000)
        
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
                page.goto(link, timeout=20000, wait_until="networkidle")
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
    
    # Initialiser la base de données
    init_database()
    
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
                
                # BOUCLE PRINCIPALE : Pour chaque combinaison ville/keyword, faire Harvesting → Enrichissement → Mining
                for city in CITIES:
                    for keyword in KEYWORDS:
                        combo = f"{city}_{keyword}"
                        
                        # Skip si déjà fait
                        if combo in completed_combos:
                            print(f"⏭️  Déjà fait: {city} - {keyword}")
                            continue
                        
                        print("\n" + "=" * 60)
                        print(f"🔄 TRAITEMENT: {keyword} à {city}")
                        print("=" * 60)
                        
                        try:
                            # Vérifier régulièrement l'état du navigateur
                            is_alive, browser, context, page = is_browser_alive(browser, context, page)
                            
                            if not is_alive:
                                print("  ⚠️  Navigateur fermé, recréation...")
                                try:
                                    browser, context, page = recreate_browser_context_internal(p, browser)
                                    random_delay(3, 5)  # Pause après recréation
                                except Exception as rec_error:
                                    print(f"  ❌ Impossible de recréer le navigateur: {rec_error}")
                                    print("  ⏸️  Pause de 30 secondes avant nouvelle tentative...")
                                    time.sleep(30)
                                    try:
                                        browser, context, page = recreate_browser_context_internal(p)
                                    except:
                                        print("  ❌ Échec définitif, arrêt du scraping")
                                        raise
                            
                            # Vérifier si la page existe, sinon en créer une nouvelle
                            if not page:
                                try:
                                    page = context.new_page()
                                    print("  ✅ Nouvelle page créée")
                                except:
                                    print("  ⚠️  Contexte fermé, recréation complète...")
                                    browser, context, page = recreate_browser_context_internal(p, browser)
                                    random_delay(2, 4)
                            
                            # Vérifier les blocages Google avant de continuer
                            try:
                                if check_google_block(page):
                                    print("  ⚠️  Blocage Google détecté, pause de 60 secondes...")
                                    time.sleep(60)
                                    # Recréer le navigateur pour éviter le blocage
                                    browser, context, page = recreate_browser_context_internal(p, browser)
                                    random_delay(5, 10)
                            except:
                                pass  # Si on ne peut pas vérifier, on continue quand même
                            
                            # ===== PHASE 1: HARVESTING =====
                            print(f"\n📡 PHASE 1: HARVESTING - {keyword} à {city}")
                            extracted = scrape_gmaps_urls(keyword, city, page, browser, context)
                            
                            if not extracted:
                                print(f"  ⚠️  Aucune entreprise trouvée pour {keyword} à {city}")
                                completed_combos.append(combo)
                                save_checkpoint(city, keyword, completed_combos)
                                continue
                            
                            print(f"  ✅ {len(extracted)} entreprises trouvées")
                            
                            # Créer un DataFrame temporaire pour cette recherche
                            df_search = pd.DataFrame(extracted)
                            
                            # ===== PHASE 2: ENRICHISSEMENT MAPS =====
                            print(f"\n🌐 PHASE 2: ENRICHISSEMENT - {len(df_search)} entreprises")
                            
                            addresses = []
                            phones = []
                            websites = []
                            ratings = []
                            reviews_counts = []
                            
                            for idx, row in df_search.iterrows():
                                try:
                                    print(f"  🔍 {row['Company']} ({idx+1}/{len(df_search)})")
                                    
                                    # Vérifier que la page est toujours ouverte
                                    is_alive, browser, context, page = is_browser_alive(browser, context, page)
                                    if not is_alive or not page:
                                        print("    ⚠️  Page fermée, recréation...")
                                    try:
                                            browser, context, page = recreate_browser_context_internal(p, browser)
                                    except:
                                            print("    ❌ Impossible de recréer, skip cette entreprise")
                                            addresses.append(None)
                                            phones.append(None)
                                            websites.append(None)
                                            ratings.append(None)
                                            reviews_counts.append(None)
                                            continue
                                    
                                    # Utiliser retry pour l'enrichissement
                                    try:
                                        details = retry_with_backoff(
                                            enrich_maps_details,
                                            max_retries=2,
                                            delay=3,
                                            page=page,
                                            maps_link=row.get('Maps_Link')
                                        )
                                    except Exception as enrich_error:
                                        print(f"    ⚠️  Erreur enrichissement après retry: {enrich_error}")
                                        details = {
                                            "Address": None,
                                            "Phone": None,
                                            "Website": None,
                                            "Rating": None,
                                            "Reviews_Count": None
                                        }
                                    
                                    # Afficher ce qui a été trouvé
                                    found_items = []
                                    if details.get('Address'):
                                        found_items.append(f"📍")
                                    if details.get('Phone'):
                                        found_items.append(f"📞")
                                    if details.get('Website'):
                                        found_items.append(f"🌐")
                                    if details.get('Rating'):
                                        found_items.append(f"⭐")
                                    if details.get('Reviews_Count'):
                                        found_items.append(f"💬")
                                    
                                    if found_items:
                                        print(f"    ✅ Trouvé: {', '.join(found_items)}")
                                    
                                    addresses.append(details.get('Address'))
                                    phones.append(details.get('Phone'))
                                    websites.append(details.get('Website'))
                                    ratings.append(details.get('Rating'))
                                    reviews_counts.append(details.get('Reviews_Count'))
                                    
                                    random_delay(MIN_PAGE_DELAY, MAX_PAGE_DELAY)
                                except Exception as e:
                                    print(f"    ⚠️  Erreur: {e}")
                                    addresses.append(None)
                                    phones.append(None)
                                    websites.append(None)
                                    ratings.append(None)
                                    reviews_counts.append(None)
                            
                            df_search['Address'] = addresses
                            df_search['Phone'] = phones
                            df_search['Website'] = websites
                            df_search['Rating'] = ratings
                            df_search['Reviews_Count'] = reviews_counts
                            
                            # ===== PHASE 3: MINING (Emails) =====
                            print(f"\n⛏️  PHASE 3: MINING - {len(df_search)} entreprises")
                            
                            final_emails = []
                            final_socials = []
                            final_status = []
                            
                            for idx, row in df_search.iterrows():
                                website = row.get('Website')
                                
                                if pd.notna(website) and website:
                                    try:
                                        print(f"  🔎 {row['Company']} ({idx+1}/{len(df_search)})")
                                        
                                        # Vérifier l'état avant le mining
                                        is_alive, browser, context, page = is_browser_alive(browser, context, page)
                                        if not is_alive or not page:
                                            print("    ⚠️  Navigateur fermé, recréation...")
                                            browser, context, page = recreate_browser_context_internal(p, browser)
                                        
                                        # Utiliser retry pour le mining
                                        try:
                                            emails, socials, status = retry_with_backoff(
                                                enrich_company_data_playwright,
                                                max_retries=2,
                                                delay=5,
                                                page=page,
                                                website_url=website
                                            )
                                        except:
                                            emails, socials, status = None, None, "Error"
                                        
                                        final_emails.append(emails)
                                        final_socials.append(socials)
                                        final_status.append(status)
                                        random_delay(2, 4)
                                    except Exception as e:
                                        print(f"    ⚠️  Erreur: {e}")
                                        final_emails.append(None)
                                        final_socials.append(None)
                                        final_status.append("Error")
                                else:
                                    final_emails.append(None)
                                    final_socials.append(None)
                                    final_status.append("No Website")
                            
                            df_search['Email'] = final_emails
                            df_search['Social_Links'] = final_socials
                            df_search['Status'] = final_status
                            
                            # Nettoyer et valider les emails
                            print(f"\n🧹 Nettoyage et validation des emails...")
                            df_search['Email'] = df_search['Email'].apply(clean_emails)
                            valid_emails = df_search['Email'].notna().sum()
                            print(f"   ✅ {valid_emails}/{len(df_search)} emails valides")
                            
                            # Ajouter au DataFrame global (sans doublons)
                            all_data.extend(df_search.to_dict('records'))
                            
                            # Supprimer les doublons basés sur le nom ET l'adresse
                            df_all = pd.DataFrame(all_data)
                            
                            # Dédupliquer par Maps_Link (URL unique)
                            df_all = df_all.drop_duplicates(subset=['Maps_Link'], keep='first')
                            
                            # Dédupliquer aussi par nom+ville pour les cas où Maps_Link diffère
                            df_all['_temp_key'] = df_all['Company'].str.lower().str.strip() + '_' + df_all['City'].fillna('').str.lower()
                            df_all = df_all.drop_duplicates(subset=['_temp_key'], keep='first')
                            df_all = df_all.drop(columns=['_temp_key'])
                            
                            # Mettre à jour all_data avec les données dédupliquées
                            all_data = df_all.to_dict('records')
                            
                            # Sauvegarder après chaque combinaison complète
                            df_all = pd.DataFrame(all_data)
                            df_all = df_all.drop_duplicates(subset=['Company'], keep='first')
                            save_intermediate_data(df_all)
                            
                            # Sauvegarder aussi dans la base de données
                            save_to_database(df_all)
                            
                            completed_combos.append(combo)
                            save_checkpoint(city, keyword, completed_combos)
                            
                            print(f"\n✅ {city} - {keyword}: {len(df_search)} entreprises complètes sauvegardées")
                            print(f"📊 Total global: {len(df_all)} entreprises uniques")
                            
                            random_delay(3, 6)  # Pause entre combinaisons
                            
                        except Exception as e:
                            error_msg = str(e).lower()
                            print(f"  ⚠️  Erreur sur {city} - {keyword}: {e}")
                            
                            # Si le navigateur est fermé, essayer de le recréer
                            if "closed" in error_msg or "browser" in error_msg or "target" in error_msg:
                                print("  ⚠️  Navigateur fermé, tentative de récupération...")
                                try:
                                    browser, context, page = recreate_browser_context_internal(p, browser)
                                    print("  ✅ Navigateur recréé, on continue")
                                    random_delay(5, 10)
                                    # Ne pas marquer comme complété, on réessaiera
                                    continue
                                except Exception as rec_error:
                                    print(f"  ❌ Impossible de recréer le navigateur: {rec_error}")
                                    print("  ⏸️  Pause de 60 secondes avant nouvelle tentative...")
                                    time.sleep(60)
                                    try:
                                        browser, context, page = recreate_browser_context_internal(p)
                                        print("  ✅ Navigateur recréé après pause, on continue")
                                        continue
                                    except:
                                        print("  ❌ Échec définitif, marquage comme complété et passage au suivant")
                                        completed_combos.append(combo)
                                        save_checkpoint(city, keyword, completed_combos)
                                        continue
                            
                            # Pour les autres erreurs, marquer comme complété et continuer
                            print(f"  ⚠️  Erreur non critique, passage au suivant")
                            completed_combos.append(combo)
                            save_checkpoint(city, keyword, completed_combos)
                            random_delay(3, 6)  # Pause avant de continuer
                            continue
                
                # Nettoyer les doublons finaux
                df = pd.DataFrame(all_data)
                if not df.empty:
                    df = df.drop_duplicates(subset=['Company'], keep='first')
                    print(f"\n📊 Total final après nettoyage: {len(df)} entreprises uniques")
                else:
                    print("\n⚠️  Aucune donnée récupérée.")
                    return
                
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
                print(f"📧 Avec email valide: {df['Email'].notna().sum()}")
                print(f"💾 Base de données: {DATABASE_FILE}")
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


import os
import re
import sqlite3
import subprocess
import time
import json
import tempfile
import io
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, urljoin, quote

# Imports optionnels pour les méthodes avancées
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

LOG_PATH = os.path.join(os.path.dirname(__file__), "pipeline.log")

# Queue globale pour les logs en temps réel (sera initialisée par app.py)
# Note: Utilise un nom différent pour éviter le conflit avec le paramètre de fonction
_global_logs_queue = None


def log(msg):
    ts = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    
    # Écrire dans le fichier (pour compatibilité)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass  # Ignore les erreurs d'écriture fichier
    
    # Écrire dans la queue pour streaming temps réel (SSE)
    global _global_logs_queue
    if _global_logs_queue is not None:
        try:
            # Si la queue est pleine, enlever l'ancien élément
            if _global_logs_queue.full():
                try:
                    _global_logs_queue.get_nowait()
                except:
                    pass
            _global_logs_queue.put_nowait(line)
        except Exception:
            pass  # Ignore les erreurs de queue (non bloquant)


class OsintPipeline:
    def __init__(self, db_path, status_ref, stop_flag_ref, logs_queue_ref=None):
        self.db_path = db_path
        self.status = status_ref
        self.stop_flag = stop_flag_ref
        self.available_tools = {}
        # Initialiser la queue globale pour les logs
        global _global_logs_queue
        _global_logs_queue = logs_queue_ref
        self.check_tools()
        self.ensure_columns()
    
    def check_tools(self):
        """Vérifie quels outils sont disponibles"""
        tools = ["curl", "whatweb", "theHarvester", "subfinder", "amass", "whois"]
        for tool in tools:
            try:
                result = subprocess.run(["which", tool], capture_output=True, timeout=3)
                self.available_tools[tool] = (result.returncode == 0)
            except:
                self.available_tools[tool] = False
        
        available = [t for t, v in self.available_tools.items() if v]
        missing = [t for t, v in self.available_tools.items() if not v]
        log(f"Outils disponibles: {', '.join(available) if available else 'aucun'}")
        if missing:
            log(f"⚠️  Outils manquants: {', '.join(missing)}")

    def ensure_columns(self):
        cols = [
            ("tech_stack", "TEXT"),
            ("emails_osint", "TEXT"),
            ("pdf_emails", "TEXT"),
            ("subdomains", "TEXT"),
            ("whois_raw", "TEXT"),
            ("wayback_urls", "TEXT"),
            ("osint_status", "TEXT"),
            ("osint_updated_at", "TEXT"),
            # Nouvelles colonnes pour les 11 méthodes OSINT
            ("osint_employees", "TEXT"),  # Noms d'employés trouvés
            ("osint_html_comments", "TEXT"),  # Emails depuis commentaires HTML
            ("osint_github_data", "TEXT"),  # Données GitHub
            ("osint_social_data", "TEXT"),  # Données réseaux sociaux
        ]
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(companies);")
        existing = {row[1] for row in cur.fetchall()}
        for col, ctype in cols:
            if col not in existing:
                cur.execute(f"ALTER TABLE companies ADD COLUMN {col} {ctype};")
        conn.commit()
        conn.close()

    def fetch_targets(self, city=None, limit=50, require_website=True):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        filters = ["(osint_status IS NULL OR osint_status NOT IN ('Done','Skipped'))"]
        params = []
        if city:
            filters.append("city = ?")
            params.append(city)
        if require_website:
            filters.append("website IS NOT NULL AND website <> ''")

        where_clause = "WHERE " + " AND ".join(filters)
        query = f"""
            SELECT id, company_name, website, email, social_links
            FROM companies
            {where_clause}
            ORDER BY id ASC
            LIMIT ?
        """
        params.append(limit)
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    def run(self, city=None, limit=50, require_website=True):
        try:
            log("=" * 60)
            log("🚀 Pipeline OSINT démarré")
            log(f"📋 Paramètres: city={city}, limit={limit}, require_website={require_website}")
            targets = self.fetch_targets(city, limit, require_website)
            total = len(targets)
            self.status["total"] = total
            if total == 0:
                self.status["message"] = "Aucune cible à enrichir"
                self.status["running"] = False
                log("⚠️  Aucune cible trouvée avec ces filtres")
                return
            
            # Afficher les IDs récupérés pour diagnostic
            ids_list = [str(row[0]) for row in targets[:10]]
            if total > 10:
                ids_preview = ", ".join(ids_list) + f"... (+{total-10} autres)"
            else:
                ids_preview = ", ".join(ids_list)
            
            log(f"✅ {total} cible(s) trouvée(s)")
            log(f"📊 IDs à enrichir: {ids_preview}")

            for idx, (cid, name, website, email, social_links) in enumerate(targets, start=1):
            if self.stop_flag():
                log("⏸️  Arrêt demandé, sortie propre.")
                self.status["message"] = "Arrêt demandé"
                break

            self.status["processed"] = idx - 1
            self.status["current"] = {"id": cid, "company": name, "website": website}
            self.status["message"] = f"Enrichissement {idx}/{total}"
            
            log("")
            log("=" * 60)
            log(f"🔄 Enrichissement #{idx}/{total}")
            log(f"📌 ID: {cid} | Entreprise: {name}")
            log(f"🌐 Site: {website}")
            log("=" * 60)

            # Initialiser les variables par défaut
            tech_stack = None
            emails_osint = None
            pdf_emails = None
            subdomains = None
            wayback_urls = None
            whois_raw = None
            osint_employees = None
            osint_html_comments = None
            osint_github_data = None
            osint_social_data = None
            web_scraping_result = None
            pdf_result = None
            google_dorks_result = None
            subdomain_scraping_result = None
            whois_result = None
            social_data = None
            html_comments_result = None
            github_data = None
            robots_sitemap_result = None

            # Wrapper pour capturer toutes les exceptions et continuer
            try:
                # Méthode 1: WhatWeb (tech stack)
                log("  🔍 Démarrage WhatWeb...")
                tech_stack = self.run_whatweb(website)
                log(f"  ✅ WhatWeb terminé")
                
                # Méthode 2: theHarvester (emails)
                log("  🔍 Démarrage theHarvester...")
                emails_osint = self.run_email_tools(website)
                log(f"  ✅ theHarvester terminé")
                
                # Méthode 3: Web Scraping (About/Team/Contact)
                log("  🔍 Démarrage Web Scraping...")
                web_scraping_result = self.run_web_scraping(website)
                log(f"  ✅ Web Scraping terminé")
                if web_scraping_result:
                    # Fusionner les emails trouvés
                    if web_scraping_result.get('emails'):
                        existing_emails = set((emails_osint or "").split(", "))
                        existing_emails.update(web_scraping_result['emails'])
                        emails_osint = ", ".join(sorted(existing_emails))
                
                # Méthode 4: Extraction PDF
                log("  🔍 Démarrage Extraction PDF...")
                pdf_result = self.run_pdf_extraction(website)
                if pdf_result:
                    pdf_emails = pdf_result.get('emails')
                    if pdf_emails:
                        existing_emails = set((emails_osint or "").split(", "))
                        existing_emails.update(pdf_result['emails'])
                        emails_osint = ", ".join(sorted(existing_emails))
                else:
                    pdf_emails = None
                log(f"  ✅ Extraction PDF terminé")
                
                # Méthode 5: Google Dorks
                log("  🔍 Démarrage Google Dorks...")
                google_dorks_result = self.run_google_dorks(website, name)
                if google_dorks_result and google_dorks_result.get('emails'):
                    existing_emails = set((emails_osint or "").split(", "))
                    existing_emails.update(google_dorks_result['emails'])
                    emails_osint = ", ".join(sorted(existing_emails))
                log(f"  ✅ Google Dorks terminé")
                
                # Méthode 6: Subdomain Scraping manuel
                log("  🔍 Démarrage Subdomain Scraping...")
                subdomain_scraping_result = self.run_subdomain_scraping(website)
                if subdomain_scraping_result and subdomain_scraping_result.get('emails'):
                    existing_emails = set((emails_osint or "").split(", "))
                    existing_emails.update(subdomain_scraping_result['emails'])
                    emails_osint = ", ".join(sorted(existing_emails))
                log(f"  ✅ Subdomain Scraping terminé")
                
                # Méthode 7: Subfinder (sous-domaines)
                log("  🔍 Démarrage Subfinder...")
                subdomains = self.run_subfinder(website)
                log(f"  ✅ Subfinder terminé")
                
                # Méthode 8: Wayback Machine
                log("  🔍 Démarrage Wayback Machine...")
                wayback_urls = self.run_wayback(website)
                log(f"  ✅ Wayback Machine terminé")
                
                # Méthode 9: WHOIS Parsing (amélioré pour emails et noms)
                log("  🔍 Démarrage WHOIS Enhanced...")
                whois_result = self.run_whois_enhanced(website)
                whois_raw = whois_result.get('raw') if whois_result else None
                if whois_result and whois_result.get('emails'):
                    existing_emails = set((emails_osint or "").split(", "))
                    existing_emails.update(whois_result['emails'])
                    emails_osint = ", ".join(sorted(existing_emails))
                log(f"  ✅ WHOIS Enhanced terminé")
                
                # Méthode 10: Réseaux sociaux
                log("  🔍 Démarrage Scraping Réseaux sociaux...")
                social_data = self.run_social_media_scraping(website, social_links)
                log(f"  ✅ Réseaux sociaux terminé")
                
                # Méthode 11: Commentaires HTML
                log("  🔍 Démarrage Extraction Commentaires HTML...")
                html_comments_result = self.run_html_comments(website)
                if html_comments_result and html_comments_result.get('emails'):
                    existing_emails = set((emails_osint or "").split(", "))
                    existing_emails.update(html_comments_result['emails'])
                    emails_osint = ", ".join(sorted(existing_emails))
                log(f"  ✅ Commentaires HTML terminé")
                
                # Méthode 12: GitHub Scraping
                log("  🔍 Démarrage GitHub Scraping...")
                github_data = self.run_github_scraping(website, name)
                log(f"  ✅ GitHub Scraping terminé")
                
                # Méthode 13: Robots.txt/Sitemap
                log("  🔍 Démarrage Robots.txt/Sitemap...")
                robots_sitemap_result = self.run_robots_sitemap(website)
                if robots_sitemap_result and robots_sitemap_result.get('emails'):
                    existing_emails = set((emails_osint or "").split(", "))
                    existing_emails.update(robots_sitemap_result['emails'])
                    emails_osint = ", ".join(sorted(existing_emails))
                log(f"  ✅ Robots.txt/Sitemap terminé")
                
            except Exception as e:
                log(f"  ❌ ERREUR lors de l'enrichissement: {str(e)}")
                import traceback
                log(f"  📋 Traceback: {traceback.format_exc()[:500]}")
                # Continuer quand même avec les données collectées jusqu'ici
            
            # Collecter tous les employés trouvés
            all_employees = set()
            if web_scraping_result and web_scraping_result.get('employees'):
                all_employees.update(web_scraping_result['employees'])
            if pdf_result and pdf_result.get('employees'):
                all_employees.update(pdf_result['employees'])
            if google_dorks_result and google_dorks_result.get('employees'):
                all_employees.update(google_dorks_result['employees'])
            if whois_result and whois_result.get('employees'):
                all_employees.update(whois_result['employees'])
            if social_data and social_data.get('employees'):
                all_employees.update(social_data['employees'])
            
            osint_employees = ", ".join(sorted(all_employees)) if all_employees else None
            osint_html_comments = html_comments_result.get('emails_str') if html_comments_result else None

            log("")
            log(f"💾 Sauvegarde en BDD...")
            log(f"   ID: {cid} | Entreprise: {name}")
            try:
                self.update_company(
                    cid,
                    tech_stack=tech_stack,
                    emails_osint=emails_osint if emails_osint else None,
                    pdf_emails=pdf_emails if pdf_emails else None,
                    subdomains=subdomains,
                    whois_raw=whois_raw,
                    wayback_urls=wayback_urls,
                    osint_employees=osint_employees,
                    osint_html_comments=osint_html_comments,
                    osint_github_data=github_data,
                    osint_social_data=social_data.get('data_str') if social_data else None,
                )
                log(f"✅ ID {cid} - {name} terminé et sauvegardé en BDD")
            except Exception as e:
                log(f"  ❌ ERREUR lors de la sauvegarde ID {cid}: {str(e)}")
                import traceback
                log(f"  📋 Traceback: {traceback.format_exc()[:500]}")
                # Continuer quand même
            
                # ✅ CORRECTION: Mettre à jour processed APRÈS avoir terminé l'entreprise
                self.status["processed"] = idx
                time.sleep(1.0)

            # ✅ CORRECTION: S'assurer que processed = total à la fin
            self.status["processed"] = total
            self.status["running"] = False
            self.status["message"] = "Terminé"
            log("Pipeline terminé.")
        except Exception as e:
            log(f"❌ ERREUR CRITIQUE dans run(): {str(e)}")
            import traceback
            log(f"📋 Traceback: {traceback.format_exc()}")
            # S'assurer que le statut est mis à jour même en cas d'erreur
            self.status["running"] = False
            self.status["message"] = f"Erreur: {str(e)[:100]}"
            # Re-lancer pour que app.py le capture dans le finally
            raise

    # ---------- Individual steps ----------
    def run_cmd(self, cmd, timeout=40, allow_nonzero=False):
        """Exécute une commande si l'outil est disponible"""
        tool_name = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
        
        # Si l'outil n'est pas marqué comme disponible, ne pas essayer
        if not self.available_tools.get(tool_name, False):
            return ""
        
        try:
            if allow_nonzero:
                # Utiliser run() pour permettre les codes de retour non-zéro
                result = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
                # Retourner la sortie même si le code de retour n'est pas 0
                return result.stdout if result.stdout else result.stderr
            else:
                # Utiliser check_output() pour les outils qui doivent retourner 0
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout, text=True)
                return out
        except subprocess.TimeoutExpired:
            # Timeout est silencieux (normal pour certains outils)
            return ""
        except subprocess.CalledProcessError as e:
            # Code de retour non-zéro : peut être normal (pas de résultats)
            # Ne pas logger comme erreur si allow_nonzero
            if allow_nonzero:
                return e.stdout if e.stdout else ""
            # Sinon, c'est une vraie erreur
            return ""
        except FileNotFoundError:
            # Marquer comme non disponible pour éviter de réessayer
            self.available_tools[tool_name] = False
            return ""
        except Exception as e:
            # Seulement logger les vraies exceptions
            if "No such file" not in str(e):
                log(f"  ⚠️  Erreur {tool_name}: {str(e)[:80]}")
            return ""

    def run_whatweb(self, website):
        if not website or not self.available_tools.get("whatweb"):
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        if not domain:
            return None
        
        # Essayer d'abord avec --log-verbose pour plus d'infos
        res = self.run_cmd(["whatweb", domain, "--log-verbose=-", "--no-errors"], timeout=30)
        if not res:
            # Fallback sur log-brief
            res = self.run_cmd(["whatweb", domain, "--log-brief=-", "--no-errors"], timeout=30)
        
        if not res:
            return None
        
        # Nettoyer les codes ANSI de couleur
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', res)
        
        # Extraire les technologies importantes
        tech_found = []
        
        # Technologies CMS
        if re.search(r'\bWordPress\b', cleaned, re.I):
            tech_found.append('WordPress')
            # Chercher la version si disponible
            wp_version = re.search(r'WordPress\[([^\]]+)\]', cleaned, re.I)
            if wp_version:
                tech_found.append(f"WP {wp_version.group(1)}")
        
        # Plugins WordPress
        if re.search(r'\bYoast\b', cleaned, re.I):
            tech_found.append('Yoast SEO')
        if re.search(r'\bWooCommerce\b', cleaned, re.I):
            tech_found.append('WooCommerce')
        if re.search(r'\bElementor\b', cleaned, re.I):
            tech_found.append('Elementor')
        
        # Serveur web
        server_match = re.search(r'HTTPServer\[([^\]]+)\]', cleaned, re.I)
        if server_match:
            tech_found.append(f"Server: {server_match.group(1)}")
        
        # Frameworks JS
        if re.search(r'\bReact\b', cleaned, re.I):
            tech_found.append('React')
        if re.search(r'\bVue\.js\b', cleaned, re.I):
            tech_found.append('Vue.js')
        if re.search(r'\bAngular\b', cleaned, re.I):
            tech_found.append('Angular')
        
        # jQuery
        jquery_match = re.search(r'JQuery\[([^\]]+)\]', cleaned, re.I)
        if jquery_match:
            tech_found.append(f"jQuery {jquery_match.group(1)}")
        
        # IP
        ip_match = re.search(r'IP\[([^\]]+)\]', cleaned, re.I)
        if ip_match:
            tech_found.append(f"IP: {ip_match.group(1)}")
        
        # Pays
        country_match = re.search(r'Country\[[^\]]+\]\[([^\]]+)\]', cleaned, re.I)
        if country_match:
            tech_found.append(f"Pays: {country_match.group(1)}")
        
        # Si aucune tech spécifique trouvée, utiliser les infos de base
        if not tech_found:
            lines = [l.strip() for l in cleaned.splitlines() if l.strip() and not l.startswith('http://')]
            # Prendre les premières infos utiles
            for line in lines[:5]:
                if 'HTTPServer' in line or 'IP' in line or 'Country' in line:
                    tech_found.append(line.split('[')[0].strip() if '[' in line else line[:50])
        
        result = " | ".join(tech_found[:8])[:500] if tech_found else None
        
        if result:
            log(f"  ✅ WhatWeb: {len(tech_found)} tech(s)")
        return result if result else None

    def run_email_tools(self, website):
        """
        Utilise theHarvester pour trouver des emails
        Inspiré du script local de l'utilisateur avec :
        - Sources fiables uniquement (bing, duckduckgo, yahoo, brave)
        - Parsing JSON propre avec fallback texte
        - Filtrage avancé des emails (exclusion des noreply, abuse, etc.)
        - Validation stricte
        """
        if not website:
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        emails = set()
        
        # theHarvester avec sources spécifiques (Google non supporté)
        if self.available_tools.get("theHarvester"):
            # Sources fiables qui fonctionnent bien (comme dans le script local)
            sources_list = ['bing', 'duckduckgo', 'yahoo', 'brave']
            
            # Préparation du domaine pour le filtrage
            domain_parts = domain.split('.')
            base_domain = '.'.join(domain_parts[-2:]) if len(domain_parts) >= 2 else domain
            domain_variations = [domain, base_domain, domain.replace('.', '')]
            
            # Patterns d'emails à exclure (comme dans le script local)
            excluded_patterns = [
                'noreply', 'no-reply', 'donotreply', 'no_reply',
                'example.com', 'test.com', 'sample.com', 'domain.com',
                'abuse@', 'postmaster@', 'hostmaster@', 'webmaster@'
            ]
            
            all_emails = set()
            
            log(f"  🔍 theHarvester: scan de {domain} ({len(sources_list)} sources fiables, limit=100)...")
            
            for source in sources_list:
                try:
                    # Crée un fichier temporaire pour les résultats JSON
                    import tempfile
                    temp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    temp_json_path = temp_json.name
                    temp_json.close()
                    
                    # Commande complète avec génération JSON
                    cmd = [
                        "theHarvester",
                        "-d", domain,
                        "-b", source,
                        "-l", "100",        # Limite de 100 résultats par source
                        "-f", temp_json_path  # Génère un fichier JSON
                    ]
                    
                    # Exécuter avec timeout raisonnable (90s par source)
                    result = self.run_cmd(cmd, allow_nonzero=True, timeout=90)
                    
                    # Essaie d'abord de lire le fichier JSON (méthode propre)
                    try:
                        if os.path.exists(temp_json_path + '.json'):
                            with open(temp_json_path + '.json', 'r') as f:
                                json_data = json.load(f)
                                # Extrait les emails depuis le JSON
                                if 'emails' in json_data:
                                    all_emails.update([e.lower() for e in json_data['emails']])
                                # Extrait aussi depuis les hosts (parfois les emails sont là)
                                if 'hosts' in json_data:
                                    for host in json_data['hosts']:
                                        if isinstance(host, dict) and 'email' in host:
                                            all_emails.add(host['email'].lower())
                    except Exception as e:
                        log(f"  ⚠️  Lecture JSON {source} échouée: {str(e)[:50]}")
                    
                    # Fallback: parse aussi la sortie texte
                    if result:
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        text_emails = re.findall(email_pattern, result)
                        all_emails.update([e.lower() for e in text_emails])
                    
                    # Nettoie le fichier temporaire
                    try:
                        os.unlink(temp_json_path)
                        if os.path.exists(temp_json_path + '.json'):
                            os.unlink(temp_json_path + '.json')
                        if os.path.exists(temp_json_path + '.xml'):
                            os.unlink(temp_json_path + '.xml')
                    except:
                        pass
                    
                except subprocess.TimeoutExpired:
                    log(f"  ⚠️  Timeout theHarvester pour source {source}")
                except Exception as e:
                    log(f"  ⚠️  Erreur theHarvester {source}: {str(e)[:50]}")
                
                # Petit délai entre les sources
                time.sleep(1)
            
            # Filtrage avancé des emails (comme dans le script local)
            valid_emails = []
            for email in all_emails:
                email_lower = email.lower()
                email_domain = email_lower.split('@')[1] if '@' in email_lower else ''
                
                # Vérifie si l'email appartient au domaine (plus flexible)
                is_domain_email = False
                for var in domain_variations:
                    if var in email_domain or email_domain.endswith('.' + var):
                        is_domain_email = True
                        break
                
                if is_domain_email:
                    # Exclut les emails génériques et techniques
                    if not any(pattern in email_lower for pattern in excluded_patterns):
                        # Exclut les emails trop courts ou suspects
                        if len(email_lower) > 5 and '.' in email_domain:
                            valid_emails.append(email_lower)
            
            emails.update(valid_emails)
            
            # Statistiques
            if emails:
                log(f"  ✅ theHarvester: {len(emails)} email(s) valide(s) pour {domain}")
            else:
                if all_emails:
                    log(f"  ℹ️  theHarvester: {len(all_emails)} email(s) trouvé(s), 0 valide après filtrage")
                else:
                    log(f"  ℹ️  theHarvester: scan terminé (aucun email trouvé)")
        
        result = ", ".join(sorted(emails)) if emails else None
        return result

    def extract_domain(self, url):
        """Extrait le domaine depuis une URL"""
        if not url:
            return ""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return url.replace('www.', '').split('/')[0]
    
    def get_session(self):
        """Crée une session requests avec headers"""
        if not REQUESTS_AVAILABLE:
            return None
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return session

    def run_subfinder(self, website):
        """
        Utilise subfinder pour trouver des sous-domaines
        Options : -silent (pas de banner), -all (toutes les sources), -recursive (recherche récursive)
        """
        if not website or not self.available_tools.get("subfinder"):
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Commande avec options avancées
        cmd = [
            "subfinder",
            "-d", domain,
            "-silent",          # Pas de banner
            "-all",             # Toutes les sources disponibles
            "-timeout", "60"    # Timeout de 60s par source
        ]
        
        log(f"  🔍 Subfinder: scan de {domain} (toutes sources)...")
        res = self.run_cmd(cmd, timeout=180)  # Timeout global de 3 minutes
        
        if not res:
            log(f"  ℹ️  Subfinder: aucun sous-domaine trouvé")
            return None
        
        # Nettoyer les codes ANSI
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned_res = ansi_escape.sub('', res)
        
        # Extraire uniquement les lignes qui sont des domaines valides
        # Ignorer les lignes de debug, erreurs, etc.
        subs = []
        for line in cleaned_res.splitlines():
            line = line.strip()
            if not line:
                continue
            
            # Ignorer les lignes qui sont clairement du debug/info (commencent par [ ou contiennent des mots-clés)
            if line.startswith('[') or line.startswith('('):
                continue
            if any(skip in line.lower() for skip in [
                'current subfinder version',
                '[inf]',
                '[warn]',
                '[error]',
                'using source',
                'timeout',
                'failed to',
                'no results found'
            ]):
                continue
            
            # Vérifier que c'est un domaine valide (contient un point, pas d'espaces, pas de caractères spéciaux)
            if '.' in line and ' ' not in line and not line.startswith('['):
                # Vérifier le format d'un domaine (lettres, chiffres, points, tirets)
                if re.match(r'^[a-zA-Z0-9.-]+$', line):
                    # Vérifier que c'est un sous-domaine du domaine cible
                    if domain.lower() in line.lower():
                        subs.append(line.lower())  # Normaliser en minuscules
        
        if subs:
            # Dédupliquer et trier
            unique_subs = sorted(set(subs))
            log(f"  ✅ Subfinder: {len(unique_subs)} sous-domaine(s) unique(s)")
            # Limiter à 100 sous-domaines pour éviter des strings trop longues en BDD
            return ", ".join(unique_subs[:100]) if unique_subs else None
        
        log(f"  ℹ️  Subfinder: aucun sous-domaine valide trouvé")
        return None

    def run_whois(self, website):
        """
        Exécute whois sur le domaine
        whois peut retourner un code non-zéro si pas de résultat
        """
        if not website or not self.available_tools.get("whois"):
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        
        # whois peut retourner code 2 si le domaine n'existe pas ou n'est pas trouvé
        res = self.run_cmd(["whois", domain], timeout=30, allow_nonzero=True)
        
        if res and len(res.strip()) > 50:  # Au moins 50 caractères pour être valide
            # Extraire les infos importantes
            lines = res.splitlines()
            important_lines = []
            for line in lines:
                lower_line = line.lower()
                # Garder les lignes avec des infos utiles
                if any(keyword in lower_line for keyword in [
                    'registrar:', 'creation date:', 'expiry date:', 'updated date:',
                    'name server:', 'status:', 'organization:', 'registrant'
                ]):
                    important_lines.append(line.strip())
            
            # Si on a des infos importantes, les utiliser, sinon garder tout
            if important_lines:
                result = "\n".join(important_lines[:30])  # Max 30 lignes importantes
                log(f"  ✅ WHOIS: {len(important_lines)} info(s) extraite(s)")
            else:
                result = res[:4000]  # Limiter à 4000 caractères
                log(f"  ✅ WHOIS: {len(res)} caractères")
            
            return result
        else:
            log(f"  ℹ️  WHOIS: pas de résultat pour {domain}")
            return None

    def run_wayback(self, website):
        if not website or not self.available_tools.get("curl"):
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        url = f"https://web.archive.org/cdx/search?url={domain}&output=txt&fl=original&filter=statuscode:200&limit=50"
        res = self.run_cmd(["curl", "-s", url], timeout=20)
        urls = [u.strip() for u in res.splitlines() if u.strip().startswith("http")]
        
        if not urls:
            return None
        
        # Nettoyer et dédupliquer les URLs
        cleaned_urls = []
        seen = set()
        
        for u in urls:
            # Normaliser l'URL (enlever trailing slash, convertir en minuscules)
            normalized = u.rstrip('/').lower()
            # Garder la version avec https si disponible
            if normalized not in seen:
                seen.add(normalized)
                # Préférer https
                if u.startswith('https://'):
                    cleaned_urls.append(u.rstrip('/'))
                elif u.startswith('http://'):
                    https_version = u.replace('http://', 'https://').rstrip('/')
                    if https_version.lower() not in seen:
                        cleaned_urls.append(https_version)
                    else:
                        # Remplacer http par https dans la liste
                        cleaned_urls = [url if url.lower() != https_version.lower() else https_version for url in cleaned_urls]
        
        # Limiter à 20 URLs uniques
        unique_urls = list(dict.fromkeys(cleaned_urls))[:20]
        
        if unique_urls:
            log(f"  ✅ Wayback: {len(unique_urls)} URLs uniques")
        return ", ".join(unique_urls) if unique_urls else None

    # ========== MÉTHODE 2: Web Scraping (About/Team/Contact) ==========
    def run_web_scraping(self, website):
        """Scrape les pages About, Team, Contact pour trouver emails et noms"""
        if not website or not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            return None
        
        log(f"  🔍 Web Scraping: scan de {website}...")
        results = {'emails': set(), 'employees': set()}
        domain = self.extract_domain(website)
        session = self.get_session()
        
        if not session:
            return None
        
        pages_to_check = [
            '/about', '/about-us', '/team', '/contact', '/contact-us',
            '/staff', '/employees', '/people', '/equipe', '/a-propos'
        ]
        pages_to_check.insert(0, '/')  # Page principale
        
        for page in pages_to_check:
            try:
                url = urljoin(website, page)
                response = session.get(url, timeout=10, allow_redirects=True, verify=True)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extraction des emails
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    text = soup.get_text()
                    emails = re.findall(email_pattern, text)
                    results['emails'].update([e.lower() for e in emails if domain.lower() in e.lower()])
                    
                    # Extraction des noms
                    name_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
                    for elem in name_elements:
                        text = elem.get_text().strip()
                        if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$', text):
                            if len(text) > 3 and len(text) < 50:
                                results['employees'].add(text)
                    
                    # Cherche dans les attributs data-*
                    for tag in soup.find_all(attrs={'data-name': True}):
                        results['employees'].add(tag['data-name'])
                
                time.sleep(1)  # Délai entre les pages
            except Exception as e:
                continue
        
        if results['emails'] or results['employees']:
            log(f"  ✅ Web Scraping: {len(results['emails'])} email(s), {len(results['employees'])} employé(s)")
        
        return {
            'emails': results['emails'],
            'employees': results['employees']
        } if (results['emails'] or results['employees']) else None

    # ========== MÉTHODE 3: Extraction PDF ==========
    def run_pdf_extraction(self, website):
        """Télécharge et extrait les emails depuis les PDFs trouvés sur le site"""
        if not website or not REQUESTS_AVAILABLE or not BS4_AVAILABLE or not PDF_AVAILABLE:
            return None
        
        log(f"  🔍 Extraction PDF: scan de {website}...")
        results = {'emails': set(), 'employees': set()}
        domain = self.extract_domain(website)
        session = self.get_session()
        
        if not session:
            return None
        
        try:
            response = session.get(website, timeout=10, verify=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                pdf_links = []
                
                # Trouve tous les liens vers des PDFs
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.lower().endswith('.pdf'):
                        full_url = urljoin(website, href)
                        pdf_links.append(full_url)
                
                # Limite à 5 PDFs
                for pdf_url in pdf_links[:5]:
                    try:
                        pdf_response = session.get(pdf_url, timeout=15, verify=True)
                        if pdf_response.status_code == 200:
                            pdf_file = io.BytesIO(pdf_response.content)
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            
                            text = ""
                            for page in pdf_reader.pages[:5]:  # Limite à 5 pages
                                text += page.extract_text()
                            
                            # Extraction des emails
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, text)
                            results['emails'].update([e.lower() for e in emails if domain.lower() in e.lower()])
                            
                            # Extraction de noms
                            lines = text.split('\n')
                            for line in lines:
                                if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line.strip()):
                                    results['employees'].add(line.strip()[:50])
                        
                        time.sleep(1)
                    except Exception:
                        continue
        except Exception:
            pass
        
        if results['emails'] or results['employees']:
            log(f"  ✅ Extraction PDF: {len(results['emails'])} email(s), {len(results['employees'])} employé(s)")
        
        return {
            'emails': results['emails'],
            'employees': results['employees']
        } if (results['emails'] or results['employees']) else None

    # ========== MÉTHODE 4: Google Dorks ==========
    def run_google_dorks(self, website, company_name):
        """Utilise Google Dorks avec Selenium/Firefox pour trouver des emails"""
        if not website:
            return None
        
        domain = self.extract_domain(website)
        log(f"  🔍 Google Dorks: scan de {domain}...")
        results = {'emails': set(), 'employees': set()}
        
        driver = None
        try:
            if SELENIUM_AVAILABLE:
                try:
                    firefox_options = FirefoxOptions()
                    firefox_options.add_argument('--headless')
                    firefox_options.add_argument('--no-sandbox')
                    firefox_options.add_argument('--disable-dev-shm-usage')
                    firefox_options.set_preference("general.useragent.override", 
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0")
                    firefox_options.set_preference("dom.webdriver.enabled", False)
                    firefox_options.set_preference("useAutomationExtension", False)
                    
                    driver = webdriver.Firefox(options=firefox_options)
                    driver.set_page_load_timeout(30)
                except WebDriverException:
                    driver = None
            
            # Dorks pour trouver des emails
            dorks = [
                f'site:{domain} "@{domain}"',
                f'site:{domain} "email" OR "contact"',
                f'"{company_name}" "@{domain}"',
            ]
            
            session = self.get_session()
            for dork in dorks:
                try:
                    search_url = f"https://www.google.com/search?q={quote(dork)}&num=20"
                    
                    if driver:
                        try:
                            driver.get(search_url)
                            time.sleep(3)
                            page_source = driver.page_source
                            soup = BeautifulSoup(page_source, 'html.parser')
                            text = soup.get_text()
                            
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, text)
                            valid_emails = [e.lower() for e in emails if domain.lower() in e.lower()]
                            results['emails'].update(valid_emails)
                            
                            # Extraction de noms
                            for result_div in soup.find_all(['div', 'h3'], class_=re.compile(r'result|search')):
                                result_text = result_div.get_text()
                                name_matches = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b', result_text)
                                for name in name_matches:
                                    if len(name) > 3 and len(name) < 50:
                                        results['employees'].add(name)
                        except TimeoutException:
                            pass
                        except Exception:
                            pass
                    elif session:
                        # Fallback: requests (moins efficace)
                        response = session.get(search_url, timeout=10, verify=True)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            text = soup.get_text()
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, text)
                            valid_emails = [e.lower() for e in emails if domain.lower() in e.lower()]
                            results['emails'].update(valid_emails)
                    
                    time.sleep(5)  # Délai pour éviter la détection
                except Exception:
                    continue
        except Exception:
            pass
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        if results['emails'] or results['employees']:
            log(f"  ✅ Google Dorks: {len(results['emails'])} email(s), {len(results['employees'])} employé(s)")
        
        return {
            'emails': results['emails'],
            'employees': results['employees']
        } if (results['emails'] or results['employees']) else None

    # ========== MÉTHODE 5: Subdomain Scraping manuel ==========
    def run_subdomain_scraping(self, website):
        """Scrape les subdomains communs pour trouver des emails"""
        if not website or not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            return None
        
        domain = self.extract_domain(website)
        log(f"  🔍 Subdomain Scraping: scan de {domain}...")
        results = {'emails': set()}
        session = self.get_session()
        
        if not session:
            return None
        
        common_subdomains = [
            'www', 'mail', 'webmail', 'blog', 'news', 'newsletter',
            'contact', 'about', 'team', 'careers', 'jobs'
        ]
        
        for subdomain in common_subdomains:
            try:
                url = f"https://{subdomain}.{domain}"
                response = session.get(url, timeout=10, allow_redirects=True, verify=True)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text()
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, text)
                    results['emails'].update([e.lower() for e in emails if domain.lower() in e.lower()])
                time.sleep(1)
            except Exception:
                continue
        
        if results['emails']:
            log(f"  ✅ Subdomain Scraping: {len(results['emails'])} email(s)")
        
        return {'emails': results['emails']} if results['emails'] else None

    # ========== MÉTHODE 9: WHOIS Enhanced (emails et noms) ==========
    def run_whois_enhanced(self, website):
        """WHOIS amélioré pour extraire emails et noms"""
        if not website or not self.available_tools.get("whois"):
            return None
        
        domain = self.extract_domain(website)
        res = self.run_cmd(["whois", domain], timeout=30, allow_nonzero=True)
        
        if not res or len(res.strip()) < 50:
            return None
        
        results = {'raw': res, 'emails': set(), 'employees': set()}
        
        # Extraction des emails depuis WHOIS
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, res)
        results['emails'].update([e.lower() for e in emails])
        
        # Extraction de noms
        name_patterns = [
            r'Registrant Name:\s*(.+)',
            r'Admin Name:\s*(.+)',
            r'Tech Name:\s*(.+)',
        ]
        for pattern in name_patterns:
            matches = re.findall(pattern, res, re.IGNORECASE)
            for match in matches:
                name = match.strip().split('\n')[0].strip()
                if name and '@' not in name and len(name) < 50:
                    results['employees'].add(name)
        
        # Extraire les infos importantes pour le raw
        lines = res.splitlines()
        important_lines = []
        for line in lines:
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in [
                'registrar:', 'creation date:', 'expiry date:', 'updated date:',
                'name server:', 'status:', 'organization:', 'registrant'
            ]):
                important_lines.append(line.strip())
        
        if important_lines:
            results['raw'] = "\n".join(important_lines[:30])
            log(f"  ✅ WHOIS Enhanced: {len(results['emails'])} email(s), {len(results['employees'])} nom(s)")
        else:
            results['raw'] = res[:4000]
            log(f"  ✅ WHOIS Enhanced: {len(results['emails'])} email(s)")
        
        return results

    # ========== MÉTHODE 10: Réseaux sociaux ==========
    def run_social_media_scraping(self, website, social_links):
        """Scrape les pages de réseaux sociaux mentionnées"""
        if not social_links or not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            return None
        
        log(f"  🔍 Réseaux sociaux: scan...")
        results = {'emails': set(), 'employees': set(), 'data_str': None}
        session = self.get_session()
        
        if not session:
            return None
        
        try:
            links = [link.strip() for link in social_links.split(',') if link.strip()]
            
            for link in links[:3]:  # Limite à 3 liens
                try:
                    if 'linkedin.com' in link.lower():
                        response = session.get(link, timeout=10, allow_redirects=True)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            text = soup.get_text()
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, text)
                            results['emails'].update([e.lower() for e in emails])
                            
                            for meta in soup.find_all('meta', property=True):
                                if 'name' in meta.get('property', '').lower():
                                    name = meta.get('content', '')
                                    if name and len(name) < 50:
                                        results['employees'].add(name)
                    
                    elif 'facebook.com' in link.lower() or 'twitter.com' in link.lower() or 'x.com' in link.lower():
                        response = session.get(link, timeout=10, allow_redirects=True)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            text = soup.get_text()
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            emails = re.findall(email_pattern, text)
                            results['emails'].update([e.lower() for e in emails])
                    
                    time.sleep(2)
                except Exception:
                    continue
        except Exception:
            pass
        
        if results['emails'] or results['employees']:
            log(f"  ✅ Réseaux sociaux: {len(results['emails'])} email(s), {len(results['employees'])} employé(s)")
            results['data_str'] = f"Emails: {len(results['emails'])}, Employés: {len(results['employees'])}"
        
        return results if (results['emails'] or results['employees']) else None

    # ========== MÉTHODE 11: Commentaires HTML ==========
    def run_html_comments(self, website):
        """Extrait les emails depuis les commentaires HTML"""
        if not website or not REQUESTS_AVAILABLE:
            return None
        
        log(f"  🔍 Commentaires HTML: scan de {website}...")
        results = {'emails': set()}
        domain = self.extract_domain(website)
        session = self.get_session()
        
        if not session:
            return None
        
        try:
            response = session.get(website, timeout=10, verify=True)
            if response.status_code == 200:
                html = response.text
                
                # Extraction des commentaires HTML
                comment_pattern = r'<!--(.*?)-->'
                comments = re.findall(comment_pattern, html, re.DOTALL)
                
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                
                for comment in comments:
                    emails = re.findall(email_pattern, comment)
                    results['emails'].update([e.lower() for e in emails if domain.lower() in e.lower()])
                
                # Extraction depuis les attributs data-* et aria-*
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(html, 'html.parser')
                    for tag in soup.find_all(attrs=True):
                        for attr, value in tag.attrs.items():
                            if isinstance(value, str) and '@' in value:
                                emails = re.findall(email_pattern, value)
                                results['emails'].update([e.lower() for e in emails if domain.lower() in e.lower()])
        except Exception:
            pass
        
        if results['emails']:
            log(f"  ✅ Commentaires HTML: {len(results['emails'])} email(s)")
            return {
                'emails': results['emails'],
                'emails_str': ", ".join(sorted(results['emails']))
            }
        
        return None

    # ========== MÉTHODE 12: GitHub Scraping ==========
    def run_github_scraping(self, website, company_name):
        """Cherche des repositories GitHub et extrait des infos"""
        if not website or not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            return None
        
        domain = self.extract_domain(website)
        log(f"  🔍 GitHub Scraping: scan de {domain}...")
        results = {'emails': set()}
        session = self.get_session()
        
        if not session:
            return None
        
        try:
            search_url = f"https://github.com/search?q={quote(domain)}&type=repositories"
            response = session.get(search_url, timeout=10, verify=True)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                results['emails'].update([e.lower() for e in emails if domain.lower() in e.lower()])
                
                # Cherche aussi dans les README des repos
                repo_links = soup.find_all('a', href=re.compile(r'/.*/.*'))
                for link in repo_links[:3]:  # Limite à 3 repos
                    try:
                        repo_url = f"https://github.com{link.get('href', '')}"
                        if '/tree/' not in repo_url and '/blob/' not in repo_url:
                            readme_url = f"{repo_url}/blob/main/README.md"
                            readme_response = session.get(readme_url, timeout=10, verify=True)
                            if readme_response.status_code == 200:
                                readme_text = readme_response.text
                                emails = re.findall(email_pattern, readme_text)
                                results['emails'].update([e.lower() for e in emails if domain.lower() in e.lower()])
                        time.sleep(1)
                    except Exception:
                        continue
        except Exception:
            pass
        
        if results['emails']:
            log(f"  ✅ GitHub Scraping: {len(results['emails'])} email(s)")
            return ", ".join(sorted(results['emails']))
        
        return None

    # ========== MÉTHODE 13: Robots.txt/Sitemap ==========
    def run_robots_sitemap(self, website):
        """Parse robots.txt et sitemap pour trouver des pages cachées"""
        if not website or not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            return None
        
        log(f"  🔍 Robots.txt/Sitemap: scan de {website}...")
        results = {'emails': set()}
        domain = self.extract_domain(website)
        session = self.get_session()
        
        if not session:
            return None
        
        try:
            # Parse robots.txt
            robots_url = urljoin(website, '/robots.txt')
            robots_response = session.get(robots_url, timeout=10, verify=True)
            if robots_response.status_code == 200:
                sitemap_urls = re.findall(r'Sitemap:\s*(.+)', robots_response.text, re.IGNORECASE)
                for sitemap_url in sitemap_urls[:2]:  # Limite à 2 sitemaps
                    try:
                        sitemap_response = session.get(sitemap_url.strip(), timeout=10, verify=True)
                        if sitemap_response.status_code == 200:
                            soup = BeautifulSoup(sitemap_response.text, 'xml')
                            urls = [loc.text for loc in soup.find_all('loc')[:10]]  # Limite à 10 URLs
                            
                            for url in urls:
                                if any(page in url.lower() for page in ['about', 'team', 'contact', 'staff']):
                                    page_response = session.get(url, timeout=10, verify=True)
                                    if page_response.status_code == 200:
                                        page_soup = BeautifulSoup(page_response.text, 'html.parser')
                                        text = page_soup.get_text()
                                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                                        emails = re.findall(email_pattern, text)
                                        results['emails'].update([e.lower() for e in emails if domain.lower() in e.lower()])
                                    time.sleep(1)
                    except Exception:
                        continue
        except Exception:
            pass
        
        if results['emails']:
            log(f"  ✅ Robots.txt/Sitemap: {len(results['emails'])} email(s)")
        
        return {'emails': results['emails']} if results['emails'] else None

    def update_company(self, cid, **fields):
        set_parts = []
        params = []
        
        # Log condensé des champs
        fields_count = len(fields)
        non_null_fields = sum(1 for v in fields.values() if v is not None)
        log(f"   📝 {non_null_fields}/{fields_count} champs avec données")
        
        for k, v in fields.items():
            set_parts.append(f"{k} = ?")
            params.append(v)
        set_parts.append("osint_status = ?")
        params.append("Done")
        set_parts.append("osint_updated_at = ?")
        params.append(datetime.now(ZoneInfo("Europe/Paris")).isoformat())
        params.append(cid)

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Vérifier d'abord si l'ID existe
        log(f"   🔍 Vérification de l'existence de l'ID {cid}...")
        cur.execute("SELECT id, company_name FROM companies WHERE id = ?", (cid,))
        existing = cur.fetchone()
        
        if not existing:
            log(f"   ❌ ERREUR CRITIQUE: ID {cid} INTROUVABLE dans la BDD !")
            log(f"   💡 L'entreprise a peut-être été supprimée pendant l'enrichissement")
            
            # Diagnostic supplémentaire
            cur.execute("SELECT MIN(id), MAX(id), COUNT(*) FROM companies")
            min_id, max_id, total = cur.fetchone()
            log(f"   📊 BDD actuelle: {total} entreprises, IDs de {min_id} à {max_id}")
            
            conn.close()
            return
        
        log(f"   ✅ ID {cid} existe bien: '{existing[1]}'")
        
        sql_query = f"UPDATE companies SET {', '.join(set_parts)} WHERE id = ?"
        cur.execute(sql_query, params)
        rows_affected = cur.rowcount
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            log(f"   ✅ SAUVEGARDE RÉUSSIE pour ID {cid}")
        else:
            log(f"   ⚠️  AUCUNE LIGNE MISE À JOUR pour ID {cid} (bizarre car l'ID existe...)")


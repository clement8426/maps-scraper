import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo

LOG_PATH = os.path.join(os.path.dirname(__file__), "pipeline.log")


def log(msg):
    ts = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


class OsintPipeline:
    def __init__(self, db_path, status_ref, stop_flag_ref):
        self.db_path = db_path
        self.status = status_ref
        self.stop_flag = stop_flag_ref
        self.available_tools = {}
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
            SELECT id, company_name, website, email
            FROM companies
            {where_clause}
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(limit)
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    def run(self, city=None, limit=50, require_website=True):
        log("=" * 60)
        log("Pipeline OSINT démarré")
        log(f"Paramètres: city={city}, limit={limit}, require_website={require_website}")
        targets = self.fetch_targets(city, limit, require_website)
        total = len(targets)
        self.status["total"] = total
        if total == 0:
            self.status["message"] = "Aucune cible à enrichir"
            log("⚠️  Aucune cible trouvée avec ces filtres")
            return
        log(f"✅ {total} cible(s) trouvée(s)")

        for idx, (cid, name, website, email) in enumerate(targets, start=1):
            if self.stop_flag():
                log("Arrêt demandé, sortie propre.")
                self.status["message"] = "Arrêt demandé"
                break

            self.status["processed"] = idx - 1
            self.status["current"] = {"id": cid, "company": name, "website": website}
            self.status["message"] = f"Enrichissement {idx}/{total}"
            log(f"Enrichissement #{idx}/{total} - {name} ({website})")

            tech_stack = self.run_whatweb(website)
            emails_osint = self.run_email_tools(website)
            pdf_emails = self.run_pdf_hunt(website)
            subdomains = self.run_subfinder(website)
            whois_raw = self.run_whois(website)
            wayback_urls = self.run_wayback(website)

            log(f"  → Mise à jour BDD pour {name}")
            self.update_company(
                cid,
                tech_stack=tech_stack,
                emails_osint=emails_osint,
                pdf_emails=pdf_emails,
                subdomains=subdomains,
                whois_raw=whois_raw,
                wayback_urls=wayback_urls,
            )
            log(f"  ✅ {name} terminé")
            time.sleep(1.0)

        self.status["processed"] = min(self.status.get("processed", 0), total)
        self.status["running"] = False
        self.status["message"] = "Terminé"
        log("Pipeline terminé.")

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
        if not website:
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        out = []
        
        # theHarvester (peut retourner code non-zéro si aucun résultat)
        if self.available_tools.get("theHarvester"):
            harvest = self.run_cmd(["theHarvester", "-d", domain, "-b", "all"], allow_nonzero=True)
            if harvest:
                log(f"  ✅ theHarvester: OK")
            out.append(harvest)
        
        # Regex extraction
        emails = set()
        for blob in out:
            if blob:
                for m in re.findall(r"[a-zA-Z0-9._%+-]+@" + re.escape(domain), blob):
                    emails.add(m.lower())
        
        result = ", ".join(sorted(emails)) if emails else None
        if result:
            log(f"  ✅ Emails: {len(emails)}")
        return result

    def run_pdf_hunt(self, website):
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        # Simple Google dork via curl to Google may fail; placeholder string
        return f"See dorks manually for {domain}"

    def run_subfinder(self, website):
        if not website or not self.available_tools.get("subfinder"):
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        res = self.run_cmd(["subfinder", "-d", domain, "-silent"])
        if not res:
            return None
        subs = [line.strip() for line in res.splitlines() if line.strip()]
        if subs:
            log(f"  ✅ Subfinder: {len(subs)} subs")
        return ", ".join(subs[:50]) if subs else None

    def run_whois(self, website):
        if not website or not self.available_tools.get("whois"):
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        # whois peut retourner code 2 si le domaine n'existe pas ou n'est pas trouvé
        res = self.run_cmd(["whois", domain], timeout=25, allow_nonzero=True)
        if res:
            log(f"  ✅ WHOIS: OK")
        return res[:4000] if res else None

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

    def update_company(self, cid, **fields):
        set_parts = []
        params = []
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
        cur.execute(f"UPDATE companies SET {', '.join(set_parts)} WHERE id = ?", params)
        conn.commit()
        conn.close()


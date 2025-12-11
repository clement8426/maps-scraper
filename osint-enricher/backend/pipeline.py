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
        self.ensure_columns()

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
    def run_cmd(self, cmd, timeout=40):
        try:
            # Vérifier que la commande existe
            which_cmd = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
            check = subprocess.run(["which", which_cmd], capture_output=True, timeout=5)
            if check.returncode != 0:
                log(f"  ⚠️  Commande non trouvée: {which_cmd}")
                return ""
            
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout, text=True)
            return out
        except subprocess.TimeoutExpired:
            log(f"  ⚠️  Timeout: {' '.join(cmd)}")
            return ""
        except FileNotFoundError:
            log(f"  ⚠️  Commande non trouvée: {cmd[0]}")
            return ""
        except Exception as e:
            log(f"  ⚠️  Erreur: {' '.join(cmd)} - {str(e)[:100]}")
            return ""

    def run_whatweb(self, website):
        if not website:
            return None
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        if not domain:
            return None
        log(f"  → WhatWeb sur {domain}")
        res = self.run_cmd(["whatweb", domain, "--log-brief=-"])
        if not res:
            log(f"  ⚠️  WhatWeb: aucun résultat")
            return None
        top = res.splitlines()[:5]
        result = "; ".join(top)
        log(f"  ✅ WhatWeb: {result[:100]}...")
        return result

    def run_email_tools(self, website):
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        log(f"  → Recherche emails pour {domain}")
        out = []
        # theHarvester
        harvest = self.run_cmd(["theHarvester", "-d", domain, "-b", "all"])
        if harvest:
            log(f"  ✅ theHarvester: {len(harvest)} caractères")
        else:
            log(f"  ⚠️  theHarvester: non disponible ou échec")
        out.append(harvest)
        # emailharvester (si installé)
        eh = self.run_cmd(["emailharvester", "-d", domain])
        if eh:
            log(f"  ✅ emailharvester: {len(eh)} caractères")
        out.append(eh)
        # Regex extraction
        emails = set()
        for blob in out:
            for m in re.findall(r"[a-zA-Z0-9._%+-]+@" + re.escape(domain), blob):
                emails.add(m.lower())
        result = ", ".join(sorted(emails)) if emails else None
        if result:
            log(f"  ✅ Emails trouvés: {len(emails)}")
        else:
            log(f"  ⚠️  Aucun email trouvé")
        return result

    def run_pdf_hunt(self, website):
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        # Simple Google dork via curl to Google may fail; placeholder string
        return f"See dorks manually for {domain}"

    def run_subfinder(self, website):
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        res = self.run_cmd(["subfinder", "-d", domain, "-silent"])
        if not res:
            return None
        subs = [line.strip() for line in res.splitlines() if line.strip()]
        return ", ".join(subs[:50]) if subs else None

    def run_whois(self, website):
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        res = self.run_cmd(["whois", domain], timeout=25)
        return res[:4000] if res else None

    def run_wayback(self, website):
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        url = f"https://web.archive.org/cdx/search?url={domain}&output=txt&fl=original&filter=statuscode:200&limit=20"
        res = self.run_cmd(["curl", "-s", url], timeout=20)
        urls = [u for u in res.splitlines() if u.startswith("http")]
        return ", ".join(urls) if urls else None

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


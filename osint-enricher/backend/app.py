import os
import sqlite3
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from pipeline import OsintPipeline

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB = os.path.abspath(os.path.join(BASE_DIR, "..", "backend", "companies.db"))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    template_folder=FRONTEND_DIR,
    static_url_path=""
)

auth = HTTPBasicAuth()

users = {}
ENV_USER = os.getenv("WEB_USERNAME", "admin")
ENV_PASS = os.getenv("WEB_PASSWORD", "admin")
users[ENV_USER] = generate_password_hash(ENV_PASS)


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None


def get_db_connection():
    db_path = os.getenv("DATABASE_PATH", DEFAULT_DB)
    return sqlite3.connect(db_path)


# ---------- OSINT PIPELINE CONTROL ----------
pipeline_lock = threading.Lock()
pipeline_runner = {"thread": None, "stop_flag": False, "status": {}}


@app.route("/api/enrich/start", methods=["POST"])
@auth.login_required
def start_enrich():
    with pipeline_lock:
        if pipeline_runner["thread"] and pipeline_runner["thread"].is_alive():
            return jsonify({"message": "Pipeline déjà en cours", "status": pipeline_runner["status"]}), 200

        payload = request.get_json(silent=True) or {}
        city = payload.get("city")
        limit = int(payload.get("limit", 50))
        require_website = bool(payload.get("require_website", True))

        pipeline_runner["stop_flag"] = False
        pipeline_runner["status"] = {
            "running": True,
            "started_at": datetime.now(ZoneInfo("Europe/Paris")).isoformat(),
            "processed": 0,
            "total": 0,
            "current": None,
            "message": "Démarrage..."
        }

        def runner():
            db_path = os.getenv("DATABASE_PATH", DEFAULT_DB)
            pipe = OsintPipeline(
                db_path=db_path,
                status_ref=pipeline_runner["status"],
                stop_flag_ref=lambda: pipeline_runner["stop_flag"]
            )
            pipe.run(city=city, limit=limit, require_website=require_website)
            pipeline_runner["status"]["running"] = False
            pipeline_runner["status"]["finished_at"] = datetime.now(ZoneInfo("Europe/Paris")).isoformat()

        th = threading.Thread(target=runner, daemon=True)
        pipeline_runner["thread"] = th
        th.start()
        return jsonify({"message": "Pipeline lancé", "status": pipeline_runner["status"]}), 200


@app.route("/api/enrich/stop", methods=["POST"])
@auth.login_required
def stop_enrich():
    with pipeline_lock:
        if pipeline_runner["thread"] and pipeline_runner["thread"].is_alive():
            pipeline_runner["stop_flag"] = True
            return jsonify({"message": "Arrêt demandé"}), 200
        return jsonify({"message": "Aucun pipeline en cours"}), 200


@app.route("/api/enrich/status", methods=["GET"])
@auth.login_required
def enrich_status():
    with pipeline_lock:
        return jsonify(pipeline_runner["status"])


@app.route("/api/enrich/logs", methods=["GET"])
@auth.login_required
def enrich_logs():
    log_path = os.path.join(BASE_DIR, "pipeline.log")
    if not os.path.exists(log_path):
        return jsonify({"lines": []})
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()[-400:]
    return jsonify({"lines": lines})


# ---------- DB VIEWER ----------
def ensure_columns():
    extra_cols = [
        ("tech_stack", "TEXT"),
        ("emails_osint", "TEXT"),
        ("pdf_emails", "TEXT"),
        ("subdomains", "TEXT"),
        ("whois_raw", "TEXT"),
        ("wayback_urls", "TEXT"),
        ("osint_status", "TEXT"),
        ("osint_updated_at", "TEXT"),
    ]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(companies);")
    existing = {row[1] for row in cur.fetchall()}
    for col, ctype in extra_cols:
        if col not in existing:
            cur.execute(f"ALTER TABLE companies ADD COLUMN {col} {ctype};")
    conn.commit()
    conn.close()


@app.route("/api/db/companies", methods=["GET"])
@auth.login_required
def list_companies():
    ensure_columns()
    params = []
    filters = []
    city = request.args.get("city")
    status = request.args.get("status")
    has_email = request.args.get("has_email")
    has_website = request.args.get("has_website")
    limit = min(int(request.args.get("limit", 50)), 500)
    offset = int(request.args.get("offset", 0))

    if city:
        filters.append("city = ?")
        params.append(city)
    if status:
        filters.append("osint_status = ?")
        params.append(status)
    if has_email == "true":
        filters.append("(email IS NOT NULL AND email <> '')")
    if has_website == "true":
        filters.append("(website IS NOT NULL AND website <> '')")

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    query = f"""
        SELECT id, company_name, city, website, email, tech_stack, osint_status, osint_updated_at
        FROM companies
        {where_clause}
        ORDER BY updated_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    data = [
        {
            "id": r[0],
            "company_name": r[1],
            "city": r[2],
            "website": r[3],
            "email": r[4],
            "tech_stack": r[5],
            "osint_status": r[6],
            "osint_updated_at": r[7],
        }
        for r in rows
    ]
    return jsonify({"items": data})


@app.route("/api/db/cities", methods=["GET"])
@auth.login_required
def list_cities():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT city FROM companies WHERE city IS NOT NULL ORDER BY city;")
    cities = [row[0] for row in cur.fetchall() if row[0]]
    conn.close()
    return jsonify({"cities": cities})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ---------- FRONTEND ROUTES ----------
@app.route("/enrich")
@auth.login_required
def enrich_page():
    return send_from_directory(FRONTEND_DIR, "enrich.html")


@app.route("/db")
@auth.login_required
def db_page():
    return send_from_directory(FRONTEND_DIR, "db.html")


@app.route("/")
def root():
    return jsonify({"message": "OSINT Enricher up", "docs": "/enrich"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)


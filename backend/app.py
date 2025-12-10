"""
API Flask pour le scraper Google Maps
Interface web pour visualiser et filtrer les entreprises
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import os
import subprocess
import threading
from datetime import datetime

app = Flask(__name__, 
            template_folder='../frontend',
            static_folder='../frontend',
            static_url_path='')
auth = HTTPBasicAuth()

# Configuration
DATABASE_FILE = "companies.db"
CHECKPOINT_FILE = "checkpoint.json"
INTERMEDIATE_FILE = "intermediate_data.csv"

# Mot de passe par défaut (à changer via variables d'environnement)
users = {
    os.getenv("WEB_USERNAME", "admin"): generate_password_hash(os.getenv("WEB_PASSWORD", "changeme123"))
}

scraper_process = None
scraper_running = False

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

@app.route('/')
@auth.login_required
def index():
    """Page d'accueil"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/companies')
@auth.login_required
def get_companies():
    """Récupère la liste des entreprises avec filtres"""
    city = request.args.get('city', '')
    has_website = request.args.get('has_website', '')
    has_email = request.args.get('has_email', '')
    search = request.args.get('search', '')
    
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM companies WHERE 1=1"
    params = []
    
    if city:
        query += " AND city = ?"
        params.append(city)
    
    if has_website == 'true':
        query += " AND website IS NOT NULL AND website != ''"
    elif has_website == 'false':
        query += " AND (website IS NULL OR website = '')"
    
    if has_email == 'true':
        query += " AND email IS NOT NULL AND email != ''"
    elif has_email == 'false':
        query += " AND (email IS NULL OR email = '')"
    
    if search:
        query += " AND (company_name LIKE ? OR address LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    companies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(companies)

@app.route('/api/stats')
@auth.login_required
def get_stats():
    """Récupère les statistiques globales"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Total
    cursor.execute("SELECT COUNT(*) FROM companies")
    total = cursor.fetchone()[0]
    
    # Avec site web
    cursor.execute("SELECT COUNT(*) FROM companies WHERE website IS NOT NULL AND website != ''")
    with_website = cursor.fetchone()[0]
    
    # Avec email
    cursor.execute("SELECT COUNT(*) FROM companies WHERE email IS NOT NULL AND email != ''")
    with_email = cursor.fetchone()[0]
    
    # Par ville (top 10)
    cursor.execute("""
        SELECT city, COUNT(*) as count 
        FROM companies 
        GROUP BY city 
        ORDER BY count DESC 
        LIMIT 10
    """)
    by_city = [{"city": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    # Dernière mise à jour
    cursor.execute("SELECT MAX(updated_at) FROM companies")
    last_update = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "total": total,
        "with_website": with_website,
        "with_email": with_email,
        "by_city": by_city,
        "last_update": last_update
    })

@app.route('/api/cities')
@auth.login_required
def get_cities():
    """Récupère la liste des villes"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city FROM companies ORDER BY city")
    cities = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return jsonify(cities)

@app.route('/api/scraper/status')
@auth.login_required
def scraper_status():
    """Récupère le statut du scraper"""
    global scraper_process, scraper_running
    
    # Vérifier si le processus est vraiment en cours
    if scraper_process:
        if scraper_process.poll() is not None:
            # Le processus est terminé
            scraper_running = False
            scraper_process = None
    
    # Lire le checkpoint
    checkpoint = {}
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint = json.load(f)
        except:
            pass
    
    return jsonify({
        "running": scraper_running,
        "last_city": checkpoint.get("last_city"),
        "last_keyword": checkpoint.get("last_keyword"),
        "completed_combinations": len(checkpoint.get("completed_combinations", [])),
        "timestamp": checkpoint.get("timestamp")
    })

@app.route('/api/scraper/start', methods=['POST'])
@auth.login_required
def start_scraper():
    """Démarre le scraper"""
    global scraper_process, scraper_running
    
    if scraper_running and scraper_process and scraper_process.poll() is None:
        return jsonify({"error": "Le scraper est déjà en cours"}), 400
    
    try:
        scraper_process = subprocess.Popen(
            ['python3', 'scraper_suisse_romande.py'],
            cwd=os.path.dirname(__file__),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        scraper_running = True
        return jsonify({"message": "Scraper démarré"})
    except Exception as e:
        scraper_running = False
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraper/stop', methods=['POST'])
@auth.login_required
def stop_scraper():
    """Arrête le scraper"""
    global scraper_process, scraper_running
    
    if not scraper_running or not scraper_process:
        return jsonify({"error": "Le scraper n'est pas en cours"}), 400
    
    try:
        scraper_process.terminate()
        scraper_process.wait(timeout=10)
        scraper_running = False
        scraper_process = None
        return jsonify({"message": "Scraper arrêté"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/csv')
@auth.login_required
def export_csv():
    """Exporte les données en CSV"""
    city = request.args.get('city', '')
    
    import csv
    from io import StringIO
    
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM companies"
    params = []
    
    if city:
        query += " WHERE city = ?"
        params.append(city)
    
    cursor.execute(query, params)
    companies = cursor.fetchall()
    conn.close()
    
    # Créer le CSV
    output = StringIO()
    if companies:
        writer = csv.DictWriter(output, fieldnames=companies[0].keys())
        writer.writeheader()
        for row in companies:
            writer.writerow(dict(row))
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=companies_{city or 'all'}_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

if __name__ == '__main__':
    # Créer la base de données si elle n'existe pas
    if not os.path.exists(DATABASE_FILE):
        from scraper_suisse_romande import init_database
        init_database()
    
    # Lancer le serveur
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'False') == 'True'
    )


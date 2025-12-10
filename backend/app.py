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
LOG_FILE = "scraper.log"

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
    # Ne pas utiliser les variables globales (problème multi-workers Gunicorn)
    # Vérifier directement avec ps si le processus tourne
    process_running = False
    
    try:
        result = subprocess.run(
            ['/usr/bin/pgrep', '-f', 'scraper_suisse_romande.py'],
            capture_output=True,
            text=True,
            timeout=2
        )
        # pgrep retourne les PIDs si trouvé, vide sinon
        if result.returncode == 0 and result.stdout.strip():
            process_running = True
            app.logger.info(f"Scraper running: PID {result.stdout.strip()}")
        else:
            app.logger.info(f"pgrep returned: code={result.returncode}, stdout='{result.stdout.strip()}'")
    except Exception as e:
        app.logger.error(f"pgrep failed: {e}")
        # Fallback sur ps aux si pgrep échoue
        try:
            result = subprocess.run(
                ['/usr/bin/ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=2
            )
            for line in result.stdout.split('\n'):
                if 'scraper_suisse_romande.py' in line and 'grep' not in line:
                    process_running = True
                    app.logger.info(f"Found scraper in ps: {line[:80]}")
                    break
        except Exception as e2:
            app.logger.error(f"ps aux failed: {e2}")
    
    # Lire le checkpoint
    checkpoint = {}
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint = json.load(f)
        except:
            pass
    
    return jsonify({
        "running": process_running,
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
        # Utiliser le Python du venv si disponible, sinon python3
        backend_dir = os.path.dirname(__file__)
        app_dir = os.path.dirname(backend_dir)
        venv_python = os.path.join(app_dir, 'venv', 'bin', 'python')
        
        if os.path.exists(venv_python):
            python_cmd = venv_python
        else:
            python_cmd = 'python3'
        
        scraper_script = os.path.join(backend_dir, 'scraper_suisse_romande.py')
        if not os.path.exists(scraper_script):
            return jsonify({"error": f"Fichier scraper non trouvé: {scraper_script}"}), 500
        
        # Ouvrir le fichier de log en mode append (ne pas fermer, le processus l'utilise)
        log_path = os.path.join(backend_dir, LOG_FILE)
        # Créer/vider le fichier de log au démarrage
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"=== Scraper démarré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
        log_file = open(log_path, 'a', encoding='utf-8', buffering=1)  # Line buffered
        
        # Lancer le scraper en arrière-plan avec redirection vers le fichier de log
        scraper_process = subprocess.Popen(
            [python_cmd, scraper_script],
            cwd=backend_dir,
            stdout=log_file,
            stderr=subprocess.STDOUT,  # Rediriger stderr vers stdout
            text=True,
            env=os.environ.copy(),
            start_new_session=True  # Détacher du groupe de processus
        )
        # Ne pas fermer log_file, le processus en a besoin
        scraper_running = True
        
        # Vérifier immédiatement si le processus a crashé
        import time
        time.sleep(1)
        if scraper_process.poll() is not None:
            # Le processus s'est terminé immédiatement (erreur)
            try:
                stdout_output, stderr_output = scraper_process.communicate(timeout=1)
                error_msg = stderr_output if stderr_output else stdout_output
            except:
                error_msg = "Impossible de lire l'erreur"
            
            scraper_running = False
            scraper_process = None
            return jsonify({"error": f"Le scraper s'est arrêté immédiatement. Erreur: {error_msg[:500]}"}), 500
        
        return jsonify({"message": "Scraper démarré"})
    except Exception as e:
        scraper_running = False
        import traceback
        return jsonify({"error": f"{str(e)}\n{traceback.format_exc()}"}), 500

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

@app.route('/api/scraper/logs')
@auth.login_required
def get_scraper_logs():
    """Récupère les logs du scraper"""
    log_path = os.path.join(os.path.dirname(__file__), LOG_FILE)
    
    # Lire les dernières lignes du fichier de log
    lines = request.args.get('lines', 100, type=int)
    
    if not os.path.exists(log_path):
        return jsonify({"logs": [], "total_lines": 0})
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            total_lines = len(all_lines)
            # Retourner les N dernières lignes
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            # Nettoyer les lignes (retirer \n, etc.)
            cleaned_lines = [line.rstrip('\n\r') for line in recent_lines]
            
            return jsonify({
                "logs": cleaned_lines,
                "total_lines": total_lines,
                "showing": len(cleaned_lines)
            })
    except Exception as e:
        return jsonify({"error": str(e), "logs": [], "total_lines": 0}), 500

@app.route('/api/export/csv')
@auth.login_required
def export_csv():
    """Exporte les données en CSV avec filtres"""
    city = request.args.get('city', '')
    has_website = request.args.get('has_website', '')
    has_email = request.args.get('has_email', '')
    search = request.args.get('search', '')
    
    import csv
    from io import StringIO
    
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
    
    # Créer un nom de fichier descriptif
    filename_parts = ["companies"]
    if city:
        filename_parts.append(city)
    if has_website == 'true':
        filename_parts.append("with_website")
    if has_email == 'true':
        filename_parts.append("with_email")
    filename_parts.append(datetime.now().strftime('%Y%m%d'))
    
    filename = "_".join(filename_parts) + ".csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
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


# OSINT Enricher (standalone)

Deux pages web :
- `/enrich` : lancer et suivre le pipeline OSINT gratuit
- `/db` : explorer/filtrer la base SQLite (companies.db)

## Installation (VPS)
```bash
cd ~/maps-scraper/osint-enricher
sudo ./scripts/install_enricher.sh
```

Ports :
- Interne Flask : 127.0.0.1:5001
- Nginx : port 81 (modifiable via NGINX_PORT env)

Requiert sur le VPS :
```
whatweb theharvester subfinder amass pdfgrep whois curl
```

## Configuration
Copier un fichier `.env` dans `osint-enricher/` :
```
WEB_USERNAME=enricher
WEB_PASSWORD=change_me
DATABASE_PATH=/home/ubuntu/maps-scraper/backend/companies.db
```

## Endpoints API
- POST `/api/enrich/start` {city?, limit?, require_website?}
- POST `/api/enrich/stop`
- GET  `/api/enrich/status`
- GET  `/api/enrich/logs`
- GET  `/api/db/companies` (filtres: city, status, has_email, has_website, limit, offset)
- GET  `/api/db/cities`
- GET  `/enrich`, `/db`

## Fonctionnement du pipeline
- Sélectionne les entreprises à enrichir (status != Done)
- Étapes gratuites : WhatWeb (stack), theHarvester/emailharvester (emails), subfinder (subdomains), whois, Wayback, placeholders PDF/dorks
- Met à jour directement `companies.db` avec colonnes : tech_stack, emails_osint, pdf_emails, subdomains, whois_raw, wayback_urls, osint_status, osint_updated_at

## Service systemd
`/etc/systemd/system/osint-enricher.service` (créé par install script)
Command : gunicorn --bind 127.0.0.1:5001 app:app --workers 2

## Nginx
`/etc/nginx/sites-available/osint-enricher` (port 81 par défaut, basic auth .htpasswd partagé)

## Utilisation rapide
- Accès : `http://<IP_VPS>:81/enrich` et `/db`
- Auth : login/password du `.env` (et .htpasswd si partagé)
- Logs pipeline : `osint-enricher/backend/pipeline.log`

## Notes
- Aucun changement sur l’app principale
- Pipeline tolérant : si un outil manque, la step passe simplement
- Pensez à ouvrir le port 81 si UFW actif : `sudo ufw allow 81/tcp`


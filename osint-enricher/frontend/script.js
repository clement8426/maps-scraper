const api = {
  start: (payload = {}) => fetch('/api/enrich/start', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}).then(r=>r.json()),
  stop: () => fetch('/api/enrich/stop', {method:'POST'}).then(r=>r.json()),
  status: () => fetch('/api/enrich/status').then(r=>r.json()),
  logs: () => fetch('/api/enrich/logs').then(r=>r.json()),
  companies: (params={}) => {
    const qs = new URLSearchParams(params).toString();
    return fetch('/api/db/companies?' + qs).then(r=>r.json());
  },
  cities: () => fetch('/api/db/cities').then(r=>r.json()),
};

// ------- ENRICH PAGE -------
async function initEnrichPage() {
  const startBtn = document.querySelector('#btnStart');
  const stopBtn = document.querySelector('#btnStop');
  const statusEl = document.querySelector('#statusText');
  const progressEl = document.querySelector('#progressText');
  const logBox = document.querySelector('#logBox');
  const citySelect = document.querySelector('#cityFilter');
  const limitInput = document.querySelector('#limitInput');
  const unlimitedMode = document.querySelector('#unlimitedMode');
  const requireWebsite = document.querySelector('#requireWebsite');

  if (!startBtn) return; // not on this page
  
  // Cache du dernier statut pour éviter les clignotements
  let lastRunningState = null;
  let consecutiveStoppedCount = 0;
  
  // Gérer le mode illimité
  if (unlimitedMode) {
    unlimitedMode.onchange = () => {
      if (unlimitedMode.checked) {
        limitInput.disabled = true;
        limitInput.value = 999999;
      } else {
        limitInput.disabled = false;
        limitInput.value = 50;
      }
    };
  }

  async function loadCities() {
    const data = await api.cities();
    citySelect.innerHTML = '<option value=\"\">Toutes</option>';
    data.cities.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      citySelect.appendChild(opt);
    });
  }

  async function refreshStatus() {
    const st = await api.status();
    
    // Détection simple : si processed >= total ET total > 0, c'est terminé
    const isCompleted = (st.total > 0 && st.processed >= st.total);
    const isRunning = st.running && !isCompleted;
    
    // Mise à jour du statut
    if (isRunning) {
      statusEl.textContent = '🔄 En cours';
      statusEl.className = 'status status-running';
      startBtn.disabled = true;
      stopBtn.disabled = false;
      lastRunningState = true;
    } else {
      statusEl.textContent = isCompleted ? '✅ Terminé' : '⏸️ Arrêté';
      statusEl.className = isCompleted ? 'status status-success' : 'status status-stopped';
      startBtn.disabled = false;
      stopBtn.disabled = true;
      lastRunningState = false;
    }
    
    // Mise à jour de la progression
    if (st.total > 0) {
      const percentage = Math.round((st.processed / st.total) * 100);
      progressEl.textContent = `${st.processed}/${st.total} (${percentage}%)`;
    } else {
      progressEl.textContent = `0/0`;
    }
  }

  async function refreshLogs() {
    try {
      const res = await api.logs();
      if (res.lines && res.lines.length > 0) {
        // Filtrer les logs : garder seulement les 100 dernières lignes
        const recentLines = res.lines.slice(-100);
        
        // Formater chaque ligne pour enlever les doublons de timestamp
        const formattedLines = recentLines.map(line => {
          // Nettoyer les lignes vides multiples
          return line.trim() ? line : '';
        }).filter(line => line !== '');
        
        logBox.textContent = formattedLines.join('\n');
        logBox.scrollTop = logBox.scrollHeight; // Auto-scroll en bas
      } else {
        logBox.textContent = 'Aucun log pour le moment. Les logs apparaîtront ici quand le pipeline sera lancé.';
      }
    } catch (e) {
      logBox.textContent = `Erreur chargement logs: ${e.message}`;
    }
  }

  startBtn.onclick = async () => {
    // Forcer l'état "en cours" immédiatement
    lastRunningState = true;
    statusEl.textContent = '🔄 En cours';
    statusEl.className = 'status status-running';
    startBtn.disabled = true;
    stopBtn.disabled = false;
    
    await api.start({
      city: citySelect.value || null,
      limit: Number(limitInput.value || 50),
      require_website: requireWebsite.checked,
    });
    
    setTimeout(refreshStatus, 1000);
  };
  
  stopBtn.onclick = async () => {
    await api.stop();
    
    // Forcer l'état "arrêté" après confirmation
    lastRunningState = false;
    consecutiveStoppedCount = 0;
    statusEl.textContent = '⏸️ Arrêté';
    statusEl.className = 'status status-stopped';
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    setTimeout(refreshStatus, 1000);
  };

  // Gestion des boutons de logs
  const toggleLogsBtn = document.getElementById('toggleLogs');
  const clearLogsBtn = document.getElementById('clearLogs');
  
  if (toggleLogsBtn) {
    toggleLogsBtn.onclick = () => {
      const logsContainer = logBox.parentElement;
      if (logsContainer.style.display === 'none') {
        logsContainer.style.display = 'block';
        toggleLogsBtn.textContent = 'Masquer';
      } else {
        logsContainer.style.display = 'none';
        toggleLogsBtn.textContent = 'Afficher';
      }
    };
  }
  
  if (clearLogsBtn) {
    clearLogsBtn.onclick = () => {
      logBox.textContent = 'Logs effacés (les nouveaux logs apparaîtront ici)';
    };
  }

  await loadCities();
  await refreshStatus();
  await refreshLogs();
  setInterval(refreshStatus, 3000);  // Plus rapide pour détecter la fin
  setInterval(refreshLogs, 5000);
}

// ------- DB PAGE -------
async function initDbPage() {
  const tableBody = document.querySelector('#dbRows');
  const citySelect = document.querySelector('#dbCity');
  const hasEmail = document.querySelector('#dbHasEmail');
  const hasWebsite = document.querySelector('#dbHasWebsite');
  const statusSel = document.querySelector('#dbStatus');
  const exportBtn = document.querySelector('#dbExport');

  if (!tableBody) return;

  async function loadCities() {
    const data = await api.cities();
    citySelect.innerHTML = '<option value=\"\">Toutes</option>';
    data.cities.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      citySelect.appendChild(opt);
    });
  }

  function showModal(title, content) {
    const modal = document.getElementById('detailModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    modalTitle.textContent = title;
    
    // Formater le contenu selon le type
    let formattedContent = content || '(vide)';
    
    // Si c'est une liste séparée par virgules, formater en liste
    if (formattedContent.includes(',') && formattedContent.length > 50) {
      const items = formattedContent.split(',').map(item => item.trim()).filter(item => item);
      
      // Dédupliquer les URLs (enlever trailing slash)
      const uniqueItems = [];
      const seen = new Set();
      
      items.forEach(item => {
        // Normaliser les URLs
        let normalized = item;
        if (item.startsWith('http')) {
          normalized = item.replace(/\/+$/, '').toLowerCase();
        }
        
        if (!seen.has(normalized)) {
          seen.add(normalized);
          uniqueItems.push(item);
        }
      });
      
      formattedContent = uniqueItems.map((item, idx) => {
        // Si c'est une URL, la rendre cliquable
        if (item.startsWith('http')) {
          return `${idx + 1}. ${item}`;
        }
        return `${idx + 1}. ${item}`;
      }).join('\n');
    }
    
    modalContent.textContent = formattedContent;
    modal.style.display = 'flex';
  }

  async function loadRows() {
    const params = {
      city: citySelect.value || '',
      has_email: hasEmail.checked,
      has_website: hasWebsite.checked,
      status: statusSel.value || '',
      limit: 500,
      offset: 0,
    };
    const data = await api.companies(params);
    tableBody.innerHTML = '';
    data.items.forEach((r) => {
      const tr = document.createElement('tr');
      
      // Fonction pour tronquer et formater le texte
      const formatText = (text, maxLength = 100) => {
        if (!text) return '—';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
      };
      
      // Formater les emails OSINT (séparer par virgules)
      const formatEmails = (emails) => {
        if (!emails) return '—';
        return emails.split(',').map(e => e.trim()).join(', ');
      };
      
      tr.innerHTML = `
        <td class="clickable" title="Cliquer pour voir le détail">${r.company_name || '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.city || '—'}</td>
        <td class="clickable" title="Cliquer pour voir le lien">${r.maps_link ? `<a href="${r.maps_link}" target="_blank" onclick="event.stopPropagation();">🗺️ Maps</a>` : '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.phone || '—'}</td>
        <td class="clickable" title="Cliquer pour voir l'adresse complète">${formatText(r.address || '', 40)}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.rating ? `⭐ ${r.rating}` : '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.reviews_count || '0'}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.tag || '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.website ? `<a href="${r.website}" target="_blank" onclick="event.stopPropagation();" title="${r.website}">${formatText(r.website.replace(/^https?:\/\//, ''), 25)}</a>` : '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail complet">${formatText(r.email || '', 30)}</td>
        <td class="clickable" title="Cliquer pour voir les réseaux sociaux">${r.social_links ? '🔗 Réseaux' : '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail complet">${formatText(r.tech_stack || '', 80)}</td>
        <td class="clickable" title="Cliquer pour voir le détail complet">${formatText(formatEmails(r.emails_osint), 50)}</td>
        <td class="clickable" title="Cliquer pour voir le détail complet">${r.subdomains ? `✓ ${r.subdomains.split(',').length} sub` : '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail complet">${r.wayback_urls ? `✓ ${r.wayback_urls.split(',').length} URLs` : '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail"><span class="badge ${r.osint_status === 'Done' ? 'badge-success' : 'badge-muted'}">${r.osint_status || 'N/A'}</span></td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.osint_updated_at ? new Date(r.osint_updated_at).toLocaleString('fr-FR', { timeZone: 'Europe/Paris', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}</td>
      `;
      
      // Ajouter les event listeners pour les clics sur toutes les cellules
      const cells = tr.querySelectorAll('td');
      
      // Entreprise (0)
      cells[0].onclick = () => showModal('Entreprise - ' + r.company_name, r.company_name || '(vide)');
      
      // Ville (1)
      cells[1].onclick = () => showModal('Ville - ' + r.company_name, r.city || '(vide)');
      
      // Lien Maps (2)
      cells[2].onclick = () => showModal('Lien Google Maps - ' + r.company_name, r.maps_link || '(vide)');
      
      // Téléphone (3)
      cells[3].onclick = () => showModal('Téléphone - ' + r.company_name, r.phone || '(vide)');
      
      // Adresse (4)
      cells[4].onclick = () => showModal('Adresse complète - ' + r.company_name, r.address_full || r.address || '(vide)');
      
      // Note (5)
      cells[5].onclick = () => showModal('Note - ' + r.company_name, r.rating || '(vide)');
      
      // Nombre d'avis (6)
      cells[6].onclick = () => showModal('Nombre d\'avis - ' + r.company_name, r.reviews_count || '0');
      
      // Tag (7)
      cells[7].onclick = () => showModal('Tag / Catégorie - ' + r.company_name, r.tag || '(vide)');
      
      // Site Web (8)
      cells[8].onclick = () => showModal('Site Web - ' + r.company_name, r.website || '(vide)');
      
      // Email Base (9)
      cells[9].onclick = () => showModal('Email Base - ' + r.company_name, r.email || '(vide)');
      
      // Réseaux sociaux (10)
      cells[10].onclick = () => showModal('Réseaux Sociaux - ' + r.company_name, r.social_links_full || r.social_links || '(vide)');
      
      // Stack Tech (11)
      cells[11].onclick = () => showModal('Stack Technique - ' + r.company_name, r.tech_stack_full || r.tech_stack || '(vide)');
      
      // Emails OSINT (12)
      cells[12].onclick = () => showModal('Emails OSINT - ' + r.company_name, r.emails_osint_full || r.emails_osint || '(vide)');
      
      // Sous-domaines (13)
      cells[13].onclick = () => showModal('Sous-domaines - ' + r.company_name, r.subdomains_full || r.subdomains || '(vide)');
      
      // Wayback URLs (14)
      cells[14].onclick = () => showModal('Wayback URLs - ' + r.company_name, r.wayback_urls_full || r.wayback_urls || '(vide)');
      
      // Status (15)
      cells[15].onclick = () => showModal('Status OSINT - ' + r.company_name, r.osint_status || 'N/A');
      
      // Date MAJ (16)
      cells[16].onclick = () => showModal('Date MAJ OSINT - ' + r.company_name, r.osint_updated_at ? new Date(r.osint_updated_at).toLocaleString('fr-FR', { timeZone: 'Europe/Paris', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '(vide)');
      
      tableBody.appendChild(tr);
    });
  }
  
  // Fermer la modal
  if (document.querySelector('.modal-close')) {
    document.querySelector('.modal-close').onclick = () => {
      document.getElementById('detailModal').style.display = 'none';
    };
  }
  window.onclick = (e) => {
    const modal = document.getElementById('detailModal');
    if (modal && e.target === modal) {
      modal.style.display = 'none';
    }
  };

  exportBtn.onclick = () => {
    const qs = new URLSearchParams({
      city: citySelect.value || '',
      has_email: hasEmail.checked,
      has_website: hasWebsite.checked,
      status: statusSel.value || '',
    });
    window.location = '/api/db/companies?' + qs.toString();
  };

  citySelect.onchange = loadRows;
  hasEmail.onchange = loadRows;
  hasWebsite.onchange = loadRows;
  statusSel.onchange = loadRows;

  await loadCities();
  await loadRows();
}

document.addEventListener('DOMContentLoaded', () => {
  initEnrichPage();
  initDbPage();
});


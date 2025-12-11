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
    statusEl.textContent = st.message || (st.running ? 'En cours' : 'Arrêté');
    progressEl.textContent = `${st.processed || 0} / ${st.total || 0}`;
    startBtn.disabled = !!st.running;
    stopBtn.disabled = !st.running;
  }

  async function refreshLogs() {
    try {
      const res = await api.logs();
      if (res.lines && res.lines.length > 0) {
        logBox.textContent = res.lines.join('');
        logBox.scrollTop = logBox.scrollHeight;
      } else {
        logBox.textContent = 'Aucun log pour le moment. Les logs apparaîtront ici quand le pipeline sera lancé.';
      }
    } catch (e) {
      logBox.textContent = `Erreur chargement logs: ${e.message}`;
    }
  }

  startBtn.onclick = async () => {
    await api.start({
      city: citySelect.value || null,
      limit: Number(limitInput.value || 50),
      require_website: requireWebsite.checked,
    });
    refreshStatus();
  };
  stopBtn.onclick = async () => {
    await api.stop();
    refreshStatus();
  };

  await loadCities();
  await refreshStatus();
  await refreshLogs();
  setInterval(refreshStatus, 5000);
  setInterval(refreshLogs, 7000);
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
      formattedContent = items.map((item, idx) => `${idx + 1}. ${item}`).join('\n');
    }
    
    // Si c'est une URL, la rendre cliquable (mais on garde le texte brut dans la modal)
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
        <td class="clickable" title="Cliquer pour voir le détail">${r.website ? `<a href="${r.website}" target="_blank" onclick="event.stopPropagation();" title="${r.website}">${formatText(r.website.replace(/^https?:\/\//, ''), 25)}</a>` : '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail complet">${formatText(r.email || '', 30)}</td>
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
      
      // Site web (2)
      cells[2].onclick = () => showModal('Site Web - ' + r.company_name, r.website || '(vide)');
      
      // Email Base (3)
      cells[3].onclick = () => showModal('Email Base - ' + r.company_name, r.email || '(vide)');
      
      // Stack Tech (4)
      cells[4].onclick = () => showModal('Stack Technique - ' + r.company_name, r.tech_stack_full || r.tech_stack || '(vide)');
      
      // Emails OSINT (5)
      cells[5].onclick = () => showModal('Emails OSINT - ' + r.company_name, r.emails_osint || '(vide)');
      
      // Sous-domaines (6)
      cells[6].onclick = () => showModal('Sous-domaines - ' + r.company_name, r.subdomains_full || r.subdomains || '(vide)');
      
      // Wayback URLs (7)
      cells[7].onclick = () => showModal('Wayback URLs - ' + r.company_name, r.wayback_urls_full || r.wayback_urls || '(vide)');
      
      // Status (8)
      cells[8].onclick = () => showModal('Status OSINT - ' + r.company_name, r.osint_status || 'N/A');
      
      // Date MAJ (9)
      cells[9].onclick = () => showModal('Date MAJ OSINT - ' + r.company_name, r.osint_updated_at ? new Date(r.osint_updated_at).toLocaleString('fr-FR', { timeZone: 'Europe/Paris', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '(vide)');
      
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


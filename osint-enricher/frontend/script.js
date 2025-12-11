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
  const requireWebsite = document.querySelector('#requireWebsite');

  if (!startBtn) return; // not on this page

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
    modalContent.textContent = content || '(vide)';
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
      tr.innerHTML = `
        <td title="${r.company_name || ''}">${r.company_name || ''}</td>
        <td>${r.city || ''}</td>
        <td>${r.website ? `<a href="${r.website}" target="_blank" title="${r.website}">${r.website.substring(0, 30)}...</a>` : ''}</td>
        <td title="${r.email || ''}">${r.email || ''}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.tech_stack || '—'}</td>
        <td title="${r.emails_osint || ''}">${r.emails_osint || '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.subdomains ? '✓ (' + (r.subdomains.split(',').length) + ')' : '—'}</td>
        <td class="clickable" title="Cliquer pour voir le détail">${r.wayback_urls ? '✓ (' + (r.wayback_urls.split(',').length) + ')' : '—'}</td>
        <td><span class="badge ${r.osint_status === 'Done' ? 'badge-success' : 'badge-muted'}">${r.osint_status || 'N/A'}</span></td>
        <td>${r.osint_updated_at ? new Date(r.osint_updated_at).toLocaleString('fr-FR', { timeZone: 'Europe/Paris' }).split(',')[0] : ''}</td>
      `;
      
      // Ajouter les event listeners pour les clics
      const cells = tr.querySelectorAll('td');
      cells[4].onclick = () => showModal('Stack Technique - ' + r.company_name, r.tech_stack_full);
      cells[6].onclick = () => showModal('Sous-domaines - ' + r.company_name, r.subdomains_full);
      cells[7].onclick = () => showModal('Wayback URLs - ' + r.company_name, r.wayback_urls_full);
      
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


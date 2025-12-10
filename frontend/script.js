// Dashboard JavaScript

let currentFilters = {
    city: '',
    has_website: '',
    has_email: '',
    search: ''
};

// Chargement initial
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM chargé, initialisation...');
    
    loadStats();
    loadCities();
    loadCompanies();
    loadScraperStatus();
    
    // Actualisation automatique toutes les 10 secondes
    setInterval(loadScraperStatus, 10000);
    setInterval(loadStats, 30000);
    
    // Event listeners
    const refreshBtn = document.getElementById('refreshBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const resetFiltersBtn = document.getElementById('resetFilters');
    const exportCsvBtn = document.getElementById('exportCsv');
    const startScraperBtn = document.getElementById('startScraper');
    const stopScraperBtn = document.getElementById('stopScraper');
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('Refresh cliqué');
            loadStats();
            loadCompanies();
        });
    }
    
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
    if (applyFiltersBtn) applyFiltersBtn.addEventListener('click', applyFilters);
    if (resetFiltersBtn) resetFiltersBtn.addEventListener('click', resetFilters);
    if (exportCsvBtn) exportCsvBtn.addEventListener('click', exportCsv);
    
    // Bouton export filtré (dans le titre des entreprises)
    const exportFilteredBtn = document.getElementById('exportFiltered');
    if (exportFilteredBtn) {
        exportFilteredBtn.addEventListener('click', exportCsv);
    }
    
    if (startScraperBtn) {
        startScraperBtn.addEventListener('click', () => {
            console.log('Bouton Démarrer cliqué');
            startScraper();
        });
    }
    
    if (stopScraperBtn) {
        stopScraperBtn.addEventListener('click', () => {
            console.log('Bouton Arrêter cliqué');
            stopScraper();
        });
    }
    
    console.log('Initialisation terminée');
});

// Statistiques
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('totalCompanies').textContent = stats.total;
        document.getElementById('withWebsite').textContent = stats.with_website;
        document.getElementById('withEmail').textContent = stats.with_email;
        document.getElementById('lastUpdate').textContent = stats.last_update ? 
            new Date(stats.last_update).toLocaleString('fr-FR', { timeZone: 'Europe/Paris' }) : '-';
        
        // Top villes
        const citiesChart = document.getElementById('citiesChart');
        if (stats.by_city && stats.by_city.length > 0) {
            const maxCount = Math.max(...stats.by_city.map(c => c.count));
            citiesChart.innerHTML = stats.by_city.map(city => `
                <div class="city-bar">
                    <span class="city-name">${city.city}</span>
                    <div class="city-bar-bg">
                        <div class="city-bar-fill" style="width: ${(city.count / maxCount) * 100}%">
                            ${city.count}
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            citiesChart.innerHTML = '<p>Aucune donnée disponible</p>';
        }
    } catch (error) {
        console.error('Erreur chargement stats:', error);
    }
}

// Villes pour le filtre
async function loadCities() {
    try {
        const response = await fetch('/api/cities');
        const cities = await response.json();
        
        const select = document.getElementById('cityFilter');
        select.innerHTML = '<option value="">Toutes les villes</option>' +
            cities.map(city => `<option value="${city}">${city}</option>`).join('');
    } catch (error) {
        console.error('Erreur chargement villes:', error);
    }
}

// Entreprises
async function loadCompanies() {
    try {
        const params = new URLSearchParams(currentFilters);
        const response = await fetch(`/api/companies?${params}`);
        const companies = await response.json();
        
        document.getElementById('companiesCount').textContent = companies.length;
        
        // Mettre à jour le compteur d'export
        const exportCount = document.getElementById('exportCount');
        if (exportCount) {
            exportCount.textContent = companies.length;
        }
        
        const tbody = document.getElementById('companiesTable');
        if (companies.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">Aucune entreprise trouvée</td></tr>';
            return;
        }
        
        tbody.innerHTML = companies.map(company => `
            <tr>
                <td><strong>${company.company_name || '-'}</strong></td>
                <td>${company.city || '-'}</td>
                <td>${company.address || '-'}</td>
                <td>${company.phone || '-'}</td>
                <td>${company.website ? `<a href="${company.website}" target="_blank">🌐 Voir</a>` : '-'}</td>
                <td>${company.email ? `<a href="mailto:${company.email}">${company.email}</a>` : '-'}</td>
                <td>${company.rating ? `⭐ ${company.rating}` : '-'}</td>
                <td>${company.reviews_count || '-'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Erreur chargement entreprises:', error);
        document.getElementById('companiesTable').innerHTML = 
            '<tr><td colspan="8" class="text-center">Erreur de chargement</td></tr>';
    }
}

// Filtres
function applyFilters() {
    currentFilters = {
        city: document.getElementById('cityFilter').value,
        has_website: document.getElementById('websiteFilter').value,
        has_email: document.getElementById('emailFilter').value,
        search: document.getElementById('searchFilter').value
    };
    loadCompanies();
}

function resetFilters() {
    document.getElementById('cityFilter').value = '';
    document.getElementById('websiteFilter').value = '';
    document.getElementById('emailFilter').value = '';
    document.getElementById('searchFilter').value = '';
    currentFilters = { city: '', has_website: '', has_email: '', search: '' };
    loadCompanies();
}

// Export CSV avec tous les filtres
function exportCsv() {
    const params = new URLSearchParams();
    
    if (currentFilters.city) params.append('city', currentFilters.city);
    if (currentFilters.has_website) params.append('has_website', currentFilters.has_website);
    if (currentFilters.has_email) params.append('has_email', currentFilters.has_email);
    if (currentFilters.search) params.append('search', currentFilters.search);
    
    const url = `/api/export/csv${params.toString() ? '?' + params.toString() : ''}`;
    
    console.log('Export CSV avec filtres:', currentFilters);
    window.location.href = url;
}

// Scraper
async function loadScraperStatus() {
    try {
        const response = await fetch('/api/scraper/status', {
            credentials: 'include'
        });
        if (!response.ok) {
            console.error('Erreur HTTP:', response.status);
            return;
        }
        const status = await response.json();
        console.log('Statut scraper:', status);
        
        const statusBadge = document.getElementById('scraperStatus');
        const progress = document.getElementById('scraperProgress');
        const startBtn = document.getElementById('startScraper');
        const stopBtn = document.getElementById('stopScraper');
        
        if (status.running) {
            statusBadge.textContent = 'En cours';
            statusBadge.className = 'status-badge status-running';
            progress.textContent = `${status.last_city || '...'} - ${status.last_keyword || '...'} (${status.completed_combinations} terminées)`;
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            statusBadge.textContent = 'Arrêté';
            statusBadge.className = 'status-badge status-stopped';
            progress.textContent = status.completed_combinations ? 
                `${status.completed_combinations} combinaisons terminées` : 'Aucune progression';
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    } catch (error) {
        console.error('Erreur statut scraper:', error);
    }
}

async function startScraper() {
    console.log('startScraper() appelé');
    
    if (!confirm('Démarrer le scraper ? Cette opération peut prendre plusieurs heures.')) {
        return;
    }
    
    try {
        console.log('Envoi requête POST /api/scraper/start');
        const response = await fetch('/api/scraper/start', { 
            method: 'POST',
            credentials: 'include'
        });
        
        console.log('Réponse reçue:', response.status);
        const result = await response.json();
        console.log('Résultat:', result);
        
        if (response.ok) {
            alert('✅ Scraper démarré !');
            // Attendre un peu avant de vérifier le statut
            setTimeout(() => {
                loadScraperStatus();
            }, 1000);
            setTimeout(() => {
                loadStats();
                loadCompanies();
            }, 2000);
        } else {
            alert('❌ Erreur: ' + result.error);
            loadScraperStatus(); // Recharger le statut même en cas d'erreur
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('❌ Erreur lors du démarrage: ' + error.message);
    }
}

async function stopScraper() {
    console.log('stopScraper() appelé');
    
    if (!confirm('Arrêter le scraper ? Les données déjà récupérées seront sauvegardées.')) {
        return;
    }
    
    try {
        console.log('Envoi requête POST /api/scraper/stop');
        const response = await fetch('/api/scraper/stop', { 
            method: 'POST',
            credentials: 'include'
        });
        
        console.log('Réponse reçue:', response.status);
        const result = await response.json();
        console.log('Résultat:', result);
        
        if (response.ok) {
            alert('✅ Scraper arrêté !');
            loadScraperStatus();
            loadStats();
            loadCompanies();
        } else {
            alert('❌ Erreur: ' + result.error);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('❌ Erreur lors de l\'arrêt: ' + error.message);
    }
}

// Déconnexion
function logout() {
    fetch('/', {
        credentials: 'include',
        headers: {
            'Authorization': 'Basic ' + btoa('logout:logout')
        }
    }).then(() => {
        window.location.reload();
    });
}

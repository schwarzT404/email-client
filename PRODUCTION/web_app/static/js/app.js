// Variables globales
let isProcessing = false;

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    loadExamples();
    updateSystemStatus();
    
    // Actualiser le statut toutes les 30 secondes
    setInterval(updateSystemStatus, 30000);
});

// Gestion du formulaire
document.getElementById('message-form').addEventListener('submit', function(e) {
    e.preventDefault();
    processMessage();
});

// Traitement du message
async function processMessage() {
    if (isProcessing) return;
    
    const email = document.getElementById('email').value.trim();
    const subject = document.getElementById('subject').value.trim();
    const message = document.getElementById('message').value.trim();
    
    if (!email || !message) {
        showToast('Erreur', 'Email et message requis', 'danger');
        return;
    }
    
    isProcessing = true;
    showLoading();
    
    try {
        const response = await fetch('/api/process-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, subject, message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResult(data.result);
            showToast('Succès', 'Message traité avec succès', 'success');
        } else {
            showError('Erreur: ' + data.error);
            showToast('Erreur', data.error, 'danger');
        }
        
    } catch (error) {
        showError('Erreur de connexion: ' + error.message);
        showToast('Erreur', 'Erreur de connexion', 'danger');
    } finally {
        isProcessing = false;
    }
}

// Afficher le résultat
function displayResult(result) {
    const resultArea = document.getElementById('result-area');
    resultArea.className = 'result-area has-content animate__animated animate__fadeIn';
    
    resultArea.innerHTML = `
        <div class="row g-3">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="text-primary mb-0"><i class="bi bi-check-circle-fill"></i> Traitement Terminé</h6>
                    <span class="badge bg-success">${result.category}</span>
                </div>
            </div>
            
            <div class="col-md-6">
                <small class="text-muted">Email Client</small>
                <div class="fw-bold">${result.email}</div>
            </div>
            
            <div class="col-md-6">
                <small class="text-muted">Score de Qualité</small>
                <div class="fw-bold text-success">${(result.quality_score * 100).toFixed(1)}%</div>
            </div>
            
            <div class="col-12">
                <small class="text-muted">Réponse Générée</small>
                <div class="bg-light p-3 rounded-3 mt-1" style="white-space: pre-line; max-height: 200px; overflow-y: auto;">
                    ${result.response}
                </div>
            </div>
            
            <div class="col-12">
                <small class="text-muted">Ticket ID</small>
                <div class="fw-bold text-info">${result.ticket_id}</div>
            </div>
            
            <div class="col-12 mt-3">
                <button class="btn btn-outline-primary btn-sm" onclick="copyResponse()">
                    <i class="bi bi-clipboard"></i> Copier la Réponse
                </button>
            </div>
        </div>
    `;
    
    // Stocker la réponse pour la copie
    window.lastResponse = result.response;
}

// Afficher l'état de chargement
function showLoading() {
    const resultArea = document.getElementById('result-area');
    resultArea.className = 'result-area';
    resultArea.innerHTML = `
        <div class="text-center">
            <div class="loading-spinner"></div>
            <p class="mt-3 text-primary">Traitement en cours...</p>
            <small class="text-muted">Classification et génération de réponse</small>
        </div>
    `;
}

// Afficher une erreur
function showError(message) {
    const resultArea = document.getElementById('result-area');
    resultArea.className = 'result-area';
    resultArea.innerHTML = `
        <div class="text-center text-danger">
            <i class="bi bi-exclamation-triangle" style="font-size: 3rem;"></i>
            <p class="mt-3 fw-bold">Erreur de Traitement</p>
            <p class="text-muted">${message}</p>
        </div>
    `;
}

// Charger les statistiques
async function loadStatistics() {
    const statsContent = document.getElementById('stats-content');
    statsContent.innerHTML = `
        <div class="text-center">
            <div class="loading-spinner"></div>
            <p class="mt-3">Chargement des statistiques...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();
        
        if (data.success) {
            displayStatistics(data.stats);
        } else {
            statsContent.innerHTML = `
                <div class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    <p>Erreur de chargement: ${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        statsContent.innerHTML = `
            <div class="text-center text-danger">
                <i class="bi bi-wifi-off"></i>
                <p>Erreur de connexion</p>
            </div>
        `;
    }
}

// Afficher les statistiques
function displayStatistics(stats) {
    const statsContent = document.getElementById('stats-content');
    
    statsContent.innerHTML = `
        <div class="row g-4">
            <div class="col-md-3">
                <div class="stats-card animate__animated animate__fadeInUp">
                    <i class="bi bi-people-fill" style="font-size: 2rem;"></i>
                    <h3 class="mt-2">${stats.nb_clients}</h3>
                    <p class="mb-0">Clients</p>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="stats-card animate__animated animate__fadeInUp" style="animation-delay: 0.1s;">
                    <i class="bi bi-cart-fill" style="font-size: 2rem;"></i>
                    <h3 class="mt-2">${stats.nb_commandes}</h3>
                    <p class="mb-0">Commandes</p>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="stats-card animate__animated animate__fadeInUp" style="animation-delay: 0.2s;">
                    <i class="bi bi-currency-euro" style="font-size: 2rem;"></i>
                    <h3 class="mt-2">${stats.ca_total.toFixed(0)}€</h3>
                    <p class="mb-0">Chiffre d'Affaires</p>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="stats-card animate__animated animate__fadeInUp" style="animation-delay: 0.3s;">
                    <i class="bi bi-basket-fill" style="font-size: 2rem;"></i>
                    <h3 class="mt-2">${stats.panier_moyen.toFixed(0)}€</h3>
                    <p class="mb-0">Panier Moyen</p>
                </div>
            </div>
        </div>
        
        <div class="row mt-5">
            <div class="col-12">
                <div class="card card-modern">
                    <div class="card-body">
                        <h5 class="card-title"><i class="bi bi-trophy-fill text-warning"></i> Top Clients</h5>
                        <div class="row">
                            ${stats.top_clients.map((client, index) => `
                                <div class="col-md-4 mb-3">
                                    <div class="d-flex align-items-center">
                                        <div class="badge bg-primary rounded-pill me-3">${index + 1}</div>
                                        <div>
                                            <div class="fw-bold">${client.prenom} ${client.nom}</div>
                                            <small class="text-muted">${client.nb_commandes} commandes</small>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Charger les exemples
async function loadExamples() {
    try {
        const response = await fetch('/api/examples');
        const data = await response.json();
        
        if (data.success) {
            displayExamples(data.examples);
        }
    } catch (error) {
        console.error('Erreur de chargement des exemples:', error);
    }
}

// Afficher les exemples
function displayExamples(examples) {
    const examplesContent = document.getElementById('examples-content');
    
    examplesContent.innerHTML = `
        <div class="row g-3">
            ${examples.map(example => `
                <div class="col-md-6">
                    <div class="card example-card" onclick="loadExample(${example.id})">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title mb-0">${example.subject}</h6>
                                <span class="badge bg-secondary">${example.category}</span>
                            </div>
                            <p class="text-muted small mb-2">${example.email}</p>
                            <p class="card-text">${example.message.substring(0, 100)}...</p>
                            <small class="text-primary"><i class="bi bi-hand-index"></i> Cliquer pour utiliser</small>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Charger un exemple
function loadExample(exampleId) {
    fetch('/api/examples')
        .then(response => response.json())
        .then(data => {
            const example = data.examples.find(ex => ex.id === exampleId);
            if (example) {
                document.getElementById('email').value = example.email;
                document.getElementById('subject').value = example.subject;
                document.getElementById('message').value = example.message;
                
                // Revenir à l'onglet traitement
                document.getElementById('process-tab').click();
                
                showToast('Exemple chargé', 'Les données ont été remplies automatiquement', 'info');
            }
        });
}

// Mettre à jour le statut du système
async function updateSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        const indicator = document.querySelector('.status-indicator');
        const text = document.querySelector('.navbar-text');
        
        if (status.agent_ready) {
            indicator.className = 'status-indicator status-connected';
            text.innerHTML = `
                <span class="status-indicator status-connected"></span>
                Système Actif
            `;
        } else {
            indicator.className = 'status-indicator status-disconnected';
            text.innerHTML = `
                <span class="status-indicator status-disconnected"></span>
                Système Inactif
            `;
        }
    } catch (error) {
        console.error('Erreur de statut:', error);
    }
}

// Fonctions utilitaires
function clearForm() {
    document.getElementById('message-form').reset();
    const resultArea = document.getElementById('result-area');
    resultArea.className = 'result-area';
    resultArea.innerHTML = `
        <div class="text-center text-muted">
            <i class="bi bi-robot" style="font-size: 3rem; opacity: 0.3;"></i>
            <p class="mt-3">Prêt à traiter votre message...</p>
        </div>
    `;
}

function copyResponse() {
    if (window.lastResponse) {
        navigator.clipboard.writeText(window.lastResponse).then(() => {
            showToast('Copié', 'Réponse copiée dans le presse-papiers', 'success');
        });
    }
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showToast(title, message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    const toastId = 'toast-' + Date.now();
    
    const toastHTML = `
        <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-${type === 'success' ? 'check-circle-fill text-success' : 
                                 type === 'danger' ? 'exclamation-triangle-fill text-danger' : 
                                 type === 'warning' ? 'exclamation-triangle-fill text-warning' : 
                                 'info-circle-fill text-info'}"></i>
                <strong class="me-auto ms-2">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
    
    // Supprimer le toast après fermeture
    document.getElementById(toastId).addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
} 
/**
 * Fonctionnalités Avancées - Support Client Claude 4
 * Inscription, monitoring API, délais de traitement
 */

// Variables globales
let apiMonitorInterval;
let isMonitoring = false;

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', function() {
    initializeEnhancedFeatures();
});

function initializeEnhancedFeatures() {
    setupRegistrationModal();
    startApiMonitoring();
    enhanceFormSubmission();
    console.log('🚀 Fonctionnalités avancées Claude 4 initialisées');
}

// === SYSTÈME D'INSCRIPTION ===

function setupRegistrationModal() {
    // Créer le bouton d'inscription
    const navbar = document.querySelector('.navbar-nav');
    if (navbar && !document.getElementById('register-btn')) {
        const registerBtn = document.createElement('li');
        registerBtn.className = 'nav-item ms-2';
        registerBtn.innerHTML = `
            <button class="btn btn-outline-light btn-sm" id="register-btn">
                <i class="bi bi-person-plus"></i> S'inscrire
            </button>
        `;
        navbar.appendChild(registerBtn);
        
        registerBtn.addEventListener('click', showRegistrationModal);
    }
}

function showRegistrationModal() {
    const modalHtml = `
        <div class="modal fade" id="registrationModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-person-plus"></i>
                            Inscription au Service Support
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="bi bi-shield-check"></i>
                            <strong>Accès membres uniquement</strong><br>
                            Seuls les clients inscrits peuvent utiliser le service.
                        </div>
                        
                        <form id="registration-form">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="reg-nom" class="form-label">Nom *</label>
                                    <input type="text" class="form-control" id="reg-nom" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="reg-prenom" class="form-label">Prénom *</label>
                                    <input type="text" class="form-control" id="reg-prenom" required>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="reg-email" class="form-label">Email *</label>
                                <input type="email" class="form-control" id="reg-email" required>
                            </div>
                            
                            <div class="alert alert-success">
                                <i class="bi bi-lightning"></i>
                                <small><strong>Inscription immédiate</strong> - Pas de vérification requise (prototype)</small>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-primary" onclick="submitRegistration()">
                            <i class="bi bi-person-check"></i> S'inscrire
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Supprimer ancien modal
    const existing = document.getElementById('registrationModal');
    if (existing) existing.remove();
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('registrationModal'));
    modal.show();
}

async function submitRegistration() {
    const nom = document.getElementById('reg-nom').value.trim();
    const prenom = document.getElementById('reg-prenom').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    
    if (!nom || !prenom || !email) {
        showAlert('Tous les champs sont requis', 'warning');
        return;
    }
    
    const btn = document.querySelector('#registrationModal .btn-primary');
    const originalText = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Inscription...';
        
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nom, prenom, email })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Bienvenue ${prenom} ! Inscription réussie.`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('registrationModal')).hide();
            
            // Pré-remplir l'email
            const emailField = document.getElementById('email');
            if (emailField) emailField.value = email;
        } else {
            showAlert(data.error || 'Erreur inscription', 'danger');
        }
    } catch (error) {
        showAlert('Erreur de connexion', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// === MONITORING API ===

function startApiMonitoring() {
    if (isMonitoring) return;
    
    isMonitoring = true;
    console.log('🔍 Monitoring API Claude 4 démarré (mode console uniquement)');
    
    testApiStatus();
    
    // Test toutes les 30 secondes
    apiMonitorInterval = setInterval(testApiStatus, 30000);
}

// Widget de monitoring supprimé - logs console uniquement

async function testApiStatus() {
    const start = Date.now();
    
    try {
        const response = await fetch('/api/status');
        const time = Date.now() - start;
        
        if (response.ok) {
            const data = await response.json();
            console.log(`🟢 [${new Date().toLocaleTimeString()}] API Status: OK (${time}ms)`, {
                claude_ready: data.claude_ready,
                db_connected: data.db_connected,
                uptime: data.uptime || 'N/A'
            });
        } else {
            console.error(`🔴 [${new Date().toLocaleTimeString()}] API Status: ERROR ${response.status} (${time}ms)`);
        }
    } catch (error) {
        const time = Date.now() - start;
        console.error(`⚫ [${new Date().toLocaleTimeString()}] API Status: OFFLINE (${time}ms)`, error.message);
    }
}

// Fonction de monitoring visuel supprimée - logs console uniquement

// === AMÉLIORATION FORMULAIRE ===

function enhanceFormSubmission() {
    const form = document.getElementById('support-form');
    if (!form) return;
    
    // Nouveau gestionnaire
    const newForm = form.cloneNode(true);
    form.parentNode.replaceChild(newForm, form);
    
    newForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value.trim();
        const subject = document.getElementById('subject').value.trim();
        const message = document.getElementById('message').value.trim();
        
        if (!email || !message) {
            showAlert('Email et message requis', 'warning');
            return;
        }
        
        await processWithDelay(email, subject, message);
    });
}

async function processWithDelay(email, subject, message) {
    const btn = document.querySelector('#support-form button[type="submit"]');
    const resultArea = document.getElementById('result-area');
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Traitement...';
    
    // Délai aléatoire 10-30s
    const delay = Math.floor(Math.random() * 21) + 10;
    
    // Interface de traitement
    resultArea.innerHTML = `
        <div class="card border-primary">
            <div class="card-header bg-primary text-white">
                <h6 class="mb-0">
                    <i class="bi bi-cpu"></i> Claude 4 Sonnet - Chaîne de Réflexion
                </h6>
            </div>
            <div class="card-body text-center">
                <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;"></div>
                <h5 id="process-status">Initialisation...</h5>
                <p class="text-muted">Intelligence artificielle avec réflexion approfondie</p>
                
                <div class="progress mb-3">
                    <div id="progress-bar" class="progress-bar progress-bar-striped progress-bar-animated bg-primary" style="width: 0%"></div>
                </div>
                
                <div class="row text-center">
                    <div class="col-6">
                        <small class="text-muted d-block">Délai prévu</small>
                        <strong>${delay}s</strong>
                    </div>
                    <div class="col-6">
                        <small class="text-muted d-block">Temps restant</small>
                        <strong id="countdown">${delay}s</strong>
                    </div>
                </div>
                
                <small class="text-info mt-3 d-block">
                    <i class="bi bi-shield-check"></i> Traitement sécurisé • Réponse personnalisée
                </small>
            </div>
        </div>
    `;
    
    // Animation
    let progress = 0;
    let remaining = delay;
    const progressBar = document.getElementById('progress-bar');
    const countdown = document.getElementById('countdown');
    const status = document.getElementById('process-status');
    
    const steps = [
        "Analyse du message...",
        "Classification automatique...",
        "Recherche base de données...",
        "Génération réflexive...",
        "Optimisation réponse...",
        "Finalisation..."
    ];
    
    const interval = setInterval(() => {
        progress += Math.random() * 3 + 1;
        if (progress > 95) progress = 95;
        progressBar.style.width = progress + '%';
        
        remaining--;
        countdown.textContent = Math.max(remaining, 0) + 's';
        
        const stepIndex = Math.floor((progress / 95) * steps.length);
        if (steps[stepIndex]) {
            status.textContent = steps[stepIndex];
        }
    }, 1000);
    
    try {
        const response = await fetch('/api/process-message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, subject, message })
        });
        
        clearInterval(interval);
        progressBar.style.width = '100%';
        countdown.textContent = '0s';
        
        const data = await response.json();
        
        if (data.success) {
            setTimeout(() => {
                displayResult(data);
                showAlert('Traité par Claude 4 avec succès !', 'success');
            }, 800);
        } else {
            if (data.requires_registration) {
                showAlert(data.error, 'warning');
                setTimeout(showRegistrationModal, 1000);
            } else {
                showAlert(data.error, 'danger');
            }
            resultArea.innerHTML = '<div class="alert alert-warning">Traitement échoué</div>';
        }
    } catch (error) {
        clearInterval(interval);
        showAlert('Erreur de connexion', 'danger');
        resultArea.innerHTML = '<div class="alert alert-danger">Erreur de connexion</div>';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-send"></i> Envoyer le message';
    }
}

function displayResult(data) {
    const resultArea = document.getElementById('result-area');
    const result = data.result;
    
    resultArea.innerHTML = `
        <div class="card border-success">
            <div class="card-header bg-success text-white">
                <div class="d-flex justify-content-between">
                    <h6 class="mb-0">
                        <i class="bi bi-check-circle"></i> Réponse Claude 4 générée
                    </h6>
                    <span class="badge bg-light text-success">${data.ai_model || 'Claude 4'}</span>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-lg-8">
                        <h6 class="text-primary"><i class="bi bi-chat-left-text"></i> Réponse :</h6>
                        <div class="bg-light p-4 rounded border-start border-4 border-primary">
                            ${result.response ? result.response.replace(/\n/g, '<br>') : 'Pas de réponse'}
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <h6 class="text-primary"><i class="bi bi-graph-up"></i> Analyse :</h6>
                        <div class="list-group list-group-flush">
                            <div class="list-group-item d-flex justify-content-between">
                                <span>Catégorie</span>
                                <span class="badge bg-primary">${result.category || 'N/A'}</span>
                            </div>
                            <div class="list-group-item d-flex justify-content-between">
                                <span>Urgence</span>
                                ${getUrgencyBadge(result.urgency)}
                            </div>
                            <div class="list-group-item d-flex justify-content-between">
                                <span>Sentiment</span>
                                ${getSentimentBadge(result.sentiment)}
                            </div>
                            <div class="list-group-item d-flex justify-content-between">
                                <span>Qualité</span>
                                ${getQualityBadge(result.quality_score)}
                            </div>
                        </div>
                        
                        <div class="mt-3 p-3 bg-info bg-opacity-10 rounded">
                            <small class="text-muted">
                                <strong>Ticket:</strong> ${result.ticket_id}<br>
                                <strong>Délai:</strong> ${data.processing_delay || 'N/A'}s<br>
                                <strong>Mode:</strong> ${data.mode}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// === UTILITAIRES ===

function getUrgencyBadge(urgency) {
    if (!urgency) return '<span class="badge bg-secondary">N/A</span>';
    const classes = ['bg-success', 'bg-info', 'bg-warning', 'bg-warning', 'bg-danger'];
    return `<span class="badge ${classes[urgency - 1] || 'bg-secondary'}">${urgency}/5</span>`;
}

function getSentimentBadge(sentiment) {
    const badges = {
        'tres_negatif': '<span class="badge bg-danger">Très négatif</span>',
        'negatif': '<span class="badge bg-warning">Négatif</span>',
        'neutre': '<span class="badge bg-info">Neutre</span>',
        'positif': '<span class="badge bg-success">Positif</span>'
    };
    return badges[sentiment] || `<span class="badge bg-secondary">${sentiment || 'N/A'}</span>`;
}

function getQualityBadge(score) {
    if (!score) return '<span class="badge bg-secondary">N/A</span>';
    const percentage = Math.round(score * 100);
    let badgeClass = 'bg-secondary';
    if (percentage >= 80) badgeClass = 'bg-success';
    else if (percentage >= 60) badgeClass = 'bg-info';
    else if (percentage >= 40) badgeClass = 'bg-warning';
    else badgeClass = 'bg-danger';
    return `<span class="badge ${badgeClass}">${percentage}%</span>`;
}

function showAlert(message, type = 'info') {
    // Supprimer alertes existantes
    document.querySelectorAll('.alert.alert-dismissible').forEach(a => a.remove());
    
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 1055; min-width: 300px;">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    setTimeout(() => {
        const alert = document.querySelector('.alert.alert-dismissible');
        if (alert) new bootstrap.Alert(alert).close();
    }, 4000);
}

// Export global
window.enhancedFeatures = {
    showRegistrationModal,
    startApiMonitoring,
    testApiStatus
}; 
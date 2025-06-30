// =================================================================================
// INITIALISATION ET VARIABLES GLOBALES
// =================================================================================
let isProcessing = false;
let cart = [];

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des listeners et des données
    document.getElementById('support-form').addEventListener('submit', processMessage);
    updateSystemStatus();
    loadProducts();
    setInterval(updateSystemStatus, 30000);
});


// =================================================================================
// PARTIE 1 : TRAITEMENT DES MESSAGES DE SUPPORT (Formulaire principal)
// =================================================================================

async function processMessage(e) {
    if (e) e.preventDefault();
    if (isProcessing) return;
    
    const email = document.getElementById('email').value.trim();
    const subject = document.getElementById('subject').value.trim();
    const message = document.getElementById('message').value.trim();
    
    if (!email || !message) {
        showToast('Erreur', 'Email et message sont requis.', 'danger');
        return;
    }
    
    isProcessing = true;
    showLoading();
    
    try {
        const response = await fetch('/api/process-message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, subject, message })
        });
        const data = await response.json();
        if (data.success) {
            displayResult(data.result);
            showToast('Succès', 'Message traité avec succès.', 'success');
        } else {
            showError('Erreur: ' + data.error);
        }
    } catch (error) {
        showError('Erreur de connexion: ' + error.message);
    } finally {
        isProcessing = false;
    }
}

function displayResult(result) {
    const resultArea = document.getElementById('result-area');
    resultArea.className = 'result-area has-content animate__animated animate__fadeIn';
    resultArea.innerHTML = `
        <h6 class="text-primary"><i class="bi bi-check-circle-fill"></i> Traitement Terminé</h6>
        <p><strong>Catégorie :</strong> <span class="badge bg-success">${result.category}</span></p>
        <p><strong>Réponse suggérée :</strong></p>
        <div class="bg-light p-2 rounded">${result.response}</div>
        <small class="text-muted">Ticket ID: ${result.ticket_id}</small>`;
    window.lastResponse = result.response;
}

function showLoading() {
    const resultArea = document.getElementById('result-area');
    resultArea.className = 'result-area';
    resultArea.innerHTML = `<div class="text-center"><div class="loading-spinner"></div><p class="mt-2">Traitement en cours...</p></div>`;
}

function showError(message) {
    const resultArea = document.getElementById('result-area');
    resultArea.className = 'result-area';
    resultArea.innerHTML = `<div class="text-center text-danger"><i class="bi bi-exclamation-triangle"></i><p>${message}</p></div>`;
}

// =================================================================================
// PARTIE 2 : GESTION DES COMMANDES (Section produits/panier)
// =================================================================================

async function loadProducts() {
    console.time("Diagnostic - Temps total de chargement des produits");
    // Note : On ne vide plus la section, le squelette est déjà là.
    
    try {
        const response = await fetch('/api/products');
        const data = await response.json();
        if (data.success) {
            displayProducts(data.products);
        } else {
            const productList = document.getElementById('product-list-container');
            if (productList) {
                productList.innerHTML = '<p class="text-danger">Erreur de chargement des produits.</p>';
            }
        }
    } catch (error) {
        const productList = document.getElementById('product-list-container');
        if (productList) {
            productList.innerHTML = '<p class="text-danger">Erreur de connexion.</p>';
        }
    } finally {
        console.timeEnd("Diagnostic - Temps total de chargement des produits");
    }
}

function displayProducts(products) {
    const productList = document.getElementById('product-list-container'); // Un nouvel ID pour le conteneur des produits
    if (!productList) return;
    
    productList.innerHTML = products.map(p => `
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                    <div class="card-body">
                    <h6 class="card-title">${p.name}</h6>
                    <div class="d-flex justify-content-between">
                        <span class="fw-bold text-primary">${p.price.toFixed(2)}€</span>
                        <span class="badge bg-${p.stock > 0 ? 'success' : 'danger'}">${p.stock > 0 ? `Stock: ${p.stock}` : 'Rupture'}</span>
                    </div>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="addToCart(${p.id}, '${p.name}', ${p.price})" ${p.stock === 0 ? 'disabled' : ''}>
                        <i class="bi bi-cart-plus"></i> Ajouter
                    </button>
                </div>
            </div>
        </div>`).join('');
}


function addToCart(id, name, price) {
    const existingItem = cart.find(item => item.id === id);
    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({ id, name, price, quantity: 1 });
    }
    updateCart();
}

function updateCart() {
    const cartItemsDiv = document.getElementById('cart-items');
    const cartTotalDiv = document.getElementById('cart-total');
    const checkoutBtn = document.getElementById('checkout-btn');

    if (cart.length === 0) {
        cartItemsDiv.innerHTML = '<p class="text-muted">Panier vide.</p>';
        cartTotalDiv.innerHTML = '';
        checkoutBtn.disabled = true;
    } else {
        cartItemsDiv.innerHTML = cart.map(item => `
            <div class="d-flex justify-content-between">
                <span>${item.name} x${item.quantity}</span>
                <span>${(item.price * item.quantity).toFixed(2)}€</span>
            </div>`).join('');
        const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
        cartTotalDiv.innerHTML = `<strong>Total: ${total.toFixed(2)}€</strong>`;
        checkoutBtn.disabled = false;
    }
}

async function checkout() {
    const email = document.getElementById('order-email').value.trim();
    if (!email) {
        showToast('Erreur', 'Veuillez renseigner un email pour la commande.', 'danger');
        return;
    }
    const emailExists = await checkEmail(email);
    if (emailExists) {
        await proceedToOrder(email);
    } else {
        const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
        document.getElementById('register-email').value = email;
        registerModal.show();
    }
}

async function checkEmail(email) {
    try {
        const response = await fetch('/api/check-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        return data.exists;
    } catch (e) { return false; }
}

async function submitRegistration() {
    const email = document.getElementById('register-email').value;
    const prenom = document.getElementById('register-prenom').value.trim();
    const nom = document.getElementById('register-nom').value.trim();

    if (!prenom || !nom) {
        showToast('Erreur', 'Nom et prénom requis.', 'warning');
        return;
    }

    const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, prenom, nom })
    });
    const data = await response.json();

    if (data.success) {
        showToast('Succès', 'Inscription réussie !', 'success');
        bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
        await proceedToOrder(email);
    } else {
        showToast('Erreur', data.error || "L'inscription a échoué.", 'danger');
    }
}

async function proceedToOrder(email) {
    if (cart.length === 0) {
        showToast('Info', 'Votre panier est vide.', 'warning');
        return;
    }
    try {
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, cart })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Commande validée !', `ID: ${data.order_uid}`, 'success');
            simulateDelivery(data.order_uid);
            cart = [];
            updateCart();
            document.getElementById('order-email').value = '';
        } else {
            showToast('Erreur de commande', data.error, 'danger');
    }
    } catch (e) {
        showToast('Erreur', 'Impossible de passer la commande.', 'danger');
    }
}

function simulateDelivery(orderUid) {
    const orderSection = document.getElementById('order-section');
    const deliveryTime = Math.floor(Math.random() * 31) + 10;
    let remaining = deliveryTime;
    orderSection.innerHTML = `
        <div class="text-center p-4">
            <h4>🚚 Livraison en cours...</h4>
            <p>Commande <strong>${orderUid}</strong>. Arrivée dans <span id="delivery-timer">${remaining}</span>s.</p>
            <div class="progress"><div id="delivery-progress" class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%;"></div></div>
        </div>`;
    const timer = setInterval(() => {
        remaining--;
        const progress = ((deliveryTime - remaining) / deliveryTime) * 100;
        document.getElementById('delivery-timer').innerText = remaining;
        document.getElementById('delivery-progress').style.width = `${progress}%`;
        if (remaining <= 0) {
            clearInterval(timer);
            orderSection.innerHTML = `
                <div class="text-center p-4">
                    <h4>✅ Commande ${orderUid} livrée !</h4>
                    <button class="btn btn-primary" onclick="reloadOrderSection()">Nouvelle Commande</button>
                </div>`;
        }
    }, 1000);
}

function reloadOrderSection() {
    // Recharge l'HTML initial de la section commande et les produits
    const orderSection = document.getElementById('order-section');
    orderSection.innerHTML = `
        <div class="row">
            <div class="col-lg-8" id="product-list-container"></div>
            <div class="col-lg-4">
                <h5><i class="bi bi-basket-fill"></i> Panier</h5>
                <div class="mb-3">
                    <label for="order-email" class="form-label fw-bold"><i class="bi bi-at"></i> Email</label>
                    <input type="email" class="form-control" id="order-email">
                </div>
                <div id="cart-items"><p class="text-muted">Panier vide.</p></div>
                <div id="cart-total" class="fw-bold fs-5 mb-3"></div>
                <button class="btn btn-gradient w-100" id="checkout-btn" onclick="checkout()" disabled>Valider</button>
        </div>
        </div>`;
    loadProducts();
}


// =================================================================================
// PARTIE 3 : FONCTIONS UTILITAIRES
// =================================================================================

async function updateSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        const indicator = document.querySelector('.status-indicator.claude-status'); // Utiliser une classe spécifique
        if (indicator) {
            indicator.classList.toggle('status-connected', data.agent_ready);
            indicator.classList.toggle('status-disconnected', !data.agent_ready);
        }
    } catch (e) { console.error('Erreur de statut'); }
}

function clearForm() {
    document.getElementById('support-form').reset();
    document.getElementById('result-area').innerHTML = '<div class="text-center text-muted"><i class="bi bi-robot" style="font-size: 2rem;"></i><p>Prêt...</p></div>';
}

function copyResponse() {
    if (window.lastResponse) {
        navigator.clipboard.writeText(window.lastResponse).then(() => showToast('Succès', 'Réponse copiée !', 'success'));
    }
}

function showToast(title, message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div class="toast align-items-center text-bg-${type} border-0" role="alert" id="${toastId}">
            <div class="d-flex"><div class="toast-body"><strong>${title}</strong><br>${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>
        </div>`;
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toast = new bootstrap.Toast(document.getElementById(toastId), { delay: 3000 });
    toast.show();
    document.getElementById(toastId).addEventListener('hidden.bs.toast', function() { this.remove(); });
} 
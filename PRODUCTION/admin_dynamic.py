#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Admin Dynamique - Support Client E-commerce
Gestion en temps réel des commandes, produits et statistiques
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin-dynamic-support-2024'

class DynamicAdminManager:
    def __init__(self):
        self.db_path = 'data/crm_ecommerce.db'
        self.init_enhanced_database()
        print("✅ Interface Admin Dynamique initialisée")
    
    def init_enhanced_database(self):
        """Initialise les tables pour la gestion dynamique"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table produits
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prix REAL NOT NULL,
                    stock INTEGER DEFAULT 0,
                    description TEXT,
                    categorie TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table commandes détaillées
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commandes_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commande_id TEXT UNIQUE NOT NULL,
                    client_email TEXT NOT NULL,
                    client_nom TEXT,
                    client_prenom TEXT,
                    produits_json TEXT,
                    montant_total REAL NOT NULL,
                    nb_articles INTEGER NOT NULL,
                    statut TEXT DEFAULT 'en_attente' CHECK (statut IN ('en_attente', 'confirmee', 'expediee', 'livree', 'annulee')),
                    methode_paiement TEXT DEFAULT 'carte',
                    adresse_livraison TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    shipped_at DATETIME,
                    delivered_at DATETIME
                )
            ''')
            
            # Insérer produits de démo si vide
            cursor.execute("SELECT COUNT(*) FROM produits")
            if cursor.fetchone()[0] == 0:
                produits_demo = [
                    ("Smartphone Pro 128GB", 599.99, 45, "Smartphone haute performance", "Électronique"),
                    ("Casque Bluetooth Premium", 129.99, 23, "Casque audio sans fil", "Audio"),
                    ("Montre Connectée Sport", 249.99, 12, "Montre intelligente étanche", "Accessoires"),
                    ("Écouteurs Sans Fil", 79.99, 67, "Écouteurs true wireless", "Audio"),
                    ("Chargeur Rapide USB-C", 29.99, 156, "Chargeur 65W compatible", "Accessoires"),
                    ("Tablette 10 pouces", 329.99, 18, "Tablette Android 128GB", "Électronique"),
                    ("Powerbank 20000mAh", 49.99, 89, "Batterie externe rapide", "Accessoires"),
                    ("Clavier Mécanique RGB", 119.99, 34, "Clavier gaming rétroéclairé", "Gaming")
                ]
                
                for nom, prix, stock, desc, cat in produits_demo:
                    cursor.execute(
                        "INSERT INTO produits (nom, prix, stock, description, categorie) VALUES (?, ?, ?, ?, ?)",
                        (nom, prix, stock, desc, cat)
                    )
            
            conn.commit()
            conn.close()
            print("✅ Base de données admin dynamique initialisée")
            
        except Exception as e:
            print(f"❌ Erreur initialisation BD admin: {e}")
    
    def create_order(self, client_email, client_nom="", client_prenom="", produits=[], adresse=""):
        """Crée une nouvelle commande avec ID automatique"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Générer ID de commande unique
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            commande_id = f"CMD-{timestamp}-{len(client_email) % 100:02d}"
            
            # Calculer totaux
            montant_total = sum(p.get('prix', 0) * p.get('quantite', 1) for p in produits)
            nb_articles = sum(p.get('quantite', 1) for p in produits)
            
            # Insérer commande
            cursor.execute('''
                INSERT INTO commandes_details 
                (commande_id, client_email, client_nom, client_prenom, produits_json, 
                 montant_total, nb_articles, adresse_livraison)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                commande_id, client_email, client_nom, client_prenom,
                json.dumps(produits), montant_total, nb_articles, adresse
            ))
            
            # Mettre à jour les stocks
            for produit in produits:
                cursor.execute(
                    "UPDATE produits SET stock = stock - ? WHERE id = ?",
                    (produit.get('quantite', 1), produit.get('id'))
                )
            
            # Aussi insérer dans l'ancienne table pour compatibilité
            try:
                cursor.execute(
                    "SELECT id FROM client WHERE email = ?", (client_email,)
                )
                client_row = cursor.fetchone()
                
                if client_row:
                    client_id = client_row[0]
                else:
                    # Créer le client s'il n'existe pas
                    cursor.execute(
                        "INSERT INTO client (nom, prenom, email) VALUES (?, ?, ?)",
                        (client_nom, client_prenom, client_email)
                    )
                    client_id = cursor.lastrowid
                
                cursor.execute(
                    "INSERT INTO commande (date, montant, nb_articles, id_client) VALUES (?, ?, ?, ?)",
                    (datetime.now().strftime('%Y-%m-%d'), montant_total, nb_articles, client_id)
                )
            except:
                pass  # Si l'ancienne table n'existe pas, on continue
            
            conn.commit()
            conn.close()
            
            print(f"✅ Commande créée: {commande_id} - {montant_total}€")
            return commande_id
            
        except Exception as e:
            print(f"❌ Erreur création commande: {e}")
            return None
    
    def get_dashboard_data(self):
        """Récupère toutes les données pour le dashboard dynamique"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) as total FROM commandes_details")
            total_commandes = cursor.fetchone()['total']
            
            cursor.execute("SELECT SUM(montant_total) as total FROM commandes_details")
            chiffre_affaires = cursor.fetchone()['total'] or 0
            
            cursor.execute("SELECT SUM(nb_articles) as total FROM commandes_details")
            total_articles = cursor.fetchone()['total'] or 0
            
            cursor.execute("SELECT COUNT(*) as total FROM produits")
            total_produits = cursor.fetchone()['total']
            
            cursor.execute("SELECT SUM(stock) as total FROM produits")
            stock_total = cursor.fetchone()['total'] or 0
            
            # Nombre total de messages
            cursor.execute("SELECT COUNT(*) as total FROM messages")
            total_messages = cursor.fetchone()['total'] or 0

            # Commandes par statut
            cursor.execute('''
                SELECT statut, COUNT(*) as count 
                FROM commandes_details 
                GROUP BY statut
            ''')
            commandes_statut = {row['statut']: row['count'] for row in cursor.fetchall()}
            
            # Commandes récentes
            cursor.execute('''
                SELECT * FROM commandes_details 
                ORDER BY created_at DESC 
                LIMIT 20
            ''')
            commandes_recentes = [dict(row) for row in cursor.fetchall()]
            
            # Statistiques aujourd'hui
            aujourd_hui = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT 
                    COUNT(*) as commandes_jour,
                    SUM(montant_total) as ca_jour,
                    SUM(nb_articles) as articles_jour
                FROM commandes_details 
                WHERE DATE(created_at) = ?
            ''', (aujourd_hui,))
            
            stats_jour = cursor.fetchone()
            
            conn.close()
            
            return {
                'stats': {
                    'total_commandes': total_commandes,
                    'total_messages': total_messages,
                    'total_articles': total_articles,
                    'total_produits': total_produits,
                    'stock_total': stock_total,
                    'commandes_jour': stats_jour['commandes_jour'] or 0,
                    'ca_jour': round(stats_jour['ca_jour'] or 0, 2),
                    'articles_jour': stats_jour['articles_jour'] or 0
                },
                'commandes_statut': commandes_statut,
                'commandes_recentes': commandes_recentes,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération données dashboard: {e}")
            return {}
    
    def update_order_status(self, commande_id, nouveau_statut):
        """Met à jour le statut d'une commande"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            update_fields = "statut = ?, updated_at = CURRENT_TIMESTAMP"
            params = [nouveau_statut, commande_id]
            
            if nouveau_statut == 'expediee':
                update_fields += ", shipped_at = CURRENT_TIMESTAMP"
            elif nouveau_statut == 'livree':
                update_fields += ", delivered_at = CURRENT_TIMESTAMP"
            
            cursor.execute(f'''
                UPDATE commandes_details 
                SET {update_fields}
                WHERE commande_id = ?
            ''', params)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour statut: {e}")
            return False

    def get_all_clients(self):
        """Récupère tous les clients depuis la base de données."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT nom, prenom, email, 'standard' as type, '' as entreprise FROM client ORDER BY nom")
            clients = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return clients
        except Exception as e:
            print(f"❌ Erreur récupération clients: {e}")
            return []

    def get_messages_by_status(self, status=None):
        """Récupère les messages par statut"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute('SELECT * FROM messages WHERE status = ? ORDER BY created_at DESC', (status,))
            else:
                cursor.execute('SELECT * FROM messages ORDER BY created_at DESC')
            
            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return messages
            
        except Exception as e:
            print(f"❌ Erreur récupération messages: {e}")
            return []

# Instance globale
admin_manager = DynamicAdminManager()

@app.route('/')
def dashboard():
    """Dashboard principal dynamique"""
    template = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dynamique - Support Client E-commerce</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .dashboard-card { 
            background: rgba(255,255,255,0.95); 
            border-radius: 15px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }
        .stat-card { 
            background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
            color: white; 
            border-radius: 15px; 
            padding: 20px; 
            margin-bottom: 15px;
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 2rem; font-weight: bold; }
        .live-indicator { 
            animation: pulse 2s infinite; 
            color: #28a745; 
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .table-responsive { max-height: 400px; overflow-y: auto; }
        .auto-refresh { position: fixed; top: 20px; right: 20px; z-index: 1000; }
    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <div class="row">
            <div class="col-12">
                <div class="dashboard-card p-4">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h1><i class="fas fa-tachometer-alt text-primary"></i> Dashboard Admin Dynamique</h1>
                        <div class="auto-refresh">
                            <span class="badge bg-success live-indicator">
                                <i class="fas fa-circle"></i> LIVE
                            </span>
                        </div>
                    </div>
                    
                    <!-- Statistiques principales -->
                    <div class="row mb-4" id="stats-container">
                        <!-- Les stats seront injectées ici -->
                    </div>
                    
                    <!-- Navigation onglets -->
                    <ul class="nav nav-tabs" id="adminTabs" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="commandes-tab" data-bs-toggle="tab" data-bs-target="#commandes" type="button">
                                <i class="fas fa-shopping-cart"></i> Commandes
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="produits-tab" data-bs-toggle="tab" data-bs-target="#produits" type="button">
                                <i class="fas fa-box"></i> Produits
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="boite-mail-tab" data-bs-toggle="tab" data-bs-target="#boite-mail" type="button">
                                <i class="fas fa-envelope-open-text"></i> Boîte Mail
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="clients-tab" data-bs-toggle="tab" data-bs-target="#clients" type="button">
                                <i class="fas fa-users"></i> Clients
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="nouvelle-commande-tab" data-bs-toggle="tab" data-bs-target="#nouvelle-commande" type="button">
                                <i class="fas fa-plus"></i> Nouvelle Commande
                            </button>
                        </li>
                    </ul>
                    
                    <!-- Contenu des onglets -->
                    <div class="tab-content" id="adminTabsContent">
                        <!-- Onglet Commandes -->
                        <div class="tab-pane fade show active" id="commandes" role="tabpanel">
                            <div class="table-responsive mt-3">
                                <table class="table table-hover" id="commandes-table">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>ID Commande</th>
                                            <th>Client</th>
                                            <th>Email</th>
                                            <th>Montant</th>
                                            <th>Articles</th>
                                            <th>Statut</th>
                                            <th>Date</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="commandes-tbody">
                                        <!-- Les commandes seront injectées ici -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <!-- Onglet Produits -->
                        <div class="tab-pane fade" id="produits" role="tabpanel">
                            <div class="table-responsive mt-3">
                                <table class="table table-hover" id="produits-table">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>ID</th>
                                            <th>Nom</th>
                                            <th>Prix</th>
                                            <th>Stock</th>
                                            <th>Catégorie</th>
                                            <th>Statut Stock</th>
                                        </tr>
                                    </thead>
                                    <tbody id="produits-tbody">
                                        <!-- Les produits seront injectés ici -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <!-- Onglet Boîte Mail -->
                        <div class="tab-pane fade" id="boite-mail" role="tabpanel">
                            <div class="table-responsive mt-3">
                                <table class="table table-hover" id="messages-table">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>Date</th>
                                            <th>Client</th>
                                            <th>Sujet</th>
                                            <th>Statut</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody id="messages-tbody">
                                        <!-- Les messages seront injectés ici -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <!-- Onglet Clients -->
                        <div class="tab-pane fade" id="clients" role="tabpanel">
                            <div class="table-responsive mt-3">
                                <table class="table table-hover" id="clients-table">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>Nom</th>
                                            <th>Prénom</th>
                                            <th>Email</th>
                                            <th>Type</th>
                                            <th>Entreprise</th>
                                        </tr>
                                    </thead>
                                    <tbody id="clients-tbody">
                                        <!-- Les clients seront injectés ici -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <!-- Onglet Nouvelle Commande -->
                        <div class="tab-pane fade" id="nouvelle-commande" role="tabpanel">
                            <div class="mt-3">
                                <h4><i class="fas fa-plus-circle text-success"></i> Créer une Nouvelle Commande</h4>
                                <form id="nouvelle-commande-form">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">Email Client *</label>
                                                <input type="email" class="form-control" id="client-email" required>
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label">Nom</label>
                                                <input type="text" class="form-control" id="client-nom">
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label">Prénom</label>
                                                <input type="text" class="form-control" id="client-prenom">
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">Adresse de Livraison</label>
                                                <textarea class="form-control" id="adresse-livraison" rows="3"></textarea>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <h5>Produits à Commander</h5>
                                    <div id="produits-commande">
                                        <!-- Les produits sélectionnés apparaîtront ici -->
                                    </div>
                                    
                                    <button type="button" class="btn btn-outline-primary" onclick="ajouterProduit()">
                                        <i class="fas fa-plus"></i> Ajouter un Produit
                                    </button>
                                    
                                    <div class="mt-4">
                                        <button type="submit" class="btn btn-success btn-lg">
                                            <i class="fas fa-check"></i> Créer la Commande
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let dashboardData = {};
        let produitsDisponibles = [];
        
        // Rafraîchissement automatique toutes les 5 secondes
        setInterval(loadDashboardData, 5000);
        
        // Chargement initial
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
            loadProduits();
            loadClients();
            loadMessages();
        });
        
        async function loadDashboardData() {
            try {
                const response = await fetch('/api/dashboard-data');
                dashboardData = await response.json();
                updateStats();
                updateCommandesTable();
            } catch (error) {
                console.error('Erreur chargement dashboard:', error);
            }
        }
        
        async function loadProduits() {
            try {
                const response = await fetch('/api/produits');
                produitsDisponibles = await response.json();
                updateProduitsTable();
            } catch (error) {
                console.error('Erreur chargement produits:', error);
            }
        }
        
        async function loadClients() {
            try {
                const response = await fetch('/api/clients');
                const clients = await response.json();
                updateClientsTable(clients);
            } catch (error) {
                console.error('Erreur chargement clients:', error);
            }
        }
        
        async function loadMessages() {
            try {
                const response = await fetch('/api/messages');
                const messages = await response.json();
                updateMessagesTable(messages);
            } catch (error) {
                console.error('Erreur chargement messages:', error);
            }
        }
        
        function updateStats() {
            const stats = dashboardData.stats || {};
            const statsHtml = `
                <div class="col-md-3">
                    <div class="stat-card text-center">
                        <i class="fas fa-shopping-cart fa-2x mb-2"></i>
                        <div class="stat-number">${stats.total_commandes || 0}</div>
                        <div>Commandes Total</div>
                        <small>Aujourd'hui: ${stats.commandes_jour || 0}</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card text-center">
                        <i class="fas fa-envelope fa-2x mb-2"></i>
                        <div class="stat-number">${stats.total_messages || 0}</div>
                        <div>Mails Reçus</div>
                        <small>Total traités</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card text-center">
                        <i class="fas fa-box fa-2x mb-2"></i>
                        <div class="stat-number">${stats.total_articles || 0}</div>
                        <div>Articles Vendus</div>
                        <small>Aujourd'hui: ${stats.articles_jour || 0}</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card text-center">
                        <i class="fas fa-warehouse fa-2x mb-2"></i>
                        <div class="stat-number">${stats.stock_total || 0}</div>
                        <div>Stock Total</div>
                        <small>Produits: ${stats.total_produits || 0}</small>
                    </div>
                </div>
            `;
            document.getElementById('stats-container').innerHTML = statsHtml;
        }
        
        function updateCommandesTable() {
            const commandes = dashboardData.commandes_recentes || [];
            const tbody = document.getElementById('commandes-tbody');
            
            tbody.innerHTML = commandes.map(cmd => {
                const statutBadge = getStatutBadge(cmd.statut);
                const date = new Date(cmd.created_at).toLocaleDateString('fr-FR');
                
                return `
                    <tr>
                        <td><strong>${cmd.commande_id}</strong></td>
                        <td>${cmd.client_nom || ''} ${cmd.client_prenom || ''}</td>
                        <td>${cmd.client_email}</td>
                        <td><strong>${cmd.montant_total}€</strong></td>
                        <td><span class="badge bg-info">${cmd.nb_articles}</span></td>
                        <td>${statutBadge}</td>
                        <td>${date}</td>
                        <td>
                            <select class="form-select form-select-sm" onchange="updateOrderStatus('${cmd.commande_id}', this.value)">
                                <option value="en_attente" ${cmd.statut === 'en_attente' ? 'selected' : ''}>En Attente</option>
                                <option value="confirmee" ${cmd.statut === 'confirmee' ? 'selected' : ''}>Confirmée</option>
                                <option value="expediee" ${cmd.statut === 'expediee' ? 'selected' : ''}>Expédiée</option>
                                <option value="livree" ${cmd.statut === 'livree' ? 'selected' : ''}>Livrée</option>
                                <option value="annulee" ${cmd.statut === 'annulee' ? 'selected' : ''}>Annulée</option>
                            </select>
                        </td>
                    </tr>
                `;
            }).join('');
        }
        
        function updateProduitsTable() {
            const tbody = document.getElementById('produits-tbody');
            
            tbody.innerHTML = produitsDisponibles.map(produit => {
                const stockBadge = produit.stock < 10 ? 
                    '<span class="badge bg-danger">Stock Faible</span>' :
                    produit.stock < 20 ? 
                    '<span class="badge bg-warning">Stock Moyen</span>' :
                    '<span class="badge bg-success">Stock OK</span>';
                
                return `
                    <tr>
                        <td>${produit.id}</td>
                        <td><strong>${produit.nom}</strong></td>
                        <td>${produit.prix}€</td>
                        <td><span class="badge ${produit.stock < 10 ? 'bg-danger' : 'bg-primary'}">${produit.stock}</span></td>
                        <td>${produit.categorie}</td>
                        <td>${stockBadge}</td>
                    </tr>
                `;
            }).join('');
        }
        
        function updateMessagesTable(messages) {
            const tbody = document.getElementById('messages-tbody');
            tbody.innerHTML = messages.map(msg => `
                <tr>
                    <td>${new Date(msg.created_at).toLocaleString('fr-FR')}</td>
                    <td>${msg.client_email}</td>
                    <td>${msg.subject}</td>
                    <td><span class="badge bg-success">${msg.status}</span></td>
                    <td><button class="btn btn-primary btn-sm">Voir</button></td>
                </tr>
            `).join('');
        }
        
        function updateClientsTable(clients) {
            const tbody = document.getElementById('clients-tbody');
            tbody.innerHTML = clients.map(client => `
                <tr>
                    <td>${client.nom || ''}</td>
                    <td>${client.prenom || ''}</td>
                    <td>${client.email}</td>
                    <td><span class="badge bg-secondary">${client.type}</span></td>
                    <td>${client.entreprise || 'N/A'}</td>
                </tr>
            `).join('');
        }
        
        function getStatutBadge(statut) {
            const badges = {
                'en_attente': '<span class="badge bg-warning">En Attente</span>',
                'confirmee': '<span class="badge bg-info">Confirmée</span>',
                'expediee': '<span class="badge bg-primary">Expédiée</span>',
                'livree': '<span class="badge bg-success">Livrée</span>',
                'annulee': '<span class="badge bg-danger">Annulée</span>'
            };
            return badges[statut] || '<span class="badge bg-secondary">Inconnu</span>';
        }
        
        async function updateOrderStatus(commandeId, nouveauStatut) {
            try {
                const response = await fetch('/api/update-order-status', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({commande_id: commandeId, statut: nouveauStatut})
                });
                
                if (response.ok) {
                    loadDashboardData(); // Rafraîchir les données
                }
            } catch (error) {
                console.error('Erreur mise à jour statut:', error);
            }
        }
        
        function ajouterProduit() {
            const container = document.getElementById('produits-commande');
            const index = container.children.length;
            
            const produitHtml = `
                <div class="row mb-3 produit-item">
                    <div class="col-md-6">
                        <select class="form-control" name="produit_${index}" required>
                            <option value="">Sélectionner un produit</option>
                            ${produitsDisponibles.map(p => 
                                `<option value="${p.id}" data-prix="${p.prix}">${p.nom} - ${p.prix}€</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <input type="number" class="form-control" name="quantite_${index}" placeholder="Quantité" min="1" value="1" required>
                    </div>
                    <div class="col-md-3">
                        <button type="button" class="btn btn-danger" onclick="this.closest('.produit-item').remove()">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            
            container.insertAdjacentHTML('beforeend', produitHtml);
        }
        
        // Gestionnaire formulaire nouvelle commande
        document.getElementById('nouvelle-commande-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('client-email').value;
            const nom = document.getElementById('client-nom').value;
            const prenom = document.getElementById('client-prenom').value;
            const adresse = document.getElementById('adresse-livraison').value;
            
            // Récupérer les produits sélectionnés
            const produits = [];
            const produitsItems = document.querySelectorAll('.produit-item');
            
            produitsItems.forEach((item, index) => {
                const select = item.querySelector(`select[name="produit_${index}"]`);
                const quantiteInput = item.querySelector(`input[name="quantite_${index}"]`);
                
                if (select.value && quantiteInput.value) {
                    const option = select.selectedOptions[0];
                    produits.push({
                        id: parseInt(select.value),
                        nom: option.text.split(' - ')[0],
                        prix: parseFloat(option.dataset.prix),
                        quantite: parseInt(quantiteInput.value)
                    });
                }
            });
            
            if (produits.length === 0) {
                alert('Veuillez ajouter au moins un produit à la commande');
                return;
            }
            
            try {
                const response = await fetch('/api/create-order', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        client_email: email,
                        client_nom: nom,
                        client_prenom: prenom,
                        adresse: adresse,
                        produits: produits
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`Commande créée avec succès ! ID: ${result.commande_id}`);
                    document.getElementById('nouvelle-commande-form').reset();
                    document.getElementById('produits-commande').innerHTML = '';
                    loadDashboardData();
                    loadProduits();
                    
                    // Retourner à l'onglet commandes
                    document.getElementById('commandes-tab').click();
                } else {
                    alert('Erreur lors de la création de la commande: ' + result.error);
                }
            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur lors de la création de la commande');
            }
        });
    </script>
</body>
</html>
'''
    return render_template_string(template)

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API pour récupérer les données du dashboard"""
    return jsonify(admin_manager.get_dashboard_data())

@app.route('/api/produits')
def get_produits():
    """API pour récupérer tous les produits"""
    try:
        conn = sqlite3.connect(admin_manager.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM produits ORDER BY nom")
        produits = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(produits)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages')
def get_messages():
    """API pour récupérer tous les messages"""
    try:
        messages = admin_manager.get_messages_by_status() # Récupère tous les messages
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients')
def get_clients():
    """API pour récupérer tous les clients"""
    try:
        clients = admin_manager.get_all_clients()
        return jsonify(clients)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-order', methods=['POST'])
def create_order():
    """API pour créer une nouvelle commande"""
    try:
        data = request.json
        
        commande_id = admin_manager.create_order(
            client_email=data['client_email'],
            client_nom=data.get('client_nom', ''),
            client_prenom=data.get('client_prenom', ''),
            produits=data.get('produits', []),
            adresse=data.get('adresse', '')
        )
        
        if commande_id:
            return jsonify({'success': True, 'commande_id': commande_id})
        else:
            return jsonify({'success': False, 'error': 'Erreur création commande'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-order-status', methods=['POST'])
def update_order_status():
    """API pour mettre à jour le statut d'une commande"""
    try:
        data = request.json
        success = admin_manager.update_order_status(
            data['commande_id'], 
            data['statut']
        )
        
        return jsonify({'success': success})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Démarrage Interface Admin Dynamique...")
    print("📊 Dashboard disponible sur: http://localhost:5001")
    print("⚡ Rafraîchissement automatique toutes les 5 secondes")
    print("🎯 Gestion complète des commandes et produits")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    ) 
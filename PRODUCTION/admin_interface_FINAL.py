#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Administrateur Améliorée - Monitoring Avancé Support Client
Affichage des emails clients et suivi des messages par statut
"""

import sys
import os
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
import sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from automation.claude_agent import ClaudeAgent

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin-support-monitoring-advanced-2024'

class AdvancedSupportMonitoring:
    def __init__(self):
        self.db_path = 'data/crm_ecommerce.db'
        self.init_advanced_db()
        self.db_manager = DatabaseManager()
        self.claude_agent = ClaudeAgent(db_manager=self.db_manager)
    
    def init_advanced_db(self):
        """Initialise la base de données avancée avec tables de messages"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table messages avec statuts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_email TEXT NOT NULL,
                    client_name TEXT,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT DEFAULT 'nouveau' CHECK (status IN ('nouveau', 'en_cours', 'traite', 'ferme')),
                    category TEXT,
                    urgency INTEGER DEFAULT 1 CHECK (urgency BETWEEN 1 AND 5),
                    sentiment TEXT,
                    response TEXT,
                    response_time REAL DEFAULT 0,
                    quality_score REAL DEFAULT 0,
                    ticket_id TEXT UNIQUE,
                    model_used TEXT DEFAULT 'claude-4-sonnet',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed_at DATETIME,
                    assigned_to TEXT DEFAULT 'IA Agent'
                )
            ''')
            
            # Table comptes entreprise
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enterprise_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    poste TEXT,
                    departement TEXT,
                    entreprise TEXT,
                    type_client TEXT DEFAULT 'entreprise',
                    is_active INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_message_at DATETIME
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Base de données avancée initialisée")
            
        except Exception as e:
            print(f"❌ Erreur initialisation BD avancée: {e}")
    
    def create_message(self, client_email: str, subject: str, message: str, client_name: str = None):
        """Crée un nouveau message avec statut"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Générer ticket_id unique
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ticket_id = f"MSG-{timestamp}-{len(message) % 1000:03d}"
            
            cursor.execute('''
                INSERT INTO messages (
                    client_email, client_name, subject, message, status, ticket_id
                ) VALUES (?, ?, ?, ?, 'nouveau', ?)
            ''', (client_email, client_name, subject, message, ticket_id))
            
            message_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return message_id
            
        except Exception as e:
            print(f"❌ Erreur création message: {e}")
            return None
    
    def update_message_status(self, message_id: int, new_status: str):
        """Met à jour le statut d'un message"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE messages 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, message_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour statut: {e}")
            return False
    
    def complete_message_processing(self, message_id: int, analysis_result: dict):
        """Complète le traitement d'un message"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE messages SET
                    status = 'traite',
                    category = ?,
                    urgency = ?,
                    sentiment = ?,
                    response = ?,
                    response_time = ?,
                    quality_score = ?,
                    model_used = ?,
                    processed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                analysis_result.get('category'),
                analysis_result.get('urgency'),
                analysis_result.get('sentiment'),
                analysis_result.get('response'),
                analysis_result.get('response_time', 0),
                analysis_result.get('quality_score', 0),
                analysis_result.get('model', 'claude-4-sonnet'),
                message_id
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Erreur finalisation: {e}")
            return False
    
    def get_all_clients(self):
        """Récupère tous les clients avec informations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            clients = []
            
            # Clients standards
            try:
                cursor.execute('SELECT nom, prenom, email, "standard" as type, "" as entreprise FROM client ORDER BY nom, prenom')
                clients.extend([dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()])
            except:
                pass
            
            # Comptes entreprise
            try:
                cursor.execute('''
                    SELECT nom, prenom, email, type_client as type, entreprise 
                    FROM enterprise_accounts 
                    WHERE is_active = 1 
                    ORDER BY entreprise, nom, prenom
                ''')
                enterprise_clients = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
                clients.extend(enterprise_clients)
            except:
                pass
            
            conn.close()
            return clients
            
        except Exception as e:
            print(f"❌ Erreur récupération clients: {e}")
            return []
    
    def get_messages_by_status(self, status=None):
        """Récupère les messages par statut"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM messages 
                    WHERE status = ? 
                    ORDER BY created_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT * FROM messages 
                    ORDER BY created_at DESC
                ''')
            
            messages = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            conn.close()
            return messages
            
        except Exception as e:
            print(f"❌ Erreur récupération messages: {e}")
            return []
    
    def get_dashboard_data(self):
        """Récupère les données complètes pour le dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Statistiques par statut
            try:
                cursor.execute('SELECT status, COUNT(*) FROM messages GROUP BY status')
                status_stats = dict(cursor.fetchall())
            except:
                status_stats = {}
            
            # Messages récents
            recent_messages = self.get_messages_by_status()[:20]
            
            # Clients
            all_clients = self.get_all_clients()
            
            # Statistiques générales
            try:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_today,
                        AVG(response_time) as avg_response_time,
                        AVG(quality_score) as avg_quality
                    FROM messages 
                    WHERE DATE(created_at) = DATE('now')
                ''')
                today_stats = dict(zip([col[0] for col in cursor.description], cursor.fetchone() or [0, 0, 0]))
            except:
                today_stats = {'total_today': 0, 'avg_response_time': 0, 'avg_quality': 0}
            
            conn.close()
            
            return {
                'status_counts': status_stats,
                'recent_messages': recent_messages,
                'all_clients': all_clients,
                'today_stats': today_stats,
                'claude_status': self.claude_agent.get_status(),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur dashboard: {e}")
            return {'error': str(e)}

# Instance globale
support_monitor = AdvancedSupportMonitoring()

@app.route('/')
def dashboard():
    """Dashboard principal amélioré"""
    template = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard Avancé - Support Client</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .stat-card { transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-5px); }
        .status-badge { font-size: 0.75rem; }
        .message-card { transition: all 0.2s; }
        .message-card:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .status-nouveau { border-left: 4px solid #dc3545; }
        .status-en_cours { border-left: 4px solid #ffc107; }
        .status-traite { border-left: 4px solid #28a745; }
        .status-ferme { border-left: 4px solid #6c757d; }
        .client-list { max-height: 400px; overflow-y: auto; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-shield-check"></i> Dashboard Admin - Support Client Avancé
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text">
                    <i class="bi bi-person-circle"></i> Administrateur
                </span>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Statistiques principales -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white stat-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>Messages Nouveaux</h6>
                                <h3 id="nouveaux-count">0</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="bi bi-envelope-exclamation" style="font-size: 2rem;"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white stat-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>En Cours</h6>
                                <h3 id="en-cours-count">0</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="bi bi-clock-history" style="font-size: 2rem;"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white stat-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>Traités</h6>
                                <h3 id="traites-count">0</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="bi bi-check-circle" style="font-size: 2rem;"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white stat-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>Clients Actifs</h6>
                                <h3 id="clients-count">0</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="bi bi-people" style="font-size: 2rem;"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Messages par statut -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="card-title mb-0"><i class="bi bi-chat-dots"></i> Messages Récents</h5>
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-sm btn-outline-primary" onclick="filterMessages('all')">Tous</button>
                            <button type="button" class="btn btn-sm btn-outline-danger" onclick="filterMessages('nouveau')">Nouveaux</button>
                            <button type="button" class="btn btn-sm btn-outline-warning" onclick="filterMessages('en_cours')">En cours</button>
                            <button type="button" class="btn btn-sm btn-outline-success" onclick="filterMessages('traite')">Traités</button>
                        </div>
                    </div>
                    <div class="card-body" style="max-height: 600px; overflow-y: auto;">
                        <div id="messages-container">
                            <!-- Messages seront chargés ici -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- Liste des clients -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0"><i class="bi bi-person-lines-fill"></i> Clients Enregistrés</h5>
                    </div>
                    <div class="card-body client-list">
                        <div id="clients-container">
                            <!-- Clients seront chargés ici -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Performance IA -->
        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0"><i class="bi bi-cpu"></i> Performance IA</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <div class="text-center">
                                    <h4 id="quality-score">0.00</h4>
                                    <small class="text-muted">Score Qualité Moyen</small>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center">
                                    <h4 id="response-time">0.0s</h4>
                                    <small class="text-muted">Temps Réponse Moyen</small>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center">
                                    <h4 id="claude-status">❌</h4>
                                    <small class="text-muted">Claude 4 Statut</small>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center">
                                    <h4 id="today-messages">0</h4>
                                    <small class="text-muted">Messages Aujourd'hui</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentFilter = 'all';
        
        function loadDashboardData() {
            fetch('/api/dashboard-data-advanced')
                .then(response => response.json())
                .then(data => {
                    updateStats(data);
                    updateMessages(data.recent_messages);
                    updateClients(data.all_clients);
                    updatePerformance(data);
                })
                .catch(error => console.error('Erreur:', error));
        }
        
        function updateStats(data) {
            const statusCounts = data.status_counts || {};
            document.getElementById('nouveaux-count').textContent = statusCounts.nouveau || 0;
            document.getElementById('en-cours-count').textContent = statusCounts.en_cours || 0;
            document.getElementById('traites-count').textContent = statusCounts.traite || 0;
            document.getElementById('clients-count').textContent = data.all_clients ? data.all_clients.length : 0;
        }
        
        function updateMessages(messages) {
            const container = document.getElementById('messages-container');
            
            let filteredMessages = messages;
            if (currentFilter !== 'all') {
                filteredMessages = messages.filter(msg => msg.status === currentFilter);
            }
            
            if (filteredMessages.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">Aucun message à afficher</p>';
                return;
            }
            
            container.innerHTML = filteredMessages.map(msg => `
                <div class="message-card card mb-2 status-${msg.status}">
                    <div class="card-body p-3">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="card-title mb-1">${msg.subject || 'Sans sujet'}</h6>
                                <p class="card-text text-muted mb-1">${msg.client_email}</p>
                                <p class="card-text small">${(msg.message || '').substring(0, 100)}...</p>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-${getStatusColor(msg.status)} status-badge">${getStatusText(msg.status)}</span>
                                <small class="d-block text-muted mt-1">${formatDate(msg.created_at)}</small>
                                ${msg.urgency ? `<small class="d-block text-warning">Urgence: ${msg.urgency}/5</small>` : ''}
                            </div>
                        </div>
                        ${msg.response ? `<div class="mt-2 p-2 bg-light rounded"><small><strong>Réponse:</strong> ${msg.response.substring(0, 100)}...</small></div>` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        function updateClients(clients) {
            const container = document.getElementById('clients-container');
            
            if (!clients || clients.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">Aucun client enregistré</p>';
                return;
            }
            
            container.innerHTML = clients.map(client => `
                <div class="d-flex justify-content-between align-items-center p-2 border-bottom">
                    <div>
                        <strong>${client.prenom} ${client.nom}</strong>
                        <br><small class="text-muted">${client.email}</small>
                        ${client.entreprise ? `<br><small class="text-info">${client.entreprise}</small>` : ''}
                    </div>
                    <span class="badge bg-${getClientTypeColor(client.type)}">${client.type}</span>
                </div>
            `).join('');
        }
        
        function updatePerformance(data) {
            const todayStats = data.today_stats || {};
            const claudeStatus = data.claude_status || {};
            
            document.getElementById('quality-score').textContent = (todayStats.avg_quality || 0).toFixed(2);
            document.getElementById('response-time').textContent = (todayStats.avg_response_time || 0).toFixed(1) + 's';
            document.getElementById('claude-status').textContent = claudeStatus.claude_ready ? '✅' : '❌';
            document.getElementById('today-messages').textContent = todayStats.total_today || 0;
        }
        
        function filterMessages(status) {
            currentFilter = status;
            loadDashboardData(); // Recharger avec le nouveau filtre
        }
        
        function getStatusColor(status) {
            const colors = {
                'nouveau': 'danger',
                'en_cours': 'warning',
                'traite': 'success',
                'ferme': 'secondary'
            };
            return colors[status] || 'secondary';
        }
        
        function getStatusText(status) {
            const texts = {
                'nouveau': 'Nouveau',
                'en_cours': 'En cours',
                'traite': 'Traité',
                'ferme': 'Fermé'
            };
            return texts[status] || status;
        }
        
        function getClientTypeColor(type) {
            const colors = {
                'entreprise': 'primary',
                'vip': 'warning',
                'particulier': 'info',
                'standard': 'secondary'
            };
            return colors[type] || 'secondary';
        }
        
        function formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR') + ' ' + date.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
        }
        
        // Charger les données au démarrage
        loadDashboardData();
        
        // Actualiser toutes les 15 secondes
        setInterval(loadDashboardData, 15000);
    </script>
</body>
</html>
'''
    return template

@app.route('/api/dashboard-data-advanced')
def get_advanced_dashboard_data():
    """API pour récupérer les données avancées du dashboard"""
    return jsonify(support_monitor.get_dashboard_data())

@app.route('/api/messages/<status>')
def get_messages_by_status(status):
    """API pour récupérer les messages par statut"""
    if status == 'all':
        status = None
    messages = support_monitor.get_messages_by_status(status)
    return jsonify(messages)

@app.route('/api/clients')
def get_all_clients():
    """API pour récupérer tous les clients"""
    clients = support_monitor.get_all_clients()
    return jsonify(clients)

if __name__ == '__main__':
    print("🔧 INTERFACE ADMINISTRATEUR AMÉLIORÉE")
    print("=====================================")
    print("🌐 Dashboard: http://localhost:5001")
    print("📊 Clients et Messages en temps réel")
    print("=====================================")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 
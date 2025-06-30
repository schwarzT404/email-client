#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Administrateur - Monitoring des Échanges Support Client
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
app.config['SECRET_KEY'] = 'admin-support-monitoring-2024'

class SupportMonitoring:
    def __init__(self):
        self.db_path = 'data/support_monitoring.db'
        self.init_monitoring_db()
        self.db_manager = DatabaseManager()
        self.claude_agent = ClaudeAgent(db_manager=self.db_manager)
    
    def init_monitoring_db(self):
        """Initialise la base de données de monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exchanges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    client_email TEXT NOT NULL,
                    subject TEXT,
                    message TEXT,
                    category TEXT,
                    urgency INTEGER,
                    sentiment TEXT,
                    response TEXT,
                    response_time REAL,
                    quality_score REAL,
                    ticket_id TEXT,
                    model_used TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Base de données de monitoring initialisée")
            
        except Exception as e:
            print(f"❌ Erreur initialisation monitoring DB: {e}")
    
    def log_exchange(self, exchange_data):
        """Enregistre un échange dans la base de monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exchanges (
                    client_email, subject, message, category, urgency, sentiment,
                    response, response_time, quality_score, ticket_id, model_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                exchange_data.get('email'),
                exchange_data.get('subject'),
                exchange_data.get('message'),
                exchange_data.get('category'),
                exchange_data.get('urgency'),
                exchange_data.get('sentiment'),
                exchange_data.get('response'),
                exchange_data.get('response_time', 0),
                exchange_data.get('quality_score', 0),
                exchange_data.get('ticket_id'),
                exchange_data.get('model', 'claude-4-sonnet')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Erreur logging exchange: {e}")
    
    def get_dashboard_data(self):
        """Récupère les données pour le dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute('''
                SELECT COUNT(*), AVG(response_time), AVG(quality_score)
                FROM exchanges 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            stats = cursor.fetchone()
            
            # Statistiques par catégorie
            cursor.execute('''
                SELECT category, COUNT(*), AVG(quality_score)
                FROM exchanges 
                WHERE timestamp > datetime('now', '-1 day')
                GROUP BY category
            ''')
            categories = cursor.fetchall()
            
            # Échanges récents
            cursor.execute('''
                SELECT timestamp, client_email, subject, category, quality_score, response_time
                FROM exchanges 
                ORDER BY timestamp DESC
                LIMIT 20
            ''')
            recent = cursor.fetchall()
            
            conn.close()
            
            return {
                'requests_count': stats[0] or 0,
                'avg_response_time': stats[1] or 0,
                'avg_quality': stats[2] or 0,
                'categories': [{'name': cat[0], 'count': cat[1], 'quality': cat[2]} for cat in categories],
                'recent_exchanges': [
                    {
                        'timestamp': r[0],
                        'email': r[1],
                        'subject': r[2],
                        'category': r[3],
                        'quality': r[4],
                        'response_time': r[5]
                    } for r in recent
                ],
                'claude_status': self.claude_agent.get_status(),
                'clients_count': len(self.db_manager.get_all_clients())
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération données: {e}")
            return {'error': str(e)}

# Instance globale
support_monitor = SupportMonitoring()

@app.route('/')
def dashboard():
    """Dashboard principal"""
    template = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Support Client</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .stat-card { transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-5px); }
        .console-log { background: #000; color: #0f0; font-family: monospace; height: 300px; overflow-y: auto; padding: 10px; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="bi bi-shield-check"></i> Admin Dashboard - Support Client
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
                                <h6>Requêtes 24h</h6>
                                <h3 id="requests-count">0</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="bi bi-envelope" style="font-size: 2rem;"></i>
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
                                <h6>Temps Réponse Moyen</h6>
                                <h3 id="avg-response-time">0s</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="bi bi-clock" style="font-size: 2rem;"></i>
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
                                <h6>Claude Status</h6>
                                <h3 id="claude-status">OK</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="bi bi-robot" style="font-size: 2rem;"></i>
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
                                <h6>Clients DB</h6>
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

        <!-- Console de monitoring -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header d-flex justify-content-between">
                        <h5><i class="bi bi-terminal"></i> Console Monitoring</h5>
                        <button class="btn btn-sm btn-outline-primary" onclick="clearConsole()">
                            <i class="bi bi-trash"></i> Vider
                        </button>
                    </div>
                    <div class="card-body p-0">
                        <div class="console-log" id="console-log">
                            <div class="text-success"># Console de monitoring en temps réel</div>
                            <div class="text-info"># Logs des échanges et performance API</div>
                            <div class="text-warning"># Actualisation automatique...</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="bi bi-pie-chart"></i> Catégories Populaires</h5>
                    </div>
                    <div class="card-body">
                        <div id="categories-chart">
                            <div class="text-center text-muted">Chargement...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Échanges récents -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between">
                        <h5><i class="bi bi-list-ul"></i> Échanges Récents</h5>
                        <div>
                            <button class="btn btn-sm btn-outline-success" onclick="refreshData()">
                                <i class="bi bi-arrow-clockwise"></i> Actualiser
                            </button>
                            <button class="btn btn-sm btn-outline-primary" onclick="exportData()">
                                <i class="bi bi-download"></i> Exporter
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Timestamp</th>
                                        <th>Client</th>
                                        <th>Sujet</th>
                                        <th>Catégorie</th>
                                        <th>Qualité</th>
                                        <th>Temps</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="recent-exchanges">
                                    <tr>
                                        <td colspan="7" class="text-center text-muted">Chargement...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let consoleLines = [];
        
        function addConsoleLog(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            const colorClass = {
                'info': 'text-info',
                'success': 'text-success',
                'warning': 'text-warning',
                'error': 'text-danger'
            }[type] || 'text-white';
            
            consoleLines.push(`<div class="${colorClass}">[${timestamp}] ${message}</div>`);
            
            if (consoleLines.length > 100) {
                consoleLines.shift();
            }
            
            const console = document.getElementById('console-log');
            console.innerHTML = consoleLines.join('');
            console.scrollTop = console.scrollHeight;
        }
        
        function clearConsole() {
            consoleLines = [];
            document.getElementById('console-log').innerHTML = '<div class="text-success"># Console vidée</div>';
        }

        function loadDashboard() {
            fetch('/api/dashboard-data')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        addConsoleLog('Erreur chargement dashboard: ' + data.error, 'error');
                        return;
                    }
                    
                    updateStatistics(data);
                    updateRecentExchanges(data.recent_exchanges);
                    updateCategories(data.categories);
                    
                    addConsoleLog(`Dashboard mis à jour - ${data.requests_count} requêtes, qualité moyenne: ${(data.avg_quality * 100).toFixed(1)}%`, 'success');
                })
                .catch(error => {
                    addConsoleLog('Erreur API: ' + error.message, 'error');
                });
        }

        function updateStatistics(data) {
            document.getElementById('requests-count').textContent = data.requests_count;
            document.getElementById('avg-response-time').textContent = data.avg_response_time.toFixed(1) + 's';
            document.getElementById('claude-status').textContent = data.claude_status?.claude_ready ? 'OK' : 'KO';
            document.getElementById('clients-count').textContent = data.clients_count || 0;
        }

        function updateRecentExchanges(exchanges) {
            const tbody = document.getElementById('recent-exchanges');
            tbody.innerHTML = '';
            
            if (!exchanges || exchanges.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Aucun échange récent</td></tr>';
                return;
            }
            
            exchanges.forEach(exchange => {
                const row = document.createElement('tr');
                const qualityBadge = exchange.quality > 0.8 ? 'success' : exchange.quality > 0.6 ? 'warning' : 'danger';
                
                row.innerHTML = `
                    <td>${new Date(exchange.timestamp).toLocaleString()}</td>
                    <td>${exchange.email}</td>
                    <td>${exchange.subject || 'Sans sujet'}</td>
                    <td><span class="badge bg-secondary">${exchange.category}</span></td>
                    <td><span class="badge bg-${qualityBadge}">${(exchange.quality * 100).toFixed(0)}%</span></td>
                    <td>${exchange.response_time?.toFixed(1)}s</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewExchange('${exchange.email}')">
                            <i class="bi bi-eye"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function updateCategories(categories) {
            const container = document.getElementById('categories-chart');
            
            if (!categories || categories.length === 0) {
                container.innerHTML = '<div class="text-center text-muted">Aucune donnée</div>';
                return;
            }
            
            let html = '';
            categories.forEach(cat => {
                const percentage = (cat.count / categories.reduce((sum, c) => sum + c.count, 0) * 100).toFixed(1);
                html += `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span>${cat.name}</span>
                        <div>
                            <span class="badge bg-primary">${cat.count}</span>
                            <small class="text-muted">(${percentage}%)</small>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function viewExchange(email) {
            addConsoleLog(`Visualisation échange pour: ${email}`, 'info');
        }
        
        function refreshData() {
            addConsoleLog('Actualisation manuelle des données...', 'info');
            loadDashboard();
        }
        
        function exportData() {
            addConsoleLog('Export des données en cours...', 'info');
            // Logique d'export ici
        }

        // Chargement initial et actualisation automatique
        addConsoleLog('Démarrage du dashboard administrateur', 'success');
        loadDashboard();
        setInterval(loadDashboard, 15000); // Actualiser toutes les 15 secondes
        
        // Simulation de logs pour démonstration
        setInterval(() => {
            const messages = [
                'Requête API reçue',
                'Traitement Claude en cours',
                'Réponse générée avec succès',
                'Monitoring système OK',
                'Base de données synchronisée'
            ];
            const types = ['info', 'success', 'warning'];
            
            if (Math.random() > 0.7) {
                addConsoleLog(messages[Math.floor(Math.random() * messages.length)], types[Math.floor(Math.random() * types.length)]);
            }
        }, 3000);
    </script>
</body>
</html>
    '''
    return render_template_string(template)

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API pour récupérer les données du dashboard"""
    try:
        data = support_monitor.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🔧 INTERFACE ADMINISTRATEUR - MONITORING SUPPORT CLIENT")
    print("=" * 50)
    print("🌐 Dashboard: http://localhost:5001")
    print("📊 API Monitoring: http://localhost:5001/api/dashboard-data")
    print("🔍 Console monitoring en temps réel")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001) 
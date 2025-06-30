#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Web Moderne - Support Client E-commerce
Interface web avec Flask, Bootstrap 5 et API REST
"""

from flask import Flask, render_template, request, jsonify, session
import sys
import os
from datetime import datetime
import threading
import json
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Flask
app = Flask(__name__)
app.secret_key = 'support_client_secret_key_2025'

# Variables globales pour l'état du système
system_status = {
    'db_connected': False,
    'notion_connected': False,
    'agent_ready': False,
    'last_update': datetime.now()
}

# Modules du système
db_manager = None
notion_manager = None
support_agent = None
claude_agent = None

def init_messages_table():
    """Initialise la table des messages avec statuts"""
    try:
        import sqlite3
        conn = sqlite3.connect('data/crm_ecommerce.db')
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
                urgency INTEGER DEFAULT 1,
                sentiment TEXT,
                response TEXT,
                response_time REAL DEFAULT 0,
                quality_score REAL DEFAULT 0,
                ticket_id TEXT UNIQUE,
                model_used TEXT DEFAULT 'claude-4-sonnet',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Table messages initialisée")
    except Exception as e:
        print(f"❌ Erreur init messages: {e}")

def create_message_record(email, subject, message, client_name=None):
    """Crée un enregistrement de message"""
    try:
        import sqlite3
        conn = sqlite3.connect('data/crm_ecommerce.db')
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        ticket_id = f"MSG-{timestamp}-{len(message) % 1000:03d}"
        
        cursor.execute('''
            INSERT INTO messages (client_email, client_name, subject, message, status, ticket_id)
            VALUES (?, ?, ?, ?, 'nouveau', ?)
        ''', (email, client_name, subject, message, ticket_id))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return message_id, ticket_id
    except Exception as e:
        print(f"❌ Erreur création message: {e}")
        return None, None

def update_message_processing(message_id, result, processing_time):
    """Met à jour le message avec les résultats du traitement"""
    try:
        import sqlite3
        conn = sqlite3.connect('data/crm_ecommerce.db')
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
            result.get('category'),
            result.get('urgency'),
            result.get('sentiment'),
            result.get('response'),
            processing_time,
            result.get('quality_score', 0),
            result.get('model', 'claude-4-sonnet'),
            message_id
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur mise à jour message: {e}")
        return False

def initialize_system():
    """Initialise les modules du système"""
    global db_manager, notion_manager, support_agent, claude_agent, system_status
    
    try:
        from database.db_manager import DatabaseManager
        from notion.notion_manager import NotionManager
        from automation.claude_agent import ClaudeAgent
        
        # Initialiser les modules de base
        db_manager = DatabaseManager()
        notion_manager = NotionManager()
        
        # Initialiser l'agent Claude avec accès à la base de données
        claude_agent = ClaudeAgent(db_manager=db_manager)
        
        # Initialiser la table des messages
        init_messages_table()
        
        # Fallback sur l'ancien support agent si nécessaire
        try:
            from automation.support_agent import SupportAgent
            support_agent = SupportAgent(db_manager, notion_manager)
        except ImportError:
            support_agent = None
        
        # Mettre à jour le statut
        claude_status = claude_agent.get_status() if claude_agent else {}
        
        system_status.update({
            'db_connected': True,
            'notion_connected': True,
            'agent_ready': True,
            'claude_available': claude_status.get('claude_available', False),
            'claude_ready': claude_status.get('claude_ready', False),
            'api_key_configured': claude_status.get('api_key_configured', False),
            'model': claude_status.get('model', 'simulation'),
            'last_update': datetime.now()
        })
        
        print("✅ Système initialisé avec Agent Claude")
        return True
        
    except Exception as e:
        print(f"Erreur d'initialisation: {e}")
        system_status.update({
            'db_connected': False,
            'notion_connected': False,
            'agent_ready': False,
            'claude_available': False,
            'claude_ready': False,
            'last_update': datetime.now(),
            'error': str(e)
        })
        return False

# Initialisation au démarrage
initialize_system()

@app.route('/')
def index():
    """Page d'accueil principale"""
    return render_template('index.html', system_status=system_status)

@app.route('/api/status')
def api_status():
    """API pour obtenir le statut du système"""
    return jsonify(system_status)

@app.route('/api/process-message', methods=['POST'])
def api_process_message():
    """API pour traiter un message client"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        # Validation
        if not email or not message:
            return jsonify({
                'success': False,
                'error': 'Email et message requis'
            }), 400
        
        if '@' not in email:
            return jsonify({
                'success': False,
                'error': 'Format d\'email invalide'
            }), 400
        
        # Vérifier si l'utilisateur est enregistré dans la base de données
        print(f"🔍 DEBUG AUTH: db_manager={db_manager is not None}, db_connected={system_status.get('db_connected', False)}")
        
        if db_manager and system_status.get('db_connected', False):
            client_info = db_manager.get_client_by_email(email)
            print(f"🔍 DEBUG AUTH: Email {email} -> client_info={client_info}")
            
            if not client_info:
                print(f"🚫 DEBUG AUTH: Accès refusé pour {email}")
                return jsonify({
                    'success': False,
                    'error': 'Accès refusé. Vous devez être inscrit pour utiliser ce service.',
                    'requires_registration': True
                }), 403
            else:
                print(f"✅ DEBUG AUTH: Accès autorisé pour {email}")
        else:
            print(f"🚫 DEBUG AUTH: Base de données indisponible (db_manager={db_manager is not None}, connected={system_status.get('db_connected', False)})")
            return jsonify({
                'success': False,
                'error': 'Base de données indisponible'
            }), 500
        
        # Créer l'enregistrement du message avec statut "nouveau"
        client_name = f"{client_info.get('prenom', '')} {client_info.get('nom', '')}" if client_info else None
        message_id, ticket_id = create_message_record(email, subject, message, client_name)
        
        if not message_id:
            return jsonify({
                'success': False,
                'error': 'Erreur enregistrement message'
            }), 500
        
        print(f"📧 Message enregistré: ID {message_id}, Ticket {ticket_id}")
        
        # Simuler un délai de traitement (10-30 secondes)
        import random
        import time
        processing_delay = random.randint(10, 30)
        
        # Traitement du message - Priorité à Claude
        if claude_agent and system_status.get('claude_ready', False):
            # Ajouter le délai de traitement
            time.sleep(processing_delay)
            
            # Traitement avec Claude (priorité)
            result = claude_agent.process_customer_message(email, message, subject)
            
            # Mettre à jour l'enregistrement du message
            update_message_processing(message_id, result, processing_delay)
            
            # Ajouter le ticket_id au résultat
            result['ticket_id'] = ticket_id
            result['message_id'] = message_id
            
            # Log pour le monitoring administrateur en console
            try:
                print(f"📊 [MONITORING] Échange traité:")
                print(f"   📧 Email: {email}")
                print(f"   🏷️  Catégorie: {result.get('category', 'N/A')}")
                print(f"   🎯 Urgence: {result.get('urgency', 'N/A')}/5")
                print(f"   😊 Sentiment: {result.get('sentiment', 'N/A')}")
                print(f"   📊 Qualité: {result.get('quality_score', 0):.2f}")
                print(f"   ⏱️  Temps total: {processing_delay:.1f}s")
                print(f"   🎫 Ticket: {ticket_id}")
                print("=" * 50)
            except Exception as log_error:
                print(f"⚠️ Erreur logging monitoring: {log_error}")
            
            return jsonify({
                'success': True,
                'result': result,
                'processed_at': datetime.now().isoformat(),
                'processing_delay': processing_delay,
                'mode': 'claude-ai',
                'ai_model': 'claude-4-sonnet'
            })
        elif support_agent and system_status['agent_ready']:
            # Ajouter le délai de traitement
            time.sleep(processing_delay)
            
            # Traitement avec l'ancien agent
            result = support_agent.process_customer_message(email, message, subject)
            
            return jsonify({
                'success': True,
                'result': result,
                'processed_at': datetime.now().isoformat(),
                'processing_delay': processing_delay,
                'mode': 'legacy-ai'
            })
        else:
            # Ajouter le délai de traitement même en simulation
            time.sleep(processing_delay)
            
            # Mode simulation
            category = classify_message_simple(message)
            response = generate_response_simple(email, category, message)
            
            return jsonify({
                'success': True,
                'result': {
                    'email': email,
                    'category': category,
                    'response': response,
                    'quality_score': 0.85,
                    'ticket_id': f'SIM-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    'mode': 'simulation'
                },
                'processed_at': datetime.now().isoformat(),
                'processing_delay': processing_delay,
                'mode': 'simulation'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistics')
def api_statistics():
    """API pour obtenir les statistiques"""
    try:
        if db_manager and system_status['db_connected']:
            stats = db_manager.get_stats()
            return jsonify({
                'success': True,
                'stats': stats,
                'retrieved_at': datetime.now().isoformat()
            })
        else:
            # Statistiques simulées
            return jsonify({
                'success': True,
                'stats': {
                    'nb_clients': 3,
                    'nb_commandes': 6,
                    'ca_total': 389.96,
                    'panier_moyen': 64.99,
                    'top_clients': [
                        {'nom': 'Martin', 'prenom': 'Marie', 'nb_commandes': 2},
                        {'nom': 'Dupont', 'prenom': 'Jean', 'nb_commandes': 2},
                        {'nom': 'Durand', 'prenom': 'Pierre', 'nb_commandes': 2}
                    ]
                },
                'retrieved_at': datetime.now().isoformat(),
                'mode': 'simulation'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    """API pour inscription d'un nouveau client"""
    try:
        data = request.get_json()
        
        nom = data.get('nom', '').strip()
        prenom = data.get('prenom', '').strip()
        email = data.get('email', '').strip()
        
        # Validation
        if not nom or not prenom or not email:
            return jsonify({
                'success': False,
                'error': 'Nom, prénom et email requis'
            }), 400
        
        if '@' not in email:
            return jsonify({
                'success': False,
                'error': 'Format d\'email invalide'
            }), 400
        
        # Vérifier si la base de données est disponible
        if not db_manager or not system_status.get('db_connected', False):
            return jsonify({
                'success': False,
                'error': 'Base de données indisponible'
            }), 500
        
        # Vérifier si l'email existe déjà
        existing_client = db_manager.get_client_by_email(email)
        if existing_client:
            return jsonify({
                'success': False,
                'error': 'Un compte avec cet email existe déjà'
            }), 409
        
        # Créer le nouveau client
        print(f"🔧 DEBUG INSCRIPTION: Création client {prenom} {nom} ({email})")
        try:
            client_id = db_manager.create_client(nom, prenom, email, type_client="standard")
            print(f"🔧 DEBUG INSCRIPTION: client_id retourné = {client_id}")
            
            if client_id:
                print(f"✅ DEBUG INSCRIPTION: Succès client_id={client_id}")
                return jsonify({
                    'success': True,
                    'message': 'Inscription réussie ! Vous pouvez maintenant utiliser le service.',
                    'client_id': client_id,
                    'registered_at': datetime.now().isoformat()
                })
            else:
                print(f"❌ DEBUG INSCRIPTION: client_id None/False")
                return jsonify({
                    'success': False,
                    'error': 'Erreur lors de l\'inscription - Aucun ID retourné'
                }), 500
        except Exception as create_error:
            print(f"❌ DEBUG INSCRIPTION: Exception create_client: {create_error}")
            return jsonify({
                'success': False,
                'error': f'Erreur création client: {str(create_error)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/examples')
def api_examples():
    """API pour obtenir des exemples de messages"""
    examples = [
        {
            'id': 1,
            'email': 'jean.dupont@email.com',
            'subject': 'Retard de livraison',
            'message': 'Bonjour, ma commande #1003 a un retard de livraison. Quand vais-je la recevoir ?',
            'category': 'Retard de livraison'
        },
        {
            'id': 2,
            'email': 'marie.martin@email.com',
            'subject': 'Demande de remboursement',
            'message': 'Je souhaite obtenir un remboursement pour ma commande #1001, je ne suis pas satisfaite du produit.',
            'category': 'Remboursement'
        },
        {
            'id': 3,
            'email': 'pierre.durand@email.com',
            'subject': 'Produit défectueux',
            'message': 'Le produit de ma commande #1002 est arrivé cassé et défectueux.',
            'category': 'Produit défectueux'
        },
        {
            'id': 4,
            'email': 'sophie.bernard@email.com',
            'subject': 'Information commande',
            'message': 'Pouvez-vous me donner des informations sur le statut de ma commande #1004 ?',
            'category': 'Information commande'
        }
    ]
    
    return jsonify({
        'success': True,
        'examples': examples
    })

def classify_message_simple(message):
    """Classification simple basée sur des mots-clés"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['retard', 'livraison', 'reçu', 'arrivé', 'expédition']):
        return 'Retard de livraison'
    elif any(word in message_lower for word in ['remboursement', 'rembourser', 'annuler', 'remboursé']):
        return 'Remboursement'
    elif any(word in message_lower for word in ['défectueux', 'cassé', 'abîmé', 'problème', 'défaut']):
        return 'Produit défectueux'
    else:
        return 'Information commande'

def generate_response_simple(email, category, message):
    """Génère une réponse simple basée sur la catégorie"""
    responses = {
        'Retard de livraison': f"""Bonjour,

Nous nous excusons sincèrement pour le retard de votre commande. 

Nous avons immédiatement contacté notre transporteur pour connaître le statut exact de votre colis et vous tiendrons informé(e) de son avancement dans les plus brefs délais.

Nous vous remercions de votre patience et compréhension.

Cordialement,
L'équipe Support Client""",
        
        'Remboursement': f"""Bonjour,

Nous avons bien reçu votre demande de remboursement et nous comprenons votre déception.

Votre demande va être traitée dans les plus brefs délais. Le remboursement sera effectué sous 3 à 5 jours ouvrés sur votre moyen de paiement initial.

Nous vous tiendrons informé(e) de l'avancement de votre dossier.

Cordialement,
L'équipe Support Client""",
        
        'Produit défectueux': f"""Bonjour,

Nous sommes sincèrement désolés que votre produit soit arrivé endommagé.

Nous allons vous faire parvenir un produit de remplacement dans les plus brefs délais. Un email de confirmation avec le numéro de suivi vous sera envoyé sous 24h.

Aucune action n'est requise de votre part concernant le produit défectueux.

Cordialement,
L'équipe Support Client""",
        
        'Information commande': f"""Bonjour,

Nous avons bien reçu votre demande d'information concernant votre commande.

Notre équipe examine actuellement votre dossier et vous fournira toutes les informations demandées dans les plus brefs délais.

Nous vous remercions de votre confiance.

Cordialement,
L'équipe Support Client"""
    }
    
    return responses.get(category, responses['Information commande'])

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("🚀 Lancement du serveur web...")
    print("📋 Interface disponible sur: http://localhost:5000")
    print("🎨 Interface moderne avec Bootstrap 5")
    print("⚡ Performance optimisée")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
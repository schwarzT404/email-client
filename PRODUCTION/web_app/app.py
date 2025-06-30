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
import pytz
import uuid
import sqlite3
import time

# Charger les variables d'environnement depuis .env
load_dotenv()

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Flask
app = Flask(__name__)
app.secret_key = 'support_client_secret_key_2025'
PARIS_TZ = pytz.timezone('Europe/Paris')

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

def get_db_connection():
    """Crée une connexion à la base de données."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'crm_ecommerce.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_messages_table():
    """Initialise la table des messages avec statuts"""
    try:
        import sqlite3
        import os
        
        # Chemin absolu cohérent
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'crm_ecommerce.db')
        
        conn = sqlite3.connect(db_path)
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now(PARIS_TZ).strftime('%Y%m%d%H%M%S')
        ticket_id = f"MSG-{timestamp}-{len(message) % 1000:03d}"
        
        cursor.execute('''
            INSERT INTO messages (client_email, client_name, subject, message, status, ticket_id, created_at)
            VALUES (?, ?, ?, ?, 'nouveau', ?, ?)
        ''', (email, client_name, subject, message, ticket_id, datetime.now(PARIS_TZ)))
        
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
        conn = get_db_connection()
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
                processed_at = ?,
                updated_at = ?
            WHERE id = ?
        ''', (
            result.get('category'),
            result.get('urgency'),
            result.get('sentiment'),
            result.get('response'),
            processing_time,
            result.get('quality_score', 0),
            result.get('model', 'claude-4-sonnet'),
            datetime.now(PARIS_TZ),
            datetime.now(PARIS_TZ),
            message_id
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as     e:
        print(f"❌ Erreur mise à jour message: {e}")
        return False

def initialize_system():
    """Initialise les modules du système"""
    global db_manager, notion_manager, support_agent, claude_agent, system_status
    
    # Initialiser les variables de statut
    db_connected = False
    notion_connected = False
    claude_ready = False
    
    try:
        # Initialiser le gestionnaire de base de données
    try:
        from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
            db_connected = True
            print("✅ DatabaseManager initialisé")
        except Exception as e:
            print(f"❌ Erreur DatabaseManager: {e}")
            db_manager = None
        
        # Initialiser Notion (optionnel)
        try:
        from notion.notion_manager import NotionManager
        notion_manager = NotionManager()
            notion_connected = True
            print("✅ NotionManager initialisé")
        except Exception as e:
            print(f"⚠️ NotionManager non disponible: {e}")
            notion_manager = None
        
        # Initialiser l'agent Claude avec accès à la base de données
        try:
            from automation.claude_agent import ClaudeAgent
        claude_agent = ClaudeAgent(db_manager=db_manager)
            claude_ready = True
            print("✅ ClaudeAgent initialisé")
        except Exception as e:
            print(f"⚠️ ClaudeAgent non disponible: {e}")
            claude_agent = None
        
        # Initialiser la table des messages (seulement si DB disponible)
        if db_connected:
        init_messages_table()
        
        # Fallback sur l'ancien support agent si nécessaire (ne pas faire échouer l'init si erreur)
        try:
            from automation.support_agent import SupportAgent
            support_agent = SupportAgent()  # Correction: pas de paramètres
            print("✅ SupportAgent initialisé")
        except Exception as e:
            print(f"⚠️ SupportAgent non disponible: {e}")
            support_agent = None
        
        # Mettre à jour le statut avec les valeurs réelles
        claude_status = claude_agent.get_status() if claude_agent else {}
        
        system_status.update({
            'db_connected': db_connected,
            'notion_connected': notion_connected,
            'agent_ready': claude_ready,
            'claude_available': claude_status.get('claude_available', False),
            'claude_ready': claude_status.get('claude_ready', False),
            'api_key_configured': claude_status.get('api_key_configured', False),
            'model': claude_status.get('model', 'simulation'),
            'last_update': datetime.now()
        })
        
        print("✅ Système initialisé avec succès")
        print(f"   - Base de données: {'✅' if db_connected else '❌'}")
        print(f"   - Notion: {'✅' if notion_connected else '❌'}")
        print(f"   - Claude Agent: {'✅' if claude_ready else '❌'}")
        print(f"   - Support Agent: {'✅' if support_agent else '❌'}")
        
        # Retourner True si au moins la base de données fonctionne
        return db_connected
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation critique: {e}")
        import traceback
        traceback.print_exc()
        
        system_status.update({
            'db_connected': db_connected,  # Conserver l'état réel de la DB
            'notion_connected': notion_connected,
            'agent_ready': claude_ready,
            'claude_available': False,
            'claude_ready': False,
            'last_update': datetime.now(),
            'error': str(e)
        })
        return db_connected  # Même si erreur, on peut continuer si DB OK

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

# Enrichir le contexte pour l'agent IA
def get_client_context(email: str) -> dict:
    """
    Récupère le contexte structuré d'un client pour l'agent IA.
    Interroge la base de données unifiée (tables client et commandes_details).
    """
    context = {
        "client": None,
        "nb_commandes": 0,
        "total_depense": 0,
        "commandes": []
    }
    try:
        conn = get_db_connection()
        
        # 1. Récupérer les informations du client depuis la table 'client'
        client_info = conn.execute('SELECT * FROM client WHERE email = ?', (email,)).fetchone()
        if client_info:
            context['client'] = dict(client_info)

        # 2. Récupérer l'historique des commandes depuis la table unifiée 'commandes_details'
        orders = conn.execute(
            """
            SELECT commande_id, created_at, statut, montant_total, produits_json
            FROM commandes_details
            WHERE client_email = ?
            ORDER BY created_at DESC
            LIMIT 5
            """, (email,)
        ).fetchall()
        
        conn.close()

        if orders:
            context['nb_commandes'] = len(orders)
            context['total_depense'] = float(sum(o['montant_total'] for o in orders))
            
            for order in orders:
                try:
                    produits = json.loads(order['produits_json'])
                except (json.JSONDecodeError, TypeError):
                    produits = [] # Gérer le cas où le JSON est invalide ou null

                context['commandes'].append({
                    'id': order['commande_id'],
                    'date': order['created_at'],
                    'statut': order['statut'],
                    'montant': float(order['montant_total']),
                    'produits': produits
                })
                
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du contexte client: {e}")
        # Retourner une structure valide mais vide en cas d'erreur
        return { "client": None, "nb_commandes": 0, "total_depense": 0, "commandes": [] }
        
    return context

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
        
        # Logger la tentative d'accès
        log_transaction(email, "TENTATIVE_ACCES", "EN_COURS", {
            'subject': subject,
            'message_length': len(message),
            'timestamp': datetime.now().isoformat()
        })
        
        if db_manager and system_status.get('db_connected', False):
            client_info = db_manager.get_client_by_email(email)
            print(f"🔍 DEBUG AUTH: Email {email} -> client_info={client_info}")
            
            if not client_info:
                print(f"🚫 DEBUG AUTH: Accès refusé pour {email}")
                
                # Logger l'échec d'authentification
                log_transaction(email, "ACCES_REFUSE", "ECHEC", {
                    'reason': 'Email non enregistré',
                    'subject': subject,
                    'message_preview': message[:100]
                })
                
                # Stocker l'email inconnu
                store_unknown_email(email, "ACCES_REFUSE")
                
                return jsonify({
                    'success': False,
                    'error': 'Accès refusé. Vous devez être inscrit pour utiliser ce service.',
                    'requires_registration': True
                }), 403
            else:
                print(f"✅ DEBUG AUTH: Accès autorisé pour {email}")
                
                # Logger l'accès autorisé
                log_transaction(email, "ACCES_AUTORISE", "SUCCES", {
                    'client_name': f"{client_info.get('prenom', '')} {client_info.get('nom', '')}",
                    'subject': subject
                })
        else:
            print(f"🚫 DEBUG AUTH: Base de données indisponible (db_manager={db_manager is not None}, connected={system_status.get('db_connected', False)})")
            
            # Logger l'erreur système
            log_transaction(email, "ERREUR_SYSTEME", "ECHEC", {
                'error': 'Base de données indisponible',
                'db_manager_exists': db_manager is not None,
                'db_connected': system_status.get('db_connected', False)
            })
            
            return jsonify({
                'success': False,
                'error': 'Base de données indisponible'
            }), 500
        
        # Enrichissement du contexte
        client_context = get_client_context(email)
        
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
            # Mesurer le temps de traitement réel
            start_time = time.time()
            
            # Traitement avec Claude (priorité)
            result = claude_agent.process_customer_message(email, message, subject, context=client_context)
            
            # Calculer la durée
            end_time = time.time()
            processing_duration = end_time - start_time
            
            # Mettre à jour l'enregistrement du message
            update_message_processing(message_id, result, processing_duration)
            
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
                print(f"   ⏱️  Temps total: {processing_duration:.2f}s")
                print(f"   🎫 Ticket: {ticket_id}")
                print("=" * 50)
            except Exception as log_error:
                print(f"⚠️ Erreur logging monitoring: {log_error}")
            
            # Logger le traitement réussi
            log_transaction(email, "MESSAGE_TRAITE", "SUCCES", {
                'ticket_id': ticket_id,
                'message_id': message_id,
                'category': result.get('category'),
                'urgency': result.get('urgency'),
                'sentiment': result.get('sentiment'),
                'quality_score': result.get('quality_score'),
                'processing_time': processing_duration,
                'model': 'claude-4-sonnet',
                'response_length': len(result.get('response', ''))
            })
            
            # Juste pour la démo, on ajoute le contexte au résultat
            result['client_context_debug'] = client_context
            return jsonify({
                'success': True,
                'result': result,
                'processed_at': datetime.now().isoformat(),
                'processing_delay': processing_duration,
                'mode': 'claude-ai',
                'ai_model': 'claude-4-sonnet'
            })
        elif support_agent and system_status['agent_ready']:
            # Ajouter le délai de traitement
            time.sleep(processing_delay)
            
            # Traitement avec l'ancien agent
            result = support_agent.process_customer_message(email, message, subject, context=client_context)
            
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

def log_transaction(email: str, action: str, status: str, details: dict = None):
    """Enregistre toutes les transactions pour monitoring admin"""
    try:
        import sqlite3
        import os
        
        # Chemin absolu cohérent
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'crm_ecommerce.db')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Table pour logs de transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insérer le log
        cursor.execute('''
            INSERT INTO transaction_logs (email, action, status, details)
            VALUES (?, ?, ?, ?)
        ''', (email, action, status, json.dumps(details) if details else None))
        
        conn.commit()
        conn.close()
        
        # Log console pour admin
        print(f"📊 [TRANSACTION LOG] {datetime.now().strftime('%H:%M:%S')} | {email} | {action} | {status}")
        
    except Exception as e:
        print(f"⚠️ Erreur log transaction: {e}")

def store_unknown_email(email: str, action: str = "TENTATIVE_ACCES"):
    """Stocke les emails inconnus pour suivi admin"""
    try:
        import sqlite3
        import os
        
        # Chemin absolu cohérent
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'crm_ecommerce.db')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Table pour emails inconnus
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unknown_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                first_attempt DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_attempt DATETIME DEFAULT CURRENT_TIMESTAMP,
                attempt_count INTEGER DEFAULT 1,
                action_type TEXT DEFAULT 'TENTATIVE_ACCES',
                status TEXT DEFAULT 'NON_AUTORISE'
            )
        ''')
        
        # Insérer ou mettre à jour
        cursor.execute('''
            INSERT OR REPLACE INTO unknown_emails 
            (email, first_attempt, last_attempt, attempt_count, action_type)
            VALUES (
                ?, 
                COALESCE((SELECT first_attempt FROM unknown_emails WHERE email = ?), CURRENT_TIMESTAMP),
                CURRENT_TIMESTAMP,
                COALESCE((SELECT attempt_count FROM unknown_emails WHERE email = ?) + 1, 1),
                ?
            )
        ''', (email, email, email, action))
        
        conn.commit()
        conn.close()
        
        print(f"📝 [EMAIL INCONNU STOCKÉ] {email} | Action: {action}")
        
    except Exception as e:
        print(f"⚠️ Erreur stockage email: {e}")

@app.route('/api/products')
def api_products():
    """Retourne la liste des produits."""
    try:
        conn = get_db_connection()
        products = conn.execute('SELECT id, name, description, price, stock, image_url FROM products').fetchall()
        conn.close()
        return jsonify({'success': True, 'products': [dict(p) for p in products]})
    except Exception as e:
        print(f"❌ Erreur API Produits: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    """Crée une nouvelle commande en utilisant la table commandes_details."""
    print("📦 [API] Réception d'une nouvelle requête de commande.")
    data = request.get_json()
    email = data.get('email')
    cart = data.get('cart') # Le panier contient {id, name, price, quantity}

    print(f"   L_ Email: {email}, Panier: {cart}")

    if not email or not cart:
        print("  L_ ❌ Erreur: Données manquantes.")
        return jsonify({'success': False, 'error': 'Données manquantes'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    print("  L_ ✅ Connexion DB établie.")

    try:
        # Récupérer les informations du client
        client_info = cursor.execute('SELECT nom, prenom FROM client WHERE email = ?', (email,)).fetchone()
        client_nom = client_info['nom'] if client_info else ''
        client_prenom = client_info['prenom'] if client_info else ''

        # Générer un ID de commande unique
        timestamp = datetime.now(PARIS_TZ).strftime('%Y%m%d%H%M%S')
        commande_id = f"CMD-{timestamp}-{len(email) % 100:02d}"

        # Calculer les totaux et vérifier le stock
        montant_total = 0
        nb_articles = 0
        produits_json_list = []

        print("  L_ 🧐 Vérification du stock et calcul des totaux...")
        for item in cart:
            product = cursor.execute('SELECT stock, prix FROM produits WHERE id = ?', (item['id'],)).fetchone()
            if product is None:
                raise Exception(f"Produit ID {item['id']} non trouvé.")
            
            if product['stock'] < item['quantity']:
                raise Exception(f"Stock insuffisant pour le produit ID {item['id']}.")
            
            montant_total += product['prix'] * item['quantity']
            nb_articles += item['quantity']
            produits_json_list.append({
                'id': item['id'],
                'nom': item['name'],
                'prix': product['prix'],
                'quantite': item['quantity']
            })

        print(f"  L_ ✅ Stock vérifié. Montant: {montant_total}, Articles: {nb_articles}")
        print(f"  L_ 📝 Création commande {commande_id} dans commandes_details...")

        # Insérer dans la table unifiée 'commandes_details'
        cursor.execute('''
            INSERT INTO commandes_details 
            (commande_id, client_email, client_nom, client_prenom, produits_json, 
             montant_total, nb_articles, statut, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmee', ?, ?)
        ''', (
            commande_id, email, client_nom, client_prenom,
            json.dumps(produits_json_list), montant_total, nb_articles,
            datetime.now(PARIS_TZ), datetime.now(PARIS_TZ)
        ))

        # Mettre à jour le stock
        print("  L_ ⬇️ Mise à jour du stock...")
        for item in cart:
            cursor.execute(
                'UPDATE produits SET stock = stock - ? WHERE id = ?',
                (item['quantity'], item['id'])
            )
        
        conn.commit()
        print("  L_ ✅ Commande enregistrée avec succès dans commandes_details.")
        
        # Le order_uid est maintenant notre commande_id
        return jsonify({'success': True, 'order_uid': commande_id, 'total': montant_total})

    except Exception as e:
        print(f"  L_ ❌ ERREUR LORS DE LA CRÉATION DE LA COMMANDE: {e}")
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()
        print("  L_ 🚪 Connexion DB fermée.")

@app.route('/api/check-email', methods=['POST'])
def api_check_email():
    """Vérifie si un email existe dans la base de données clients."""
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'exists': False, 'error': 'Email manquant'}), 400
    
    conn = get_db_connection()
    # Recherche dans la table 'client'
    client = conn.execute('SELECT id FROM client WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    return jsonify({'exists': client is not None})

if __name__ == '__main__':
    print("🚀 Lancement du serveur web...")
    print("📋 Interface disponible sur: http://localhost:5000")
    print("🎨 Interface moderne avec Bootstrap 5")
    print("⚡ Performance optimisée")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
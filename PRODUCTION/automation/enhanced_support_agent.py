#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent de Support Client Amélioré
Utilise les nouvelles bases de données et l'intégration Notion
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from automation.claude_agent import ClaudeAgent


class EnhancedSupportAgent:
    """Agent de support client avec base de connaissances et intégration Notion"""
    
    def __init__(self, db_path: str = 'data/crm_ecommerce.db'):
        self.db_path = db_path
        self.claude_agent = ClaudeAgent()
        self.init_enhanced_tables()
        print("✅ Agent de support amélioré initialisé")
    
    def init_enhanced_tables(self):
        """Initialise les nouvelles tables dans la base existante"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table réponses support
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    categorie TEXT NOT NULL,
                    reponse_generique TEXT NOT NULL,
                    tags TEXT,
                    variables_template TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Table contacts clients améliorée
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_client TEXT NOT NULL,
                    nom_prenom TEXT,
                    id_commande INTEGER,
                    message_initial TEXT NOT NULL,
                    categorie TEXT,
                    reponse_personnalisee TEXT,
                    statut TEXT DEFAULT 'nouveau' CHECK (statut IN ('nouveau', 'en_cours', 'traite', 'ferme', 'escalade')),
                    ticket_id TEXT UNIQUE,
                    urgence INTEGER DEFAULT 1 CHECK (urgence BETWEEN 1 AND 5),
                    sentiment TEXT,
                    model_used TEXT DEFAULT 'claude-4-sonnet',
                    quality_score REAL DEFAULT 0,
                    response_time REAL DEFAULT 0,
                    notion_page_id TEXT,
                    notion_sync_status TEXT DEFAULT 'pending',
                    notion_last_sync DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed_at DATETIME,
                    closed_at DATETIME,
                    assigned_to TEXT DEFAULT 'IA Agent'
                )
            ''')
            
            # Insérer réponses par défaut si la table est vide
            cursor.execute("SELECT COUNT(*) FROM support_responses")
            if cursor.fetchone()[0] == 0:
                self._insert_default_responses(cursor)
            
            conn.commit()
            conn.close()
            print("✅ Tables améliorées initialisées")
            
        except Exception as e:
            print(f"❌ Erreur initialisation tables: {e}")
    
    def _insert_default_responses(self, cursor):
        """Insère les réponses par défaut"""
        default_responses = [
            {
                'categorie': 'retard_livraison',
                'reponse_generique': '''Bonjour {{nom_client}},

Nous avons bien reçu votre message concernant le retard de livraison de votre commande {{id_commande}}.

Nous nous excusons sincèrement pour ce désagrément. Nous avons immédiatement contacté notre transporteur pour localiser votre colis.

{{info_suivi}}

Nous restons à votre disposition pour tout complément d'information.

Cordialement,
Service Client''',
                'tags': 'livraison,retard,colis,transporteur',
                'variables_template': '{"nom_client": "string", "id_commande": "number", "info_suivi": "string"}'
            },
            {
                'categorie': 'remboursement',
                'reponse_generique': '''Bonjour {{nom_client}},

Nous avons bien reçu votre demande de remboursement pour la commande {{id_commande}}.

{{motif_remboursement}}

Votre remboursement sera traité dans un délai de 3 à 5 jours ouvrés. Vous recevrez une confirmation par email une fois le remboursement effectué.

Nous nous excusons pour la gêne occasionnée.

Cordialement,
Service Client''',
                'tags': 'remboursement,retour,annulation',
                'variables_template': '{"nom_client": "string", "id_commande": "number", "motif_remboursement": "string"}'
            },
            {
                'categorie': 'produit_defectueux',
                'reponse_generique': '''Bonjour {{nom_client}},

Nous sommes désolés d'apprendre que le produit {{nom_produit}} de votre commande {{id_commande}} présente un défaut.

Pour traiter votre réclamation dans les meilleurs délais :
{{procedure_retour}}

Un nouveau produit vous sera expédié dès réception de l'article défectueux.

Nous vous remercions de votre compréhension.

Cordialement,
Service Client''',
                'tags': 'defectueux,qualite,remplacement,garantie',
                'variables_template': '{"nom_client": "string", "nom_produit": "string", "id_commande": "number", "procedure_retour": "string"}'
            },
            {
                'categorie': 'information_commande',
                'reponse_generique': '''Bonjour {{nom_client}},

Concernant votre commande {{id_commande}} :

{{details_commande}}

Vous pouvez suivre l'évolution de votre commande en temps réel sur notre site web dans la section "Mes commandes".

N'hésitez pas à nous contacter si vous avez d'autres questions.

Cordialement,
Service Client''',
                'tags': 'commande,statut,suivi,information',
                'variables_template': '{"nom_client": "string", "id_commande": "number", "details_commande": "string"}'
            },
            {
                'categorie': 'reclamation',
                'reponse_generique': '''Bonjour {{nom_client}},

Nous avons bien pris note de votre réclamation concernant {{objet_reclamation}}.

Votre satisfaction est notre priorité. Nous étudions votre dossier avec attention et vous proposerons une solution adaptée dans les plus brefs délais.

{{action_corrective}}

Nous vous remercions de nous avoir fait part de votre mécontentement, cela nous aide à améliorer nos services.

Cordialement,
Service Client''',
                'tags': 'reclamation,insatisfaction,amelioration',
                'variables_template': '{"nom_client": "string", "objet_reclamation": "string", "action_corrective": "string"}'
            }
        ]
        
        for response_data in default_responses:
            cursor.execute(
                """INSERT INTO support_responses 
                   (categorie, reponse_generique, tags, variables_template) 
                   VALUES (?, ?, ?, ?)""",
                (response_data['categorie'], response_data['reponse_generique'], 
                 response_data['tags'], response_data['variables_template'])
            )
    
    def process_customer_message_enhanced(self, email_client: str, message: str, 
                                        nom_prenom: str = None, id_commande: int = None,
                                        subject: str = "") -> Dict:
        """Traite un message client avec les nouvelles fonctionnalités"""
        start_time = datetime.now()
        
        try:
            # 1. Créer le contact client
            contact_id = self.create_contact_client(email_client, message, nom_prenom, id_commande)
            if not contact_id:
                return {"success": False, "error": "Erreur création contact"}
            
            # 2. Analyser avec Claude
            analysis = self.claude_agent.classify_message(message, subject)
            
            # 3. Générer réponse personnalisée
            response = self.generate_personalized_response(
                analysis.get('category', 'autre'),
                email_client,
                nom_prenom,
                id_commande
            )
            
            # 4. Calculer métriques
            processing_time = (datetime.now() - start_time).total_seconds()
            quality_score = self._calculate_quality_score(analysis, response)
            
            # 5. Finaliser le contact
            analysis_result = {
                'category': analysis.get('category'),
                'urgency': analysis.get('urgency', 1),
                'sentiment': analysis.get('sentiment'),
                'response': response,
                'response_time': processing_time,
                'quality_score': quality_score,
                'model': 'claude-4-sonnet'
            }
            
            self.complete_contact_processing(contact_id, analysis_result)
            
            # 6. Programmer synchronisation Notion (si configuré)
            self.schedule_notion_sync(contact_id)
            
            return {
                "success": True,
                "contact_id": contact_id,
                "analysis": analysis,
                "response": response,
                "processing_time": processing_time,
                "quality_score": quality_score,
                "ticket_id": self.get_ticket_id(contact_id)
            }
            
        except Exception as e:
            print(f"❌ Erreur traitement message: {e}")
            return {"success": False, "error": str(e)}
    
    def create_contact_client(self, email_client: str, message_initial: str, 
                            nom_prenom: str = None, id_commande: int = None) -> Optional[int]:
        """Crée un nouveau contact client"""
        try:
            # Générer ticket_id unique
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ticket_id = f"TKT-{timestamp}-{len(message_initial) % 1000:03d}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO contacts_clients 
                   (email_client, nom_prenom, id_commande, message_initial, ticket_id) 
                   VALUES (?, ?, ?, ?, ?)""",
                (email_client, nom_prenom, id_commande, message_initial, ticket_id)
            )
            conn.commit()
            contact_id = cursor.lastrowid
            conn.close()
            
            print(f"✅ Contact client créé: ID {contact_id}, Ticket {ticket_id}")
            return contact_id
            
        except Exception as e:
            print(f"❌ Erreur création contact: {e}")
            return None
    
    def generate_personalized_response(self, categorie: str, email_client: str, 
                                     nom_prenom: str = None, id_commande: int = None) -> str:
        """Génère une réponse personnalisée basée sur un template"""
        try:
            # Récupérer le template
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT reponse_generique, variables_template FROM support_responses WHERE categorie = ? AND is_active = 1",
                (categorie,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return "Nous avons bien reçu votre message et nous vous répondrons dans les plus brefs délais."
            
            template, variables_json = result
            
            # Préparer les variables de remplacement
            variables = {
                'nom_client': nom_prenom or email_client.split('@')[0],
                'id_commande': str(id_commande) if id_commande else 'N/A',
                'email_client': email_client
            }
            
            # Variables spécifiques par catégorie
            if categorie == 'retard_livraison':
                variables['info_suivi'] = "Votre colis sera livré dans les prochaines 24-48h."
            elif categorie == 'remboursement':
                variables['motif_remboursement'] = "Nous procédons au remboursement selon votre demande."
            elif categorie == 'produit_defectueux':
                variables['nom_produit'] = "le produit concerné"
                variables['procedure_retour'] = "1. Emballez l'article\n2. Utilisez l'étiquette de retour\n3. Déposez le colis en point relais"
            elif categorie == 'information_commande':
                variables['details_commande'] = "Votre commande est actuellement en cours de traitement."
            elif categorie == 'reclamation':
                variables['objet_reclamation'] = "votre demande"
                variables['action_corrective'] = "Nous mettons tout en œuvre pour résoudre votre problème."
            
            # Remplacer les variables dans le template
            response = template
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                response = response.replace(placeholder, str(var_value))
            
            return response
            
        except Exception as e:
            print(f"❌ Erreur génération réponse: {e}")
            return "Nous avons bien reçu votre message et nous vous répondrons dans les plus brefs délais."
    
    def complete_contact_processing(self, contact_id: int, analysis_result: Dict) -> bool:
        """Complète le traitement d'un contact"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE contacts_clients SET
                   categorie = ?, urgence = ?, sentiment = ?, 
                   reponse_personnalisee = ?, response_time = ?, 
                   quality_score = ?, model_used = ?,
                   statut = 'traite', processed_at = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (
                    analysis_result.get('category'),
                    analysis_result.get('urgency'),
                    analysis_result.get('sentiment'),
                    analysis_result.get('response'),
                    analysis_result.get('response_time', 0),
                    analysis_result.get('quality_score', 0),
                    analysis_result.get('model', 'claude-4-sonnet'),
                    contact_id
                )
            )
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Erreur finalisation contact: {e}")
            return False
    
    def schedule_notion_sync(self, contact_id: int):
        """Programme la synchronisation avec Notion"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE contacts_clients SET notion_sync_status = 'pending' WHERE id = ?",
                (contact_id,)
            )
            conn.commit()
            conn.close()
            print(f"📋 Synchronisation Notion programmée pour contact {contact_id}")
            
        except Exception as e:
            print(f"❌ Erreur programmation sync Notion: {e}")
    
    def get_ticket_id(self, contact_id: int) -> Optional[str]:
        """Récupère le ticket_id d'un contact"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT ticket_id FROM contacts_clients WHERE id = ?", (contact_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
            
        except Exception as e:
            print(f"❌ Erreur récupération ticket_id: {e}")
            return None
    
    def _calculate_quality_score(self, analysis: Dict, response: str) -> float:
        """Calcule un score de qualité pour la réponse"""
        try:
            score = 0.0
            
            # Score basé sur la confiance de classification
            confidence = analysis.get('confidence', 0.5)
            score += confidence * 0.4
            
            # Score basé sur la longueur de réponse
            if len(response) > 100:
                score += 0.3
            elif len(response) > 50:
                score += 0.2
            
            # Score basé sur la personnalisation
            if '{{' not in response:  # Variables remplacées
                score += 0.3
            
            return min(1.0, score)
            
        except:
            return 0.7  # Score par défaut
    
    def get_contacts_stats(self) -> Dict:
        """Récupère les statistiques des contacts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_contacts,
                    COUNT(CASE WHEN statut = 'nouveau' THEN 1 END) as nouveaux,
                    COUNT(CASE WHEN statut = 'en_cours' THEN 1 END) as en_cours,
                    COUNT(CASE WHEN statut = 'traite' THEN 1 END) as traites,
                    COUNT(CASE WHEN statut = 'ferme' THEN 1 END) as fermes,
                    AVG(quality_score) as score_qualite_moyen,
                    AVG(response_time) as temps_reponse_moyen
                FROM contacts_clients
            """)
            
            stats = cursor.fetchone()
            conn.close()
            
            if stats:
                return {
                    "total_contacts": stats[0],
                    "nouveaux": stats[1],
                    "en_cours": stats[2],
                    "traites": stats[3],
                    "fermes": stats[4],
                    "score_qualite_moyen": round(stats[5] or 0, 2),
                    "temps_reponse_moyen": round(stats[6] or 0, 2)
                }
            
            return {}
            
        except Exception as e:
            print(f"❌ Erreur statistiques: {e}")
            return {}
    
    def get_recent_contacts(self, limit: int = 10) -> List[Dict]:
        """Récupère les contacts récents"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM contacts_clients ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            
            results = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            print(f"❌ Erreur contacts récents: {e}")
            return [] 
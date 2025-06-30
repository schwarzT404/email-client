#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Messages avec Statuts
Système de suivi temps réel pour le support client
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class MessageManager:
    """Gestionnaire pour les messages avec statuts et suivi temps réel"""
    
    def __init__(self, db_path: str = "data/crm_ecommerce.db"):
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.init_message_tables()
        self.populate_enterprise_accounts()
        self.populate_simulation_scenarios()
    
    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            print("✅ MessageManager connecté à la base de données")
        except sqlite3.Error as e:
            print(f"❌ Erreur connexion MessageManager: {e}")
            raise
    
    def init_message_tables(self):
        """Initialise les tables pour les messages"""
        try:
            # Lire le schéma des messages
            schema_path = "database/schema_messages.sql" 
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                # Exécuter le schéma
                self.connection.executescript(schema_sql)
                self.connection.commit()
                print("✅ Tables de messages initialisées")
            else:
                # Créer les tables manuellement si le fichier n'existe pas
                self._create_tables_manually()
        except Exception as e:
            print(f"❌ Erreur initialisation tables: {e}")
            self._create_tables_manually()
    
    def _create_tables_manually(self):
        """Crée les tables manuellement si le fichier SQL n'est pas disponible"""
        try:
            cursor = self.connection.cursor()
            
            # Table messages
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
            
            # Table enterprise_accounts
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
            
            # Table message_history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    previous_status TEXT,
                    new_status TEXT,
                    changed_by TEXT DEFAULT 'System',
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (message_id) REFERENCES messages(id)
                )
            ''')
            
            # Table simulation_scenarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS simulation_scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    urgency INTEGER DEFAULT 3,
                    subject_template TEXT NOT NULL,
                    message_template TEXT NOT NULL,
                    expected_response_type TEXT,
                    probability REAL DEFAULT 1.0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            self.connection.commit()
            print("✅ Tables créées manuellement")
            
        except Exception as e:
            print(f"❌ Erreur création manuelle: {e}")
    
    def create_message(self, client_email: str, subject: str, message: str, 
                      client_name: str = None) -> Optional[int]:
        """Crée un nouveau message avec statut 'nouveau'"""
        try:
            cursor = self.connection.cursor()
            
            # Générer ticket_id unique
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ticket_id = f"MSG-{timestamp}-{len(message) % 1000:03d}"
            
            cursor.execute('''
                INSERT INTO messages (
                    client_email, client_name, subject, message, status, ticket_id
                ) VALUES (?, ?, ?, ?, 'nouveau', ?)
            ''', (client_email, client_name, subject, message, ticket_id))
            
            message_id = cursor.lastrowid
            self.connection.commit()
            
            print(f"📧 Nouveau message créé: ID {message_id}, Ticket {ticket_id}")
            return message_id
            
        except Exception as e:
            print(f"❌ Erreur création message: {e}")
            return None
    
    def update_message_status(self, message_id: int, new_status: str, 
                             notes: str = None) -> bool:
        """Met à jour le statut d'un message"""
        try:
            cursor = self.connection.cursor()
            
            # Récupérer le statut actuel
            cursor.execute('SELECT status FROM messages WHERE id = ?', (message_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            old_status = result['status']
            
            # Mettre à jour le statut
            cursor.execute('''
                UPDATE messages 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, message_id))
            
            # Ajouter à l'historique
            cursor.execute('''
                INSERT INTO message_history (message_id, previous_status, new_status, notes)
                VALUES (?, ?, ?, ?)
            ''', (message_id, old_status, new_status, notes))
            
            self.connection.commit()
            print(f"🔄 Message {message_id}: {old_status} → {new_status}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour statut: {e}")
            return False
    
    def complete_message_processing(self, message_id: int, analysis_result: Dict) -> bool:
        """Complète le traitement d'un message avec les résultats de l'analyse"""
        try:
            cursor = self.connection.cursor()
            
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
            
            self.connection.commit()
            print(f"✅ Message {message_id} traitement terminé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur finalisation traitement: {e}")
            return False
    
    def get_messages_by_status(self, status: str = None) -> List[Dict]:
        """Récupère les messages par statut"""
        try:
            cursor = self.connection.cursor()
            
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
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(f"❌ Erreur récupération messages: {e}")
            return []
    
    def get_message_stats(self) -> Dict:
        """Récupère les statistiques des messages"""
        try:
            cursor = self.connection.cursor()
            
            # Statistiques par statut
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM messages 
                GROUP BY status
            ''')
            status_stats = dict(cursor.fetchall())
            
            # Statistiques générales aujourd'hui
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_today,
                    AVG(response_time) as avg_response_time,
                    AVG(quality_score) as avg_quality
                FROM messages 
                WHERE DATE(created_at) = DATE('now')
            ''')
            today_stats = dict(cursor.fetchone() or {})
            
            # Statistiques par catégorie
            cursor.execute('''
                SELECT category, COUNT(*) as count, AVG(quality_score) as avg_quality
                FROM messages 
                WHERE category IS NOT NULL
                GROUP BY category
            ''')
            category_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'status_counts': status_stats,
                'today_stats': today_stats,
                'category_stats': category_stats,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erreur statistiques: {e}")
            return {}
    
    def get_all_clients(self) -> List[Dict]:
        """Récupère tous les clients (de la table client + enterprise_accounts)"""
        try:
            cursor = self.connection.cursor()
            
            clients = []
            
            # Clients de la table client
            try:
                cursor.execute('SELECT nom, prenom, email, "standard" as type FROM client ORDER BY nom, prenom')
                clients.extend([dict(row) for row in cursor.fetchall()])
            except:
                pass  # Table client peut ne pas exister
            
            # Comptes entreprise
            cursor.execute('''
                SELECT nom, prenom, email, type_client as type, entreprise, poste 
                FROM enterprise_accounts 
                WHERE is_active = 1 
                ORDER BY entreprise, nom, prenom
            ''')
            enterprise_clients = [dict(row) for row in cursor.fetchall()]
            clients.extend(enterprise_clients)
            
            return clients
            
        except Exception as e:
            print(f"❌ Erreur récupération clients: {e}")
            return []
    
    def populate_enterprise_accounts(self):
        """Peuple la table avec des comptes d'entreprise pré-enregistrés"""
        try:
            cursor = self.connection.cursor()
            
            # Vérifier si des comptes existent déjà
            cursor.execute('SELECT COUNT(*) FROM enterprise_accounts')
            if cursor.fetchone()[0] > 0:
                return  # Déjà peuplé
            
            # Comptes d'entreprise réalistes
            enterprise_accounts = [
                # TechCorp Solutions
                ("Dubois", "Sophie", "sophie.dubois@techcorp.fr", "Directrice Marketing", "Marketing", "TechCorp Solutions", "entreprise"),
                ("Martin", "Alexandre", "alexandre.martin@techcorp.fr", "Chef de Projet", "IT", "TechCorp Solutions", "vip"),
                ("Leroy", "Camille", "camille.leroy@techcorp.fr", "Assistante RH", "Ressources Humaines", "TechCorp Solutions", "entreprise"),
                
                # Groupe Mercure
                ("Moreau", "Pierre", "pierre.moreau@mercure.com", "Responsable Achats", "Achats", "Groupe Mercure", "vip"),
                ("Petit", "Julie", "julie.petit@mercure.com", "Comptable", "Finance", "Groupe Mercure", "entreprise"),
                ("Roux", "Thomas", "thomas.roux@mercure.com", "Commercial Senior", "Ventes", "Groupe Mercure", "entreprise"),
                
                # StartUp Innova
                ("Garcia", "Marine", "marine.garcia@innova.io", "CEO", "Direction", "StartUp Innova", "vip"),
                ("Fournier", "Lucas", "lucas.fournier@innova.io", "CTO", "Technique", "StartUp Innova", "vip"),
                ("Simon", "Emma", "emma.simon@innova.io", "Développeuse", "R&D", "StartUp Innova", "entreprise"),
                
                # Clients particuliers VIP
                ("Laurent", "Michel", "michel.laurent@gmail.com", "Consultant Indépendant", "Freelance", "Indépendant", "vip"),
                ("Bertrand", "Amélie", "amelie.bertrand@outlook.fr", "Architecte", "Architecture", "Cabinet Privé", "particulier"),
                ("Morel", "David", "david.morel@yahoo.fr", "Photographe", "Création", "Studio Photo", "particulier"),
                
                # Professionnels de santé
                ("Girard", "Dr. Marie", "marie.girard@clinique-sante.fr", "Médecin", "Santé", "Clinique Santé Plus", "vip"),
                ("Bonnet", "Paul", "paul.bonnet@pharmacie-centrale.fr", "Pharmacien", "Santé", "Pharmacie Centrale", "entreprise"),
                
                # Secteur éducation
                ("Dupont", "Claire", "claire.dupont@universite-lyon.fr", "Professeure", "Éducation", "Université Lyon", "entreprise"),
                ("Rousseau", "Jean", "jean.rousseau@lycee-pasteur.edu", "Proviseur", "Éducation", "Lycée Pasteur", "entreprise")
            ]
            
            cursor.executemany('''
                INSERT INTO enterprise_accounts (nom, prenom, email, poste, departement, entreprise, type_client)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', enterprise_accounts)
            
            self.connection.commit()
            print(f"✅ {len(enterprise_accounts)} comptes d'entreprise créés")
            
        except Exception as e:
            print(f"❌ Erreur population comptes: {e}")
    
    def populate_simulation_scenarios(self):
        """Peuple les scénarios de simulation"""
        try:
            cursor = self.connection.cursor()
            
            # Vérifier si des scénarios existent déjà
            cursor.execute('SELECT COUNT(*) FROM simulation_scenarios')
            if cursor.fetchone()[0] > 0:
                return
            
            scenarios = [
                # Retards de livraison
                ("Retard Livraison Standard", "retard_livraison", 3, 
                 "Ma commande n'est pas arrivée", 
                 "Bonjour, ma commande {commande_id} était prévue pour {date_prevue} mais je n'ai toujours rien reçu. Pouvez-vous me dire où elle en est ? Merci.", 
                 "tracking_info", 0.3),
                
                ("Retard Livraison Urgent", "retard_livraison", 4,
                 "URGENT - Colis en retard pour événement important",
                 "C'est urgent ! Ma commande {commande_id} devait arriver avant {evenement} qui a lieu {date_evenement}. Le retard va compromettre mon événement. Que pouvez-vous faire ?",
                 "priority_handling", 0.15),
                
                # Produits défectueux
                ("Produit Cassé Standard", "produit_defectueux", 3,
                 "Produit reçu endommagé",
                 "Le produit que j'ai reçu dans ma commande {commande_id} est arrivé cassé. L'emballage semblait intact mais l'article à l'intérieur est inutilisable. Comment procéder pour un échange ?",
                 "replacement", 0.2),
                
                ("Produit Non Conforme", "produit_defectueux", 4,
                 "Produit ne correspond pas à la description",
                 "Le produit reçu ne correspond absolument pas à ce qui était décrit sur votre site ! C'est de la fausse publicité. Je veux un remboursement immédiat et une explication.",
                 "refund", 0.1),
                
                # Demandes de remboursement
                ("Remboursement Simple", "remboursement", 2,
                 "Demande de remboursement",
                 "Bonjour, j'aimerais être remboursé(e) de ma commande {commande_id}. Le produit ne me convient pas. Quelle est la procédure à suivre ?",
                 "refund_process", 0.15),
                
                ("Remboursement Urgent", "remboursement", 4,
                 "Remboursement URGENT - Problème financier",
                 "J'ai besoin d'être remboursé(e) de ma commande {commande_id} de toute urgence suite à un problème financier imprévu. C'est vraiment urgent, pouvez-vous accélérer la procédure ?",
                 "priority_refund", 0.05),
                
                # Informations commande
                ("Info Commande Standard", "information_commande", 2,
                 "Demande d'information sur ma commande",
                 "Pouvez-vous me donner des informations sur ma commande {commande_id} ? J'aimerais connaître le statut et la date de livraison prévue.",
                 "order_status", 0.25),
                
                ("Facture Demandée", "information_commande", 1,
                 "Demande de facture",
                 "Pouvez-vous m'envoyer la facture de ma commande {commande_id} ? J'en ai besoin pour ma comptabilité. Merci d'avance.",
                 "invoice", 0.1),
                
                # Réclamations
                ("Réclamation Service", "reclamation", 4,
                 "Très mécontent du service client",
                 "Je suis extrêmement déçu(e) de votre service client. C'est la {nieme_fois} fois que j'ai un problème et personne ne semble s'en préoccuper. Je pense sérieusement à changer de fournisseur !",
                 "complaint_handling", 0.08),
                
                ("Réclamation Qualité", "reclamation", 3,
                 "Qualité des produits en baisse",
                 "J'ai remarqué une baisse de qualité dans vos produits récemment. Mes {nb_commandes} dernières commandes étaient décevantes. Que comptez-vous faire pour améliorer cela ?",
                 "quality_improvement", 0.05)
            ]
            
            cursor.executemany('''
                INSERT INTO simulation_scenarios (name, category, urgency, subject_template, message_template, expected_response_type, probability)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', scenarios)
            
            self.connection.commit()
            print(f"✅ {len(scenarios)} scénarios de simulation créés")
            
        except Exception as e:
            print(f"❌ Erreur population scénarios: {e}")
    
    def get_random_scenario(self) -> Optional[Dict]:
        """Récupère un scénario aléatoire pour la simulation"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM simulation_scenarios 
                WHERE is_active = 1 
                ORDER BY RANDOM() 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"❌ Erreur scénario aléatoire: {e}")
            return None
    
    def get_random_enterprise_account(self) -> Optional[Dict]:
        """Récupère un compte d'entreprise aléatoire"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM enterprise_accounts 
                WHERE is_active = 1 
                ORDER BY RANDOM() 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"❌ Erreur compte aléatoire: {e}")
            return None 
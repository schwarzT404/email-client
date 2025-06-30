#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Base de Données Support Client Amélioré
Gestion des réponses support et contacts clients avec intégration Notion
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config import DATABASE_CONFIG


class SupportDatabaseManager:
    """Gestionnaire spécialisé pour les bases de données support client"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_CONFIG.get('database_path', 'data/support_client.db')
        self.connection = None
        self.init_database()
        self.connect()
    
    def init_database(self):
        """Initialise la base de données avec le nouveau schéma"""
        try:
            # Créer le répertoire data s'il n'existe pas
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connexion temporaire pour créer les tables
            conn = sqlite3.connect(self.db_path)
            
            # Lire et exécuter le schéma SQL
            schema_path = 'database/schema_support_enhanced.sql'
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as file:
                    schema_sql = file.read()
                conn.executescript(schema_sql)
                print("✅ Base de données support initialisée avec succès")
            else:
                print("⚠️ Fichier schéma non trouvé, création des tables de base")
                self._create_basic_tables(conn)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de la base: {e}")
    
    def _create_basic_tables(self, conn):
        """Crée les tables de base si le fichier schéma n'est pas trouvé"""
        conn.execute('''
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
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contacts_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_client TEXT NOT NULL,
                nom_prenom TEXT,
                id_commande INTEGER,
                message_initial TEXT NOT NULL,
                categorie TEXT,
                reponse_personnalisee TEXT,
                statut TEXT DEFAULT 'nouveau',
                ticket_id TEXT UNIQUE,
                urgence INTEGER DEFAULT 1,
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
    
    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            print("✅ Connexion à la base de données support établie")
        except sqlite3.Error as e:
            print(f"❌ Erreur de connexion: {e}")
            raise
    
    def disconnect(self):
        """Ferme la connexion"""
        if self.connection:
            self.connection.close()
            print("🔌 Connexion fermée")
    
    # =======================================================
    # GESTION DES RÉPONSES SUPPORT
    # =======================================================
    
    def get_response_by_category(self, categorie: str) -> Optional[Dict]:
        """Récupère la réponse générique pour une catégorie"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM support_responses WHERE categorie = ? AND is_active = 1",
                (categorie,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"❌ Erreur récupération réponse: {e}")
            return None
    
    def get_all_support_responses(self) -> List[Dict]:
        """Récupère toutes les réponses support actives"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM support_responses WHERE is_active = 1 ORDER BY categorie")
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Erreur récupération réponses: {e}")
            return []
    
    def create_support_response(self, categorie: str, reponse_generique: str, 
                              tags: str = None, variables_template: str = None) -> Optional[int]:
        """Crée une nouvelle réponse support"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT INTO support_responses 
                   (categorie, reponse_generique, tags, variables_template) 
                   VALUES (?, ?, ?, ?)""",
                (categorie, reponse_generique, tags, variables_template)
            )
            self.connection.commit()
            response_id = cursor.lastrowid
            print(f"✅ Réponse support créée avec ID: {response_id}")
            return response_id
        except Exception as e:
            print(f"❌ Erreur création réponse: {e}")
            return None
    
    def update_support_response(self, response_id: int, **kwargs) -> bool:
        """Met à jour une réponse support"""
        try:
            # Construire la requête dynamiquement
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['categorie', 'reponse_generique', 'tags', 'variables_template', 'is_active']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
                
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(response_id)
            
            query = f"UPDATE support_responses SET {', '.join(fields)} WHERE id = ?"
            
            cursor = self.connection.cursor()
            cursor.execute(query, values)
            self.connection.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"❌ Erreur mise à jour réponse: {e}")
            return False
    
    # =======================================================
    # GESTION DES CONTACTS CLIENTS
    # =======================================================
    
    def create_contact_client(self, email_client: str, message_initial: str, 
                            nom_prenom: str = None, id_commande: int = None) -> Optional[int]:
        """Crée un nouveau contact client"""
        try:
            # Générer un ticket_id unique
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ticket_id = f"TKT-{timestamp}-{len(message_initial) % 1000:03d}"
            
            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT INTO contacts_clients 
                   (email_client, nom_prenom, id_commande, message_initial, ticket_id) 
                   VALUES (?, ?, ?, ?, ?)""",
                (email_client, nom_prenom, id_commande, message_initial, ticket_id)
            )
            self.connection.commit()
            contact_id = cursor.lastrowid
            print(f"✅ Contact client créé avec ID: {contact_id}, Ticket: {ticket_id}")
            return contact_id
        except Exception as e:
            print(f"❌ Erreur création contact: {e}")
            return None
    
    def get_contact_by_id(self, contact_id: int) -> Optional[Dict]:
        """Récupère un contact par son ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM contacts_clients WHERE id = ?", (contact_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"❌ Erreur récupération contact: {e}")
            return None
    
    def get_contact_by_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Récupère un contact par son ticket ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM contacts_clients WHERE ticket_id = ?", (ticket_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"❌ Erreur récupération contact: {e}")
            return None
    
    def get_contacts_by_status(self, statut: str = None) -> List[Dict]:
        """Récupère les contacts par statut"""
        try:
            cursor = self.connection.cursor()
            if statut:
                cursor.execute(
                    "SELECT * FROM contacts_clients WHERE statut = ? ORDER BY created_at DESC",
                    (statut,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM contacts_clients ORDER BY created_at DESC"
                )
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Erreur récupération contacts: {e}")
            return []
    
    def update_contact_status(self, contact_id: int, nouveau_statut: str) -> bool:
        """Met à jour le statut d'un contact"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE contacts_clients SET statut = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (nouveau_statut, contact_id)
            )
            self.connection.commit()
            
            # Enregistrer la date de fermeture si nécessaire
            if nouveau_statut == 'ferme':
                cursor.execute(
                    "UPDATE contacts_clients SET closed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (contact_id,)
                )
                self.connection.commit()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Erreur mise à jour statut: {e}")
            return False
    
    def complete_contact_processing(self, contact_id: int, analysis_result: Dict) -> bool:
        """Complète le traitement d'un contact avec les résultats d'analyse"""
        try:
            cursor = self.connection.cursor()
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
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Erreur finalisation contact: {e}")
            return False
    
    # =======================================================
    # INTÉGRATION NOTION
    # =======================================================
    
    def update_notion_sync(self, contact_id: int, notion_page_id: str, 
                          sync_status: str = 'synced') -> bool:
        """Met à jour les informations de synchronisation Notion"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """UPDATE contacts_clients SET 
                   notion_page_id = ?, notion_sync_status = ?, 
                   notion_last_sync = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (notion_page_id, sync_status, contact_id)
            )
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Erreur mise à jour Notion: {e}")
            return False
    
    def get_contacts_to_sync(self) -> List[Dict]:
        """Récupère les contacts qui doivent être synchronisés avec Notion"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """SELECT * FROM contacts_clients 
                   WHERE notion_sync_status IN ('pending', 'error') 
                   ORDER BY created_at ASC"""
            )
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Erreur récupération contacts à sync: {e}")
            return []
    
    # =======================================================
    # STATISTIQUES ET REPORTING
    # =======================================================
    
    def get_dashboard_stats(self) -> Dict:
        """Récupère les statistiques pour le dashboard"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM v_dashboard_stats")
            result = cursor.fetchone()
            return dict(result) if result else {}
        except Exception as e:
            print(f"❌ Erreur statistiques dashboard: {e}")
            return {}
    
    def get_stats_by_category(self) -> List[Dict]:
        """Récupère les statistiques par catégorie"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM v_stats_categories ORDER BY total_contacts DESC")
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Erreur statistiques catégories: {e}")
            return []
    
    def get_recent_contacts(self, limit: int = 10) -> List[Dict]:
        """Récupère les contacts récents"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM contacts_clients ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Erreur contacts récents: {e}")
            return []
    
    # =======================================================
    # TEMPLATE ENGINE POUR RÉPONSES
    # =======================================================
    
    def generate_personalized_response(self, categorie: str, variables: Dict) -> Optional[str]:
        """Génère une réponse personnalisée basée sur un template"""
        try:
            # Récupérer le template
            response_template = self.get_response_by_category(categorie)
            if not response_template:
                return None
            
            # Remplacer les variables dans le template
            response_text = response_template['reponse_generique']
            
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                response_text = response_text.replace(placeholder, str(var_value))
            
            return response_text
            
        except Exception as e:
            print(f"❌ Erreur génération réponse: {e}")
            return None
    
    # =======================================================
    # HISTORIQUE DES INTERACTIONS
    # =======================================================
    
    def add_interaction_history(self, contact_id: int, action_type: str, 
                              old_value: str = None, new_value: str = None, 
                              notes: str = None, user_agent: str = 'System') -> bool:
        """Ajoute une entrée dans l'historique des interactions"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """INSERT INTO interactions_history 
                   (contact_id, action_type, old_value, new_value, notes, user_agent) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (contact_id, action_type, old_value, new_value, notes, user_agent)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Erreur ajout historique: {e}")
            return False
    
    def get_contact_history(self, contact_id: int) -> List[Dict]:
        """Récupère l'historique d'un contact"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """SELECT * FROM interactions_history 
                   WHERE contact_id = ? 
                   ORDER BY created_at DESC""",
                (contact_id,)
            )
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"❌ Erreur récupération historique: {e}")
            return []


# Fonction utilitaire pour initialiser la base de données
def init_support_database(db_path: str = None):
    """Initialise la base de données support"""
    try:
        manager = SupportDatabaseManager(db_path)
        print("✅ Base de données support initialisée avec succès")
        return manager
    except Exception as e:
        print(f"❌ Erreur initialisation base support: {e}")
        return None 
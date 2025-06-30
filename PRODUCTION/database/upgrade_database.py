#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de mise à jour de la base de données
Ajoute les tables pour la base de connaissances et l'intégration Notion
"""

import sqlite3
import os
from datetime import datetime


def upgrade_database(db_path='data/crm_ecommerce.db'):
    """Met à jour la base de données avec les nouvelles tables"""
    
    print("🔄 Mise à jour de la base de données...")
    
    try:
        # Créer une sauvegarde
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(db_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"📋 Sauvegarde créée: {backup_path}")
        
        # Connexion à la base
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Créer la table des réponses support
        print("📦 Création table support_responses...")
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
        
        # Index pour les réponses support
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_responses_categorie ON support_responses(categorie)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_responses_active ON support_responses(is_active)')
        
        # 2. Créer la table des contacts clients
        print("📦 Création table contacts_clients...")
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
                
                -- Champs techniques
                ticket_id TEXT UNIQUE,
                urgence INTEGER DEFAULT 1 CHECK (urgence BETWEEN 1 AND 5),
                sentiment TEXT,
                model_used TEXT DEFAULT 'claude-4-sonnet',
                quality_score REAL DEFAULT 0,
                response_time REAL DEFAULT 0,
                
                -- Intégration Notion
                notion_page_id TEXT,
                notion_sync_status TEXT DEFAULT 'pending',
                notion_last_sync DATETIME,
                
                -- Timestamps
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_at DATETIME,
                closed_at DATETIME,
                
                -- Assignation
                assigned_to TEXT DEFAULT 'IA Agent'
            )
        ''')
        
        # Index pour les contacts clients
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts_clients(email_client)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_statut ON contacts_clients(statut)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_categorie ON contacts_clients(categorie)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_created ON contacts_clients(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_ticket ON contacts_clients(ticket_id)')
        
        # 3. Créer la table historique des interactions
        print("📦 Création table interactions_history...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                user_agent TEXT DEFAULT 'System',
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts_clients(id)
            )
        ''')
        
        # 4. Créer la table d'intégration Notion
        print("📦 Création table notion_integration...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notion_integration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                notion_database_id TEXT NOT NULL,
                notion_page_id TEXT NOT NULL,
                sync_status TEXT DEFAULT 'pending',
                last_sync_at DATETIME,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts_clients(id)
            )
        ''')
        
        # 5. Créer les triggers
        print("⚙️ Création des triggers...")
        
        # Trigger pour mettre à jour updated_at
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_contacts_timestamp 
                AFTER UPDATE ON contacts_clients
            BEGIN
                UPDATE contacts_clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        
        # Trigger pour l'historique des changements de statut
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS log_contact_status_change 
                AFTER UPDATE OF statut ON contacts_clients
                WHEN OLD.statut != NEW.statut
            BEGIN
                INSERT INTO interactions_history (contact_id, action_type, old_value, new_value, notes)
                VALUES (NEW.id, 'status_change', OLD.statut, NEW.statut, 'Changement de statut automatique');
            END
        ''')
        
        # Trigger pour l'envoi de réponses
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS log_response_sent 
                AFTER UPDATE OF reponse_personnalisee ON contacts_clients
                WHEN OLD.reponse_personnalisee IS NULL AND NEW.reponse_personnalisee IS NOT NULL
            BEGIN
                INSERT INTO interactions_history (contact_id, action_type, new_value, notes)
                VALUES (NEW.id, 'response_sent', NEW.reponse_personnalisee, 'Réponse automatique générée');
            END
        ''')
        
        # 6. Créer les vues pour les statistiques
        print("📊 Création des vues statistiques...")
        
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS v_stats_categories AS
            SELECT 
                categorie,
                COUNT(*) as total_contacts,
                COUNT(CASE WHEN statut = 'nouveau' THEN 1 END) as nouveaux,
                COUNT(CASE WHEN statut = 'en_cours' THEN 1 END) as en_cours,
                COUNT(CASE WHEN statut = 'traite' THEN 1 END) as traites,
                COUNT(CASE WHEN statut = 'ferme' THEN 1 END) as fermes,
                AVG(quality_score) as score_qualite_moyen,
                AVG(response_time) as temps_reponse_moyen
            FROM contacts_clients 
            GROUP BY categorie
        ''')
        
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS v_dashboard_stats AS
            SELECT 
                COUNT(*) as total_contacts,
                COUNT(CASE WHEN statut = 'nouveau' THEN 1 END) as nouveaux,
                COUNT(CASE WHEN statut = 'en_cours' THEN 1 END) as en_cours,
                COUNT(CASE WHEN statut = 'traite' THEN 1 END) as traites,
                COUNT(CASE WHEN statut = 'ferme' THEN 1 END) as fermes,
                AVG(quality_score) as score_qualite_moyen,
                AVG(response_time) as temps_reponse_moyen,
                COUNT(CASE WHEN DATE(created_at) = DATE('now') THEN 1 END) as contacts_aujourdhui
            FROM contacts_clients
        ''')
        
        # 7. Insérer les réponses par défaut
        print("💬 Insertion des réponses support par défaut...")
        insert_default_responses(cursor)
        
        # 8. Valider les changements
        conn.commit()
        conn.close()
        
        print("✅ Base de données mise à jour avec succès !")
        print("📋 Nouvelles fonctionnalités disponibles :")
        print("   - Base de connaissances des réponses support")
        print("   - Gestion avancée des contacts clients")
        print("   - Intégration Notion")
        print("   - Historique des interactions")
        print("   - Vues statistiques")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        return False


def insert_default_responses(cursor):
    """Insère les réponses par défaut dans la base de connaissances"""
    
    # Vérifier si des réponses existent déjà
    cursor.execute("SELECT COUNT(*) FROM support_responses")
    if cursor.fetchone()[0] > 0:
        print("   Réponses support déjà présentes, saut de l'insertion")
        return
    
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
    
    print(f"   ✅ {len(default_responses)} réponses support insérées")


if __name__ == "__main__":
    print("🚀 Démarrage de la mise à jour de la base de données...")
    success = upgrade_database()
    
    if success:
        print("\n🎉 Mise à jour terminée avec succès !")
        print("Vous pouvez maintenant utiliser les nouvelles fonctionnalités.")
    else:
        print("\n❌ Erreur durant la mise à jour.")
        print("Vérifiez les logs ci-dessus pour plus de détails.") 
-- =======================================================
-- SCHÉMA BASE DE DONNÉES SUPPORT CLIENT AMÉLIORÉ
-- Système d'automatisation du support client e-commerce
-- =======================================================

-- =======================================================
-- 1. GESTION DES COMMANDES & PRODUITS
-- =======================================================

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    image_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_uid TEXT NOT NULL UNIQUE, -- ID visible par le client
    client_email TEXT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_purchase REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_orders_client_email ON orders(client_email);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- =======================================================
-- 2. BASE DE CONNAISSANCES "RÉPONSES SUPPORT"
-- =======================================================

CREATE TABLE IF NOT EXISTS support_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categorie TEXT NOT NULL,
    reponse_generique TEXT NOT NULL,
    tags TEXT, -- Pour filtrer et rechercher
    variables_template TEXT, -- Variables à remplacer (JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

-- Index pour la recherche rapide par catégorie
CREATE INDEX IF NOT EXISTS idx_support_responses_categorie ON support_responses(categorie);
CREATE INDEX IF NOT EXISTS idx_support_responses_active ON support_responses(is_active);

-- =======================================================
-- 3. BASE DE GESTION DES ÉCHANGES "CONTACTS CLIENTS"
-- =======================================================

CREATE TABLE IF NOT EXISTS contacts_clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_client TEXT NOT NULL,
    nom_prenom TEXT,
    order_id INTEGER, -- Remplacé par order_uid pour correspondre à la nouvelle table
    message_initial TEXT NOT NULL,
    categorie TEXT,
    reponse_personnalisee TEXT,
    statut TEXT DEFAULT 'nouveau' CHECK (statut IN ('nouveau', 'en_cours', 'traite', 'ferme', 'escalade')),
    
    -- Champs techniques
    ticket_id TEXT UNIQUE,
    urgence INTEGER DEFAULT 1 CHECK (urgence BETWEEN 1 AND 5),
    sentiment TEXT, -- positif, neutre, negatif
    model_used TEXT DEFAULT 'claude-4-sonnet',
    quality_score REAL DEFAULT 0,
    response_time REAL DEFAULT 0,
    
    -- Intégration Notion
    notion_page_id TEXT, -- ID de la page Notion correspondante
    notion_sync_status TEXT DEFAULT 'pending', -- pending, synced, error
    notion_last_sync DATETIME,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    closed_at DATETIME,
    
    -- Assignation
    assigned_to TEXT DEFAULT 'IA Agent'
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts_clients(email_client);
CREATE INDEX IF NOT EXISTS idx_contacts_statut ON contacts_clients(statut);
CREATE INDEX IF NOT EXISTS idx_contacts_categorie ON contacts_clients(categorie);
CREATE INDEX IF NOT EXISTS idx_contacts_created ON contacts_clients(created_at);
CREATE INDEX IF NOT EXISTS idx_contacts_ticket ON contacts_clients(ticket_id);

-- =======================================================
-- 4. TABLE HISTORIQUE DES INTERACTIONS
-- =======================================================

CREATE TABLE IF NOT EXISTS interactions_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    action_type TEXT NOT NULL, -- 'status_change', 'response_sent', 'note_added', 'escalated'
    old_value TEXT,
    new_value TEXT,
    user_agent TEXT DEFAULT 'System',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts_clients(id)
);

-- =======================================================
-- 5. TABLE NOTION INTEGRATION
-- =======================================================

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
);

-- =======================================================
-- 6. TRIGGERS AUTOMATIQUES
-- =======================================================

-- Trigger pour mettre à jour updated_at sur contacts_clients
CREATE TRIGGER IF NOT EXISTS update_contacts_timestamp 
    AFTER UPDATE ON contacts_clients
BEGIN
    UPDATE contacts_clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger pour enregistrer les changements de statut
CREATE TRIGGER IF NOT EXISTS log_contact_status_change 
    AFTER UPDATE OF statut ON contacts_clients
    WHEN OLD.statut != NEW.statut
BEGIN
    INSERT INTO interactions_history (contact_id, action_type, old_value, new_value, notes)
    VALUES (NEW.id, 'status_change', OLD.statut, NEW.statut, 'Changement de statut automatique');
END;

-- Trigger pour enregistrer les réponses
CREATE TRIGGER IF NOT EXISTS log_response_sent 
    AFTER UPDATE OF reponse_personnalisee ON contacts_clients
    WHEN OLD.reponse_personnalisee IS NULL AND NEW.reponse_personnalisee IS NOT NULL
BEGIN
    INSERT INTO interactions_history (contact_id, action_type, new_value, notes)
    VALUES (NEW.id, 'response_sent', NEW.reponse_personnalisee, 'Réponse automatique générée');
END;

-- =======================================================
-- 7. DONNÉES INITIALES - RÉPONSES SUPPORT
-- =======================================================

INSERT OR REPLACE INTO support_responses (id, categorie, reponse_generique, tags, variables_template) VALUES
(1, 'retard_livraison', 
 'Bonjour {{nom_client}},\n\nNous avons bien reçu votre message concernant le retard de livraison de votre commande {{id_commande}}.\n\nNous nous excusons sincèrement pour ce désagrément. Nous avons immédiatement contacté notre transporteur pour localiser votre colis.\n\n{{info_suivi}}\n\nNous restons à votre disposition pour tout complément d''information.\n\nCordialement,\nService Client', 
 'livraison,retard,colis,transporteur',
 '{"nom_client": "string", "id_commande": "number", "info_suivi": "string"}'),

(2, 'remboursement',
 'Bonjour {{nom_client}},\n\nNous avons bien reçu votre demande de remboursement pour la commande {{id_commande}}.\n\n{{motif_remboursement}}\n\nVotre remboursement sera traité dans un délai de 3 à 5 jours ouvrés. Vous recevrez une confirmation par email une fois le remboursement effectué.\n\nNous nous excusons pour la gêne occasionnée.\n\nCordialement,\nService Client',
 'remboursement,retour,annulation',
 '{"nom_client": "string", "id_commande": "number", "motif_remboursement": "string"}'),

(3, 'produit_defectueux',
 'Bonjour {{nom_client}},\n\nNous sommes désolés d''apprendre que le produit {{nom_produit}} de votre commande {{id_commande}} présente un défaut.\n\nPour traiter votre réclamation dans les meilleurs délais :\n{{procedure_retour}}\n\nUn nouveau produit vous sera expédié dès réception de l''article défectueux.\n\nNous vous remercions de votre compréhension.\n\nCordialement,\nService Client',
 'defectueux,qualite,remplacement,garantie',
 '{"nom_client": "string", "nom_produit": "string", "id_commande": "number", "procedure_retour": "string"}'),

(4, 'information_commande',
 'Bonjour {{nom_client}},\n\nConcernant votre commande {{id_commande}} :\n\n{{details_commande}}\n\nVous pouvez suivre l''évolution de votre commande en temps réel sur notre site web dans la section "Mes commandes".\n\nN''hésitez pas à nous contacter si vous avez d''autres questions.\n\nCordialement,\nService Client',
 'commande,statut,suivi,information',
 '{"nom_client": "string", "id_commande": "number", "details_commande": "string"}'),

(5, 'reclamation',
 'Bonjour {{nom_client}},\n\nNous avons bien pris note de votre réclamation concernant {{objet_reclamation}}.\n\nVotre satisfaction est notre priorité. Nous étudions votre dossier avec attention et vous proposerons une solution adaptée dans les plus brefs délais.\n\n{{action_corrective}}\n\nNous vous remercions de nous avoir fait part de votre mécontentement, cela nous aide à améliorer nos services.\n\nCordialement,\nService Client',
 'reclamation,insatisfaction,amelioration',
 '{"nom_client": "string", "objet_reclamation": "string", "action_corrective": "string"}');

-- =======================================================
-- 8. VUES UTILES POUR REPORTING
-- =======================================================

-- Vue pour les statistiques par catégorie
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
GROUP BY categorie;

-- Vue pour le dashboard principal
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
FROM contacts_clients; 
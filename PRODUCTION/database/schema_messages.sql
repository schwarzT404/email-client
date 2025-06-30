-- Schéma pour le système de messages avec statuts
-- Support client e-commerce avec suivi temps réel

-- Table pour stocker les messages avec statuts
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
);

-- Table pour l'historique des changements de statut
CREATE TABLE IF NOT EXISTS message_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    changed_by TEXT DEFAULT 'System',
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

-- Table pour les comptes emails d'entreprise pré-enregistrés
CREATE TABLE IF NOT EXISTS enterprise_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    poste TEXT,
    departement TEXT,
    entreprise TEXT,
    type_client TEXT DEFAULT 'entreprise' CHECK (type_client IN ('entreprise', 'particulier', 'vip')),
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_message_at DATETIME
);

-- Table pour les scénarios de simulation
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
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_client_email ON messages(client_email);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_category ON messages(category);
CREATE INDEX IF NOT EXISTS idx_enterprise_accounts_email ON enterprise_accounts(email);

-- Trigger pour mettre à jour updated_at automatiquement
CREATE TRIGGER IF NOT EXISTS update_messages_timestamp 
    AFTER UPDATE ON messages
BEGIN
    UPDATE messages SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger pour enregistrer l'historique des changements de statut
CREATE TRIGGER IF NOT EXISTS log_status_change 
    AFTER UPDATE OF status ON messages
    WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO message_history (message_id, previous_status, new_status, notes)
    VALUES (NEW.id, OLD.status, NEW.status, 'Status changed automatically');
END; 
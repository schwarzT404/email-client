-- Création de la base de données CRM E-commerce SQLite
-- Table des clients
CREATE TABLE IF NOT EXISTS client (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser la recherche par email
CREATE INDEX IF NOT EXISTS idx_client_email ON client(email);

-- Table des commandes
CREATE TABLE IF NOT EXISTS commande (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    montant REAL NOT NULL,
    nb_articles INTEGER NOT NULL,
    id_client INTEGER NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_client) REFERENCES client(id) ON DELETE CASCADE
);

-- Index pour optimiser la recherche par client et date
CREATE INDEX IF NOT EXISTS idx_commande_client ON commande(id_client);
CREATE INDEX IF NOT EXISTS idx_commande_date ON commande(date);

-- Insertion de données d'exemple pour les tests
INSERT INTO client (email, nom, prenom) VALUES 
('jean.dupont@email.com', 'Dupont', 'Jean'),
('marie.martin@email.com', 'Martin', 'Marie'),
('pierre.durand@email.com', 'Durand', 'Pierre');

INSERT INTO commande (date, montant, nb_articles, id_client) VALUES 
('2024-01-15', 89.99, 2, 1),
('2024-01-16', 156.50, 4, 2),
('2024-01-17', 45.00, 1, 1),
('2024-01-18', 203.75, 6, 3); 
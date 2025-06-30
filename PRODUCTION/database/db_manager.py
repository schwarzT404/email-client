"""
Gestionnaire de base de données SQLite pour le CRM E-commerce
"""
import sqlite3
import os
from typing import Dict, List, Optional, Tuple
from config import DATABASE_CONFIG


class DatabaseManager:
    """Gestionnaire pour les opérations de base de données SQLite"""
    
    def __init__(self):
        self.db_path = DATABASE_CONFIG['database_path']
        self.connection = None
        self.connect()
    
    def connect(self):
        """Établit la connexion à la base de données SQLite"""
        try:
            # Créer le répertoire data s'il n'existe pas
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connexion SQLite avec support multi-thread
            self.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False  # Permettre l'usage multi-thread
            )
            self.connection.row_factory = sqlite3.Row  # Pour avoir des résultats sous forme de dictionnaire
            
            # Activer les clés étrangères
            self.connection.execute("PRAGMA foreign_keys = ON")
            print("✅ Connexion à la base de données SQLite établie (multi-thread)")
        except sqlite3.Error as e:
            print(f"❌ Erreur de connexion à la base de données: {e}")
            raise
    
    def disconnect(self):
        """Ferme la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            print("🔌 Connexion fermée")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Exécute une requête SELECT et retourne les résultats"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            results = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return results
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de l'exécution de la requête: {e}")
            return []
    
    def execute_insert_update(self, query: str, params: Optional[Tuple] = None) -> bool:
        """Exécute une requête INSERT/UPDATE/DELETE"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            cursor.close()
            return True
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de l'exécution de la requête: {e}")
            self.connection.rollback()
            return False
    
    # === GESTION DES CLIENTS ===
    
    def get_client_by_email(self, email: str) -> Optional[Dict]:
        """Récupère un client par son email"""
        query = "SELECT * FROM client WHERE email = ?"
        results = self.execute_query(query, (email,))
        return results[0] if results else None
    
    def get_client_by_id(self, client_id: int) -> Optional[Dict]:
        """Récupère un client par son ID"""
        query = "SELECT * FROM client WHERE id = ?"
        results = self.execute_query(query, (client_id,))
        return results[0] if results else None
    
    def create_client(self, nom: str, prenom: str, email: str, type_client: str = "standard") -> Optional[int]:
        """Crée un nouveau client et retourne son ID"""
        try:
            cursor = self.connection.cursor()
            # La table client n'a pas de colonne type_client
            query = "INSERT INTO client (nom, prenom, email) VALUES (?, ?, ?)"
            cursor.execute(query, (nom, prenom, email))
            self.connection.commit()
            client_id = cursor.lastrowid
            cursor.close()
            print(f"✅ Client créé avec ID: {client_id}")
            return client_id
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la création du client: {e}")
            self.connection.rollback()
            return None
    
    def get_all_clients(self) -> List[Dict]:
        """Récupère tous les clients"""
        query = "SELECT * FROM client ORDER BY nom, prenom"
        return self.execute_query(query)
    
    # === GESTION DES COMMANDES ===
    
    def get_orders_by_client_id(self, client_id: int) -> List[Tuple]:
        """Récupère les commandes d'un client (format tuple pour compatibilité)"""
        try:
            cursor = self.connection.cursor()
            query = "SELECT * FROM commande WHERE id_client = ? ORDER BY date DESC"
            cursor.execute(query, (client_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la récupération des commandes: {e}")
            return []
    
    def get_commandes_by_client(self, client_id: int) -> List[Dict]:
        """Récupère toutes les commandes d'un client"""
        query = """
        SELECT c.*, cl.nom, cl.prenom, cl.email 
        FROM commande c 
        JOIN client cl ON c.id_client = cl.id 
        WHERE c.id_client = %s 
        ORDER BY c.date DESC
        """
        return self.execute_query(query, (client_id,))
    
    def get_commande_by_id(self, commande_id: int) -> Optional[Dict]:
        """Récupère une commande par son ID avec les infos client"""
        query = """
        SELECT c.*, cl.nom, cl.prenom, cl.email 
        FROM commande c 
        JOIN client cl ON c.id_client = cl.id 
        WHERE c.id = %s
        """
        results = self.execute_query(query, (commande_id,))
        return results[0] if results else None
    
    def create_commande(self, date: str, montant: float, nb_articles: int, id_client: int) -> bool:
        """Crée une nouvelle commande"""
        query = "INSERT INTO commande (date, montant, nb_articles, id_client) VALUES (%s, %s, %s, %s)"
        return self.execute_insert_update(query, (date, montant, nb_articles, id_client))
    
    def get_recent_commandes(self, limit: int = 50) -> List[Dict]:
        """Récupère les commandes récentes avec infos client"""
        query = """
        SELECT c.*, cl.nom, cl.prenom, cl.email 
        FROM commande c 
        JOIN client cl ON c.id_client = cl.id 
        ORDER BY c.date DESC 
        LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    # === STATISTIQUES ET RAPPORTS ===
    
    def get_client_stats(self, client_id: int) -> Dict:
        """Récupère les statistiques d'un client"""
        query = """
        SELECT 
            COUNT(*) as nb_commandes,
            SUM(montant) as total_achats,
            AVG(montant) as montant_moyen,
            SUM(nb_articles) as total_articles,
            MAX(date) as derniere_commande
        FROM commande 
        WHERE id_client = %s
        """
        results = self.execute_query(query, (client_id,))
        return results[0] if results else {}
    
    def search_clients_commandes(self, search_term: str) -> List[Dict]:
        """Recherche dans les clients et commandes"""
        query = """
        SELECT DISTINCT c.*, cl.nom, cl.prenom, cl.email 
        FROM commande c 
        JOIN client cl ON c.id_client = cl.id 
        WHERE cl.nom LIKE %s OR cl.prenom LIKE %s OR cl.email LIKE %s
        ORDER BY c.date DESC
        """
        search_pattern = f"%{search_term}%"
        return self.execute_query(query, (search_pattern, search_pattern, search_pattern))


# Fonction utilitaire pour initialiser la base de données
def init_database():
    """Initialise la base de données SQLite avec le schéma"""
    try:
        # Créer le répertoire data s'il n'existe pas
        db_path = DATABASE_CONFIG['database_path']
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Lire et exécuter le fichier SQL
        with open('database/schema.sql', 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Connexion à SQLite
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Activer les clés étrangères
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Exécuter le script SQL complet
        cursor.executescript(sql_script)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Base de données SQLite initialisée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False


if __name__ == "__main__":
    # Test de connexion
    db = DatabaseManager()
    clients = db.get_all_clients()
    print(f"📊 Nombre de clients: {len(clients)}")
    db.disconnect() 
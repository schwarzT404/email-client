"""
Configuration du projet - Variables d'environnement
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration de la base de données SQLite
DATABASE_CONFIG = {
    'database_path': os.getenv('DB_PATH', 'data/crm_ecommerce.db')
}

# Configuration Notion
NOTION_CONFIG = {
    'token': os.getenv('NOTION_TOKEN'),
    'base_reponses_id': os.getenv('NOTION_BASE_REPONSES_ID'),
    'base_contacts_id': os.getenv('NOTION_BASE_CONTACTS_ID')
}

# Configuration OpenAI (optionnel pour l'IA)
OPENAI_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY')
}

# Vérification des variables obligatoires
def check_config():
    """Vérifie que toutes les variables d'environnement nécessaires sont définies"""
    missing_vars = []
    
    if not NOTION_CONFIG['token']:
        missing_vars.append('NOTION_TOKEN')
    
    if missing_vars:
        raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
    
    return True 
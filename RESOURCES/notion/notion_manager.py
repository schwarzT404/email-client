"""
Gestionnaire Notion pour les bases de connaissances et suivi des tickets
"""
from notion_client import Client
from typing import Dict, List, Optional
import json
from datetime import datetime
from config import NOTION_CONFIG


class NotionManager:
    """Gestionnaire pour les opérations Notion"""
    
    def __init__(self):
        if not NOTION_CONFIG['token']:
            raise ValueError("Token Notion manquant dans la configuration")
        
        self.client = Client(auth=NOTION_CONFIG['token'])
        self.base_reponses_id = NOTION_CONFIG['base_reponses_id']
        self.base_contacts_id = NOTION_CONFIG['base_contacts_id']
    
    # === GESTION BASE RÉPONSES SUPPORT ===
    
    def get_reponses_by_categorie(self, categorie: str) -> List[Dict]:
        """Récupère les réponses type par catégorie"""
        try:
            response = self.client.databases.query(
                database_id=self.base_reponses_id,
                filter={
                    "property": "catégorie",
                    "select": {
                        "equals": categorie
                    }
                }
            )
            
            results = []
            for page in response['results']:
                props = page['properties']
                results.append({
                    'id': page['id'],
                    'categorie': self._extract_select_value(props.get('catégorie')),
                    'reponse_generique': self._extract_rich_text(props.get('réponse_générique'))
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Erreur récupération réponses: {e}")
            return []
    
    def create_reponse_type(self, categorie: str, reponse_generique: str) -> bool:
        """Crée une nouvelle réponse type"""
        try:
            self.client.pages.create(
                parent={"database_id": self.base_reponses_id},
                properties={
                    "catégorie": {
                        "select": {"name": categorie}
                    },
                    "réponse_générique": {
                        "rich_text": [{"text": {"content": reponse_generique}}]
                    }
                }
            )
            return True
            
        except Exception as e:
            print(f"❌ Erreur création réponse: {e}")
            return False
    
    def get_all_categories(self) -> List[str]:
        """Récupère toutes les catégories disponibles"""
        try:
            response = self.client.databases.query(database_id=self.base_reponses_id)
            categories = set()
            
            for page in response['results']:
                props = page['properties']
                cat = self._extract_select_value(props.get('catégorie'))
                if cat:
                    categories.add(cat)
            
            return list(categories)
            
        except Exception as e:
            print(f"❌ Erreur récupération catégories: {e}")
            return []
    
    # === GESTION BASE CONTACTS CLIENTS ===
    
    def create_contact_ticket(self, email_client: str, nom_prenom: str, 
                            id_commande: int, message_initial: str, 
                            categorie: str = "Non classé") -> Optional[str]:
        """Crée un nouveau ticket de contact client"""
        try:
            response = self.client.pages.create(
                parent={"database_id": self.base_contacts_id},
                properties={
                    "email_client": {
                        "email": email_client
                    },
                    "nom_prenom": {
                        "title": [{"text": {"content": nom_prenom}}]
                    },
                    "id_commande": {
                        "number": id_commande
                    },
                    "message_initial": {
                        "rich_text": [{"text": {"content": message_initial}}]
                    },
                    "catégorie": {
                        "select": {"name": categorie}
                    },
                    "statut": {
                        "select": {"name": "Nouveau"}
                    }
                }
            )
            
            return response['id']
            
        except Exception as e:
            print(f"❌ Erreur création ticket: {e}")
            return None
    
    def update_ticket_response(self, ticket_id: str, reponse_personnalisee: str, 
                              statut: str = "Traité") -> bool:
        """Met à jour un ticket avec la réponse personnalisée"""
        try:
            self.client.pages.update(
                page_id=ticket_id,
                properties={
                    "réponse_personnalisée": {
                        "rich_text": [{"text": {"content": reponse_personnalisee}}]
                    },
                    "statut": {
                        "select": {"name": statut}
                    }
                }
            )
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour ticket: {e}")
            return False
    
    def get_pending_tickets(self) -> List[Dict]:
        """Récupère les tickets en attente de traitement"""
        try:
            response = self.client.databases.query(
                database_id=self.base_contacts_id,
                filter={
                    "or": [
                        {
                            "property": "statut",
                            "select": {"equals": "Nouveau"}
                        },
                        {
                            "property": "statut",
                            "select": {"equals": "En cours"}
                        }
                    ]
                },
                sorts=[
                    {
                        "timestamp": "created_time",
                        "direction": "descending"
                    }
                ]
            )
            
            results = []
            for page in response['results']:
                props = page['properties']
                results.append({
                    'id': page['id'],
                    'email_client': self._extract_email(props.get('email_client')),
                    'nom_prenom': self._extract_title(props.get('nom_prenom')),
                    'id_commande': self._extract_number(props.get('id_commande')),
                    'message_initial': self._extract_rich_text(props.get('message_initial')),
                    'categorie': self._extract_select_value(props.get('catégorie')),
                    'statut': self._extract_select_value(props.get('statut')),
                    'created_time': page['created_time']
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Erreur récupération tickets: {e}")
            return []
    
    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict]:
        """Récupère un ticket par son ID"""
        try:
            page = self.client.pages.retrieve(page_id=ticket_id)
            props = page['properties']
            
            return {
                'id': page['id'],
                'email_client': self._extract_email(props.get('email_client')),
                'nom_prenom': self._extract_title(props.get('nom_prenom')),
                'id_commande': self._extract_number(props.get('id_commande')),
                'message_initial': self._extract_rich_text(props.get('message_initial')),
                'categorie': self._extract_select_value(props.get('catégorie')),
                'reponse_personnalisee': self._extract_rich_text(props.get('réponse_personnalisée')),
                'statut': self._extract_select_value(props.get('statut')),
                'created_time': page['created_time']
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération ticket: {e}")
            return None
    
    # === MÉTHODES UTILITAIRES ===
    
    def _extract_rich_text(self, prop) -> str:
        """Extrait le texte d'une propriété rich_text"""
        if not prop or not prop.get('rich_text'):
            return ""
        return "".join([t['plain_text'] for t in prop['rich_text']])
    
    def _extract_title(self, prop) -> str:
        """Extrait le texte d'une propriété title"""
        if not prop or not prop.get('title'):
            return ""
        return "".join([t['plain_text'] for t in prop['title']])
    
    def _extract_select_value(self, prop) -> str:
        """Extrait la valeur d'une propriété select"""
        if not prop or not prop.get('select'):
            return ""
        return prop['select']['name'] if prop['select'] else ""
    
    def _extract_email(self, prop) -> str:
        """Extrait la valeur d'une propriété email"""
        if not prop:
            return ""
        return prop.get('email', "")
    
    def _extract_number(self, prop) -> int:
        """Extrait la valeur d'une propriété number"""
        if not prop:
            return 0
        return prop.get('number', 0) or 0
    
    # === INITIALISATION DES BASES ===
    
    def init_reponses_base(self):
        """Initialise la base avec des réponses types"""
        reponses_types = [
            {
                "categorie": "Retard de livraison",
                "reponse": "Bonjour {nom_client},\n\nNous nous excusons pour le retard de votre commande #{id_commande}. Nous vérifions actuellement le statut de votre livraison avec notre transporteur. Vous recevrez une mise à jour dans les 24h.\n\nCordialement,\nL'équipe Support"
            },
            {
                "categorie": "Remboursement",
                "reponse": "Bonjour {nom_client},\n\nNous avons bien reçu votre demande de remboursement pour la commande #{id_commande} d'un montant de {montant}€. Le remboursement sera traité sous 3-5 jours ouvrés.\n\nCordialement,\nL'équipe Support"
            },
            {
                "categorie": "Produit défectueux",
                "reponse": "Bonjour {nom_client},\n\nNous sommes désolés d'apprendre que votre commande #{id_commande} présente un défaut. Nous allons immédiatement vous envoyer un produit de remplacement. Merci de conserver le produit défectueux.\n\nCordialement,\nL'équipe Support"
            },
            {
                "categorie": "Information commande",
                "reponse": "Bonjour {nom_client},\n\nVoici les détails de votre commande #{id_commande} :\n- Date : {date_commande}\n- Montant : {montant}€\n- Articles : {nb_articles}\n\nCordialement,\nL'équipe Support"
            }
        ]
        
        for reponse in reponses_types:
            self.create_reponse_type(reponse["categorie"], reponse["reponse"])
            print(f"✅ Réponse type créée : {reponse['categorie']}")


if __name__ == "__main__":
    # Test de connexion
    try:
        notion = NotionManager()
        categories = notion.get_all_categories()
        print(f"📊 Catégories disponibles: {categories}")
        
        # tickets = notion.get_pending_tickets()
        # print(f"📋 Tickets en attente: {len(tickets)}")
        
    except Exception as e:
        print(f"❌ Erreur de test: {e}") 
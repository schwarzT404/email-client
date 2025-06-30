"""
Agent IA pour l'automatisation du support client e-commerce
"""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import openai

from database.db_manager import DatabaseManager
from notion.notion_manager import NotionManager
from config import OPENAI_CONFIG


class SupportAgent:
    """Agent IA pour automatiser les réponses du support client"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.notion = NotionManager()
        
        # Configuration OpenAI (optionnel)
        if OPENAI_CONFIG.get('api_key'):
            openai.api_key = OPENAI_CONFIG['api_key']
            self.ai_enabled = True
        else:
            self.ai_enabled = False
            print("⚠️ OpenAI non configuré - mode automatique simple activé")
    
    def process_customer_message(self, email: str, message: str, 
                               commande_id: Optional[int] = None) -> Dict:
        """Traite un message client et génère une réponse automatique"""
        
        print(f"📨 Traitement du message de {email}")
        
        # 1. Récupérer les infos client
        client = self.db.get_client_by_email(email)
        if not client:
            return {
                'success': False,
                'error': 'Client non trouvé dans la base de données'
            }
        
        # 2. Récupérer les infos commande si fournie
        commande = None
        if commande_id:
            commande = self.db.get_commande_by_id(commande_id)
        else:
            # Essayer d'extraire l'ID de commande du message
            commande_id = self._extract_order_id(message)
            if commande_id:
                commande = self.db.get_commande_by_id(commande_id)
        
        # 3. Classifier le message
        categorie = self._classify_message(message)
        
        # 4. Créer le ticket dans Notion
        nom_prenom = f"{client['prenom']} {client['nom']}"
        ticket_id = self.notion.create_contact_ticket(
            email_client=email,
            nom_prenom=nom_prenom,
            id_commande=commande_id or 0,
            message_initial=message,
            categorie=categorie
        )
        
        if not ticket_id:
            return {
                'success': False,
                'error': 'Erreur lors de la création du ticket'
            }
        
        # 5. Générer la réponse personnalisée
        reponse_personnalisee = self._generate_response(
            categorie=categorie,
            client=client,
            commande=commande,
            message=message
        )
        
        # 6. Mettre à jour le ticket avec la réponse
        success = self.notion.update_ticket_response(
            ticket_id=ticket_id,
            reponse_personnalisee=reponse_personnalisee,
            statut="Traité automatiquement"
        )
        
        return {
            'success': success,
            'ticket_id': ticket_id,
            'categorie': categorie,
            'reponse': reponse_personnalisee,
            'client_info': {
                'nom': nom_prenom,
                'email': email
            },
            'commande_info': commande if commande else None
        }
    
    def _extract_order_id(self, message: str) -> Optional[int]:
        """Extrait l'ID de commande du message"""
        # Recherche des patterns courants pour les numéros de commande
        patterns = [
            r'commande[^\d]*(\d+)',
            r'#(\d+)',
            r'n[°u]m[eé]ro[^\d]*(\d+)',
            r'order[^\d]*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    def _classify_message(self, message: str) -> str:
        """Classifie le message selon les catégories définies"""
        message_lower = message.lower()
        
        # Mots-clés par catégorie
        categories = {
            "Retard de livraison": [
                "retard", "livraison", "délai", "reçu", "arrivé", "transporteur", 
                "suivi", "où est", "quand", "expédition"
            ],
            "Remboursement": [
                "remboursement", "rembourser", "annuler", "argent", "paiement", 
                "remboursé", "reçu", "satisfait", "retour"
            ],
            "Produit défectueux": [
                "défectueux", "cassé", "abîmé", "défaut", "problème", "marche pas", 
                "fonctionne pas", "endommagé", "qualité", "mauvais état"
            ],
            "Information commande": [
                "information", "détail", "statut", "état", "facture", "reçu", 
                "confirmation", "résumé", "liste", "contenu"
            ]
        }
        
        # Score par catégorie
        scores = {}
        for categorie, mots_cles in categories.items():
            score = sum(1 for mot in mots_cles if mot in message_lower)
            if score > 0:
                scores[categorie] = score
        
        # Retourner la catégorie avec le score le plus élevé
        if scores:
            return max(scores, key=scores.get)
        
        return "Non classé"
    
    def _generate_response(self, categorie: str, client: Dict, 
                          commande: Optional[Dict], message: str) -> str:
        """Génère une réponse personnalisée"""
        
        # Récupérer le template de réponse
        reponses_templates = self.notion.get_reponses_by_categorie(categorie)
        
        if not reponses_templates:
            return self._generate_default_response(client, commande)
        
        template = reponses_templates[0]['reponse_generique']
        
        # Variables de personnalisation
        variables = {
            'nom_client': f"{client['prenom']} {client['nom']}",
            'prenom_client': client['prenom'],
            'email_client': client['email']
        }
        
        if commande:
            variables.update({
                'id_commande': str(commande['id']),
                'date_commande': str(commande['date']),
                'montant': f"{commande['montant']:.2f}",
                'nb_articles': str(commande['nb_articles'])
            })
        else:
            variables.update({
                'id_commande': "N/A",
                'date_commande': "N/A",
                'montant': "N/A",
                'nb_articles': "N/A"
            })
        
        # Remplacer les variables dans le template
        reponse = template
        for var, value in variables.items():
            reponse = reponse.replace(f'{{{var}}}', value)
        
        # Amélioration avec IA si disponible
        if self.ai_enabled:
            reponse = self._enhance_with_ai(reponse, message, categorie)
        
        return reponse
    
    def _generate_default_response(self, client: Dict, commande: Optional[Dict]) -> str:
        """Génère une réponse par défaut"""
        nom = f"{client['prenom']} {client['nom']}"
        
        reponse = f"Bonjour {nom},\n\n"
        reponse += "Nous avons bien reçu votre message et nous vous remercions de nous avoir contactés.\n\n"
        
        if commande:
            reponse += f"Concernant votre commande #{commande['id']} du {commande['date']} "
            reponse += f"d'un montant de {commande['montant']}€, "
        
        reponse += "notre équipe va analyser votre demande et vous répondra dans les plus brefs délais.\n\n"
        reponse += "Cordialement,\nL'équipe Support"
        
        return reponse
    
    def _enhance_with_ai(self, base_response: str, original_message: str, 
                        category: str) -> str:
        """Améliore la réponse avec l'IA OpenAI"""
        try:
            prompt = f"""
            Tu es un agent du support client e-commerce. 
            
            Message client: "{original_message}"
            Catégorie détectée: {category}
            Réponse de base: "{base_response}"
            
            Améliore cette réponse pour qu'elle soit:
            - Plus personnalisée selon le message du client
            - Empathique et professionnelle
            - Concise mais complète
            
            Garde le même format et la signature "L'équipe Support".
            Réponse améliorée:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            enhanced_response = response.choices[0].message.content.strip()
            return enhanced_response
            
        except Exception as e:
            print(f"⚠️ Erreur amélioration IA: {e}")
            return base_response
    
    def process_pending_tickets(self) -> List[Dict]:
        """Traite tous les tickets en attente"""
        tickets = self.notion.get_pending_tickets()
        results = []
        
        print(f"🔄 Traitement de {len(tickets)} tickets en attente")
        
        for ticket in tickets:
            try:
                result = self.process_customer_message(
                    email=ticket['email_client'],
                    message=ticket['message_initial'],
                    commande_id=ticket['id_commande'] if ticket['id_commande'] > 0 else None
                )
                
                result['original_ticket_id'] = ticket['id']
                results.append(result)
                
                print(f"✅ Ticket {ticket['id']} traité - Catégorie: {result.get('categorie')}")
                
            except Exception as e:
                print(f"❌ Erreur traitement ticket {ticket['id']}: {e}")
                results.append({
                    'success': False,
                    'original_ticket_id': ticket['id'],
                    'error': str(e)
                })
        
        return results
    
    def get_statistics(self) -> Dict:
        """Récupère les statistiques du support"""
        tickets = self.notion.get_pending_tickets()
        
        # Compter par catégorie
        categories = {}
        for ticket in tickets:
            cat = ticket['categorie'] or 'Non classé'
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_tickets_pending': len(tickets),
            'categories_breakdown': categories,
            'ai_enabled': self.ai_enabled
        }


if __name__ == "__main__":
    # Test de l'agent
    agent = SupportAgent()
    
    # Test avec un message d'exemple
    test_result = agent.process_customer_message(
        email="jean.dupont@email.com",
        message="Bonjour, je n'ai toujours pas reçu ma commande #1. Pouvez-vous me dire où elle en est ?",
        commande_id=1
    )
    
    print("\n=== RÉSULTAT DU TEST ===")
    print(f"Succès: {test_result['success']}")
    if test_result['success']:
        print(f"Catégorie: {test_result['categorie']}")
        print(f"Réponse générée:\n{test_result['reponse']}")
    else:
        print(f"Erreur: {test_result['error']}")
    
    # Statistiques
    stats = agent.get_statistics()
    print(f"\n📊 Statistiques: {stats}")
    
    agent.db.disconnect() 
"""
Script principal pour l'automatisation du support client e-commerce
"""
import argparse
import sys
from datetime import datetime

from database.db_manager import DatabaseManager, init_database
from notion.notion_manager import NotionManager
from automation.support_agent import SupportAgent
from config import check_config


def setup_system():
    """Initialise le système complet"""
    print("🚀 Initialisation du système d'automatisation du support client")
    
    try:
        # Vérifier la configuration
        check_config()
        
        # Initialiser la base de données
        print("\n📊 Initialisation de la base de données...")
        if init_database():
            print("✅ Base de données initialisée")
        else:
            print("❌ Erreur lors de l'initialisation de la base de données")
            return False
        
        # Initialiser les bases Notion
        print("\n📝 Initialisation des bases Notion...")
        notion = NotionManager()
        notion.init_reponses_base()
        
        print("✅ Système initialisé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False


def process_single_message(email: str, message: str, commande_id: int = None):
    """Traite un seul message client"""
    print(f"\n📨 Traitement du message de {email}")
    
    try:
        agent = SupportAgent()
        result = agent.process_customer_message(email, message, commande_id)
        
        if result['success']:
            print("✅ Message traité avec succès!")
            print(f"Catégorie détectée: {result['categorie']}")
            print(f"Ticket créé: {result['ticket_id']}")
            print("\n📝 Réponse générée:")
            print("-" * 50)
            print(result['reponse'])
            print("-" * 50)
        else:
            print(f"❌ Erreur: {result['error']}")
        
        agent.db.disconnect()
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        return {'success': False, 'error': str(e)}


def process_pending_tickets():
    """Traite tous les tickets en attente"""
    print("\n🔄 Traitement des tickets en attente")
    
    try:
        agent = SupportAgent()
        results = agent.process_pending_tickets()
        
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        print(f"\n📊 Résultats:")
        print(f"Total traités: {total_count}")
        print(f"Succès: {success_count}")
        print(f"Échecs: {total_count - success_count}")
        
        agent.db.disconnect()
        return results
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        return []


def show_statistics():
    """Affiche les statistiques du système"""
    print("\n📊 Statistiques du système")
    
    try:
        # Statistiques base de données
        db = DatabaseManager()
        clients = db.get_all_clients()
        commandes_recentes = db.get_recent_commandes(limit=10)
        
        print(f"\n🗄️ Base de données:")
        print(f"  Clients total: {len(clients)}")
        print(f"  Commandes récentes: {len(commandes_recentes)}")
        
        # Statistiques support
        agent = SupportAgent()
        stats = agent.get_statistics()
        
        print(f"\n🎫 Support:")
        print(f"  Tickets en attente: {stats['total_tickets_pending']}")
        print(f"  IA activée: {'✅' if stats['ai_enabled'] else '❌'}")
        
        if stats['categories_breakdown']:
            print("  Répartition par catégorie:")
            for cat, count in stats['categories_breakdown'].items():
                print(f"    - {cat}: {count}")
        
        db.disconnect()
        agent.db.disconnect()
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des statistiques: {e}")


def interactive_mode():
    """Mode interactif pour tester le système"""
    print("\n🎮 Mode interactif - Support client automatisé")
    print("Tapez 'quit' pour quitter\n")
    
    agent = SupportAgent()
    
    try:
        while True:
            print("-" * 60)
            email = input("📧 Email du client: ")
            if email.lower() == 'quit':
                break
            
            message = input("💬 Message du client: ")
            if message.lower() == 'quit':
                break
            
            commande_input = input("🛒 ID de commande (optionnel): ")
            commande_id = None
            if commande_input.strip() and commande_input.isdigit():
                commande_id = int(commande_input)
            
            print("\n🔄 Traitement en cours...")
            result = agent.process_customer_message(email, message, commande_id)
            
            if result['success']:
                print("✅ Traitement réussi!")
                print(f"Catégorie: {result['categorie']}")
                print("\n📝 Réponse générée:")
                print("-" * 40)
                print(result['reponse'])
                print("-" * 40)
            else:
                print(f"❌ Erreur: {result['error']}")
            
            print("\n")
            
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
    finally:
        agent.db.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Automatisation du support client e-commerce')
    
    parser.add_argument('--setup', action='store_true', 
                       help='Initialise le système complet')
    
    parser.add_argument('--process-pending', action='store_true',
                       help='Traite tous les tickets en attente')
    
    parser.add_argument('--stats', action='store_true',
                       help='Affiche les statistiques du système')
    
    parser.add_argument('--interactive', action='store_true',
                       help='Lance le mode interactif')
    
    parser.add_argument('--message', nargs=2, metavar=('EMAIL', 'MESSAGE'),
                       help='Traite un message spécifique (email, message)')
    
    parser.add_argument('--order-id', type=int,
                       help='ID de commande pour --message')
    
    args = parser.parse_args()
    
    # Affichage de bienvenue
    print("=" * 60)
    print("🤖 AUTOMATISATION DU SUPPORT CLIENT E-COMMERCE")
    print("=" * 60)
    
    if args.setup:
        setup_system()
    
    elif args.process_pending:
        process_pending_tickets()
    
    elif args.stats:
        show_statistics()
    
    elif args.interactive:
        interactive_mode()
    
    elif args.message:
        email, message = args.message
        process_single_message(email, message, args.order_id)
    
    else:
        parser.print_help()
        print("\n💡 Exemples d'utilisation:")
        print("  python main.py --setup                    # Initialiser le système")
        print("  python main.py --interactive              # Mode interactif")
        print("  python main.py --process-pending          # Traiter les tickets")
        print("  python main.py --stats                    # Voir les statistiques")
        print('  python main.py --message "email@test.com" "Mon message"')


if __name__ == "__main__":
    main() 
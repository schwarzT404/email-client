#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Direct de l'Agent Claude
Vérification du traitement des messages sans serveur web
"""

import sys
import os
from datetime import datetime
import time

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_claude_agent():
    """Test direct de l'agent Claude"""
    print("🚀 TEST DIRECT DE L'AGENT CLAUDE")
    print("=" * 50)
    
    try:
        # Importer les modules
        from automation.claude_agent import ClaudeAgent
        from database.db_manager import DatabaseManager
        
        print("✅ Modules importés avec succès")
        
        # Initialiser la base de données
        db_manager = DatabaseManager()
        print("✅ Base de données initialisée")
        
        # Initialiser l'agent Claude
        claude_agent = ClaudeAgent(db_manager=db_manager)
        status = claude_agent.get_status()
        
        print(f"\n🔍 STATUT AGENT CLAUDE:")
        print(f"   📚 Module anthropic: {'✅' if status.get('claude_available') else '❌'}")
        print(f"   🔑 API configurée: {'✅' if status.get('api_key_configured') else '❌'}")
        print(f"   🤖 Agent prêt: {'✅' if status.get('claude_ready') else '❌'}")
        print(f"   🧠 Modèle: {status.get('model', 'N/A')}")
        
        if not status.get('claude_ready'):
            print("\n⚠️ Agent Claude non prêt. Test en mode fallback...")
        
        # Messages de test
        test_messages = [
            {
                "email": "marie.martin@example.com",
                "subject": "Problème livraison urgent",
                "message": "Bonjour, cela fait 3 semaines que j'attends ma commande #12345. C'était pour l'anniversaire de mon fils qui a eu lieu hier. Je suis très déçue et j'aimerais être remboursée rapidement. C'est inacceptable !",
                "expected_category": "retard_livraison"
            },
            {
                "email": "jean.dupont@example.com", 
                "subject": "Produit défectueux",
                "message": "Le produit que j'ai reçu est complètement cassé. L'emballage était intact mais l'objet à l'intérieur est en mille morceaux. Je veux un remplacment immédiat ou un remboursement.",
                "expected_category": "produit_defectueux"
            }
        ]
        
        print(f"\n🧪 LANCEMENT DE {len(test_messages)} TESTS:")
        print("=" * 50)
        
        for i, test_data in enumerate(test_messages, 1):
            print(f"\n📧 TEST {i}: {test_data['subject']}")
            print(f"   Client: {test_data['email']}")
            print(f"   Message: {test_data['message'][:80]}...")
            
            start_time = time.time()
            
            # Traitement du message
            result = claude_agent.process_customer_message(
                email=test_data["email"],
                message=test_data["message"],
                subject=test_data["subject"]
            )
            
            processing_time = time.time() - start_time
            
            if result.get('error'):
                print(f"   ❌ Erreur: {result['error']}")
                continue
            
            print(f"\n   ✅ RÉSULTATS:")
            print(f"      🏷️  Catégorie: {result.get('category', 'N/A')}")
            print(f"      🎯 Urgence: {result.get('urgency', 'N/A')}/5")
            print(f"      😊 Sentiment: {result.get('sentiment', 'N/A')}")
            print(f"      📊 Qualité: {result.get('quality_score', 0):.2f}")
            print(f"      🤖 Modèle: {result.get('model', 'N/A')}")
            print(f"      ⏱️  Temps: {processing_time:.1f}s")
            print(f"      🎫 Ticket: {result.get('ticket_id', 'N/A')}")
            
            # Vérifier la classification
            expected = test_data["expected_category"]
            actual = result.get('category', '')
            match = expected in actual or actual in expected
            print(f"      🎯 Classification: {'✅ Correcte' if match else '⚠️ Différente'}")
            
            # Afficher la réponse
            response = result.get('response', 'Pas de réponse')
            print(f"\n   📝 RÉPONSE GÉNÉRÉE:")
            print("   " + "─" * 47)
            # Afficher la réponse avec indentation
            for line in response.split('\n'):
                print(f"   {line}")
            print("   " + "─" * 47)
            
            # Analyse qualité
            analyze_response_quality(response)
            
        print(f"\n✅ TESTS TERMINÉS")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Vérifiez que tous les modules sont installés")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

def analyze_response_quality(response_text):
    """Analyse la qualité de la réponse"""
    print(f"\n   🔍 ANALYSE QUALITÉ:")
    
    checks = {
        "Longueur appropriée": 100 <= len(response_text) <= 1000,
        "Contient salutation": any(word in response_text.lower() for word in ['bonjour', 'bonsoir', 'salut']),
        "Personnalisé": any(name in response_text for name in ['Marie', 'Jean', 'Pierre', 'Dupont', 'Martin']),
        "Évite phrases génériques": "Dans les plus brefs délais" not in response_text,
        "Contient excuse/empathie": any(word in response_text.lower() for word in ['désolé', 'excuse', 'comprends', 'navré']),
        "Propose action concrète": any(word in response_text.lower() for word in ['rembours', 'remplac', 'expédi', 'envoi'])
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        print(f"      {'✅' if result else '❌'} {check}")
    
    score = passed/total*100
    print(f"      📊 Score: {passed}/{total} ({score:.0f}%)")
    
    return score

def test_classification_only():
    """Test uniquement la classification sans génération de réponse"""
    print("\n🎯 TEST CLASSIFICATION RAPIDE")
    print("=" * 30)
    
    try:
        from automation.claude_agent import ClaudeAgent
        from database.db_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        claude_agent = ClaudeAgent(db_manager=db_manager)
        
        messages = [
            ("Mon colis n'est pas arrivé depuis 2 semaines", "retard_livraison"),
            ("Je veux être remboursé de ma commande", "remboursement"), 
            ("Le produit reçu est cassé", "produit_defectueux"),
            ("Pouvez-vous m'envoyer ma facture ?", "information_commande"),
            ("Votre service client est nul !", "reclamation")
        ]
        
        print("📊 Précision de classification:")
        correct = 0
        total = len(messages)
        
        for message, expected in messages:
            result = claude_agent.classify_message(message)
            category = result.get('category', 'autre')
            urgency = result.get('urgency', 0)
            sentiment = result.get('sentiment', 'neutre')
            
            match = expected in category or category in expected
            if match:
                correct += 1
            
            print(f"   📝 '{message[:40]}...'")
            print(f"      Attendu: {expected} | Obtenu: {category} {'✅' if match else '❌'}")
            print(f"      Urgence: {urgency}/5 | Sentiment: {sentiment}")
        
        accuracy = correct/total*100
        print(f"\n📊 Précision globale: {correct}/{total} ({accuracy:.0f}%)")
        
    except Exception as e:
        print(f"❌ Erreur test classification: {e}")

if __name__ == "__main__":
    print("🧪 TESTS DIRECTS DE L'AGENT CLAUDE")
    print("=" * 60)
    
    # Test principal
    test_claude_agent()
    
    # Test classification rapide
    test_classification_only()
    
    print("\n�� TESTS TERMINÉS") 
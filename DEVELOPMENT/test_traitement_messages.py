#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du Traitement des Messages par l'IA Claude
Vérification de la qualité et cohérence des réponses
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_URL = "http://localhost:5001"

# Messages de test avec différents scénarios
TEST_MESSAGES = [
    {
        "email": "marie.martin@example.com",
        "subject": "Problème avec ma commande",
        "message": "Bonjour, j'ai commandé il y a 2 semaines et je n'ai toujours rien reçu. Ma commande était prévue pour arriver la semaine dernière. Pouvez-vous me dire où en est ma livraison ? Je commence à m'inquiéter car c'était un cadeau important. Merci de votre aide.",
        "type_attendu": "retard_livraison",
        "urgence_attendue": 3
    },
    {
        "email": "jean.dupont@example.com", 
        "subject": "Demande de remboursement urgent",
        "message": "URGENT - Je souhaite absolument être remboursé de ma commande #12345. Le produit ne correspond pas du tout à ce qui était annoncé sur votre site. Je suis très déçu et je veux récupérer mon argent rapidement. C'est inadmissible !",
        "type_attendu": "remboursement",
        "urgence_attendue": 4
    },
    {
        "email": "pierre.durand@example.com",
        "subject": "Produit défectueux reçu",
        "message": "Bonjour, j'ai reçu mon colis hier mais malheureusement le produit est arrivé cassé. L'emballage était abîmé et l'article à l'intérieur est inutilisable. Que puis-je faire pour obtenir un remplacement ? Merci d'avance pour votre aide.",
        "type_attendu": "produit_defectueux",
        "urgence_attendue": 3
    },
    {
        "email": "marie.martin@example.com",
        "subject": "Question sur ma facture",
        "message": "Bonjour, j'aimerais obtenir plus d'informations sur ma dernière commande. Pouvez-vous m'envoyer le détail de ma facture ? J'ai besoin de ces informations pour ma comptabilité. Merci beaucoup.",
        "type_attendu": "information_commande", 
        "urgence_attendue": 2
    },
    {
        "email": "jean.dupont@example.com",
        "subject": "Service client décevant",
        "message": "Je dois dire que je suis très mécontent de la qualité de service de votre entreprise. Cela fait plusieurs fois que j'ai des problèmes et personne ne semble s'en préoccuper. Je pense sérieusement à changer de fournisseur si ça continue comme ça.",
        "type_attendu": "reclamation",
        "urgence_attendue": 4
    }
]

def check_system_status():
    """Vérifie que le système est opérationnel"""
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"🔍 Statut système:")
            print(f"   🗄️  Base de données: {'✅' if status.get('db_connected') else '❌'}")
            print(f"   🤖 Agent Claude: {'✅' if status.get('claude_ready') else '❌'}")
            print(f"   📡 API configurée: {'✅' if status.get('api_key_configured') else '❌'}")
            print(f"   🧠 Modèle: {status.get('model', 'N/A')}")
            return status.get('claude_ready', False)
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_message_processing(test_data):
    """Teste le traitement d'un message"""
    print(f"\n🧪 TEST: {test_data['subject']}")
    print(f"📧 Client: {test_data['email']}")
    print(f"💬 Message: {test_data['message'][:100]}...")
    
    try:
        # Envoyer le message
        response = requests.post(
            f"{BASE_URL}/api/process-message",
            json={
                "email": test_data["email"],
                "subject": test_data["subject"], 
                "message": test_data["message"]
            },
            timeout=45  # Timeout augmenté pour le traitement IA
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                analysis = result['result']
                
                print(f"✅ Message traité avec succès!")
                print(f"   🏷️  Catégorie détectée: {analysis.get('category', 'N/A')}")
                print(f"   🎯 Urgence: {analysis.get('urgency', 'N/A')}/5")
                print(f"   😊 Sentiment: {analysis.get('sentiment', 'N/A')}")
                print(f"   📊 Score qualité: {analysis.get('quality_score', 0):.2f}")
                print(f"   🤖 Modèle: {analysis.get('model', 'N/A')}")
                print(f"   ⏱️  Temps traitement: {result.get('processing_delay', 'N/A')}s")
                print(f"   🎫 Ticket: {analysis.get('ticket_id', 'N/A')}")
                
                # Vérifier la classification
                expected_category = test_data["type_attendu"]
                actual_category = analysis.get('category', '')
                category_match = expected_category in actual_category or actual_category in expected_category
                
                print(f"   🎯 Classification: {'✅ Correcte' if category_match else '⚠️ Différente'}")
                if not category_match:
                    print(f"      Attendu: {expected_category}")
                    print(f"      Obtenu: {actual_category}")
                
                # Afficher la réponse générée
                response_text = analysis.get('response', 'Pas de réponse')
                print(f"\n📝 RÉPONSE GÉNÉRÉE:")
                print("─" * 60)
                print(response_text)
                print("─" * 60)
                
                # Analyser la qualité de la réponse
                analyze_response_quality(response_text, test_data)
                
                return {
                    'success': True,
                    'category_match': category_match,
                    'quality_score': analysis.get('quality_score', 0),
                    'response_length': len(response_text),
                    'processing_time': result.get('processing_delay', 0)
                }
            else:
                print(f"❌ Erreur traitement: {result.get('error', 'Erreur inconnue')}")
                return {'success': False, 'error': result.get('error')}
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except requests.exceptions.Timeout:
        print("⏱️ Timeout - Le traitement IA prend plus de 45 secondes")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return {'success': False, 'error': str(e)}

def analyze_response_quality(response_text, test_data):
    """Analyse la qualité de la réponse générée"""
    print(f"\n🔍 ANALYSE QUALITÉ:")
    
    # Vérifications de base
    checks = {
        "Longueur appropriée": 150 <= len(response_text) <= 800,
        "Contient salutation": any(word in response_text.lower() for word in ['bonjour', 'bonsoir', 'salut']),
        "Personnalisé (prénom)": any(name in response_text for name in ['Marie', 'Jean', 'Pierre']),
        "Évite phrases génériques": not any(phrase in response_text for phrase in [
            'Nous avons bien reçu votre demande',
            'Dans les plus brefs délais',
            'Cordialement l\'équipe support'
        ]),
        "Référence au problème": any(word in response_text.lower() for word in test_data['message'].lower().split()[:10]),
        "Contient signature": any(word in response_text for word in ['Cordialement', 'Bien à vous', 'Sincèrement'])
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        print(f"   {'✅' if result else '❌'} {check}")
    
    print(f"   📊 Score: {passed}/{total} ({passed/total*100:.0f}%)")
    
    return passed/total

def run_comprehensive_test():
    """Lance une série de tests complets"""
    print("🚀 DÉMARRAGE TESTS COMPLETS DU SYSTÈME")
    print("=" * 60)
    
    # Vérifier le statut du système
    if not check_system_status():
        print("❌ Système non prêt. Veuillez d'abord lancer le système.")
        return
    
    print(f"\n🧪 Lancement de {len(TEST_MESSAGES)} tests...")
    
    results = []
    start_time = time.time()
    
    for i, test_data in enumerate(TEST_MESSAGES, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}/{len(TEST_MESSAGES)}")
        print(f"{'='*60}")
        
        result = test_message_processing(test_data)
        results.append(result)
        
        # Pause entre les tests pour éviter la surcharge
        if i < len(TEST_MESSAGES):
            print(f"\n⏳ Pause de 5 secondes avant le test suivant...")
            time.sleep(5)
    
    # Résumé final
    total_time = time.time() - start_time
    successful_tests = sum(1 for r in results if r.get('success'))
    
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ FINAL")
    print(f"{'='*60}")
    print(f"✅ Tests réussis: {successful_tests}/{len(TEST_MESSAGES)}")
    print(f"⏱️ Temps total: {total_time:.1f}s")
    print(f"⚡ Temps moyen par test: {total_time/len(TEST_MESSAGES):.1f}s")
    
    if successful_tests > 0:
        avg_quality = sum(r.get('quality_score', 0) for r in results if r.get('success')) / successful_tests
        avg_response_length = sum(r.get('response_length', 0) for r in results if r.get('success')) / successful_tests
        category_accuracy = sum(1 for r in results if r.get('category_match')) / successful_tests
        
        print(f"📊 Score qualité moyen: {avg_quality:.2f}")
        print(f"📏 Longueur réponse moyenne: {avg_response_length:.0f} caractères") 
        print(f"🎯 Précision classification: {category_accuracy*100:.0f}%")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    if successful_tests == len(TEST_MESSAGES):
        print("   ✅ Système fonctionnel - Toutes les réponses sont cohérentes")
    else:
        print(f"   ⚠️ {len(TEST_MESSAGES) - successful_tests} tests ont échoué")
        print("   🔧 Vérifiez la configuration Claude et la base de données")
    
    return results

if __name__ == "__main__":
    # Attendre un peu que le système se lance
    print("⏳ Attente du démarrage du système (10 secondes)...")
    time.sleep(10)
    
    run_comprehensive_test() 
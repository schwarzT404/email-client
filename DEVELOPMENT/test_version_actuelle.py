#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de la Version Actuelle Complète
Test des interfaces web et du traitement en temps réel
"""

import requests
import json
import time
from datetime import datetime
import threading

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_URL = "http://localhost:5001"

def wait_for_system():
    """Attendre que le système soit opérationnel"""
    print("⏳ Attente du démarrage du système...")
    for i in range(30):  # Attendre max 30 secondes
        try:
            response = requests.get(f"{BASE_URL}/api/status", timeout=2)
            if response.status_code == 200:
                print("✅ Système opérationnel !")
                return True
        except:
            pass
        print(f"   Tentative {i+1}/30...")
        time.sleep(1)
    return False

def test_system_status():
    """Tester le statut du système"""
    print("\n🔍 TEST STATUT SYSTÈME")
    print("-" * 40)
    
    try:
        # Test client app
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("📱 APPLICATION CLIENT (Port 5000):")
            print(f"   🗄️  Base de données: {'✅' if status.get('db_connected') else '❌'}")
            print(f"   🤖 Agent prêt: {'✅' if status.get('agent_ready') else '❌'}")
            print(f"   🧠 Claude disponible: {'✅' if status.get('claude_ready') else '❌ (mode fallback)'}")
            print(f"   📡 API configurée: {'✅' if status.get('api_key_configured') else '❌'}")
            print(f"   🎯 Modèle: {status.get('model', 'N/A')}")
        else:
            print("❌ Application client non accessible")
            return False
            
        # Test admin interface
        admin_response = requests.get(f"{ADMIN_URL}/api/dashboard-data", timeout=5)
        if admin_response.status_code == 200:
            print("\n👑 INTERFACE ADMINISTRATEUR (Port 5001):")
            print("   ✅ Dashboard accessible")
            print("   ✅ API monitoring fonctionnelle")
        else:
            print("\n❌ Interface admin non accessible")
            
        return True
            
    except Exception as e:
        print(f"❌ Erreur test statut: {e}")
        return False

def test_user_registration():
    """Tester l'inscription utilisateur"""
    print("\n👤 TEST INSCRIPTION UTILISATEUR")
    print("-" * 40)
    
    test_user = {
        "prenom": "Baptiste",
        "nom": "Test", 
        "email": f"baptiste.test.{int(time.time())}@email.com"  # Email unique
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/register",
            json=test_user,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Inscription réussie: {test_user['email']}")
                return test_user['email']
            else:
                print(f"❌ Erreur inscription: {result.get('error')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur inscription: {e}")
        
    return None

def test_message_processing(email):
    """Tester le traitement de messages"""
    print("\n💬 TEST TRAITEMENT MESSAGES")
    print("-" * 40)
    
    test_messages = [
        {
            "subject": "Retard de livraison",
            "message": "Bonjour, ma commande #12345 n'est toujours pas arrivée alors qu'elle était prévue la semaine dernière. Pouvez-vous me dire où elle en est ? Merci.",
            "expected_category": "retard_livraison"
        },
        {
            "subject": "Produit défectueux",  
            "message": "Le produit que j'ai reçu est complètement cassé ! L'emballage était pourtant intact. Je veux un remboursement immédiat.",
            "expected_category": "produit_defectueux"
        },
        {
            "subject": "Demande d'information",
            "message": "Pouvez-vous m'envoyer la facture de ma dernière commande ? J'en ai besoin pour ma comptabilité. Merci d'avance.",
            "expected_category": "information_commande"
        }
    ]
    
    results = []
    
    for i, test_data in enumerate(test_messages, 1):
        print(f"\n📧 TEST MESSAGE {i}/3: {test_data['subject']}")
        print(f"   📝 '{test_data['message'][:60]}...'")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/process-message",
                json={
                    "email": email,
                    "subject": test_data["subject"],
                    "message": test_data["message"]
                },
                timeout=45  # Timeout pour le traitement
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    analysis = result['result']
                    
                    print(f"   ✅ Traité en {processing_time:.1f}s")
                    print(f"   🏷️  Catégorie: {analysis.get('category', 'N/A')}")
                    print(f"   🎯 Urgence: {analysis.get('urgency', 'N/A')}/5")
                    print(f"   😊 Sentiment: {analysis.get('sentiment', 'N/A')}")
                    print(f"   📊 Qualité: {analysis.get('quality_score', 0):.2f}")
                    print(f"   🤖 Mode: {result.get('mode', 'N/A')}")
                    
                    # Vérifier classification
                    expected = test_data["expected_category"]
                    actual = analysis.get('category', '')
                    match = expected in actual or actual in expected
                    print(f"   🎯 Classification: {'✅ Correcte' if match else '⚠️ Différente'}")
                    
                    # Afficher un extrait de la réponse
                    response_text = analysis.get('response', '')
                    if response_text:
                        print(f"   📝 Réponse: '{response_text[:100]}...'")
                        print(f"   📏 Longueur: {len(response_text)} caractères")
                    
                    results.append({
                        'success': True,
                        'category_match': match,
                        'processing_time': processing_time,
                        'quality_score': analysis.get('quality_score', 0)
                    })
                else:
                    print(f"   ❌ Erreur: {result.get('error')}")
                    results.append({'success': False})
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}")
                results.append({'success': False})
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout après {processing_time:.1f}s")
            results.append({'success': False, 'timeout': True})
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results.append({'success': False})
    
    return results

def test_admin_monitoring():
    """Tester le monitoring administrateur"""
    print("\n📊 TEST MONITORING ADMIN")
    print("-" * 40)
    
    try:
        response = requests.get(f"{ADMIN_URL}/api/dashboard-data", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Dashboard données récupérées:")
            print(f"   📈 Total échanges: {data.get('total_exchanges', 0)}")
            print(f"   📊 Stats par catégorie disponibles: {'✅' if data.get('category_stats') else '❌'}")
            print(f"   ⏱️  Dernière mise à jour: {data.get('last_update', 'N/A')}")
            return True
        else:
            print(f"❌ Erreur dashboard: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur monitoring: {e}")
        return False

def run_complete_test():
    """Lancer un test complet du système"""
    print("🚀 TEST COMPLET DE LA VERSION ACTUELLE")
    print("=" * 60)
    
    # 1. Attendre le système
    if not wait_for_system():
        print("❌ Système non accessible après 30 secondes")
        return
    
    # 2. Tester le statut
    if not test_system_status():
        print("❌ Statut système non satisfaisant")
        return
    
    # 3. Tester l'inscription
    user_email = test_user_registration()
    if not user_email:
        print("⚠️ Utilisation d'un compte de test existant")
        user_email = "marie.martin@example.com"  # Compte de test
    
    # 4. Tester le traitement des messages
    results = test_message_processing(user_email)
    
    # 5. Tester le monitoring admin
    monitoring_ok = test_admin_monitoring()
    
    # 6. Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 60)
    
    successful_messages = sum(1 for r in results if r.get('success'))
    total_messages = len(results)
    
    print(f"✅ Messages traités avec succès: {successful_messages}/{total_messages}")
    
    if successful_messages > 0:
        avg_time = sum(r.get('processing_time', 0) for r in results if r.get('success')) / successful_messages
        avg_quality = sum(r.get('quality_score', 0) for r in results if r.get('success')) / successful_messages
        accuracy = sum(1 for r in results if r.get('category_match')) / successful_messages
        
        print(f"⏱️  Temps traitement moyen: {avg_time:.1f}s")
        print(f"📊 Score qualité moyen: {avg_quality:.2f}")
        print(f"🎯 Précision classification: {accuracy*100:.0f}%")
    
    print(f"📈 Monitoring admin: {'✅ Fonctionnel' if monitoring_ok else '❌ Problème'}")
    
    # Recommandations
    print(f"\n💡 ÉTAT DU SYSTÈME:")
    if successful_messages == total_messages and monitoring_ok:
        print("   🎉 EXCELLENT - Système entièrement fonctionnel")
        print("   ✅ Prêt pour la production")
        print("   📱 Interfaces web opérationnelles") 
        print("   🤖 IA de support efficace")
    elif successful_messages > 0:
        print("   ✅ BON - Fonctionnalités principales opérationnelles")
        print("   🔧 Quelques ajustements mineurs possibles")
    else:
        print("   ⚠️ PROBLÈMES - Vérifier la configuration")
    
    print(f"\n🌐 ACCÈS:")
    print(f"   👤 Interface client: http://localhost:5000")
    print(f"   👑 Interface admin: http://localhost:5001")

if __name__ == "__main__":
    run_complete_test() 
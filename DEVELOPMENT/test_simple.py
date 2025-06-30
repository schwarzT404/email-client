#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("🚀 TEST RAPIDE AGENT CLAUDE")
print("=" * 40)

try:
    from automation.claude_agent import ClaudeAgent
    from database.db_manager import DatabaseManager
    
    print("✅ Modules importés")
    
    # Initialiser
    db = DatabaseManager()
    agent = ClaudeAgent(db_manager=db)
    status = agent.get_status()
    
    print(f"📚 Module anthropic: {status.get('claude_available', False)}")
    print(f"🔑 API configurée: {status.get('api_key_configured', False)}")
    print(f"🤖 Agent prêt: {status.get('claude_ready', False)}")
    print(f"🧠 Modèle: {status.get('model', 'N/A')}")
    
    print("\n🧪 TEST CLASSIFICATION:")
    message = "Mon colis n'arrive pas depuis 2 semaines, je suis très mécontent !"
    result = agent.classify_message(message)
    
    print(f"📝 Message: {message}")
    print(f"🏷️ Catégorie: {result.get('category', 'N/A')}")
    print(f"🎯 Urgence: {result.get('urgency', 0)}/5")
    print(f"😊 Sentiment: {result.get('sentiment', 'N/A')}")
    print(f"🤖 Modèle utilisé: {result.get('model', 'N/A')}")
    
    print("\n🧪 TEST GÉNÉRATION RÉPONSE:")
    response = agent.generate_response(message, result)
    
    print("📝 RÉPONSE GÉNÉRÉE:")
    print("-" * 40)
    print(response)
    print("-" * 40)
    
    # Analyse qualité
    print(f"📏 Longueur: {len(response)} caractères")
    print(f"🎯 Contient salutation: {'bonjour' in response.lower()}")
    print(f"💬 Évite générique: {'Dans les plus brefs délais' not in response}")
    
    print("\n✅ TEST COMPLET RÉUSSI!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc() 
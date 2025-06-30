#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 LANCEUR SYSTÈME COMPLET
Version rapide et efficace
"""

import os
import sys
import time
import subprocess
import webbrowser
from datetime import datetime

def main():
    """Lancement rapide du système"""
    print("🚀 LANCEMENT SYSTÈME SUPPORT CLIENT E-COMMERCE")
    print("=" * 55)
    print()
    
    # Menu de choix
    print("🎯 CHOISISSEZ VOTRE ACTION :")
    print("   1. 🛠️  Réparer + Lancer système complet")
    print("   2. 🌐 Lancer seulement l'application web")
    print("   3. 👑 Lancer seulement l'interface admin")
    print("   4. 🤖 Lancer le bot de simulation")
    print("   5. ✨ Démonstration spectaculaire")
    print()
    
    choix = input("Votre choix (1-5) : ").strip()
    
    if choix == "1":
        print("\n🛠️  RÉPARATION + LANCEMENT COMPLET")
        print("-" * 40)
        
        # Réparer d'abord
        print("🔧 Réparation de la base de données...")
        subprocess.run([sys.executable, 'reparation_urgente.py'])
        
        print("\n🌐 Lancement application web...")
        os.chdir('web_app')
        web_process = subprocess.Popen([sys.executable, 'app.py'])
        os.chdir('..')
        
        time.sleep(2)
        print("👑 Lancement interface admin...")
        admin_process = subprocess.Popen([sys.executable, 'admin_interface.py'])
        
        time.sleep(3)
        print("🌍 Ouverture navigateur...")
        webbrowser.open('http://localhost:5000')
        time.sleep(1)
        webbrowser.open('http://localhost:5001')
        
        print("\n✅ SYSTÈME COMPLET LANCÉ !")
        print("🌐 Application web: http://localhost:5000")
        print("👑 Interface admin: http://localhost:5001")
        print("\n🎯 Pressez Ctrl+C pour arrêter")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du système...")
            web_process.terminate()
            admin_process.terminate()
            print("✅ Arrêté proprement")
    
    elif choix == "2":
        print("\n🌐 LANCEMENT APPLICATION WEB UNIQUEMENT")
        print("-" * 40)
        
        os.chdir('web_app')
        print("🚀 Démarrage sur http://localhost:5000...")
        time.sleep(2)
        webbrowser.open('http://localhost:5000')
        subprocess.run([sys.executable, 'app.py'])
    
    elif choix == "3":
        print("\n👑 LANCEMENT INTERFACE ADMIN UNIQUEMENT")
        print("-" * 40)
        
        print("🚀 Démarrage sur http://localhost:5001...")
        time.sleep(2)
        webbrowser.open('http://localhost:5001')
        subprocess.run([sys.executable, 'admin_interface.py'])
    
    elif choix == "4":
        print("\n🤖 LANCEMENT BOT DE SIMULATION")
        print("-" * 40)
        
        subprocess.run([sys.executable, 'bot_simulation_emails.py'])
    
    elif choix == "5":
        print("\n✨ LANCEMENT DÉMONSTRATION SPECTACULAIRE")
        print("-" * 40)
        
        subprocess.run([sys.executable, 'demo_spectaculaire.py'])
    
    else:
        print("❌ Choix invalide")
        return False
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    input("\nPressez Entrée pour quitter...") 
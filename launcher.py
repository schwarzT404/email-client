#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 LANCEUR SYSTÈME COMPLET
Lancement automatique des serveurs
"""

import os
import sys
import time
import subprocess
import webbrowser
from datetime import datetime

def main():
    """Lancement automatique du système complet"""
    print("🚀 LANCEMENT AUTOMATIQUE DU SYSTÈME SUPPORT CLIENT E-COMMERCE")
    print("=" * 65)
    print()
    
    print("🛠️  DÉMARRAGE DU SYSTÈME COMPLET")
    print("-" * 40)
    
    # Chemin vers le dossier de production
    prod_dir = 'PRODUCTION'
    
    # Vérification de la base de données
    print("🔧 Vérification de la base de données...")
    
    print("\n🌐 Lancement application web...")
    web_app_dir = os.path.join(prod_dir, 'web_app')
    web_process = subprocess.Popen([sys.executable, 'app.py'], cwd=web_app_dir)
    
    time.sleep(2)
    print("👑 Lancement interface admin...")
    admin_process = subprocess.Popen([sys.executable, 'admin_dynamic.py'], cwd=prod_dir)
    
    time.sleep(3)
    print("🌍 Ouverture navigateur...")
    webbrowser.open('http://localhost:5000')
    time.sleep(1)
    webbrowser.open('http://localhost:5001')
    
    print("\n✅ SYSTÈME COMPLET LANCÉ AUTOMATIQUEMENT !")
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
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    input("\nPressez Entrée pour quitter...") 
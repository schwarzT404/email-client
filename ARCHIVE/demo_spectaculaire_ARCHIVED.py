#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌟 DÉMONSTRATION SPECTACULAIRE 🌟
Système complet d'automatisation du support client e-commerce avec Claude 4
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser
from datetime import datetime
import sqlite3

def banner_spectaculaire():
    """Banner spectaculaire avec animation"""
    clear = "cls" if os.name == "nt" else "clear"
    os.system(clear)
    
    print("🌟" + "=" * 80 + "🌟")
    print("🚀               DÉMONSTRATION SPECTACULAIRE                🚀")
    print("🌟   SYSTÈME D'AUTOMATISATION SUPPORT CLIENT E-COMMERCE    🌟") 
    print("🤖                    PROPULSÉ PAR CLAUDE 4                🤖")
    print("🌟" + "=" * 80 + "🌟")
    print()
    
    # Animation de chargement
    for i in range(3):
        print(f"⚡ Initialisation{'.' * (i+1)}", end='\r')
        time.sleep(0.8)
    
    print("✨ PRÊT À VOUS FAIRE RÊVER ! ✨" + " " * 20)
    print()

def verifier_environnement():
    """Vérifie l'environnement et les dépendances"""
    print("🔍 VÉRIFICATION DE L'ENVIRONNEMENT")
    print("-" * 40)
    
    # Vérifier Python
    python_version = sys.version.split()[0]
    print(f"🐍 Python: {python_version} ✅")
    
    # Vérifier venv
    if sys.prefix != sys.base_prefix:
        print("📦 Environnement virtuel: ACTIF ✅")
    else:
        print("❌ Environnement virtuel: NON ACTIF")
        print("💡 Activez avec: venv\\Scripts\\activate")
        return False
    
    # Vérifier modules requis
    modules = {
        'flask': 'Flask',
        'anthropic': 'Anthropic',
        'sqlite3': 'SQLite3'
    }
    
    for module, nom in modules.items():
        try:
            __import__(module)
            print(f"📚 {nom}: INSTALLÉ ✅")
        except ImportError:
            print(f"❌ {nom}: MANQUANT")
            return False
    
    print("🎉 Environnement PARFAIT !")
    print()
    return True

def reparer_base_donnees():
    """Répare automatiquement la base de données"""
    print("🛠️  RÉPARATION BASE DE DONNÉES")
    print("-" * 40)
    
    try:
        # Exécuter le script de réparation
        result = subprocess.run([sys.executable, 'reparation_urgente.py'], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ Base de données RÉPARÉE avec succès !")
            return True
        else:
            print(f"❌ Erreur réparation: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur réparation: {e}")
        return False

def lancer_application_web():
    """Lance l'application web en arrière-plan"""
    print("🌐 LANCEMENT APPLICATION WEB")
    print("-" * 40)
    
    try:
        # Changer vers le dossier web_app
        os.chdir('web_app')
        
        # Lancer Flask en arrière-plan
        process = subprocess.Popen([sys.executable, 'app.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        print("🚀 Application web lancée sur http://localhost:5000")
        print("⏱️  Attente du démarrage...")
        
        # Attendre que l'app soit prête
        time.sleep(3)
        
        # Retourner au répertoire parent
        os.chdir('..')
        
        return process
        
    except Exception as e:
        print(f"❌ Erreur lancement: {e}")
        return None

def lancer_interface_admin():
    """Lance l'interface administrateur"""
    print("👑 LANCEMENT INTERFACE ADMIN")
    print("-" * 40)
    
    try:
        # Lancer interface admin en arrière-plan
        process = subprocess.Popen([sys.executable, 'admin_interface.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        print("👑 Interface admin lancée sur http://localhost:5001")
        print("⏱️  Attente du démarrage...")
        
        time.sleep(2)
        return process
        
    except Exception as e:
        print(f"❌ Erreur lancement admin: {e}")
        return None

def ouvrir_navigateur():
    """Ouvre automatiquement les pages dans le navigateur"""
    print("🌍 OUVERTURE AUTOMATIQUE NAVIGATEUR")
    print("-" * 40)
    
    try:
        time.sleep(1)
        print("🔗 Ouverture application principale...")
        webbrowser.open('http://localhost:5000')
        
        time.sleep(2)
        print("🔗 Ouverture interface admin...")
        webbrowser.open('http://localhost:5001')
        
        print("✅ Navigateur ouvert avec les 2 interfaces !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur navigateur: {e}")
        return False

def demonstration_temps_reel():
    """Fait une démonstration en temps réel"""
    print("🎭 DÉMONSTRATION EN TEMPS RÉEL")
    print("=" * 40)
    
    # Afficher statistiques DB
    try:
        conn = sqlite3.connect('data/crm_ecommerce.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM client')
        nb_clients = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM commande')
        nb_commandes = cursor.fetchone()[0]
        
        print(f"👥 Clients enregistrés: {nb_clients}")
        print(f"📦 Commandes totales: {nb_commandes}")
        
        # Afficher quelques clients
        print("\n🎯 CLIENTS DE TEST DISPONIBLES:")
        cursor.execute('SELECT nom, prenom, email FROM client LIMIT 5')
        clients = cursor.fetchall()
        
        for nom, prenom, email in clients:
            print(f"   📧 {prenom} {nom} - {email}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur stats: {e}")
    
    print("\n🎪 FONCTIONNALITÉS ACTIVES:")
    print("   ✅ Authentification par email")
    print("   ✅ Inscription automatique")
    print("   ✅ Claude 4 avec chaîne de réflexion")
    print("   ✅ Délais de traitement réalistes (10-30s)")
    print("   ✅ Monitoring API en temps réel")
    print("   ✅ Réponses personnalisées (pas de générique)")
    print("   ✅ Interface admin avec métriques")
    print("   ✅ Bot de simulation d'emails")
    
    print("\n🌟 LE SYSTÈME EST MAINTENANT OPÉRATIONNEL !")
    print("\n📋 GUIDE RAPIDE:")
    print("   1. Application cliente: http://localhost:5000")
    print("   2. Interface admin: http://localhost:5001")
    print("   3. Utiliser les emails de test ci-dessus")
    print("   4. Ou s'inscrire avec un nouveau compte")
    print("   5. Envoyer un message et voir Claude 4 répondre !")

def monitorer_systeme(processes):
    """Monitore le système en temps réel"""
    print("\n🔍 MONITORING SYSTÈME ACTIF")
    print("-" * 40)
    
    try:
        while True:
            # Vérifier que les processus tournent
            web_status = "🟢 ACTIF" if processes['web'].poll() is None else "🔴 ARRÊTÉ"
            admin_status = "🟢 ACTIF" if processes['admin'].poll() is None else "🔴 ARRÊTÉ"
            
            print(f"\r⚡ Web App: {web_status} | Admin: {admin_status} | {datetime.now().strftime('%H:%M:%S')}", end='')
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du monitoring...")
    except Exception as e:
        print(f"\n❌ Erreur monitoring: {e}")

def main():
    """Fonction principale - La magie opère ici ! ✨"""
    banner_spectaculaire()
    
    # 1. Vérification environnement
    if not verifier_environnement():
        print("❌ Environnement non prêt !")
        return False
    
    # 2. Réparation base de données
    print("🛠️  Réparation automatique...")
    if not reparer_base_donnees():
        print("❌ Réparation échouée !")
        return False
    
    print("✅ Système réparé !")
    print()
    
    # 3. Lancement applications
    print("🚀 LANCEMENT DU SYSTÈME COMPLET")
    print("=" * 50)
    
    web_process = lancer_application_web()
    if not web_process:
        print("❌ Échec lancement web app")
        return False
    
    admin_process = lancer_interface_admin() 
    if not admin_process:
        print("❌ Échec lancement interface admin")
        web_process.terminate()
        return False
    
    # 4. Ouverture navigateur
    time.sleep(2)
    ouvrir_navigateur()
    
    # 5. Démonstration
    print()
    demonstration_temps_reel()
    
    # 6. Monitoring continu
    processes = {
        'web': web_process,
        'admin': admin_process
    }
    
    try:
        print("\n" + "🎉" * 20)
        print("✨ SYSTÈME OPÉRATIONNEL - PROFITEZ DE LA MAGIE ! ✨")
        print("🎯 Pressez Ctrl+C pour arrêter le système")
        print("🎉" * 20)
        print()
        
        monitorer_systeme(processes) 
        
    except KeyboardInterrupt:
        print("\n\n🛑 ARRÊT DU SYSTÈME...")
        print("⏹️  Fermeture des processus...")
        
        web_process.terminate()
        admin_process.terminate()
        
        print("✅ Système arrêté proprement")
        print("🙏 Merci d'avoir utilisé notre système !")
        
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Échec de la démonstration")
        input("Pressez Entrée pour quitter...")
    else:
        print("\n🎊 Démonstration terminée avec succès !")
        input("Pressez Entrée pour quitter...") 
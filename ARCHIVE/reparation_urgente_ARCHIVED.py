#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚨 RÉPARATION URGENTE DU SYSTÈME
Répare la base de données et lance l'application
"""

import os
import sqlite3
from datetime import datetime

def banner_reparation():
    """Banner de réparation"""
    print("🚨" + "=" * 60 + "🚨")
    print("🛠️  RÉPARATION D'URGENCE DU SYSTÈME")
    print("🚨" + "=" * 60 + "🚨")
    print()

def verifier_base_donnees():
    """Vérifie et répare la base de données"""
    print("🔍 Vérification de la base de données...")
    
    db_path = 'data/crm_ecommerce.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier les tables existantes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Tables trouvées: {[table[0] for table in tables]}")
        
        # Vérifier si table client existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client'")
        client_table = cursor.fetchone()
        
        if not client_table:
            print("❌ Table 'client' manquante - Création en cours...")
            
            # Créer table client
            cursor.execute('''
                CREATE TABLE client (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    type_client TEXT DEFAULT 'particulier',
                    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Créer index
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_email ON client(email)')
            
            print("✅ Table 'client' créée avec succès")
            
            # Insérer des données de test
            clients_test = [
                ('Martin', 'Marie', 'marie.martin@example.com'),
                ('Dupont', 'Jean', 'jean.dupont@example.com'),
                ('Durand', 'Pierre', 'pierre.durand@example.com'),
                ('Bernard', 'Sophie', 'sophie.bernard@example.com'),
                ('Moreau', 'Thomas', 'thomas.moreau@example.com'),
                ('Petit', 'Emma', 'emma.petit@example.com')
            ]
            
            for nom, prenom, email in clients_test:
                try:
                    cursor.execute(
                        'INSERT INTO client (nom, prenom, email) VALUES (?, ?, ?)',
                        (nom, prenom, email)
                    )
                except sqlite3.IntegrityError:
                    pass  # Client déjà existant
            
            print(f"✅ {len(clients_test)} clients de test ajoutés")
        else:
            print("✅ Table 'client' existe déjà")
        
        # Vérifier table commande
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='commande'")
        commande_table = cursor.fetchone()
        
        if not commande_table:
            print("❌ Table 'commande' manquante - Création en cours...")
            
            cursor.execute('''
                CREATE TABLE commande (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    montant REAL NOT NULL,
                    statut TEXT DEFAULT 'en_cours',
                    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES client(id)
                )
            ''')
            
            print("✅ Table 'commande' créée avec succès")
            
            # Ajouter quelques commandes de test
            commandes_test = [
                (1, '2024-01-15', 89.99, 'livree'),
                (1, '2024-01-20', 156.50, 'en_cours'),
                (2, '2024-01-18', 45.00, 'livree'),
                (3, '2024-01-22', 203.75, 'expedie'),
                (2, '2024-01-25', 78.30, 'en_cours')
            ]
            
            for client_id, date, montant, statut in commandes_test:
                cursor.execute(
                    'INSERT INTO commande (client_id, date, montant, statut) VALUES (?, ?, ?, ?)',
                    (client_id, date, montant, statut)
                )
            
            print(f"✅ {len(commandes_test)} commandes de test ajoutées")
        else:
            print("✅ Table 'commande' existe déjà")
        
        conn.commit()
        conn.close()
        
        print("🎉 Base de données réparée avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur réparation: {e}")
        return False

def verifier_structure_projet():
    """Vérifie la structure du projet"""
    print("\n📁 Vérification structure projet...")
    
    fichiers_requis = [
        'web_app/app.py',
        'admin_interface.py', 
        'bot_simulation_emails.py',
        'automation/claude_agent.py',
        'database/db_manager.py'
    ]
    
    for fichier in fichiers_requis:
        if os.path.exists(fichier):
            print(f"   ✅ {fichier}")
        else:
            print(f"   ❌ {fichier} MANQUANT")
    
    print("✅ Structure projet vérifiée")

def corriger_templates():
    """Corrige les templates manquants"""
    print("\n🎨 Correction des templates...")
    
    # Créer template 404.html manquant
    template_404 = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Page non trouvée</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6 text-center">
                <h1 class="display-1 text-primary">404</h1>
                <h2>Page non trouvée</h2>
                <p class="lead">La page que vous cherchez n'existe pas.</p>
                <a href="/" class="btn btn-primary">Retour à l'accueil</a>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    os.makedirs('web_app/templates', exist_ok=True)
    with open('web_app/templates/404.html', 'w', encoding='utf-8') as f:
        f.write(template_404)
    
    print("✅ Template 404.html créé")

def tester_base_donnees():
    """Test rapide de la base de données"""
    print("\n🧪 Test de la base de données...")
    
    try:
        conn = sqlite3.connect('data/crm_ecommerce.db')
        cursor = conn.cursor()
        
        # Compter les clients
        cursor.execute('SELECT COUNT(*) FROM client')
        nb_clients = cursor.fetchone()[0]
        print(f"👥 {nb_clients} clients dans la base")
        
        # Lister quelques clients
        cursor.execute('SELECT nom, prenom, email FROM client LIMIT 3')
        clients = cursor.fetchall()
        
        for nom, prenom, email in clients:
            print(f"   📧 {prenom} {nom} - {email}")
        
        conn.close()
        print("✅ Base de données fonctionnelle !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test DB: {e}")
        return False

def main():
    """Fonction principale de réparation"""
    banner_reparation()
    
    print("🔧 Début de la réparation automatique...")
    print()
    
    # 1. Vérifier structure
    verifier_structure_projet()
    
    # 2. Réparer base de données
    if verifier_base_donnees():
        print()
        
        # 3. Tester DB
        if tester_base_donnees():
            print()
            
            # 4. Corriger templates
            corriger_templates()
            
            print()
            print("🎉" + "=" * 60 + "🎉")
            print("✅ RÉPARATION TERMINÉE AVEC SUCCÈS !")
            print("🎉" + "=" * 60 + "🎉")
            print()
            print("🚀 Le système est maintenant prêt !")
            print()
            print("📋 PROCHAINES ÉTAPES :")
            print("   1. cd web_app")
            print("   2. python app.py")
            print("   3. Ouvrir http://localhost:5000")
            print("   4. S'inscrire avec un nouveau compte")
            print("   5. Tester l'envoi de messages")
            print()
            print("🎯 CLIENTS DE TEST DISPONIBLES :")
            print("   📧 marie.martin@example.com")
            print("   📧 jean.dupont@example.com") 
            print("   📧 pierre.durand@example.com")
            print()
            
            return True
    
    print("❌ Réparation échouée")
    return False

if __name__ == "__main__":
    main() 
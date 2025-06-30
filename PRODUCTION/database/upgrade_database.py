#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de mise à jour de la base de données
Ajoute les tables pour la base de connaissances et l'intégration Notion
"""

import sqlite3
import os
from datetime import datetime
import pytz  # Ajout pour la gestion du fuseau horaire

# Définir le fuseau horaire de Paris
PARIS_TZ = pytz.timezone('Europe/Paris')

def get_current_paris_time():
    """Retourne l'heure actuelle à Paris"""
    return datetime.now(PARIS_TZ)

def upgrade_database(db_path='data/crm_ecommerce.db'):
    """Met à jour la base de données avec les nouvelles tables"""
    
    print("🔄 Mise à jour de la base de données...")
    
    try:
        # Créer une sauvegarde
        backup_path = f"{db_path}.backup_{get_current_paris_time().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(db_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"📋 Sauvegarde créée: {backup_path}")
        
        # Connexion à la base
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Exécuter tout le schéma d'un coup
        schema_path = os.path.join(os.path.dirname(__file__), 'schema_support_enhanced.sql')
        print(f"📜 Exécution du schéma SQL complet depuis : {schema_path}")
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        
        print("📦 Tables et vues créées/mises à jour.")

        # Insérer les produits par défaut
        print("🛍️ Insertion des produits par défaut...")
        insert_default_products(cursor)

        # Insérer les réponses support par défaut (déjà dans le schéma, mais on s'assure qu'elles y sont)
        print("💬 Vérification des réponses support par défaut...")
        # L'instruction `INSERT OR REPLACE` dans le schéma gère déjà cela.

        # Valider les changements
        conn.commit()
        conn.close()
        
        print("✅ Base de données mise à jour avec succès !")
        print("📋 Nouvelles fonctionnalités disponibles :")
        print("  - Gestion des produits et des stocks")
        print("  - Système de commandes clients")

    except sqlite3.Error as e:
        print(f"❌ Erreur SQLite lors de la mise à jour: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


def insert_default_products(cursor):
    """Insère une liste de produits par défaut dans la base de données."""
    
    products = [
        ('Chargeur Rapide USB-C 65W', 'Un chargeur universel et puissant pour tous vos appareils.', 29.99, 150, 'static/images/charger.jpg'),
        ('Écouteurs Sans Fil "AuraPods"', 'Qualité sonore immersive et réduction de bruit active.', 89.90, 80, 'static/images/earbuds.jpg'),
        ('Batterie Externe 20000mAh', 'Ne tombez plus jamais en panne de batterie. Double port USB.', 45.50, 200, 'static/images/powerbank.jpg'),
        ('Clavier Mécanique Rétroéclairé "ProType"', 'Frappe précise et confortable, idéal pour le travail et le jeu.', 75.00, 40, 'static/images/keyboard.jpg'),
        ('Souris Gamer Ergonomique "SwiftClick"', 'Capteur haute précision 16000 DPI et 8 boutons programmables.', 55.20, 0, 'static/images/mouse.jpg') # En rupture de stock
    ]
    
    # Utiliser INSERT OR IGNORE pour éviter les doublons si le nom est unique
    # Pour cet exemple, nous allons utiliser une approche simple de suppression/insertion
    # ou de vérification avant insertion
    
    for product in products:
        cursor.execute("SELECT id FROM products WHERE name = ?", (product[0],))
        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT INTO products (name, description, price, stock, image_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (*product, get_current_paris_time()))
    
    print(f"  -> {len(products)} produits vérifiés/insérés.")


if __name__ == '__main__':
    # Définir le chemin de la DB relatif au script
    db_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)
    
    db_path = os.path.join(db_directory, 'crm_ecommerce.db')
    
    print(f"Base de données cible : {db_path}")
    upgrade_database(db_path)
    print("\nScript terminé.") 
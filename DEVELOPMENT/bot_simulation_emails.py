#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot de Simulation d'Emails - Test de Charge du Support Client
Envoie automatiquement des messages avec les adresses de la base de données
"""

import sys
import os
import time
import random
import threading
from datetime import datetime, timedelta
import requests
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager

class EmailBot:
    """Bot de simulation d'emails pour tester la charge du support"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.db_manager = DatabaseManager()
        self.is_running = False
        self.sent_count = 0
        self.error_count = 0
        self.response_times = []
        
        # Messages de simulation variés
        self.message_templates = {
            'retard_livraison': [
                "Bonjour, ma commande #{order_id} est en retard de {days} jours. Pouvez-vous me donner des nouvelles ?",
                "Salut, je n'ai toujours pas reçu ma commande passée le {date}. C'est urgent !",
                "Bonjour, où en est ma livraison ? Cela fait une semaine que j'attends.",
                "Ma commande #{order_id} devait arriver hier. Que se passe-t-il ?",
                "Pouvez-vous vérifier le statut de ma commande ? Elle est très en retard."
            ],
            'produit_defectueux': [
                "Le produit que j'ai reçu hier est cassé. Je veux un échange immédiat.",
                "Mon {product} ne fonctionne pas du tout. L'écran est fissuré.",
                "Produit défectueux reçu ! Je demande un remboursement complet.",
                "Le {product} commandé est arrivé endommagé dans le colis.",
                "Très déçu, le produit reçu ne correspond pas à la description."
            ],
            'remboursement': [
                "Je souhaite annuler ma commande #{order_id} et être remboursé.",
                "Bonjour, pouvez-vous procéder au remboursement de ma commande ?",
                "Je veux un remboursement pour ma commande du {date}.",
                "Commande non conforme, je demande le remboursement intégral.",
                "Problème avec ma commande, remboursement souhaité SVP."
            ],
            'information_commande': [
                "Bonjour, pouvez-vous me donner le statut de ma commande #{order_id} ?",
                "Où en est ma commande passée le {date} ?",
                "J'aimerais connaître la date de livraison prévue.",
                "Pouvez-vous me donner le numéro de suivi de mon colis ?",
                "Ma commande a-t-elle bien été expédiée ?"
            ],
            'reclamation': [
                "C'est inadmissible ! Votre service client ne répond jamais !",
                "Je suis très mécontent de votre service. Cela fait 2 semaines que j'attends !",
                "Votre site a des bugs, impossible de suivre ma commande !",
                "Service client décevant, je vais laisser un avis négatif !",
                "Très insatisfait de mon expérience d'achat chez vous."
            ]
        }
        
        self.subjects = [
            "Problème avec ma commande",
            "Retard de livraison",
            "Produit défectueux",
            "Demande de remboursement",
            "Question sur ma commande",
            "Réclamation",
            "Urgent - Commande",
            "Service client",
            "Problème technique",
            "Insatisfaction"
        ]
        
        self.products = [
            "smartphone", "ordinateur portable", "écouteurs", "montre", "tablette",
            "appareil photo", "imprimante", "casque gaming", "clavier", "souris"
        ]
    
    def get_random_client(self):
        """Récupère un client aléatoire de la base de données"""
        try:
            clients = self.db_manager.get_all_clients()
            if clients:
                return random.choice(clients)
            return None
        except Exception as e:
            print(f"Erreur récupération client: {e}")
            return None
    
    def generate_message(self, category):
        """Génère un message aléatoire selon la catégorie"""
        templates = self.message_templates.get(category, self.message_templates['information_commande'])
        template = random.choice(templates)
        
        # Variables de remplacement
        replacements = {
            '{order_id}': random.randint(10000, 99999),
            '{days}': random.randint(2, 10),
            '{date}': (datetime.now() - timedelta(days=random.randint(1, 14))).strftime('%d/%m/%Y'),
            '{product}': random.choice(self.products)
        }
        
        message = template
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, str(value))
        
        return message
    
    def send_message(self, client_email, subject, message):
        """Envoie un message au support via l'API"""
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/process-message",
                json={
                    'email': client_email,
                    'subject': subject,
                    'message': message
                },
                timeout=60
            )
            
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            if response.status_code == 200:
                data = response.json()
                self.sent_count += 1
                
                # Log détaillé
                print(f"✅ [BOT] Message envoyé - {client_email}")
                print(f"   📝 Sujet: {subject}")
                print(f"   🏷️  Catégorie détectée: {data.get('category', 'N/A')}")
                print(f"   ⏱️  Temps de traitement: {response_time:.1f}s")
                print(f"   📊 Qualité: {data.get('quality_score', 0):.2f}")
                print(f"   📨 Réponse: {len(data.get('response', ''))} caractères")
                
                return True, data
            else:
                self.error_count += 1
                print(f"❌ [BOT] Erreur {response.status_code} - {client_email}")
                return False, None
                
        except Exception as e:
            self.error_count += 1
            print(f"💥 [BOT] Exception - {client_email}: {e}")
            return False, None
    
    def run_simulation(self, duration_minutes=30, messages_per_minute=2):
        """Lance la simulation d'emails"""
        print(f"🤖 DÉMARRAGE SIMULATION BOT EMAIL")
        print(f"⏱️  Durée: {duration_minutes} minutes")
        print(f"📧 Fréquence: {messages_per_minute} messages/minute")
        print(f"🎯 Total prévu: {duration_minutes * messages_per_minute} messages")
        print("=" * 60)
        
        self.is_running = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        message_interval = 60 / messages_per_minute  # Intervalle entre messages
        
        while self.is_running and time.time() < end_time:
            # Récupérer un client aléatoire
            client = self.get_random_client()
            if not client:
                print("⚠️  Aucun client disponible, pause 30s...")
                time.sleep(30)
                continue
            
            client_email = client[3]  # email est le 4ème champ
            
            # Générer message aléatoire
            category = random.choice(list(self.message_templates.keys()))
            subject = random.choice(self.subjects)
            message = self.generate_message(category)
            
            # Envoyer le message
            success, response_data = self.send_message(client_email, subject, message)
            
            # Attendre avant le prochain message
            if self.is_running:
                time.sleep(message_interval)
        
        self.is_running = False
        self.print_statistics()
    
    def run_burst_test(self, burst_count=10, delay_between_bursts=5):
        """Test en rafale pour vérifier la résistance"""
        print(f"💥 TEST EN RAFALE - {burst_count} messages simultanés")
        print("=" * 50)
        
        threads = []
        
        for i in range(burst_count):
            client = self.get_random_client()
            if not client:
                continue
                
            category = random.choice(list(self.message_templates.keys()))
            subject = f"[BURST-{i+1:02d}] {random.choice(self.subjects)}"
            message = self.generate_message(category)
            
            thread = threading.Thread(
                target=self.send_message,
                args=(client[3], subject, message)
            )
            threads.append(thread)
        
        # Lancer tous les threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Attendre la fin
        for thread in threads:
            thread.join()
        
        burst_time = time.time() - start_time
        print(f"🏁 Rafale terminée en {burst_time:.1f}s")
        
        time.sleep(delay_between_bursts)
    
    def print_statistics(self):
        """Affiche les statistiques de la simulation"""
        print("\n" + "=" * 60)
        print("📊 STATISTIQUES DE SIMULATION")
        print("=" * 60)
        
        print(f"✅ Messages envoyés: {self.sent_count}")
        print(f"❌ Erreurs: {self.error_count}")
        print(f"📈 Taux de succès: {(self.sent_count / (self.sent_count + self.error_count) * 100):.1f}%")
        
        if self.response_times:
            avg_time = sum(self.response_times) / len(self.response_times)
            min_time = min(self.response_times)
            max_time = max(self.response_times)
            
            print(f"⏱️  Temps de réponse moyen: {avg_time:.1f}s")
            print(f"⚡ Temps minimum: {min_time:.1f}s")
            print(f"🐌 Temps maximum: {max_time:.1f}s")
        
        print("=" * 60)
    
    def stop_simulation(self):
        """Arrête la simulation"""
        self.is_running = False
        print("🛑 Arrêt de la simulation demandé...")

def main():
    """Menu principal du bot"""
    bot = EmailBot()
    
    print("🤖 BOT DE SIMULATION D'EMAILS - SUPPORT CLIENT")
    print("=" * 50)
    print("1. Simulation continue (30 min, 2 msg/min)")
    print("2. Simulation rapide (5 min, 5 msg/min)")
    print("3. Test en rafale (10 messages simultanés)")
    print("4. Simulation personnalisée")
    print("5. Test unique")
    print("0. Quitter")
    
    try:
        choice = input("\nChoisissez une option: ")
        
        if choice == "1":
            bot.run_simulation(30, 2)
        elif choice == "2":
            bot.run_simulation(5, 5)
        elif choice == "3":
            bot.run_burst_test(10)
        elif choice == "4":
            duration = int(input("Durée en minutes: "))
            frequency = int(input("Messages par minute: "))
            bot.run_simulation(duration, frequency)
        elif choice == "5":
            client = bot.get_random_client()
            if client:
                category = random.choice(list(bot.message_templates.keys()))
                subject = random.choice(bot.subjects)
                message = bot.generate_message(category)
                
                print(f"\n📧 Test avec: {client[3]}")
                print(f"📝 Sujet: {subject}")
                print(f"💬 Message: {message}")
                
                success, data = bot.send_message(client[3], subject, message)
                if success:
                    print("✅ Test réussi !")
                else:
                    print("❌ Test échoué")
        elif choice == "0":
            print("👋 Au revoir !")
        else:
            print("❌ Option invalide")
            
    except KeyboardInterrupt:
        print("\n🛑 Interruption utilisateur")
        bot.stop_simulation()
    except Exception as e:
        print(f"💥 Erreur: {e}")

if __name__ == "__main__":
    main() 
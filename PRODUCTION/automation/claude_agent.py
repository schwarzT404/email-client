#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Claude - Traitement Intelligent des Messages Client
Utilise l'API Claude d'Anthropic pour la classification et génération de réponses
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Module anthropic non disponible. Installation: pip install anthropic")

class ClaudeAgent:
    """Agent Claude pour le traitement intelligent des messages client"""
    
    def __init__(self, api_key: Optional[str] = None, db_manager=None):
        """
        Initialise l'agent Claude
        """
        print("🤖 [ClaudeAgent] Initialisation en cours...")
        self.db_manager = db_manager
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self.is_ready = False
        
        if not ANTHROPIC_AVAILABLE:
            print("❌ [ClaudeAgent] Librairie 'anthropic' non trouvée. Agent inactif.")
            return

        if not self.api_key:
            print("❌ [ClaudeAgent] Clé API ANTHROPIC_API_KEY non trouvée. Agent inactif.")
            return
        
        print("🔑 [ClaudeAgent] Clé API trouvée.")

        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.is_ready = True
            print("✅ [ClaudeAgent] Initialisation réussie. Agent prêt.")
        except Exception as e:
            print(f"❌ [ClaudeAgent] ERREUR D'INITIALISATION : {e}")
            self.client = None
            self.is_ready = False
    
    def get_customer_context(self, email: str) -> Dict[str, Any]:
        """Récupère le contexte client depuis la base de données (DÉSACTIVÉ)"""
        return {}
    
    def classify_message(self, message: str, subject: str = "", customer_context: Dict = None) -> Dict[str, Any]:
        """
        Classifie un message client avec Claude
        
        Args:
            message: Message du client
            subject: Sujet du message
            customer_context: Contexte client (commandes, historique)
            
        Returns:
            Dict avec la classification et les détails
        """
        if not self.is_ready:
            return self._fallback_classification(message)
            
        try:
            # Préparer le contexte
            context_str = ""
            if customer_context and customer_context.get("client"):
                client = customer_context["client"]
                context_str = f"""
CONTEXTE CLIENT:
- Nom: {client.get('prenom')} {client.get('nom')}
- Email: {client.get('email')}
- Type: {client.get('type')}
- Nombre de commandes: {customer_context.get('nb_commandes', 0)}
- Total dépensé: {customer_context.get('total_depense', 0)}€
"""
                
                if customer_context.get("commandes"):
                    context_str += "\nDERNIÈRES COMMANDES:\n"
                    for cmd in customer_context["commandes"][-3:]:  # 3 dernières
                        context_str += f"- Commande #{cmd['id']}: {cmd['montant']}€ ({cmd['statut']})\n"
            
            # Prompt pour la classification
            prompt = f"""Tu es un assistant IA spécialisé dans le support client e-commerce. 

{context_str}

SUJET: {subject}
MESSAGE CLIENT: {message}

Analyse ce message et fournis une classification JSON avec:
1. "category": Une des catégories principales
   - "retard_livraison": Problèmes de livraison, retards, colis perdu
   - "remboursement": Demandes de remboursement, retours
   - "produit_defectueux": Produits cassés, défectueux, non conformes
   - "information_commande": Statut commande, suivi, modifications
   - "reclamation": Insatisfaction, plaintes, réclamations
   - "autre": Autres demandes

2. "urgency": Niveau d'urgence (1-5, 5=très urgent)
3. "sentiment": Sentiment client ("positif", "neutre", "negatif", "tres_negatif")
4. "key_elements": Liste des éléments clés identifiés
5. "requires_human": true/false si nécessite intervention humaine
6. "confidence": Score de confiance (0-1)

Réponds uniquement avec le JSON, sans autres commentaires."""

            # Appel à l'API Claude
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parser la réponse JSON
            result = json.loads(response.content[0].text)
            
            # Ajouter des métadonnées
            result.update({
                "processed_at": datetime.now().isoformat(),
                "model": "claude-3-sonnet-20240229",
                "has_context": bool(customer_context and customer_context.get("client"))
            })
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Erreur parsing JSON Claude: {e}")
            return self._fallback_classification(message)
        except Exception as e:
            print(f"Erreur classification Claude: {e}")
            return self._fallback_classification(message)
    
    def generate_response(self, message: str, classification: Dict, customer_context: Dict = None) -> str:
        """
        Génère une réponse personnalisée avec Claude
        
        Args:
            message: Message original du client
            classification: Résultat de la classification
            customer_context: Contexte client
            
        Returns:
            Réponse générée par Claude
        """
        if not self.is_ready:
            return self._fallback_response(classification.get("category", "autre"))
            
        try:
            # Préparer le contexte client
            context_str = ""
            client_name = ""
            
            if customer_context and customer_context.get("client"):
                client = customer_context["client"]
                client_name = client.get("prenom", "")
                context_str = f"""
INFORMATIONS CLIENT:
- Nom: {client.get('prenom')} {client.get('nom')}
- Type de client: {client.get('type')}
- Historique: {customer_context.get('nb_commandes', 0)} commandes, {customer_context.get('total_depense', 0)}€ dépensés
"""
                
                # Ajouter info sur les commandes récentes si pertinent
                if customer_context.get("commandes") and classification.get("category") in ["retard_livraison", "information_commande"]:
                    recent_orders = customer_context["commandes"][-2:]
                    context_str += "\nCOMMANDES RÉCENTES:\n"
                    for cmd in recent_orders:
                        context_str += f"- Commande #{cmd['id']}: {cmd['montant']}€ - {cmd['statut']}\n"
            
            # Instructions spécifiques selon la catégorie
            category_instructions = {
                "retard_livraison": "Excuses sincères, explication des démarches entreprises, délai de résolution",
                "remboursement": "Compréhension, processus de remboursement, délais",
                "produit_defectueux": "Excuses, solution de remplacement immédiate, geste commercial",
                "information_commande": "Informations précises, transparence, suivi",
                "reclamation": "Écoute active, prise en charge personnalisée, solution",
                "autre": "Réponse personnalisée selon le contexte"
            }
            
            category = classification.get("category", "autre")
            urgency = classification.get("urgency", 3)
            sentiment = classification.get("sentiment", "neutre")
            
            # Adapter le ton selon l'urgence et le sentiment
            tone_instruction = ""
            if urgency >= 4 or sentiment == "tres_negatif":
                tone_instruction = "Ton très attentionné et prioritaire. Intervention immédiate."
            elif sentiment == "negatif":
                tone_instruction = "Ton empathique et rassurant."
            else:
                tone_instruction = "Ton professionnel et bienveillant."
            
            # Prompt pour la génération de réponse
            prompt = f"""Tu es un expert en support client e-commerce français. Ta mission est de créer une réponse UNIQUE et PERSONNALISÉE.

{context_str}

MESSAGE ORIGINAL DU CLIENT: {message}

ANALYSE:
- Catégorie: {category}
- Urgence: {urgency}/5
- Sentiment: {sentiment}
- Éléments clés: {classification.get('key_elements', [])}

CONTRAINTES ABSOLUES:
❌ INTERDIT: Utiliser des phrases génériques comme "Nous avons bien reçu votre demande", "Dans les plus brefs délais", "Cordialement l'équipe support"
❌ INTERDIT: Formules toutes faites et automatiques
❌ INTERDIT: Réponses qui pourraient être envoyées à n'importe qui

✅ OBLIGATOIRE: 
- Répondre SPÉCIFIQUEMENT aux points mentionnés dans le message
- Utiliser des détails concrets du message du client
- Personnaliser selon {client_name if client_name else "le client"}
- Adopter un ton naturel et humain
- Proposer des solutions concrètes et précises
- {tone_instruction}

STRUCTURE REQUISE:
1. Salutation personnalisée avec prénom si disponible
2. Référence EXPLICITE au problème spécifique mentionné
3. Explication détaillée de la situation
4. Actions concrètes entreprises ou à entreprendre
5. Délais précis (pas de "dans les plus brefs délais")
6. Signature personnalisée

EXEMPLES DE BONNES PRATIQUES:
- "J'ai vérifié votre commande #12345 et je constate que..."
- "Concernant le produit XYZ que vous avez reçu..."
- "Votre colis parti le 15/01 devrait arriver demain avant 14h"
- "Je vous rembourse dès maintenant les 47,99€ sur votre carte"

LONGUEUR: 150-300 mots maximum, direct et efficace.

Génère maintenant une réponse UNIQUE et PERSONNALISÉE:"""

            # Appel à Claude 4 pour génération avec réflexion
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",  # Remplacé par le dernier modèle Sonnet
                max_tokens=3000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"Erreur génération réponse Claude: {e}")
            return self._fallback_response(classification.get("category", "autre"))
    
    def process_customer_message(self, email: str, message: str, subject: str = "", context: Dict = None) -> Dict[str, Any]:
        """
        Traite complètement un message client avec Claude
        
        Args:
            email: Email du client
            message: Message du client
            subject: Sujet du message
            context: Contexte client (commandes, historique)
            
        Returns:
            Dict avec classification, réponse et métadonnées
        """
        try:
            customer_context = context or {}
            
            # 2. Classifier le message
            classification = self.classify_message(message, subject, customer_context)
            
            # 3. Générer la réponse
            response = self.generate_response(message, classification, customer_context)
            
            # 4. Créer le ticket ID
            ticket_id = f"CL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 5. Calculer le score de qualité
            quality_score = self._calculate_quality_score(
                classification, 
                len(response), 
                bool(customer_context.get("client"))
            )
            
            return {
                "email": email,
                "subject": subject,
                "message": message,
                "category": classification.get("category"),
                "urgency": classification.get("urgency"),
                "sentiment": classification.get("sentiment"),
                "key_elements": classification.get("key_elements", []),
                "requires_human": classification.get("requires_human", False),
                "confidence": classification.get("confidence", 0.85),
                "response": response,
                "quality_score": quality_score,
                "ticket_id": ticket_id,
                "processed_at": datetime.now().isoformat(),
                "customer_context": customer_context,
                "model": "claude-3-sonnet-20240229",
                "has_customer_data": bool(customer_context.get("client"))
            }
            
        except Exception as e:
            print(f"Erreur traitement message: {e}")
            return {
                "email": email,
                "error": str(e),
                "processed_at": datetime.now().isoformat(),
                "model": "claude-3-sonnet-20240229 (erreur)"
            }
    
    def _fallback_classification(self, message: str) -> Dict[str, Any]:
        """Classification de secours basée sur mots-clés"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['retard', 'livraison', 'reçu', 'arrivé', 'expédition']):
            category = 'retard_livraison'
        elif any(word in message_lower for word in ['remboursement', 'rembourser', 'annuler']):
            category = 'remboursement'
        elif any(word in message_lower for word in ['défectueux', 'cassé', 'abîmé', 'problème']):
            category = 'produit_defectueux'
        elif any(word in message_lower for word in ['mécontent', 'insatisfait', 'plainte']):
            category = 'reclamation'
        else:
            category = 'information_commande'
            
        return {
            "category": category,
            "urgency": 3,
            "sentiment": "neutre",
            "key_elements": [],
            "requires_human": False,
            "confidence": 0.6,
            "model": "fallback"
        }
    
    def _fallback_response(self, category: str) -> str:
        """Réponse de secours personnalisée basée sur la catégorie"""
        import random
        
        responses = {
            'retard_livraison': [
                """Bonjour,

Je comprends votre inquiétude concernant votre commande qui tarde à arriver. 

Je viens de vérifier le suivi de votre colis auprès de notre transporteur. Votre commande est actuellement en transit et devrait vous être livrée sous 48h maximum.

Je vous envoie par email le numéro de suivi pour que vous puissiez suivre l'acheminement en temps réel.

Si votre colis n'arrive pas mercredi, contactez-moi directement et je vous propose une solution immédiate.

Bien à vous,
Sophie - Service Client""",

                """Bonjour,

Désolée pour ce retard qui doit vous contrarier, c'est tout à fait compréhensible.

Votre commande a été expédiée mais notre transporteur a eu un incident sur votre secteur. J'ai fait remonter votre dossier en priorité et votre colis sera livré demain avant 17h.

En compensation de ce désagrément, je vous accorde un bon de réduction de 15% valable sur votre prochaine commande.

Je reste à votre disposition si besoin.

Cordialement,
Marc - Support Client"""
            ],
            
            'remboursement': [
                """Bonjour,

J'ai bien noté votre demande de remboursement et je la comprends parfaitement.

Je lance immédiatement la procédure : vous recevrez un email de confirmation d'ici 2h et le remboursement sera effectif sur votre compte sous 72h.

Le montant remboursé est de [montant] € et apparaîtra sur votre relevé bancaire avec la mention "REMB COMMANDE".

N'hésitez pas si vous avez des questions.

Cordialement,
Julie - Service Client""",
                
                """Bonjour,

Votre demande de remboursement est tout à fait justifiée, je m'en occupe de suite.

Je viens de valider le remboursement de votre commande. Vous devriez voir le crédit apparaître sur votre compte bancaire d'ici vendredi.

Si ce n'est pas le cas, recontactez-moi avec cette référence : RBT-{datetime.now().strftime('%Y%m%d')}.

Merci de votre confiance.

Bien à vous,
Thomas - Support Client"""
            ],
            
            'produit_defectueux': [
                """Bonjour,

Je suis vraiment navré que votre produit soit arrivé dans cet état, c'est inacceptable de notre part.

Je vous expédie dès aujourd'hui un produit de remplacement identique, livraison prévue demain. Vous n'avez rien à renvoyer, gardez le produit défectueux.

En plus, je vous offre un geste commercial de 20€ sur votre prochaine commande pour ce désagrément.

Voici votre numéro de suivi : il arrivera par SMS dans 1h.

Très cordialement,
Emma - Service Client""",
                
                """Bonjour,

Quelle déception cela doit être de recevoir un produit abîmé ! Mes excuses sincères.

Je traite votre dossier en urgence : nouveau produit expédié ce matin par Chronopost, vous le recevrez demain avant midi.

Je vous rembourse aussi les frais de port de votre commande initiale (7,90€) qui seront crédités sous 24h.

Tenez-moi au courant de la réception.

Bien à vous,
Paul - Support Client"""
            ],
            
            'reclamation': [
                """Bonjour,

Je prends très au sérieux votre réclamation et je vous présente toutes mes excuses pour cette expérience décevante.

J'ai immédiatement fait remonter votre situation à ma responsable et nous mettons tout en œuvre pour rectifier le tir.

Je vous rappelle personnellement demain matin avant 11h pour vous présenter une solution concrète et satisfaisante.

Votre satisfaction est ma priorité absolue.

Très cordialement,
Lucie - Service Client""",
                
                """Bonjour,

Votre mécontentement est parfaitement légitime et je m'en excuse au nom de toute l'équipe.

Je prends personnellement en charge votre dossier pour éviter que cela se reproduise. D'ici ce soir, vous aurez une proposition de compensation adaptée.

En attendant, voici mon email direct : support.prioritaire@monsite.com pour toute urgence.

Comptez sur moi pour résoudre cette situation.

Cordialement,
Antoine - Responsable Support"""
            ],
            
            'information_commande': [
                """Bonjour,

Concernant votre demande d'information sur votre commande, voici le point complet :

Votre commande est confirmée et en cours de préparation dans notre entrepôt. L'expédition aura lieu demain et la livraison est prévue jeudi.

Vous recevrez un SMS avec le créneau de livraison précis mercredi soir.

Autres infos utiles : commande payée, produits en stock, transporteur Colissimo.

J'espère avoir répondu à vos questions !

Bien à vous,
Sarah - Service Client""",
                
                """Bonjour,

Voici les informations que vous souhaitiez sur votre commande :

Statut actuel : expédiée hier, en transit vers votre adresse
Livraison estimée : demain entre 9h et 17h  
Transporteur : DPD (numéro de suivi en pièce jointe)

Si vous souhaitez modifier l'adresse de livraison, c'est encore possible jusqu'à ce soir 18h.

N'hésitez pas pour toute autre question.

Cordialement,
Kevin - Support Client"""
            ]
        }
        
        # Sélectionner aléatoirement une réponse dans la catégorie
        category_responses = responses.get(category, responses['information_commande'])
        return random.choice(category_responses)
    
    def _calculate_quality_score(self, classification: Dict, response_length: int, has_context: bool) -> float:
        """Calcule un score de qualité pour la réponse"""
        score = 0.7  # Score de base
        
        # Bonus pour la confiance de classification
        confidence = classification.get("confidence", 0.5)
        score += confidence * 0.2
        
        # Bonus pour la longueur de réponse appropriée
        if 200 <= response_length <= 800:
            score += 0.1
        
        # Bonus pour le contexte client
        if has_context:
            score += 0.1
        
        # Bonus pour l'utilisation de Claude
        if self.is_ready:
            score += 0.1
        
        return min(score, 1.0)  # Max 1.0

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut de l'agent Claude"""
        return {
            "claude_available": ANTHROPIC_AVAILABLE,
            "claude_ready": self.is_ready,
            "api_key_configured": bool(self.api_key),
            "model": "claude-3-sonnet-20240229" if self.is_ready else None,
            "last_check": datetime.now().isoformat()
        } 
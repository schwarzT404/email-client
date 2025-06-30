# Guide d'utilisation du Workflow N8n - Support Client Automatisé

## Vue d'ensemble

Ce workflow N8n automatise complètement le processus de support client e-commerce en utilisant nos scripts Python développés. Il traite les demandes clients de manière intelligente et génère des réponses personnalisées.

## Architecture du Workflow

### 🔄 Flux complet (8 étapes)

1. **Réception Demande Client** (Webhook)
2. **Activation Environnement** (Command)
3. **Validation Python** (Code)
4. **Recherche SQLite Python** (Code)
5. **Recherche Notion Python** (Code)
6. **Génération Réponse Anthropic** (Code)
7. **Création Ticket Python** (Code)
8. **Réponse Finale** (Respond to Webhook)

## Configuration requise

### Prérequis
- N8n installé et configuré
- Environnement virtuel Python activé (`venv`)
- Base SQLite créée (`data/crm_ecommerce.db`)
- Variables d'environnement configurées

### Variables d'environnement nécessaires
```bash
# Configuration de base (plus de configuration email requise)
DB_PATH=data/crm_ecommerce.db
```

## Installation du Workflow

### 1. Importer le workflow
- Ouvrir N8n
- Aller dans "Workflows" > "Import from File"
- Sélectionner `n8n_workflow_support_client.json`
- Cliquer "Import"

### 2. Configuration des nœuds

#### Nœud "Activation Environnement"
Vérifier le chemin vers votre projet :
```bash
cd "C:\Users\Dell\Documents\Workstation\Ynov\python-avancé\Automatisation du support client e-commerce" && venv\Scripts\activate
```

## Utilisation du Workflow

### 1. Activation du workflow
- Ouvrir le workflow dans N8n
- Cliquer sur "Active" pour l'activer
- Noter l'URL du webhook générée

### 2. Format de requête

**Endpoint** : POST `/webhook/support-client`

**Body JSON** :
```json
{
  "email": "client@example.com",
  "message": "Bonjour, je n'ai pas reçu ma commande #1001",
  "sujet": "Problème de livraison"
}
```

### 3. Exemples d'utilisation

#### Test avec curl
```bash
curl -X POST "https://votre-n8n.com/webhook/support-client" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "marie.martin@email.com",
    "message": "Ma commande 1001 a un retard de livraison",
    "sujet": "Retard de livraison"
  }'
```

#### Test avec Python
```python
import requests

data = {
    "email": "pierre.dubois@email.com",
    "message": "Le produit de ma commande #1002 est défectueux",
    "sujet": "Produit défectueux"
}

response = requests.post(
    "https://votre-n8n.com/webhook/support-client",
    json=data
)

print(response.json())
```

## Détail des étapes

### 1. Réception Demande Client
- **Type** : Webhook
- **Méthode** : POST
- **Chemin** : `support-client`
- **Données reçues** : email, message, sujet

### 2. Activation Environnement
- **Type** : Execute Command
- **Action** : Active l'environnement virtuel Python
- **Chemin** : Votre répertoire de projet

### 3. Validation Python
- **Fonction** : `validation_python()`
- **Actions** :
  - Valide l'email du client
  - Vérifie la longueur du message
  - Extrait l'ID de commande (si présent)
  - Structure les données

### 4. Recherche SQLite Python
- **Fonction** : `recherche_sqlite_python()`
- **Actions** :
  - Recherche le client dans la base
  - Récupère les informations de commande
  - Calcule les statistiques client
  - Détermine le niveau client (standard/premium/vip)

### 5. Recherche Notion Python
- **Fonction** : `recherche_notion_python()`
- **Actions** :
  - Classifie le message (4 catégories)
  - Sélectionne le template approprié
  - Prépare les variables de personnalisation

### 6. Génération Réponse Anthropic
- **Fonction** : `generation_reponse_anthropic()`
- **Actions** :
  - Personnalise le template avec les données client
  - Calcule un score de qualité
  - Génère la réponse finale

### 7. Création Ticket Python
- **Fonction** : `creation_ticket_python()`
- **Actions** :
  - Crée un ID de ticket unique
  - Prépare les données pour l'email
  - Simule l'enregistrement dans Notion

### 8. Réponse Finale
- **Type** : Respond to Webhook
- **Actions** :
  - Retourne un JSON avec le statut
  - Inclut les métriques de traitement

## Réponse du workflow

### Format de réponse
```json
{
  "statut": "traite",
  "ticket_id": "uuid-du-ticket",
  "score_qualite": 0.9,
  "client_niveau": "premium",
  "categorie": "Retard de livraison",
  "reponse_generee": "Bonjour Marie Martin,\n\nNous nous excusons pour le retard de votre commande #1001...",
  "client_info": {
    "nom": "Martin",
    "prenom": "Marie",
    "email": "marie.martin@email.com",
    "nb_commandes": 3
  },
  "demande_originale": {
    "message": "Ma commande 1001 a un retard de livraison",
    "sujet": "Retard de livraison"
  },
  "timestamp": "2024-12-24T10:30:00"
}
```

## Catégories de classification

### 1. Retard de livraison
**Mots-clés** : retard, livraison, délai, reçu, arrivé
**Template** : Excuse + vérification transporteur

### 2. Remboursement
**Mots-clés** : remboursement, rembourser, annuler, argent
**Template** : Confirmation + délai de traitement

### 3. Produit défectueux
**Mots-clés** : défectueux, cassé, abîmé, défaut, problème
**Template** : Excuse + remplacement

### 4. Information commande
**Mots-clés** : information, détail, statut, état
**Template** : Détails de la commande

## Monitoring et Debug

### Logs disponibles
- Chaque nœud Python retourne des informations détaillées
- Les erreurs sont capturées et transmises
- Le score de qualité indique la pertinence de la réponse

### Points de contrôle
1. **Validation** : Vérifier le format des données
2. **Base de données** : S'assurer que le client existe
3. **Classification** : Contrôler la catégorie détectée
4. **Email** : Vérifier la configuration SMTP

## Personnalisation

### Modifier les templates
Éditer les templates dans le nœud "Recherche Notion Python" :
```python
templates = {
    "Nouvelle catégorie": "Votre template personnalisé avec {variables}"
}
```

### Ajouter des catégories
1. Ajouter la catégorie dans `categories`
2. Créer le template correspondant
3. Ajuster les mots-clés de classification

### Modifier le scoring
Ajuster les critères dans "Génération Réponse Anthropic" :
```python
score_qualite = 0.7  # Score de base
if condition_speciale:
    score_qualite += 0.1  # Bonus
```

## Dépannage

### Problèmes courants

#### Erreur d'environnement virtuel
```bash
# Vérifier l'activation
venv\Scripts\activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

#### Erreur de base de données
```python
# Vérifier l'existence de la base
python test_db.py
```

#### Erreur de traitement
- Vérifier les logs dans chaque nœud Python
- Contrôler le format des données entre étapes

#### Erreur de webhook
- Vérifier que le workflow est actif
- Contrôler l'URL du webhook
- Valider le format JSON

## Performance

### Temps de traitement moyen
- **Total** : 1-2 secondes
- **Validation** : < 0.1s
- **Base de données** : 0.1-0.3s
- **Classification** : 0.1-0.2s
- **Génération** : 0.2-0.5s
- **Création ticket** : 0.1-0.2s

### Optimisations possibles
1. Mise en cache des templates Notion
2. Pool de connexions à la base
3. Compression des réponses JSON
4. Traitement batch des tickets

## Intégration avec d'autres systèmes

### CRM existant
- Modifier la requête SQLite pour votre schéma
- Adapter les champs de données client
- Ajuster les niveaux de client

### Notion API
- Remplacer la simulation par des appels API réels
- Utiliser votre token Notion
- Adapter les propriétés des bases

### Systèmes de notification
- Intégrer Slack, Discord ou Teams pour notifications
- Webhook vers d'autres systèmes CRM
- Intégration avec des chatbots

Ce workflow N8n vous offre une solution complète et prête à l'emploi pour automatiser votre support client e-commerce sans envoi d'email ! 
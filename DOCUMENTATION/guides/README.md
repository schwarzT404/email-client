# 🤖 Automatisation du support client e-commerce

Système intelligent d'automatisation du support client pour les entreprises e-commerce, intégrant une base de données relationnelle, des bases de connaissances Notion et un agent IA pour générer des réponses personnalisées.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)

## ✨ Fonctionnalités

### 🗄️ Base de données relationnelle (MySQL/MariaDB)
- **Table `client`** : Gestion centralisée des informations clients
- **Table `commande`** : Suivi complet des commandes avec relations
- Requêtes optimisées et indexées
- Données d'exemple pour les tests

### 📝 Intégration Notion
- **Base "Réponses support"** : Templates de réponses par catégorie
- **Base "Contacts clients"** : Suivi des tickets et échanges
- Gestion automatisée des statuts
- Personnalisation avancée des réponses

### 🤖 Agent IA intelligent
- Classification automatique des messages clients
- Génération de réponses personnalisées
- Intégration OpenAI pour l'amélioration des réponses
- Extraction automatique des numéros de commande
- Traitement en lot des tickets en attente

### 🛠️ Outils de gestion
- Interface en ligne de commande complète
- Mode interactif pour les tests
- Statistiques et rapports détaillés
- Scripts d'initialisation automatique

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MESSAGE       │    │   AGENT IA      │    │   RÉPONSE       │
│   CLIENT        │───▶│   CLASSIFIER    │───▶│   PERSONNALISÉE │
│                 │    │   & GENERATOR   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   BASE DE       │              │
         └─────────────▶│   DONNÉES       │◀─────────────┘
                        │   MYSQL         │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   BASES         │
                        │   NOTION        │
                        │   (Knowledge &  │
                        │    Tickets)     │
                        └─────────────────┘
```

## 🚀 Installation

### Prérequis
- Python 3.8+
- MySQL ou MariaDB
- Compte Notion avec accès API
- Compte OpenAI (optionnel)

### 1. Cloner le projet
```bash
git clone <repository-url>
cd automatisation-support-client
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configuration de la base de données
```bash
# Créer la base de données MySQL
mysql -u root -p
CREATE DATABASE crm_ecommerce;
exit

# Initialiser les tables
mysql -u root -p crm_ecommerce < database/schema.sql
```

## ⚙️ Configuration

### 1. Variables d'environnement
Créez un fichier `.env` basé sur `env.example` :

```bash
cp env.example .env
```

Éditez `.env` avec vos paramètres :

```env
# Base de données
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=crm_ecommerce

# Notion
NOTION_TOKEN=secret_abc123...
NOTION_BASE_REPONSES_ID=database_id_1
NOTION_BASE_CONTACTS_ID=database_id_2

# OpenAI (optionnel)
OPENAI_API_KEY=sk-...
```

### 2. Configuration Notion

#### Base "Réponses support"
Créez une base de données Notion avec ces propriétés :
- `catégorie` (Select)
- `réponse_générique` (Rich Text)

#### Base "Contacts clients"  
Créez une base de données Notion avec ces propriétés :
- `nom_prenom` (Title)
- `email_client` (Email)
- `id_commande` (Number)
- `message_initial` (Rich Text)
- `catégorie` (Select)
- `réponse_personnalisée` (Rich Text)
- `statut` (Select : Nouveau, En cours, Traité, Traité automatiquement)

### 3. Récupérer les IDs Notion
```bash
# URL de votre base : https://notion.so/workspace/DATABASE_ID?v=...
# L'ID est la partie entre les derniers "/" et "?"
```

## 🎯 Utilisation

### Initialisation du système
```bash
python main.py --setup
```

### Mode interactif (recommandé pour les tests)
```bash
python main.py --interactive
```

### Traiter un message spécifique
```bash
python main.py --message "client@email.com" "Message du client"
python main.py --message "client@email.com" "Problème commande #123" --order-id 123
```

### Traiter tous les tickets en attente
```bash
python main.py --process-pending
```

### Afficher les statistiques
```bash
python main.py --stats
```

## 📁 Structure du projet

```
automatisation-support-client/
├── 📁 database/
│   ├── schema.sql              # Structure de la base de données
│   └── db_manager.py          # Gestionnaire base de données
├── 📁 notion/
│   └── notion_manager.py      # Gestionnaire Notion
├── 📁 automation/
│   └── support_agent.py       # Agent IA principal
├── config.py                  # Configuration centrale
├── main.py                   # Script principal
├── requirements.txt          # Dépendances Python
├── env.example              # Template de configuration
└── README.md               # Documentation
```

## 🔧 API Reference

### DatabaseManager
```python
from database.db_manager import DatabaseManager

db = DatabaseManager()

# Gestion des clients
client = db.get_client_by_email("email@test.com")
db.create_client("email@test.com", "Nom", "Prénom")

# Gestion des commandes
commande = db.get_commande_by_id(123)
commandes = db.get_commandes_by_client(client_id)

# Statistiques
stats = db.get_client_stats(client_id)
```

### NotionManager
```python
from notion.notion_manager import NotionManager

notion = NotionManager()

# Réponses types
reponses = notion.get_reponses_by_categorie("Retard de livraison")
notion.create_reponse_type("Catégorie", "Template réponse")

# Tickets clients
ticket_id = notion.create_contact_ticket(email, nom, id_commande, message)
notion.update_ticket_response(ticket_id, réponse, "Traité")
tickets = notion.get_pending_tickets()
```

### SupportAgent
```python
from automation.support_agent import SupportAgent

agent = SupportAgent()

# Traitement d'un message
result = agent.process_customer_message(
    email="client@test.com",
    message="Message du client",
    commande_id=123
)

# Traitement en lot
results = agent.process_pending_tickets()

# Statistiques
stats = agent.get_statistics()
```

## 📊 Catégories de messages supportées

Le système classifie automatiquement les messages selon ces catégories :

| Catégorie | Mots-clés détectés | Template de réponse |
|-----------|-------------------|-------------------|
| **Retard de livraison** | retard, livraison, délai, transporteur, suivi | Excuse + suivi + délai de réponse |
| **Remboursement** | remboursement, annuler, argent, retour | Confirmation + délai de traitement |
| **Produit défectueux** | défectueux, cassé, abîmé, défaut, problème | Excuse + remplacement |
| **Information commande** | information, détail, statut, facture | Récapitulatif de la commande |
| **Non classé** | Autres | Réponse générique |

## 🔍 Troubleshooting

### Erreur de connexion MySQL
```bash
# Vérifier que MySQL est démarré
sudo systemctl status mysql

# Vérifier les identifiants dans .env
# Tester la connexion
mysql -u root -p -h localhost
```

### Erreur Notion API
```bash
# Vérifier le token dans .env
# Vérifier les permissions de l'intégration Notion
# Vérifier les IDs des bases de données
```

### Erreur OpenAI
```bash
# L'OpenAI est optionnel, le système fonctionne sans
# Vérifier la clé API si vous souhaitez l'utiliser
```

### Problème de modules Python
```bash
# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall

# Vérifier la version Python
python --version  # Doit être 3.8+
```

## 📈 Améliorations futures

- [ ] Interface web avec Flask/FastAPI
- [ ] Intégration avec des services email (IMAP/SMTP)
- [ ] Webhooks pour traitement en temps réel
- [ ] Métriques avancées et tableaux de bord
- [ ] Support multilingue
- [ ] Machine Learning pour améliorer la classification
- [ ] API REST pour intégrations tierces

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour vos modifications
3. Soumettre une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

**Développé avec ❤️ pour automatiser et améliorer l'expérience client e-commerce** 
# 🚀 Guide de Démarrage Rapide - Support Client Automatisé

## 📋 Configuration SQLite et Environnement Virtuel

### 1. Configuration automatique de l'environnement

**Sur Windows :**
```bash
# Double-cliquez sur setup_env.bat ou exécutez :
setup_env.bat
```

**Sur Linux/Mac :**
```bash
# Rendez le script exécutable et lancez-le :
chmod +x setup_env.sh
./setup_env.sh
```

### 2. Activation manuelle de l'environnement

**Sur Windows :**
```bash
venv\Scripts\activate
```

**Sur Linux/Mac :**
```bash
source venv/bin/activate
```

### 3. Configuration des variables d'environnement

```bash
# Copiez le fichier d'exemple
cp env.example .env

# Éditez le fichier .env avec vos paramètres
```

**Contenu minimum du fichier `.env` :**
```env
# Base de données SQLite (créée automatiquement)
DB_PATH=data/crm_ecommerce.db

# Configuration Notion (OBLIGATOIRE)
NOTION_TOKEN=secret_votre_token_notion
NOTION_BASE_REPONSES_ID=votre_id_base_reponses
NOTION_BASE_CONTACTS_ID=votre_id_base_contacts

# IA optionnelles
OPENAI_API_KEY=sk-votre_cle_openai
ANTHROPIC_API_KEY=sk-ant-votre_cle_anthropic
```

## 🎯 Démarrage Rapide

### Étape 1 : Initialisation du système
```bash
# Activez l'environnement virtuel
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Initialisez la base SQLite et Notion
python main.py --setup
```

### Étape 2 : Test interactif
```bash
# Lancez le mode interactif pour tester
python main.py --interactive
```

### Étape 3 : Exemple de test
```
Email du client: jean.dupont@email.com
Message du client: Bonjour, je n'ai pas reçu ma commande #1
ID de commande (optionnel): 1
```

## 🗄️ Avantages de SQLite

✅ **Aucune installation de serveur requis**  
✅ **Base de données dans un fichier** (`data/crm_ecommerce.db`)  
✅ **Parfait pour le développement et tests**  
✅ **Portable et léger**  
✅ **Compatible avec le système existant**  

## 📝 Configuration Notion

### 1. Créer une intégration Notion
1. Allez sur https://www.notion.so/my-integrations
2. Cliquez sur "Nouvelle intégration"
3. Donnez un nom à votre intégration
4. Copiez le **token secret**

### 2. Créer les bases de données

#### Base "Réponses Support"
Créez une base avec ces colonnes :
- `catégorie` (Select) : Retard de livraison, Remboursement, etc.
- `réponse_générique` (Rich Text) : Template de réponse

#### Base "Contacts Clients"
Créez une base avec ces colonnes :
- `nom_prenom` (Title)
- `email_client` (Email) 
- `id_commande` (Number)
- `message_initial` (Rich Text)
- `catégorie` (Select)
- `réponse_personnalisée` (Rich Text)
- `statut` (Select) : Nouveau, En cours, Traité, Traité automatiquement

### 3. Partager les bases avec votre intégration
1. Dans chaque base, cliquez sur "Partager"
2. Ajoutez votre intégration
3. Copiez l'ID de la base depuis l'URL

## 🤖 Workflow N8n (Optionnel)

Le système inclut des fonctions prêtes pour N8n dans `n8n_functions/support_workflow.py` :

### Nœuds Python à configurer :

1. **Validation Python** : `n8n_validation(items)`
2. **Recherche SQLite** : `n8n_recherche_mysql(items)`
3. **Recherche Notion** : `n8n_recherche_notion(items)`
4. **Génération Réponse** : `n8n_generation_anthropic(items)`
5. **Création Ticket** : `n8n_creation_ticket(items)`

## 🧪 Tests et Vérification

### Test complet du système :
```bash
# Test avec un message réel
python main.py --message "jean.dupont@email.com" "Problème livraison commande #1"

# Voir les statistiques
python main.py --stats

# Traiter les tickets en attente
python main.py --process-pending
```

### Test des fonctions N8n :
```bash
python n8n_functions/support_workflow.py
```

## 🔧 Dépannage Rapide

### Problème : Module non trouvé
```bash
# Réactivez l'environnement virtuel
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Réinstallez les dépendances
pip install -r requirements.txt
```

### Problème : Base de données SQLite
```bash
# La base se recrée automatiquement
python main.py --setup
```

### Problème : Configuration Notion
```bash
# Vérifiez votre fichier .env
cat .env  # Linux/Mac
type .env  # Windows

# Testez la connexion
python -c "from notion.notion_manager import NotionManager; n=NotionManager(); print('✅ Notion OK')"
```

## 📊 Structure des Données

### Client (SQLite)
```
id, email, nom, prenom, date_creation
```

### Commande (SQLite)
```
id, date, montant, nb_articles, id_client, date_creation
```

### Flux de Données N8n
```
Webhook → Validation → SQLite → Notion → IA → Ticket → Email
```

---

**🎉 Vous êtes prêt à automatiser votre support client !**

Pour toute question, consultez le `README.md` complet ou testez les exemples fournis. 
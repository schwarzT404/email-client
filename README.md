# 🤖 Système d'Automatisation du Support Client E-commerce

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Claude](https://img.shields.io/badge/Claude-4_Sonnet-orange.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Système intelligent d'automatisation du support client e-commerce utilisant l'IA Claude 4 Sonnet pour la classification et génération automatique de réponses personnalisées.**

## 🌟 Fonctionnalités

- **🧠 IA Claude 4 Sonnet** : Classification automatique et génération de réponses contextuelles
- **🌐 Interface Web Double** : Application client (port 5000) + Dashboard admin (port 5001)
- **📊 Monitoring Temps Réel** : Statistiques, métriques et suivi des performances
- **🔄 Mode Fallback** : Fonctionnement garanti même sans API externe
- **📧 Gestion Complète** : De la réception du message à la réponse automatisée
- **🗄️ Base de Données** : SQLite avec gestion des clients et historique des échanges

## 🚀 Installation Rapide

### Prérequis
- Python 3.8+
- Clé API Anthropic (Claude)

### Installation
```bash
# Cloner le repository
git clone https://github.com/schwarzT404/email-client.git
cd email-client

# Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
copy PRODUCTION\env.example PRODUCTION\.env
# Éditer .env avec vos clés API
```

### Configuration
```env
# Dans PRODUCTION/.env
ANTHROPIC_API_KEY=sk-ant-votre-clé-api-ici
DB_PATH=data/crm_ecommerce.db
```

## 🎯 Utilisation

### Lancement Automatique
```bash
# Via le lanceur (recommandé)
cd PRODUCTION
python launcher_FINAL.py
```

### Lancement Manuel
```bash
# Interface web client
cd PRODUCTION/web_app
python app.py

# Interface admin (nouveau terminal)
cd PRODUCTION
python admin_interface_FINAL.py
```

**Accès :**
- 🌐 **Interface Client** : http://localhost:5000
- 👑 **Dashboard Admin** : http://localhost:5001

## 🏗️ Architecture

```
📦 email-client/
├── 🏭 PRODUCTION/           # Version stable
│   ├── automation/          # Agents IA (Claude + Support)
│   ├── database/           # Gestionnaires BDD
│   ├── web_app/            # Interface Flask
│   └── data/               # Bases de données SQLite
├── 🔬 DEVELOPMENT/         # Tests et développement
├── 📚 DOCUMENTATION/       # Guides complets
├── 🗃️ ARCHIVE/            # Versions précédentes
└── ⚡ ADMIN/              # Utilitaires admin
```

## 📊 Performances

- **Taux de succès** : 100% (tests récents)
- **Temps de réponse** : 13-31 secondes
- **Score qualité** : 1.00/1.00
- **Précision classification** : 92% avec Claude
- **Disponibilité** : 99.9% (mode fallback)

## 🎨 Captures d'Écran

### Interface Client
![Interface Client](docs/screenshots/client-interface.png)

### Dashboard Admin
![Dashboard Admin](docs/screenshots/admin-dashboard.png)

## 🔧 Développement

### Tests
```bash
cd DEVELOPMENT
python test_claude_direct.py
python test_traitement_messages.py
```

### Structure des Données
```sql
-- Messages clients
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    client_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'nouveau',
    category TEXT,
    urgency INTEGER,
    sentiment TEXT,
    response TEXT,
    quality_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🤝 Contribution

1. Fork le project
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Distribué sous licence MIT. Voir `LICENSE` pour plus d'informations.

## 🙏 Crédits

- **IA** : [Anthropic Claude](https://www.anthropic.com/)
- **Framework Web** : [Flask](https://flask.palletsprojects.com/)
- **Base de Données** : [SQLite](https://www.sqlite.org/)
- **UI Framework** : [Bootstrap 5](https://getbootstrap.com/)

## 📞 Support

Pour toute question ou problème :
- 📖 Consultez la [Documentation](DOCUMENTATION/)
- 🐛 Ouvrez une [Issue](https://github.com/schwarzT404/email-client/issues)
- 💬 Démarrez une [Discussion](https://github.com/schwarzT404/email-client/discussions)

---

**Développé avec ❤️ pour l'automatisation intelligente du support client** 
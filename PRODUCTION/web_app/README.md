# 🌐 Application Web - Support Client IA

## 🚀 Application Web Moderne avec Flask

Cette application web remplace l'interface tkinter traditionnelle par une interface moderne, fluide et performante construite avec **Flask** et **Bootstrap 5**.

## ⚡ Lancement Rapide

```bash
# Lancement direct
python app_web.py

# Ou depuis le dossier web_app
cd web_app
python app.py
```

L'application sera accessible sur **http://localhost:5000**

## 🎨 Fonctionnalités

### ✨ **Interface Moderne**
- **Bootstrap 5** avec animations CSS
- **Design responsive** (mobile/tablette/desktop)
- **Thème dégradé** avec effets de transparence
- **Notifications toast** pour le feedback utilisateur

### 🔧 **Fonctionnalités Techniques**
- **API REST** complète
- **Chargement asynchrone** des données
- **Gestion d'état** en temps réel
- **Mode simulation** si modules indisponibles

### 📊 **Modules Intégrés**
- **Traitement messages** avec classification IA
- **Statistiques dynamiques** avec métriques
- **Exemples pré-configurés** pour tests
- **Copie automatique** des réponses

## 🏗️ Structure

```
web_app/
├── app.py              # Application Flask principale
├── templates/
│   └── index.html      # Interface HTML avec Bootstrap 5
├── static/
│   ├── css/           # Styles personnalisés (intégrés)
│   └── js/
│       └── app.js     # JavaScript de l'application
└── README.md          # Ce fichier
```

## 🔗 API Endpoints

- **GET /** - Interface principale
- **GET /api/status** - Statut du système
- **POST /api/process-message** - Traitement messages
- **GET /api/statistics** - Statistiques système
- **GET /api/examples** - Exemples de messages

## 🛠️ Technologies Utilisées

- **Flask 3.0.0** - Framework web Python
- **Bootstrap 5.3.2** - Framework CSS moderne
- **Bootstrap Icons** - Icônes vectorielles
- **Animate.css** - Animations CSS
- **JavaScript ES6+** - Interactions dynamiques

## 🎯 Avantages

✅ **Interface moderne et professionnelle**  
✅ **Performance optimisée avec API REST**  
✅ **Responsive design multi-plateforme**  
✅ **Facilité de maintenance et d'évolution**  
✅ **Accessible depuis n'importe quel navigateur**  

## 📱 Screenshots

L'interface propose 3 onglets principaux :

1. **📧 Traitement Messages** - Formulaire intelligent avec validation
2. **📊 Statistiques** - Métriques animées en temps réel  
3. **📝 Exemples** - Messages pré-configurés pour tests

## 🔧 Configuration

### Paramètres Serveur
```python
# Dans app.py
app.run(
    debug=False,        # Mode production
    host='127.0.0.1',   # Localhost
    port=5000,          # Port par défaut
)
```

### Personnalisation CSS
Les variables CSS peuvent être modifiées dans `templates/index.html` :
```css
:root {
    --primary-color: #0d6efd;
    --gradient-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

## 🚀 Prochaines Améliorations

- [ ] Dashboard analytics avec graphiques
- [ ] Mode sombre avec switch automatique  
- [ ] Export PDF des rapports
- [ ] WebSocket pour temps réel
- [ ] Progressive Web App (PWA)

---

**Développé avec ❤️ pour une expérience utilisateur moderne** 
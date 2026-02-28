# 🚀 Guide de Lancement - Application Streamlit

## 📋 Étapes d'Installation

### Étape 1: Copier les fichiers dans votre projet

Copiez ces 3 fichiers dans le dossier `UI/`:

```
project/
└── UI/
    ├── app.py              # ← Application principale (REMPLACER l'existant)
    ├── streamlit_utils.py  # ← NOUVEAU fichier
    └── quiz_handler.py     # ← NOUVEAU fichier
```

### Étape 2: Installer Streamlit

```bash
pip install streamlit
```

### Étape 3: Vérifier les dépendances

Assurez-vous d'avoir toutes ces librairies installées:

```bash
pip install streamlit groq pdfplumber sentence-transformers faiss-cpu
```

### Étape 4: Configuration de la clé API Groq

```bash
# Windows (PowerShell)
$env:GROQ_API_KEY="votre_clé_api"

# Ou créez un fichier .env à la racine du projet
GROQ_API_KEY=votre_clé_api
```

## 🎯 Lancement de l'Application

### Méthode 1: Depuis la racine du projet (RECOMMANDÉ)

```bash
cd c:\Users\HP\project
streamlit run UI/app.py
```

### Méthode 2: Depuis le dossier UI

```bash
cd c:\Users\HP\project\UI
streamlit run app.py
```

## 🖥️ Interface de l'Application

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────┐
│  🎓 RAG Assistant & Quiz Generator                      │
│  Posez vos questions ou générez un quiz interactif      │
└─────────────────────────────────────────────────────────┘

┌─────────┐  ┌──────────────────────────────────────────┐
│ Sidebar │  │                                          │
│         │  │  MODE: 💬 Q&A  ou  📝 Quiz               │
│ 📄 PDF  │  │                                          │
│ Upload  │  │  [Barre de recherche...]          [🔍]  │
│         │  │                                          │
│ 📊 Info │  │  ┌────────────────────────────────┐      │
│         │  │  │  💡 Réponse                    │      │
│ 🎯 Mode │  │  │  [Contenu de la réponse...]    │      │
│         │  │  └────────────────────────────────┘      │
└─────────┘  └──────────────────────────────────────────┘
```

### Fonctionnalités

#### Mode Q&A (Questions & Réponses)
- 🔍 Barre de recherche avec icône
- 💡 Réponse en temps réel
- 📚 Sources avec similarité
- 📜 Historique des questions
- ⏰ Timestamp de chaque réponse

#### Mode Quiz
- ⚙️ Configuration personnalisée
  - Nombre de questions (1-20)
  - Niveau de difficulté (facile/moyen/difficile)
  - Types de questions (8 types disponibles)
  - Sujet spécifique (optionnel)
  - Format de sortie (HTML/JSON/Markdown)
- 🎯 Génération avec barre de progression
- 📋 Affichage interactif des questions
- ⬇️ Téléchargement du quiz
- 📊 Statistiques détaillées

#### Sidebar (Barre latérale)
- 📄 Upload de PDF
- 📊 Info du document actif
- 🎯 Sélection du mode
- 🗑️ Suppression du document

## 🎨 Personnalisation

### Modifier les couleurs

Éditez `UI/streamlit_utils.py`, section CSS:

```python
# Gradient principal
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

# Changez vers vos couleurs préférées:
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);  # Bleu
background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);  # Vert
background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);  # Rose-Jaune
```

### Modifier le titre

Éditez `UI/app.py`:

```python
st.set_page_config(
    page_title="Votre Titre",  # ← Changez ici
    page_icon="🎓",            # ← Changez l'icône
    layout="wide"
)
```

### Changer le PDF par défaut

Éditez `UI/app.py`:

```python
default_pdf = Path("Data/votre_pdf.pdf")  # ← Changez le chemin
```

## 🚦 Gestion des Erreurs Courantes

### Erreur: "No module named 'streamlit'"
```bash
pip install streamlit
```

### Erreur: "GROQ_API_KEY not set"
```bash
# Définissez la variable d'environnement
$env:GROQ_API_KEY="votre_clé"
```

### Erreur: "Cannot find module 'core'"
```bash
# Assurez-vous d'être dans la racine du projet
cd c:\Users\HP\project
streamlit run UI/app.py
```

### L'application ne se lance pas
```bash
# Vérifiez que tous les fichiers sont au bon endroit
dir UI\  # Doit montrer app.py, streamlit_utils.py, quiz_handler.py
```

### Rate Limit (429 Too Many Requests)
- Réduisez le nombre de questions à 5 maximum
- Attendez 1-2 minutes entre les générations
- Voir le guide `RATE_LIMITS_GUIDE.md` pour plus d'infos

## 📱 Utilisation Mobile

Streamlit fonctionne également sur mobile! Après le lancement:

```
Network URL: http://192.168.x.x:8501
```

Ouvrez cette URL sur votre smartphone connecté au même réseau WiFi.

## 🔧 Options de Lancement Avancées

### Changer le port

```bash
streamlit run UI/app.py --server.port 8080
```

### Mode développement (auto-reload)

```bash
streamlit run UI/app.py --server.runOnSave true
```

### Désactiver le cache

```bash
streamlit run UI/app.py --server.enableCORS false
```

### Configuration du thème

Créez `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#ffffff"
textColor = "#262730"
font = "sans serif"
```

## 📊 Structure des Données

### Session State

L'application utilise ces variables d'état:

```python
st.session_state.qa_history       # Liste des Q&A
st.session_state.quiz_data        # Données du quiz généré
st.session_state.current_pdf      # Chemin du PDF actif
st.session_state.last_query       # Dernière question posée
st.session_state.mode             # Mode actuel (Q&A ou Quiz)
st.session_state.quiz_generating  # État de génération
```

### Structure du Quiz

```python
{
    "metadata": {
        "topic": str,
        "difficulty": str,
        "num_questions": int,
        "generated_at": str,
        "question_types": list
    },
    "questions": [
        {
            "id": int,
            "type": str,
            "type_label": str,
            "section": str,
            "difficulty": str,
            "raw_content": str
        }
    ]
}
```

## 🎓 Workflow Recommandé

### Pour l'étudiant:

1. **Upload du PDF** via la sidebar
2. **Mode Q&A**: Posez des questions pour comprendre
3. **Mode Quiz**: Générez un quiz pour tester vos connaissances
4. **Téléchargez le quiz** HTML pour réviser hors ligne

### Pour l'enseignant:

1. **Upload du cours** (PDF)
2. **Testez avec Q&A** pour vérifier le contenu
3. **Générez plusieurs quiz** avec différentes difficultés
4. **Téléchargez en JSON** pour intégration LMS
5. **Distribuez aux étudiants**

## 🔮 Fonctionnalités Futures

Idées d'amélioration que vous pouvez implémenter:

- [ ] Mode multi-PDF (combiner plusieurs documents)
- [ ] Historique persistant (base de données)
- [ ] Système de notation automatique
- [ ] Export PDF des quiz
- [ ] Statistiques de performance
- [ ] Mode sombre
- [ ] Authentification utilisateur
- [ ] Partage de quiz via lien
- [ ] Quiz collaboratif en temps réel

## 💡 Conseils d'Utilisation

### Pour de meilleurs résultats:

1. **Questions précises**: Plus vos questions sont spécifiques, meilleures sont les réponses
2. **PDF structuré**: Les PDF bien formatés donnent de meilleurs résultats
3. **Sections claires**: Si votre PDF a des titres/sections, le système les utilisera
4. **Quiz courts**: Commencez avec 3-5 questions pour tester
5. **Types variés**: Mélangez différents types de questions pour plus d'engagement

### Raccourcis clavier:

- `Enter` dans la barre de recherche → Lance la recherche
- `Ctrl+R` → Rafraîchit l'application
- `Ctrl+Shift+R` → Force le rafraîchissement (clear cache)

## 🆘 Support

Si vous rencontrez des problèmes:

1. Vérifiez les logs dans le terminal
2. Consultez `RATE_LIMITS_GUIDE.md` pour les problèmes d'API
3. Vérifiez que tous les fichiers sont présents
4. Testez avec le PDF par défaut d'abord
5. Vérifiez votre connexion internet (pour Groq API)

## 📝 Checklist de Démarrage

- [ ] Tous les fichiers copiés dans `UI/`
- [ ] Streamlit installé (`pip install streamlit`)
- [ ] Dépendances installées
- [ ] Clé API Groq configurée
- [ ] Dans la racine du projet
- [ ] Lancement: `streamlit run UI/app.py`
- [ ] Application ouverte dans le navigateur
- [ ] PDF importé ou PDF par défaut détecté
- [ ] Test Q&A fonctionnel
- [ ] Test génération quiz fonctionnel

---

**Prêt à démarrer! 🚀**

```bash
streamlit run UI/app.py
```

Puis ouvrez votre navigateur à `http://localhost:8501` 🎉
# Assistant RAG pour cours et quiz

## Présentation

Cet assistant est un **système de RAG (Retrieval-Augmented Generation)** conçu pour analyser des documents pédagogiques (PDF, cours, TP…) et :  
- Extraire et structurer le contenu de manière intelligente  
- Générer des **résumés et réponses aux questions** basées sur le contenu  
- Créer automatiquement des **quizzes QCM** à partir des documents  

Il agit comme un assistant pédagogique : tu lui donnes un cours, il comprend les concepts principaux, retrouve des passages pertinents et peut produire un quiz pour l’évaluation.  

---

## Fonctionnalités principales

1. **Analyse et compréhension du document**  
   - Extraction du texte depuis des PDF  
   - Détection automatique du type de document et de la langue  
   - Identification des titres, sections et concepts principaux  

2. **Chunking sémantique**  
   - Découpage du texte en morceaux logiques ou “chunks”  
   - Association des chunks aux concepts détectés  
   - Optimisation pour l’indexation et la recherche contextuelle  

3. **Indexation et embeddings**  
   - Génération d’**embeddings** via un modèle de type SentenceTransformer  
   - Stockage des vecteurs pour une récupération rapide des informations pertinentes  

4. **RAG – Retrieval-Augmented Generation**  
   - Recherche des chunks les plus pertinents pour une question donnée  
   - Utilisation d’un **LLM (Ollama)** pour générer des réponses basées sur le contexte  
   - Réponses concises et précises, avec références aux chunks utilisés  

5. **Génération de quiz**  
   - Création automatique de QCM basés sur les sections et concepts principaux  
   - Questions avec 4 choix et réponse unique  
   - Export possible en JSON ou texte pour utilisation externe  

---

## Architecture technique

- **Processor** : `IntelligentDocumentProcessor`  
  Analyse le PDF, extrait le texte, détecte titres, sections et concepts, et génère une structure `DocumentUnderstanding`.  

- **Chunker** : `SemanticChunker`  
  Transforme le texte en chunks sémantiques basés sur la longueur et les concepts. Chaque chunk contient le texte, la section, les concepts associés et un identifiant.  

- **Embeddings & Index** : `EmbeddingsModel`  
  Encode les chunks en vecteurs numériques et les sauvegarde pour une recherche rapide.  

- **RAG / Question Answering** : `CourseRetriever`  
  Recherche les chunks les plus pertinents pour une question et envoie le contexte au LLM pour produire la réponse.  

- **Quiz Generator** : `QuizGenerator`  
  Génère automatiquement des QCM basés sur les chunks, contrôle le nombre de questions par section et le format de sortie.  


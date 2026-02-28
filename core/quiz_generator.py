import time
import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import os
from groq import Groq

try:
    # When run as module: python -m core.quiz_generator
    from .semantic_chunker import RobustPDFChunker
    from .hybrid_retriever import HybridRetriever
except ImportError:
    # When run directly: python quiz_generator.py
    from core.semantic_chunker import RobustPDFChunker
    from core.hybrid_retriever import HybridRetriever

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
PDF_PATH = Path("Data/cours_.pdf")
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_DIR = Path("Data/vector_store")
LLM_MODEL = "llama-3.1-8b-instant"

# Rate limiting configuration
API_DELAY_SECONDS = 2.0  # Délai entre chaque requête API
MAX_RETRIES = 3  # Nombre max de tentatives en cas d'erreur
RETRY_BACKOFF_BASE = 2.0  # Délai de base pour backoff exponentiel

# Quiz configuration
QUIZ_OUTPUT_DIR = Path("Data/quizzes")
QUIZ_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==================== GROQ CLIENT ====================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ==================== QUESTION TYPES ====================
QUESTION_TYPES = {
    "multiple_choice": "Questions à choix multiples (4 options)",
    "true_false": "Vrai/Faux avec justification",
    "fill_blank": "Compléter les blancs",
    "matching": "Associer les concepts",
    "short_answer": "Réponse courte (2-3 phrases)",
    "scenario": "Étude de cas / Scénario pratique",
    "error_detection": "Trouver l'erreur dans l'affirmation",
    "ranking": "Classer par ordre (chronologique, importance, etc.)"
}

DIFFICULTY_LEVELS = {
    "facile": "Rappel de faits et définitions basiques",
    "moyen": "Compréhension et application des concepts",
    "difficile": "Analyse, synthèse et résolution de problèmes complexes"
}

# ==================== PDF EXTRACTION ====================
def extract_pdf_text(pdf_path: Path) -> str:
    logger.info(f"Extraction du PDF: {pdf_path}")
    
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    pages.append(f"--- Page {i} ---\n{text}")
            return "\n\n".join(pages)
    except Exception as e:
        logger.error(f"Erreur extraction PDF: {e}")
        raise

# ==================== QUIZ GENERATOR ====================
class CreativeQuizGenerator:
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        
    def generate_quiz(
        self,
        topic: str = None,
        num_questions: int = 10,
        difficulty: str = "moyen",
        question_types: List[str] = None,
        diverse: bool = True
    ) -> Dict:
        """
        Generate a creative quiz from the PDF content.
        
        Args:
            topic: Specific topic/section to focus on (None = all content)
            num_questions: Number of questions to generate
            difficulty: 'facile', 'moyen', or 'difficile'
            question_types: List of question types to use (None = all types)
            diverse: If True, mix different question types
        """
        logger.info(f"Génération quiz: {num_questions} questions, niveau {difficulty}")
        
        # Get relevant chunks
        if topic:
            chunks = self.retriever.retrieve(topic, top_k=min(15, num_questions * 2))
        else:
            # Sample random chunks from the entire document
            chunks = self._get_diverse_chunks(num_questions * 2)
        
        # Determine question types to use
        if question_types is None:
            question_types = list(QUESTION_TYPES.keys())
        
        # Generate questions
        questions = []
        
        if diverse:
            # Mix different types
            type_cycle = question_types * (num_questions // len(question_types) + 1)
            random.shuffle(type_cycle)
            selected_types = type_cycle[:num_questions]
        else:
            # Use specified types randomly
            selected_types = random.choices(question_types, k=num_questions)
        
        for i, q_type in enumerate(selected_types, 1):
            chunk = chunks[i % len(chunks)]
            
            question = self._generate_question(
                chunk=chunk,
                q_type=q_type,
                difficulty=difficulty,
                question_number=i
            )
            
            if question:
                questions.append(question)
            
            # Rate limiting for API - increased delay to avoid 429 errors
            time.sleep(2.0)  # Augmenté de 0.5s à 2s
        
        quiz_data = {
            "metadata": {
                "topic": topic or "Contenu complet",
                "difficulty": difficulty,
                "num_questions": len(questions),
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "question_types": list(set(q["type"] for q in questions))
            },
            "questions": questions
        }
        
        return quiz_data
    
    def _get_diverse_chunks(self, num_chunks: int) -> List[Dict]:
        """Get diverse chunks from different sections"""
        # This is a simplified version - you might want to implement
        # section-based sampling for better diversity
        if not self.retriever.metadata:
            logger.warning("No chunks in retriever metadata")
            return []
        
        all_chunks = self.retriever.metadata[:num_chunks * 2]
        return random.sample(all_chunks, min(num_chunks, len(all_chunks)))
    
    def _generate_question(
        self,
        chunk: Dict,
        q_type: str,
        difficulty: str,
        question_number: int
    ) -> Dict:
        """Generate a single question using LLM with retry logic"""
        
        context = chunk["content"]
        section = chunk.get("section", "Unknown")
        
        # Create specialized prompt based on question type
        prompt = self._create_prompt(q_type, context, difficulty, section)
        
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "Expert pédagogique créant des questions d'évaluation de haute qualité."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                content = response.choices[0].message.content.strip()
                
                # Parse the response
                question_data = self._parse_question_response(content, q_type, question_number, section, difficulty)
                
                return question_data
                
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limit atteint pour question {question_number}, attente de {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Échec après {max_retries} tentatives pour question {question_number}")
                        return None
                else:
                    logger.error(f"Erreur génération question {question_number}: {e}")
                    return None
        
        return None
    
    def _create_prompt(self, q_type: str, context: str, difficulty: str, section: str) -> str:
        """Create specialized prompts for different question types"""
        
        base_instructions = f"""
Contexte (section: {section}):
{context}

Niveau de difficulté: {difficulty}
{DIFFICULTY_LEVELS[difficulty]}

"""
        
        if q_type == "multiple_choice":
            return base_instructions + """
Crée une question à choix multiples (QCM) avec:
- Une question claire et précise
- 4 options (A, B, C, D)
- UNE SEULE réponse correcte
- Des distracteurs plausibles mais incorrects
- Une explication de la bonne réponse

Format:
QUESTION: [ta question]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
CORRECT: [lettre de la bonne réponse]
EXPLICATION: [pourquoi cette réponse est correcte]
"""
        
        elif q_type == "true_false":
            return base_instructions + """
Crée une affirmation Vrai/Faux avec:
- Une affirmation claire basée sur le contexte
- La réponse (VRAI ou FAUX)
- Une justification détaillée

Format:
AFFIRMATION: [ton affirmation]
REPONSE: [VRAI ou FAUX]
JUSTIFICATION: [explication détaillée]
"""
        
        elif q_type == "fill_blank":
            return base_instructions + """
Crée une phrase à compléter avec:
- Une phrase avec 2-3 blancs (_____) 
- Les mots/concepts à trouver
- Une explication

Format:
PHRASE: [phrase avec _____ pour les blancs]
REPONSES: [mot1], [mot2], [mot3]
EXPLICATION: [contexte de la réponse]
"""
        
        elif q_type == "matching":
            return base_instructions + """
Crée un exercice d'association avec:
- 4-5 paires de concepts/définitions à associer
- Mélange l'ordre des éléments de droite

Format:
QUESTION: Associez les concepts suivants:
GAUCHE:
1. [concept 1]
2. [concept 2]
3. [concept 3]
4. [concept 4]
DROITE:
A. [définition mélangée]
B. [définition mélangée]
C. [définition mélangée]
D. [définition mélangée]
CORRECT: 1-[lettre], 2-[lettre], 3-[lettre], 4-[lettre]
"""
        
        elif q_type == "short_answer":
            return base_instructions + """
Crée une question ouverte nécessitant:
- 2-3 phrases de réponse
- Réflexion et compréhension approfondie
- Une réponse modèle

Format:
QUESTION: [ta question]
REPONSE_MODELE: [réponse attendue en 2-3 phrases]
POINTS_CLES: [3-4 éléments essentiels à mentionner]
"""
        
        elif q_type == "scenario":
            return base_instructions + """
Crée un scénario pratique avec:
- Une situation réelle/problème à résoudre
- Des détails contextuels
- Une solution attendue

Format:
SCENARIO: [description de la situation]
QUESTION: [que doit faire/analyser l'étudiant?]
SOLUTION: [approche recommandée]
CRITERES: [critères d'évaluation]
"""
        
        elif q_type == "error_detection":
            return base_instructions + """
Crée une affirmation avec une erreur subtile:
- Une phrase contenant UNE erreur factuelle
- L'erreur doit être plausible
- Correction et explication

Format:
AFFIRMATION: [phrase contenant une erreur]
ERREUR: [quelle partie est incorrecte]
CORRECTION: [version correcte]
EXPLICATION: [pourquoi c'était faux]
"""
        
        elif q_type == "ranking":
            return base_instructions + """
Crée un exercice de classement avec:
- 4-5 éléments à ordonner
- Critère de classement clair (chronologique, importance, étapes, etc.)
- Ordre correct avec justification

Format:
QUESTION: Classez les éléments suivants [critère]:
ELEMENTS: [élément 1], [élément 2], [élément 3], [élément 4]
ORDRE_CORRECT: [élément X], [élément Y], [élément Z], [élément W]
JUSTIFICATION: [pourquoi cet ordre]
"""
        
        return base_instructions + "Crée une question pertinente basée sur le contexte."
    
    def _parse_question_response(
        self,
        content: str,
        q_type: str,
        question_number: int,
        section: str,
        difficulty: str
    ) -> Dict:
        """Parse LLM response into structured question data"""
        
        question_data = {
            "id": question_number,
            "type": q_type,
            "type_label": QUESTION_TYPES[q_type],
            "section": section,
            "difficulty": difficulty,
            "raw_content": content
        }
        
        # Basic parsing - you might want to make this more robust
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith("QUESTION:"):
                question_data["question"] = line.replace("QUESTION:", "").strip()
            elif line.startswith("AFFIRMATION:"):
                question_data["statement"] = line.replace("AFFIRMATION:", "").strip()
            elif line.startswith("PHRASE:"):
                question_data["sentence"] = line.replace("PHRASE:", "").strip()
            elif line.startswith("SCENARIO:"):
                question_data["scenario"] = line.replace("SCENARIO:", "").strip()
            elif line.startswith("CORRECT:"):
                question_data["correct_answer"] = line.replace("CORRECT:", "").strip()
            elif line.startswith("REPONSE:"):
                question_data["answer"] = line.replace("REPONSE:", "").strip()
            elif line.startswith("EXPLICATION:") or line.startswith("JUSTIFICATION:"):
                key = "EXPLICATION:" if "EXPLICATION:" in line else "JUSTIFICATION:"
                question_data["explanation"] = line.replace(key, "").strip()
        
        return question_data

# ==================== QUIZ PIPELINE ====================
def run_quiz_pipeline(
    pdf_path: Path,
    topic: str = None,
    num_questions: int = 10,
    difficulty: str = "moyen",
    question_types: List[str] = None,
    output_format: str = "json"
) -> Tuple[Dict, str]:
    """
    Main pipeline to generate a quiz from PDF
    
    Args:
        pdf_path: Path to PDF file
        topic: Optional topic to focus on
        num_questions: Number of questions to generate
        difficulty: Difficulty level
        question_types: Types of questions to include
        output_format: 'json' or 'html' or 'markdown'
    
    Returns:
        Quiz data and output file path
    """
    start_time = time.time()
    
    # STEP 1 - Extract PDF
    raw_text = extract_pdf_text(pdf_path)
    logger.info(f"PDF extracted: {len(raw_text)} characters")
    
    # STEP 2 - Chunk document
    chunker = RobustPDFChunker(max_words=180, overlap=30)
    chunks = chunker.chunk_document(raw_text)
    logger.info(f"{len(chunks)} chunks created")
    
    # STEP 3 - Build/Load index
    retriever = HybridRetriever(
        embed_model_name=EMBED_MODEL,
        vector_dir=VECTOR_DIR
    )
    
    if not retriever.load_index():
        retriever.build_index([
            {
                "content": c.content,
                "section": c.section,
                "chunk_id": c.chunk_id,
                "word_count": c.word_count
            }
            for c in chunks
        ])
    
    # STEP 4 - Generate quiz
    quiz_gen = CreativeQuizGenerator(retriever)
    quiz_data = quiz_gen.generate_quiz(
        topic=topic,
        num_questions=num_questions,
        difficulty=difficulty,
        question_types=question_types
    )
    
    # STEP 5 - Save quiz
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    topic_slug = topic.replace(" ", "_") if topic else "all"
    
    output_file = QUIZ_OUTPUT_DIR / f"quiz_{topic_slug}_{difficulty}_{timestamp}.{output_format}"
    
    if output_format == "json":
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, ensure_ascii=False, indent=2)
    
    elif output_format == "html":
        html_content = generate_html_quiz(quiz_data)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    elif output_format == "markdown":
        md_content = generate_markdown_quiz(quiz_data)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    total_time = time.time() - start_time
    logger.info(f"Quiz généré en {total_time:.2f}s: {output_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"🎯 QUIZ GÉNÉRÉ: {quiz_data['metadata']['num_questions']} questions")
    print(f"📚 Sujet: {quiz_data['metadata']['topic']}")
    print(f"⚡ Difficulté: {difficulty}")
    print(f"📝 Types: {', '.join(quiz_data['metadata']['question_types'])}")
    print(f"💾 Fichier: {output_file}")
    print("=" * 70 + "\n")
    
    return quiz_data, str(output_file)

# ==================== OUTPUT FORMATTERS ====================
def generate_html_quiz(quiz_data: Dict) -> str:
    """Generate interactive HTML quiz"""
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quiz - {quiz_data['metadata']['topic']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .quiz-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .quiz-header {{
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #667eea;
            margin: 0;
        }}
        .metadata {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        .badge {{
            background: #f0f0f0;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
        }}
        .question {{
            background: #f9f9f9;
            padding: 25px;
            margin: 25px 0;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }}
        .question-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .question-number {{
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 50%;
            font-weight: bold;
        }}
        .question-type {{
            color: #666;
            font-size: 13px;
            font-style: italic;
        }}
        .question-text {{
            font-size: 18px;
            font-weight: 500;
            margin: 15px 0;
            color: #333;
        }}
        .answer-section {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
        }}
        .show-answer {{
            background: #764ba2;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }}
        .show-answer:hover {{
            background: #667eea;
        }}
        .answer-content {{
            display: none;
            margin-top: 15px;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 8px;
            border-left: 4px solid #4caf50;
        }}
        .section-tag {{
            display: inline-block;
            background: #fff3cd;
            color: #856404;
            padding: 3px 10px;
            border-radius: 5px;
            font-size: 12px;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="quiz-container">
        <div class="quiz-header">
            <h1>🎓 Quiz Interactif</h1>
            <div class="metadata">
                <span class="badge">📚 {quiz_data['metadata']['topic']}</span>
                <span class="badge">⚡ {quiz_data['metadata']['difficulty']}</span>
                <span class="badge">📝 {quiz_data['metadata']['num_questions']} questions</span>
            </div>
        </div>
"""
    
    for q in quiz_data['questions']:
        html += f"""
        <div class="question">
            <div class="question-header">
                <span class="question-number">{q['id']}</span>
                <span class="question-type">{q.get('type_label', q['type'])}</span>
            </div>
            <span class="section-tag">📖 {q['section']}</span>
            <div class="question-text">{q.get('question', q.get('statement', q.get('scenario', 'Question')))}</div>
            <button class="show-answer" onclick="toggleAnswer({q['id']})">Voir la réponse</button>
            <div id="answer-{q['id']}" class="answer-content">
                <pre style="white-space: pre-wrap; font-family: inherit;">{q.get('raw_content', 'Réponse non disponible')}</pre>
            </div>
        </div>
"""
    
    html += """
    </div>
    <script>
        function toggleAnswer(id) {
            const answerDiv = document.getElementById('answer-' + id);
            if (answerDiv.style.display === 'none' || answerDiv.style.display === '') {
                answerDiv.style.display = 'block';
            } else {
                answerDiv.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""
    return html

def generate_markdown_quiz(quiz_data: Dict) -> str:
    """Generate markdown formatted quiz"""
    md = f"""# 🎓 Quiz - {quiz_data['metadata']['topic']}

**Difficulté:** {quiz_data['metadata']['difficulty']}  
**Nombre de questions:** {quiz_data['metadata']['num_questions']}  
**Types de questions:** {', '.join(quiz_data['metadata']['question_types'])}  
**Généré le:** {quiz_data['metadata']['generated_at']}

---

"""
    
    for q in quiz_data['questions']:
        md += f"""## Question {q['id']} - {q['type_label']}

**Section:** {q['section']}  
**Difficulté:** {q['difficulty']}

"""
        md += q.get('raw_content', 'Contenu non disponible')
        md += "\n\n---\n\n"
    
    return md

# ==================== MAIN ====================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Générateur de quiz créatif depuis PDF")
    parser.add_argument("--pdf", type=str, default=str(PDF_PATH), help="Chemin du PDF")
    parser.add_argument("--topic", type=str, default=None, help="Sujet spécifique (optionnel)")
    parser.add_argument("--num", type=int, default=10, help="Nombre de questions")
    parser.add_argument("--difficulty", type=str, default="moyen", 
                       choices=["facile", "moyen", "difficile"])
    parser.add_argument("--types", type=str, nargs="+", 
                       choices=list(QUESTION_TYPES.keys()),
                       help="Types de questions à inclure")
    parser.add_argument("--format", type=str, default="html",
                       choices=["json", "html", "markdown"])
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        logger.error(f"PDF introuvable: {pdf_path}")
        exit(1)
    
    quiz_data, output_file = run_quiz_pipeline(
        pdf_path=pdf_path,
        topic=args.topic,
        num_questions=args.num,
        difficulty=args.difficulty,
        question_types=args.types,
        output_format=args.format
    )
    
    print(f"\n✅ Quiz sauvegardé: {output_file}")
    if args.format == "html":
        print(f"🌐 Ouvrez le fichier dans votre navigateur!")
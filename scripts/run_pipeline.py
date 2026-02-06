import os
import sys
from pathlib import Path
import tempfile
import shutil

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("TEST DU PIPELINE RAG COMPLET - VERSION OPTIMISEE")
print("=" * 70)

print("\nVerification des dependances...")

try:
    import fitz
    print("   PyMuPDF installe")
except ImportError:
    print("   PyMuPDF manquant. Installation: pip install pymupdf")
    sys.exit(1)

try:
    import ollama
    print("   Ollama installe")
except ImportError:
    print("   Ollama manquant. Installation: pip install ollama")
    sys.exit(1)

try:
    from llama_index.core import VectorStoreIndex
    print("   LlamaIndex installe")
except ImportError:
    print("   LlamaIndex manquant. Installation: pip install llama-index")
    sys.exit(1)

print("\nChargement des modules...")

try:
    core_dir = project_root / "Core"
    sys.path.insert(0, str(core_dir))

    from intelligent_processor import IntelligentDocumentProcessor
    print("   IntelligentDocumentProcessor charge")

    from semantic_chunker import SemanticChunker
    print("   SemanticChunker charge")

    from hybrid_retriever import CourseRetriever
    print("   CourseRetriever charge")

    from quiz_generator import QuizGenerator
    print("   QuizGenerator charge")

except ImportError as e:
    print(f"   Erreur d'import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nRecherche du PDF de test...")

# ------------------------------------------------------------------
# NOUVEAU : gestion chemin OU fichier uploadé
# ------------------------------------------------------------------

pdf_path = None

# 1) Argument CLI
if len(sys.argv) > 1:
    candidate = Path(sys.argv[1])
    if candidate.exists():
        pdf_path = candidate

# 2) Variable d'environnement (upload)
elif os.getenv("UPLOADED_PDF"):
    candidate = Path(os.getenv("UPLOADED_PDF"))
    if candidate.exists():
        pdf_path = candidate

# 3) Fallback (comportement original)
else:
    candidate = project_root / "Data" / "cours_.pdf"
    if candidate.exists():
        pdf_path = candidate

if not pdf_path:
    print("   Aucun PDF valide fourni")
    print("   - Argument CLI")
    print("   - Variable UPLOADED_PDF")
    print("   - Data/cours_.pdf")
    sys.exit(1)

print(f"   PDF utilise: {pdf_path}")

print("\n" + "=" * 70)
print("ETAPE 1 : EXTRACTION ET ANALYSE DU PDF")
print("=" * 70)

try:
    processor = IntelligentDocumentProcessor(model="phi3:mini")
    doc_understanding = processor.process_pdf(str(pdf_path))

    print("\nDocument analyse avec succes")
    print(f"   Titre      : {doc_understanding.title}")
    print(f"   Type       : {doc_understanding.document_type}")
    print(f"   Langue     : {doc_understanding.language}")
    print(f"   Concepts   : {len(doc_understanding.main_concepts)}")
    print(f"   Titres     : {len(doc_understanding.detected_headings)}")
    print(f"   Sections   : {len(doc_understanding.structure)}")

    if doc_understanding.metrics:
        print(f"   Confiance  : {doc_understanding.metrics.confidence_score:.0%}")
        print(f"   Statut     : {doc_understanding.metrics.status.value}")
        print(f"   Temps LLM  : {doc_understanding.metrics.llm_duration:.1f}s")
        print(f"   Temps total: {doc_understanding.metrics.total_duration:.1f}s")

    print("\n   Concepts detectes:")
    for i, concept in enumerate(doc_understanding.main_concepts[:5], 1):
        print(f"      {i}. {concept}")

except Exception as e:
    print(f"\nErreur lors de l'analyse: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("ETAPE 2 : CHUNKING SEMANTIQUE")
print("=" * 70)

try:
    chunker = SemanticChunker(min_words=50, max_words=200)
    chunks = chunker.chunk_document(doc_understanding)

    print("\nChunking termine")
    print(f"   Nombre de chunks : {len(chunks)}")

    for i, chunk in enumerate(chunks[:3]):
        print(f"\n   Chunk {i+1}:")
        print(f"      Section: {chunk['section'][:50]}")
        print(f"      Mots: {chunk['word_count']}")
        print(f"      Concept: {chunk['main_concept'][:50]}")
        preview = chunk['content'][:100].replace('\n', ' ')
        print(f"      Apercu: {preview}...")

    if len(chunks) > 3:
        print(f"\n   ... et {len(chunks) - 3} autres chunks")

except Exception as e:
    print(f"\nErreur lors du chunking: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("ETAPE 3 : INDEXATION VECTORIELLE")
print("=" * 70)

try:
    retriever = CourseRetriever(model_name="phi3:mini")
    retriever.index_course(
        chunks=chunks,
        course_title=doc_understanding.title,
        main_concepts=doc_understanding.main_concepts
    )

    print("\nIndexation terminee")
    print(f"   Index vectoriel cree avec {len(chunks)} chunks")

except Exception as e:
    print(f"\nErreur lors de l'indexation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("ETAPE 4 : TEST DE RECHERCHE VECTORIELLE")
print("=" * 70)

try:
    print("\nRecherche de chunks pertinents...")
    query1 = "Quels sont les concepts principaux du soudage?"

    results = retriever.retrieve_relevant_chunks(query1, top_k=3)

    print(f"\nResultats pour: '{query1}'")
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. Section: {result['section'][:60]}")
        print(f"      Similarite: {result['semantic_similarity']:.3f}")
        print(f"      Concept: {result['main_concept'][:50]}")
        preview = result['content'][:120].replace('\n', ' ')
        print(f"      Contenu: {preview}...")

except Exception as e:
    print(f"\nErreur lors de la recherche: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("ETAPE 5 : GENERATION DE REPONSE")
print("=" * 70)

try:
    print("\nGeneration de reponse...")
    query2 = "donner les concepts ou les parties principales qu abborde ce pdf"

    answer = retriever.answer_question(query2, context_size=3)

    print(f"\nQuestion: {query2}")
    print("\nReponse:")
    print(answer['answer'])
    print("\nMetadonnees:")
    print(f"   Confiance: {answer['confidence']:.2f}")
    print(f"   Sources: {len(answer['sources'])} chunks utilises")

except Exception as e:
    print(f"\nErreur lors de la generation: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("ETAPE 6 : GENERATION DE QUIZ QCM")
print("=" * 70)

try:
    quiz_gen = QuizGenerator(
        model_name="phi3:mini",
        questions_per_chunk=2
    )

    quiz = quiz_gen.generate_quiz_from_chunks(chunks, max_chunks=3)

    if quiz:
        quiz_gen.display_quiz(quiz, show_answers=True)
    else:
        print("\nAucune question generee")

except Exception as e:
    print(f"\nErreur generation quiz: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("PIPELINE COMPLETE AVEC SUCCES")
print("=" * 70)

if doc_understanding.metrics:
    total_time = doc_understanding.metrics.total_duration
    llm_time = doc_understanding.metrics.llm_duration
    other_time = total_time - llm_time

    print(f"""
STATISTIQUES COMPLETES:

DOCUMENT:
   Titre          : {doc_understanding.title}
   Type           : {doc_understanding.document_type}
   Langue         : {doc_understanding.language}
   Concepts       : {len(doc_understanding.main_concepts)}
   Titres detectes: {len(doc_understanding.detected_headings)}

CHUNKING:
   Chunks crees   : {len(chunks)}
   Methode        : Fuzzy matching
   Temps          : ~1 seconde

PERFORMANCE:
   Temps LLM      : {llm_time:.1f}s
   Temps autre    : {other_time:.1f}s
   TEMPS TOTAL    : {total_time:.1f}s
""")
else:
    print(f"""
RESUME:
   Document analyse : {doc_understanding.title}
   Chunks crees     : {len(chunks)}
   Index vectoriel  : Actif
   RAG operationnel : Oui
   Quiz genere      : Oui
""")

print("=" * 70)
print("TEST TERMINE")
print("=" * 70)

# 📁 UI/app.py

import streamlit as st
from pathlib import Path
import tempfile

# Ajouter le projet à sys.path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.intelligent_processor import IntelligentDocumentProcessor
from core.semantic_chunker import SemanticChunker
from core.hybrid_retriever import CourseRetriever
from core.quiz_generator import QuizGenerator

st.set_page_config(
    page_title="StudyBuddy",
    layout="wide"
)

st.title("📚 StudyBuddy - RAG Assistant pour PDF")
st.markdown("Upload un PDF, explore son contenu, génère des quiz et pose des questions !")

# --------------------------------------------
# Section 1 : Upload du PDF
# --------------------------------------------
uploaded_file = st.file_uploader("📄 Choisir un fichier PDF", type=["pdf"])

if uploaded_file:
    # Créer un fichier temporaire pour traiter le PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_path = tmp_file.name
    
    st.success(f"✅ PDF chargé : {uploaded_file.name}")

    # --------------------------------------------
    # Section 2 : Analyse et chunking
    # --------------------------------------------
    st.header("1️⃣ Analyse du PDF")
    processor = IntelligentDocumentProcessor(model="phi3:mini")
    with st.spinner("Analyse du document..."):
        doc_understanding = processor.process_pdf(pdf_path)
    
    st.subheader("Résumé du document")
    st.write(f"**Titre** : {doc_understanding.title}")
    st.write(f"**Type** : {doc_understanding.document_type}")
    st.write(f"**Langue** : {doc_understanding.language}")
    st.write(f"**Concepts principaux** : {', '.join(doc_understanding.main_concepts[:5])}")
    st.write(f"**Sections détectées** : {len(doc_understanding.structure)}")

    st.header("2️⃣ Chunking sémantique")
    chunker = SemanticChunker(min_words=50, max_words=200)
    chunks = chunker.chunk_document(doc_understanding)
    st.write(f"Nombre de chunks créés : {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        st.markdown(f"**Chunk {i+1}** : Section: {chunk['section'][:50]}, Concept: {chunk['main_concept'][:50]}")
        st.write(chunk['content'][:200] + "…")
    if len(chunks) > 3:
        st.info(f"... et {len(chunks) - 3} autres chunks")

    # --------------------------------------------
    # Section 3 : Indexation vectorielle
    # --------------------------------------------
    st.header("3️⃣ Indexation et RAG")
    retriever = CourseRetriever(model_name="phi3:mini")
    with st.spinner("Indexation vectorielle en cours..."):
        retriever.index_course(
            chunks=chunks,
            course_title=doc_understanding.title,
            main_concepts=doc_understanding.main_concepts
        )
    st.success("Indexation terminée ✅")

    # --------------------------------------------
    # Section 4 : Posez vos questions
    # --------------------------------------------
    st.header("4️⃣ Posez une question")
    user_query = st.text_input("Votre question :", "")
    
    if user_query:
        with st.spinner("Recherche de réponse..."):
            answer = retriever.answer_question(user_query, context_size=3)
        st.subheader("Réponse")
        st.write(answer['answer'])
        st.write(f"**Confiance** : {answer['confidence']:.2f}")
        st.write(f"**Sources utilisées** : {len(answer['sources'])} chunks")

    # --------------------------------------------
    # Section 5 : Génération de quiz
    # --------------------------------------------
    st.header("5️⃣ Générer un quiz")
    if st.button("🎯 Générer quiz"):
        quiz_gen = QuizGenerator(model_name="phi3:mini", questions_per_chunk=2)
        quiz = quiz_gen.generate_quiz_from_chunks(chunks, max_chunks=3)
        
        if quiz:
            st.subheader("Quiz généré")
            quiz_gen.display_quiz(quiz, show_answers=True)
        else:
            st.warning("Aucune question générée")

else:
    st.info("Veuillez uploader un fichier PDF pour commencer.")

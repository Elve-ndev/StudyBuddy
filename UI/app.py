"""
Application Streamlit moderne pour RAG Q&A et génération de quiz
"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.rag_pipeline import run_rag_pipeline
from core.quiz_generator import run_quiz_pipeline, QUESTION_TYPES
from UI.streamlit_utils import apply_custom_css, init_session_state, save_uploaded_pdf
from UI.quiz_handler import display_quiz_interface

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="RAG Assistant & Quiz Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CUSTOM CSS ====================
apply_custom_css()

# ==================== SESSION STATE ====================
init_session_state()

# ==================== HEADER ====================
st.markdown("""
    <div class="main-header">
        <h1> StudyBuddy:RAG Assistant & Quiz Generator</h1>
        <p>Posez vos questions ou générez un quiz interactif depuis vos documents PDF</p>
    </div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR - PDF UPLOAD ====================
with st.sidebar:
    st.markdown("###  Gestion des Documents")
    
    uploaded_file = st.file_uploader(
        "Importer un PDF",
        type=["pdf"],
        help="Importez votre document PDF pour commencer"
    )
    
    if uploaded_file:
        pdf_path = save_uploaded_pdf(uploaded_file)
        st.session_state.current_pdf = pdf_path
        st.success(f" PDF chargé: {uploaded_file.name}")
    
    # Default PDF if none uploaded
    if st.session_state.current_pdf is None:
        default_pdf = Path("Data/cours_.pdf")
        if default_pdf.exists():
            st.session_state.current_pdf = default_pdf
            st.info(f" Utilisation du PDF par défaut: {default_pdf.name}")
    
    st.markdown("---")
    
    # PDF Info
    if st.session_state.current_pdf:
        st.markdown("** Document actif:**")
        st.text(st.session_state.current_pdf.name)
        
        if st.button(" Supprimer", use_container_width=True):
            st.session_state.current_pdf = None
            st.rerun()
    
    st.markdown("---")
    
    # Mode selector
    st.markdown("###  Mode")
    mode = st.radio(
        "Choisissez votre mode:",
        [" Questions & Réponses", " Génération de Quiz"],
        label_visibility="collapsed"
    )
    st.session_state.mode = mode

# ==================== MAIN CONTENT ====================

# Mode: Q&A
if st.session_state.mode == " Questions & Réponses":
    
    # Search Bar Container
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([8, 1])
    
    with col1:
        query = st.text_input(
            "search",
            placeholder=" Posez votre question ici... ",
            label_visibility="collapsed",
            key="search_input"
        )
    
    with col2:
        search_button = st.button("🔍", use_container_width=True, type="primary")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process query
    if (search_button and query) or (query and st.session_state.last_query != query):
        
        if not st.session_state.current_pdf:
            st.error(" Veuillez d'abord importer un PDF dans la barre latérale")
        else:
            st.session_state.last_query = query
            
            with st.spinner(" Recherche en cours..."):
                try:
                    answer, chunks = run_rag_pipeline(
                        pdf_path=st.session_state.current_pdf,
                        query=query,
                        use_cached_index=True
                    )
                    
                    # Store in history
                    st.session_state.qa_history.append({
                        "query": query,
                        "answer": answer,
                        "chunks": chunks,
                        "timestamp": time.strftime("%H:%M:%S")
                    })
                    
                except Exception as e:
                    st.error(f" Erreur: {e}")
    
    # Display current answer
    if st.session_state.qa_history:
        latest = st.session_state.qa_history[-1]
        
        st.markdown("---")
        
        # Answer Card
        st.markdown(f"""
            <div class="answer-card">
                <div class="answer-header">
                    <span class="answer-icon">💡</span>
                    <span class="answer-title">Réponse</span>
                    <span class="answer-time">{latest['timestamp']}</span>
                </div>
                <div class="answer-content">
                    {latest['answer']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Sources (expandable)
        with st.expander(" Sources utilisées", expanded=False):
            for i, chunk in enumerate(latest['chunks'], 1):
                st.markdown(f"""
                    **Source {i}** - Section: `{chunk.get('section', 'N/A')}`
                    
                    {chunk['content'][:300]}...
                    
                    *Similarité: {chunk.get('semantic_similarity', 0):.2%}*
                """)
                st.markdown("---")
    
    # History
    if len(st.session_state.qa_history) > 1:
        st.markdown("---")
        st.markdown("###  Historique des questions")
        
        for i, item in enumerate(reversed(st.session_state.qa_history[:-1]), 1):
            with st.expander(f" {item['query']} - {item['timestamp']}", expanded=False):
                st.markdown(item['answer'])

# Mode: Quiz Generation
else:
    display_quiz_interface()

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <small>Propulsé par Groq LLM • FAISS • Sentence Transformers</small>
    </div>
""", unsafe_allow_html=True)
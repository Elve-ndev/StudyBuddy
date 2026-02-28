"""
Gestionnaire de quiz pour l'interface Streamlit
"""

import streamlit as st
from pathlib import Path
import json
from core.quiz_generator import run_quiz_pipeline, QUESTION_TYPES, DIFFICULTY_LEVELS
from UI.streamlit_utils import display_question_card, create_download_button

def display_quiz_interface():
    """Display the quiz generation interface"""
    
    st.markdown("""
        <div class="quiz-card">
            <h2> Générateur de Quiz Interactif</h2>
            <p>Créez un quiz personnalisé à partir de votre document PDF</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Check if PDF is loaded
    if not st.session_state.current_pdf:
        st.warning(" Veuillez d'abord importer un PDF dans la barre latérale")
        return
    
    # Quiz Configuration
    st.markdown("###  Configuration du Quiz")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_questions = st.number_input(
            "Nombre de questions",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="API gratuite: 5 questions max recommandé"
        )
        
        if num_questions > 5:
            st.warning(" Plus de 5 questions peut causer des rate limits (API gratuite)")
    
    with col2:
        difficulty = st.selectbox(
            "Difficulté",
            options=["facile", "moyen", "difficile"],
            index=1,
            help="Niveau de complexité des questions"
        )
    
    with col3:
        output_format = st.selectbox(
            "Format de sortie",
            options=["html", "json", "markdown"],
            index=0,
            help="Format du fichier de quiz généré"
        )
    
    # Topic (optional)
    topic = st.text_input(
        "Sujet spécifique (optionnel)",
        placeholder="Ex: brasure, soudage TIG, techniques...",
        help="Laissez vide pour couvrir tout le document"
    )
    
    # Question types selection
    st.markdown("###  Types de Questions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    selected_types = []
    
    with col1:
        if st.checkbox("QCM", value=True):
            selected_types.append("multiple_choice")
        if st.checkbox("Vrai/Faux", value=True):
            selected_types.append("true_false")
    
    with col2:
        if st.checkbox("Compléter", value=False):
            selected_types.append("fill_blank")
        if st.checkbox("Association", value=False):
            selected_types.append("matching")
    
    with col3:
        if st.checkbox("Réponse courte", value=True):
            selected_types.append("short_answer")
        if st.checkbox("Scénario", value=False):
            selected_types.append("scenario")
    
    with col4:
        if st.checkbox("Trouver l'erreur", value=False):
            selected_types.append("error_detection")
        if st.checkbox("Classement", value=False):
            selected_types.append("ranking")
    
    # Info about selected types
    if selected_types:
        st.info(f" {len(selected_types)} type(s) sélectionné(s): {', '.join(selected_types)}")
    else:
        st.warning(" Veuillez sélectionner au moins un type de question")
    
    st.markdown("---")
    
    # Generation button
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col2:
        generate_button = st.button(
            " Générer le Quiz",
            type="primary",
            use_container_width=True,
            disabled=not selected_types or st.session_state.quiz_generating
        )
    
    # Generate quiz
    if generate_button:
        st.session_state.quiz_generating = True
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Extraction
            status_text.text(" Extraction du PDF...")
            progress_bar.progress(20)
            
            # Step 2: Generate quiz
            status_text.text(f" Génération de {num_questions} questions...")
            progress_bar.progress(40)
            
            quiz_data, output_file = run_quiz_pipeline(
                pdf_path=st.session_state.current_pdf,
                topic=topic if topic else None,
                num_questions=num_questions,
                difficulty=difficulty,
                question_types=selected_types if selected_types else None,
                output_format=output_format
            )
            
            progress_bar.progress(100)
            status_text.text(" Quiz généré avec succès!")
            
            # Store in session state
            st.session_state.quiz_data = quiz_data
            st.session_state.quiz_output_file = output_file
            
            st.success(f" Quiz généré avec succès! {quiz_data['metadata']['num_questions']} questions créées")
            
        except Exception as e:
            st.error(f" Erreur lors de la génération: {e}")
            import traceback
            with st.expander("🔍 Détails de l'erreur"):
                st.code(traceback.format_exc())
        
        finally:
            st.session_state.quiz_generating = False
            progress_bar.empty()
            status_text.empty()
    
    # Display generated quiz
    if st.session_state.quiz_data:
        st.markdown("---")
        st.markdown("##  Quiz Généré")
        
        quiz_data = st.session_state.quiz_data
        metadata = quiz_data['metadata']
        
        # Quiz metadata
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(" Questions", metadata['num_questions'])
        
        with col2:
            st.metric(" Difficulté", metadata['difficulty'])
        
        with col3:
            st.metric(" Sujet", metadata['topic'][:15] + "..." if len(metadata['topic']) > 15 else metadata['topic'])
        
        with col4:
            st.metric(" Types", len(metadata['question_types']))
        
        st.markdown("---")
        
        # Download button
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            create_download_button(quiz_data, st.session_state.quiz_output_file)
        
        st.markdown("---")
        
        # Display questions in tabs or accordion
        display_mode = st.radio(
            "Mode d'affichage:",
            [" Par numéro", " Par type"],
            horizontal=True
        )
        
        if display_mode == " Par numéro":
            # Display all questions
            for i, question in enumerate(quiz_data['questions'], 1):
                display_question_card(question, i)
                st.markdown("---")
        
        else:
            # Group by type
            questions_by_type = {}
            for q in quiz_data['questions']:
                q_type = q.get('type_label', q['type'])
                if q_type not in questions_by_type:
                    questions_by_type[q_type] = []
                questions_by_type[q_type].append(q)
            
            # Display by type
            for q_type, questions in questions_by_type.items():
                with st.expander(f" {q_type} ({len(questions)} question(s))", expanded=True):
                    for i, question in enumerate(questions, 1):
                        display_question_card(question, question['id'])
                        if i < len(questions):
                            st.markdown("---")
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(" Générer un nouveau quiz", use_container_width=True):
                st.session_state.quiz_data = None
                st.session_state.quiz_output_file = None
                st.rerun()
        
        with col2:
            if output_format == "html" and Path(st.session_state.quiz_output_file).exists():
                st.markdown(f"""
                    <a href="file:///{Path(st.session_state.quiz_output_file).absolute()}" target="_blank">
                        <button style="width:100%; padding:10px; background:#667eea; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:600;">
                             Ouvrir dans le navigateur
                        </button>
                    </a>
                """, unsafe_allow_html=True)
        
        with col3:
            if st.button(" Voir les statistiques", use_container_width=True):
                show_quiz_statistics(quiz_data)

def show_quiz_statistics(quiz_data: dict):
    """Show statistics about the generated quiz"""
    st.markdown("---")
    st.markdown("###  Statistiques du Quiz")
    
    metadata = quiz_data['metadata']
    questions = quiz_data['questions']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Distribution par type:**")
        type_counts = {}
        for q in questions:
            q_type = q.get('type_label', q['type'])
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        for q_type, count in type_counts.items():
            st.write(f"- {q_type}: {count} question(s)")
    
    with col2:
        st.markdown("**Sections couvertes:**")
        sections = set(q.get('section', 'N/A') for q in questions)
        for section in sections:
            section_count = sum(1 for q in questions if q.get('section') == section)
            st.write(f"- {section}: {section_count} question(s)")
    
    st.markdown("---")
    
    # JSON preview
    with st.expander(" Voir les données JSON"):
        st.json(metadata)
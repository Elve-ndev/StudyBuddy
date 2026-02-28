"""
Utilitaires pour l'application Streamlit
"""

import streamlit as st
from pathlib import Path
import shutil

def apply_custom_css():
    """Apply modern, minimal CSS styling"""
    st.markdown("""
        <style>
        /* Main container */
        .main {
            padding: 2rem;
        }
        
        /* Header */
        .main-header {
            text-align: center;
            padding: 2rem 0 3rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .main-header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        
        .main-header p {
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.95;
        }
        
        /* Search container */
        .search-container {
            margin: 2rem 0;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Custom input styling */
        .stTextInput input {
            border-radius: 25px;
            border: 2px solid #e0e0e0;
            padding: 12px 20px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        .stTextInput input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
        }
        
        /* Button styling */
        .stButton button {
            border-radius: 25px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
        }
        
        .stButton button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Answer card */
        .answer-card {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        
        .answer-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .answer-icon {
            font-size: 1.5rem;
        }
        
        .answer-title {
            font-weight: 700;
            font-size: 1.2rem;
            color: #333;
            flex-grow: 1;
        }
        
        .answer-time {
            color: #999;
            font-size: 0.9rem;
        }
        
        .answer-content {
            color: #444;
            line-height: 1.7;
            font-size: 1.05rem;
        }
        
        /* Quiz card */
        .quiz-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .quiz-question {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            border-left: 4px solid #764ba2;
        }
        
        .quiz-question-number {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 6px 14px;
            border-radius: 50%;
            font-weight: 700;
            margin-right: 10px;
        }
        
        .quiz-type-badge {
            display: inline-block;
            background: #ffd700;
            color: #333;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-left: 10px;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #2e1a47 0%, #1e3a8a 100%);
        }
        
        section[data-testid="stSidebar"] .stMarkdown h3 {
            color: #667eea;
            font-weight: 700;
        }
        
        /* File uploader */
        .stFileUploader {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            border: 2px dashed #e0e0e0;
        }
        
        /* Success/Error/Info messages */
        .stSuccess {
            border-radius: 10px;
        }
        
        .stError {
            border-radius: 10px;
        }
        
        .stInfo {
            border-radius: 10px;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background: #f8f9fa;
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* Radio buttons */
        .stRadio > label {
            font-weight: 600;
            color: #333;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-color: #667eea !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 12px 24px;
            font-weight: 600;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        </style>
    """, unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'qa_history' not in st.session_state:
        st.session_state.qa_history = []
    
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = None
    
    if 'current_pdf' not in st.session_state:
        st.session_state.current_pdf = None
    
    if 'last_query' not in st.session_state:
        st.session_state.last_query = ""
    
    if 'mode' not in st.session_state:
        st.session_state.mode = " Questions & Réponses"
    
    if 'quiz_generating' not in st.session_state:
        st.session_state.quiz_generating = False

def save_uploaded_pdf(uploaded_file) -> Path:
    """
    Save uploaded PDF to Data directory
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Path to saved PDF
    """
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("Data/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    pdf_path = uploads_dir / uploaded_file.name
    
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return pdf_path

def format_quiz_for_display(quiz_data: dict) -> str:
    """
    Format quiz data for nice display
    
    Args:
        quiz_data: Quiz data dictionary
        
    Returns:
        Formatted HTML string
    """
    html = f"""
    <div class="quiz-card">
        <h2> {quiz_data['metadata']['topic']}</h2>
        <p><strong>Difficulté:</strong> {quiz_data['metadata']['difficulty']} | 
           <strong>Questions:</strong> {quiz_data['metadata']['num_questions']}</p>
    </div>
    """
    return html

def display_question_card(question: dict, index: int):
    """
    Display a single question in a nice card format
    
    Args:
        question: Question data dictionary
        index: Question number
    """
    st.markdown(f"""
        <div class="quiz-question">
            <span class="quiz-question-number">{index}</span>
            <strong>{question.get('type_label', 'Question')}</strong>
            <span class="quiz-type-badge">{question.get('difficulty', 'moyen')}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Display question content
    st.markdown(f"**Section:** {question.get('section', 'N/A')}")
    st.markdown("---")
    
    # Display raw content in expandable section
    with st.expander(" Voir la question et la réponse", expanded=True):
        st.code(question.get('raw_content', 'Contenu non disponible'), language=None)

def create_download_button(quiz_data: dict, output_file: str):
    """
    Create a download button for the quiz file
    
    Args:
        quiz_data: Quiz data
        output_file: Path to output file
    """
    output_path = Path(output_file)
    
    if output_path.exists():
        with open(output_path, 'rb') as f:
            file_data = f.read()
        
        file_ext = output_path.suffix[1:]  # Remove the dot
        mime_types = {
            'html': 'text/html',
            'json': 'application/json',
            'markdown': 'text/markdown'
        }
        
        st.download_button(
            label=f"⬇ Télécharger le quiz ({file_ext.upper()})",
            data=file_data,
            file_name=output_path.name,
            mime=mime_types.get(file_ext, 'text/plain'),
            use_container_width=True
        )
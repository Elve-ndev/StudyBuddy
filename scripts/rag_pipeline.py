import time
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import os
from groq import Groq

from core.semantic_chunker import RobustPDFChunker
from core.hybrid_retriever import HybridRetriever

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
PDF_PATH = Path("Data/cours_.pdf")
TOP_K = 3
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_DIR = Path("Data/vector_store")

# Modèle Groq gratuit recommandé
LLM_MODEL = "llama-3.1-8b-instant"

MIN_WORDS = 5
MAX_WORDS = 150
OVERLAP = 20

# ==================== GROQ CLIENT ====================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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


# ==================== RAG PIPELINE ====================
def run_rag_pipeline(
    pdf_path: Path,
    query: str,
    use_cached_index: bool = True
) -> Tuple[str, List[Dict]]:

    start_total = time.time()

    # STEP 1 - Extraction
    raw_text = extract_pdf_text(pdf_path)

# ===== DEBUG PDF =====
    print("\n===== DEBUG PDF =====")
    print("PDF PATH:", pdf_path.resolve())
    print("TEXT LENGTH:", len(raw_text))
    print("FIRST 300 CHARS:\n", raw_text[:300])
    print("=====================\n")
 


    # STEP 2 - Chunking
    
    chunker = RobustPDFChunker(
    max_words=180,
    overlap=30
    )


    chunks = chunker.chunk_document(raw_text)
    logger.info(f"{len(chunks)} chunks créés")

    # STEP 3 - Index
    retriever = HybridRetriever(
        embed_model_name=EMBED_MODEL,
        vector_dir=VECTOR_DIR
    )

    if not (use_cached_index and retriever.load_index()):
        retriever.build_index([
            {
                "content": c.content,
                "section": c.section,
                "chunk_id": c.chunk_id,
                "word_count": c.word_count
            }
            for c in chunks
        ])

    # STEP 4 - Retrieval
    top_chunks = retriever.retrieve(query, top_k=TOP_K)

    # STEP 5 - Construction du contexte
    context = "\n\n---\n\n".join(
        f"[Section: {c['section']}]\n{c['content']}"
        for c in top_chunks
    )

    prompt = f"""
Contexte:
{context}

Question: {query}

Réponds uniquement à partir du contexte fourni.
Si l'information n'est pas présente, dis que ce n'est pas mentionné.
"""

    # STEP 6 - Appel Groq
    start_llm = time.time()

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "Assistant technique factuel."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=300
    )

    llm_time = time.time() - start_llm
    answer = response.choices[0].message.content

    total_time = time.time() - start_total

    logger.info(f"Temps LLM: {llm_time:.2f}s | Total: {total_time:.2f}s")

    print("\n" + "=" * 60)
    print(answer)
    print("=" * 60)

    return answer, top_chunks

# ==================== MAIN ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=str, default=str(PDF_PATH))
    parser.add_argument("--query", type=str)
    parser.add_argument("--no-cache", action="store_true")

    args = parser.parse_args()
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        logger.error(f"PDF introuvable: {pdf_path}")
        exit(1)

    question = args.query or "Qu'est-ce que la brasure ?"

    run_rag_pipeline(
        pdf_path,
        question,
        use_cached_index=not args.no_cache
    )

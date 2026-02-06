
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "Data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
COURSE_CACHE_DIR = DATA_DIR / "course_cache"
QUIZ_CACHE_DIR = DATA_DIR / "precomputed_quizzes"

for d in [DATA_DIR, VECTOR_STORE_DIR, COURSE_CACHE_DIR, QUIZ_CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBEDDING_BATCH_SIZE = 32


CHUNK_MIN_TOKENS = 120
CHUNK_MAX_TOKENS = 350
SIMILARITY_THRESHOLD = 0.78   

TOP_K = 5
 
LLM_MODEL_NAME = "llama-3.2"
LLM_MAX_TOKENS = 512
LLM_TEMPERATURE = 0.2


DEVICE = "auto"  # "cpu", "cuda", ou "auto"
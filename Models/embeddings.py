import numpy as np
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingsHandler:
    def __init__(self, model_name: str, vector_dir: str = "./vectors"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)
        self.vector_dir = Path(vector_dir)
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Embedding model loaded: {model_name} on {self.device}")

    def embed_texts(self, texts, batch_size: int = 8, normalize: bool = True) -> np.ndarray:
        """
        Compute embeddings for a list of texts (CPU-friendly).
        texts: str or list of str
        normalize: if True, output vectors will be L2-normalized
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            device=self.device
        )

        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-10)

        return embeddings

    def save_embeddings(self, embeddings: np.ndarray, filename: str = "embeddings.pkl"):
        path = self.vector_dir / filename
        with open(path, "wb") as f:
            pickle.dump(embeddings, f)
        logger.info(f"Embeddings saved to {path}")

    def load_embeddings(self, filename: str = "embeddings.pkl") -> np.ndarray:
        path = self.vector_dir / filename
        if path.exists():
            with open(path, "rb") as f:
                embeddings = pickle.load(f)
            logger.info(f"Embeddings loaded from {path}")
            return embeddings
        else:
            logger.warning(f"No embeddings found at {path}")
            return None


# ---------------------- CPU-friendly example usage ----------------------
if __name__ == "__main__":
    # Small chunks for CPU
    texts = [
        "Le soudage est un procédé d'assemblage permanent.",
        "On chauffe le métal jusqu'à fusion.",
        "Un joint solide se forme au refroidissement.",
        "Le soudage nécessite des compétences spécifiques."
    ]

    # Initialize embeddings handler
    emb_handler = EmbeddingsHandler(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        vector_dir="./vectors"
    )

    # Compute embeddings with small batch size (CPU-friendly)
    embs = emb_handler.embed_texts(texts, batch_size=4)
    print("Embeddings shape:", embs.shape)

    # Save embeddings for later
    emb_handler.save_embeddings(embs)

    # Load embeddings to verify
    loaded_embs = emb_handler.load_embeddings()
    print("Loaded embeddings shape:", loaded_embs.shape if loaded_embs is not None else "None")

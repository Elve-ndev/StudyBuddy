
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
from pathlib import Path
from utils.config import EMBEDDING_MODEL_NAME, EMBEDDING_DIM, EMBEDDING_BATCH_SIZE, VECTOR_STORE_DIR

class EmbeddingsModel:
    def __init__(self, model_name=EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.vector_store_dir = VECTOR_STORE_DIR
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)

    def embed(self, texts, batch_size=EMBEDDING_BATCH_SIZE):
        """
        texts: list of str
        returns: np.ndarray (len(texts), EMBEDDING_DIM)
        """
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)
        return np.array(embeddings)

    def save_embeddings(self, embeddings, filename="embeddings.pkl"):
        path = self.vector_store_dir / filename
        with open(path, "wb") as f:
            pickle.dump(embeddings, f)
        print(f"Embeddings saved to {path}")

    def load_embeddings(self, filename="embeddings.pkl"):
        path = self.vector_store_dir / filename
        if path.exists():
            with open(path, "rb") as f:
                embeddings = pickle.load(f)
            print(f"Embeddings loaded from {path}")
            return embeddings
        else:
            print(f"No embeddings found at {path}")
            return None

if __name__ == "__main__":
    texts = [
        "Voici un premier paragraphe exemple.",
        "Un second paragraphe avec un peu plus de contenu."
    ]
    emb_model = EmbeddingsModel()
    embs = emb_model.embed(texts)
    print("Embeddings shape:", embs.shape)
    emb_model.save_embeddings(embs)
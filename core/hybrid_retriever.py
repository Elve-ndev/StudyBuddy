from typing import List, Dict
import logging
import numpy as np
from pathlib import Path
import faiss
import pickle
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class HybridRetriever:
    """
    Semantic retrieval using FAISS and SentenceTransformers.
    Optimized for CPU usage.
    """
    def __init__(
        self,
        embed_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        vector_dir: str = "./vector_store",
    ):
        self.embed_model_name = embed_model_name
        self.vector_dir = Path(vector_dir)
        self.vector_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        logger.info(f"Loading embedding model: {embed_model_name}")
        self.embed_model = SentenceTransformer(embed_model_name, device="cpu")

        # FAISS index and metadata
        self.index = None
        self.metadata = []  # list of chunk metadata dicts
        self.dimension = self.embed_model.get_sentence_embedding_dimension()
        self.index_path = self.vector_dir / "faiss.index"
        self.meta_path = self.vector_dir / "metadata.pkl"

    def embed_texts(self, texts: List[str], batch_size: int = 8) -> np.ndarray:
        """
        Compute embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Batch size for encoding (smaller = less memory)
            
        Returns:
            Normalized embeddings array (n_texts, dimension)
        """
        embeddings = self.embed_model.encode(
            texts, 
            batch_size=batch_size, 
            convert_to_numpy=True, 
            show_progress_bar=True
        )
        
        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-10)
        
        return embeddings

    def build_index(self, chunks: List[Dict]):
        """
        Build FAISS index from chunks.
        
        Args:
            chunks: List of dicts with at least {"content": str, ...}
        """
        logger.info(f"Building index for {len(chunks)} chunks...")
        
        texts = [c["content"] for c in chunks]
        embeddings = self.embed_texts(texts)

        # Build FAISS index (FlatIP = Inner Product for cosine similarity)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings.astype(np.float32))
        self.metadata = chunks

        # Save to disk
        self.save_index()
        logger.info(f"FAISS index built and saved with {len(chunks)} chunks.")

    def save_index(self):
        """Save index and metadata to disk"""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
        logger.info(f"Index saved to {self.index_path}")

    def load_index(self):
        """Load index and metadata from disk"""
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(f"FAISS index loaded with {len(self.metadata)} chunks.")
            return True
        else:
            logger.warning("No saved FAISS index found.")
            return False

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve top-k most similar chunks for a query.
        
        Args:
            query: Query string
            top_k: Number of chunks to retrieve
            
        Returns:
            List of chunk dicts with added 'semantic_similarity' score
        """
        if self.index is None:
            raise ValueError("FAISS index not built or loaded. Call build_index() or load_index() first.")

        # Embed query
        query_emb = self.embed_texts([query])
        
        # Search in FAISS index
        distances, indices = self.index.search(query_emb.astype(np.float32), top_k)

        # Prepare results
        results = []
        for score, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):  # Valid index
                chunk = self.metadata[idx].copy()
                chunk["semantic_similarity"] = float(score)
                results.append(chunk)

        return results
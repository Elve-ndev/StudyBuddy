# test_embeddings.py
import time
from Models.embeddings import EmbeddingsModel

# Exemple de textes à embedder
texts = [
    "Voici le premier paragraphe d'exemple pour tester les embeddings.",
    "Un second paragraphe, légèrement plus long, pour observer la différence.",
    "Le troisième texte contient quelques phrases supplémentaires pour tester la robustesse."
]

def test_embeddings(texts):
    start_time = time.time()  # Début du timer

    
    emb_model = EmbeddingsModel()
    
   
    embeddings = emb_model.embed(texts)
    
    end_time = time.time()  # Fin du timer
    elapsed = end_time - start_time

    print(f"Nombre de textes : {len(texts)}")
    print(f"Shape des embeddings : {embeddings.shape}")
    print(f"Temps d'exécution : {elapsed:.2f} secondes")
 
    emb_model.save_embeddings(embeddings, filename="test_embs.pkl")

if __name__ == "__main__":
    test_embeddings(texts)
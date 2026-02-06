from typing import List, Dict
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import logging
import ollama

logger = logging.getLogger(__name__)


class CourseRetriever:
    def __init__(self, model_name: str = "phi3:mini"):
        self.model_name = model_name
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.index = None
        self.chunks = []
        self.course_title = ""
        self.main_concepts = []

    def index_course(self, chunks: List[Dict], course_title: str, main_concepts: List[str]):
        self.chunks = chunks
        self.course_title = course_title
        self.main_concepts = main_concepts

        nodes = []
        for chunk in chunks:
            node = TextNode(
                text=chunk["content"],
                metadata={
                    "section": chunk["section"],
                    "main_concept": chunk["main_concept"],
                    "matched_concepts": chunk["matched_concepts"],
                    "chunk_id": chunk["chunk_id"],
                },
            )
            nodes.append(node)

        self.index = VectorStoreIndex(
            nodes=nodes,
            embed_model=self.embed_model,
        )

        logger.info(f"Index created with {len(chunks)} chunks")

    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = 5,
        use_reranking: bool = False,
    ) -> List[Dict]:
        if self.index is None:
            raise ValueError("Index not created")

        retriever = self.index.as_retriever(similarity_top_k=top_k * 2)
        nodes = retriever.retrieve(query)

        if use_reranking:
            logger.warning("Reranking disabled due to memory constraints")

        nodes = nodes[:top_k]

        results = []
        for node in nodes:
            results.append(
                {
                    "content": node.node.text,
                    "section": node.node.metadata.get("section", "Unknown"),
                    "main_concept": node.node.metadata.get("main_concept", ""),
                    "matched_concepts": node.node.metadata.get(
                        "matched_concepts", []
                    ),
                    "chunk_id": node.node.metadata.get("chunk_id", -1),
                    "semantic_similarity": node.score or 0.0,
                }
            )

        return results

    def answer_question(
        self,
        question: str,
        context_size: int = 3,
    ) -> Dict:
        relevant_chunks = self.retrieve_relevant_chunks(
            question,
            top_k=context_size,
            use_reranking=False,
        )

        combined_context = "\n\n---\n\n".join(
            [
                f"Section {i + 1} ({chunk['section']}):\n{chunk['content']}"
                for i, chunk in enumerate(relevant_chunks)
            ]
        )

        prompt = f"""Contexte extrait du document:
{combined_context}

Question: {question}

Réponds de manière concise et précise en te basant uniquement sur le contexte fourni."""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un assistant qui répond aux questions basées sur le contexte fourni.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 300,
                },
            )

            final_answer = response["message"]["content"]

            return {
                "answer": final_answer,
                "confidence": 0.8,
                "sources": relevant_chunks,
            }

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {
                "answer": f"Generation error: {str(e)}",
                "confidence": 0.0,
                "sources": relevant_chunks,
            }

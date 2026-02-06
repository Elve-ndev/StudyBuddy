from typing import List, Dict
import ollama
import logging
import re

logger = logging.getLogger(__name__)


class QuizGenerator:
    def __init__(
        self,
        model_name: str = "phi3:mini",
        questions_per_chunk: int = 2,
        timeout: int = 120,
    ):
        self.model_name = model_name
        self.questions_per_chunk = questions_per_chunk
        self.timeout = timeout

        try:
            ollama.show(model_name)
            logger.info(f"Model {model_name} available")
        except Exception as e:
            logger.error(f"Model {model_name} not found: {e}")
            raise

    def _build_batch_prompt(self, chunks: List[Dict], total_questions: int) -> str:
        combined_content = "\n\n---SECTION---\n\n".join(
            [
                f"SECTION {i + 1}: {chunk.get('section', 'Sans titre')}\n{chunk['content'][:500]}"
                for i, chunk in enumerate(chunks)
            ]
        )

        return f"""Tu es un enseignant technique créant un QCM.

À partir du contenu ci-dessous, génère EXACTEMENT {total_questions} questions QCM.

Contraintes:
- Questions factuelles basées sur le contenu
- Sections différentes couvertes
- 4 choix (A, B, C, D)
- Une seule bonne réponse

Format obligatoire:

Q1: Question
A) Option
B) Option
C) Option
D) Option
Réponse: A

CONTENU:
{combined_content[:2000]}

Commence par Q1 et termine à Q{total_questions}.
"""

    def _parse_text_response(self, text: str) -> List[Dict]:
        questions = []
        text = text.strip()
        blocks = re.split(r"\n(?=Q\d+[\s:.])", text)

        for block in blocks:
            if not block.strip():
                continue

            q_match = re.search(
                r"Q\d+[\s:.]\s*(.*?)(?=\n[A-D][\s\)])",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if not q_match:
                continue

            question_text = q_match.group(1).strip()

            options = {}
            for letter in ["A", "B", "C", "D"]:
                pattern = rf"{letter}[\)\s]\s*(.*?)(?=\n[A-D][\)\s]|\nR[ée]ponse|\Z)"
                opt_match = re.search(
                    pattern,
                    block,
                    re.MULTILINE | re.DOTALL | re.IGNORECASE,
                )
                if opt_match:
                    options[letter] = " ".join(opt_match.group(1).split())

            if len(options) != 4:
                continue

            ans_match = re.search(
                r"R[ée]ponse\s*[:=]?\s*([A-D])",
                block,
                re.IGNORECASE,
            )
            if not ans_match:
                continue

            correct_answer = ans_match.group(1).upper()
            if correct_answer not in options:
                continue

            questions.append(
                {
                    "question": question_text,
                    "options": options,
                    "correct_answer": correct_answer,
                }
            )

        return questions

    def generate_quiz_from_chunks(
        self,
        chunks: List[Dict],
        max_chunks: int = 5,
    ) -> List[Dict]:
        selected_chunks = chunks[:max_chunks]
        total_questions = len(selected_chunks) * self.questions_per_chunk

        try:
            prompt = self._build_batch_prompt(selected_chunks, total_questions)

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 700,
                    "top_k": 40,
                    "top_p": 0.9,
                },
            )

            return self._parse_text_response(response.get("response", ""))

        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return []

    def display_quiz(self, questions: List[Dict], show_answers: bool = True):
        if not questions:
            return

        for i, q in enumerate(questions, 1):
            print(f"\nQ{i}. {q['question']}")
            for key in ["A", "B", "C", "D"]:
                print(f"  {key}) {q['options'].get(key, '')}")
            if show_answers:
                print(f"Réponse: {q['correct_answer']}")

    def export_quiz_json(self, questions: List[Dict], filepath: str):
        import json

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"JSON export failed: {e}")

    def export_quiz_text(self, questions: List[Dict], filepath: str):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for i, q in enumerate(questions, 1):
                    f.write(f"Q{i}. {q['question']}\n")
                    for key in ["A", "B", "C", "D"]:
                        f.write(f"  {key}) {q['options'][key]}\n")
                    f.write(f"Réponse: {q['correct_answer']}\n\n")
        except Exception as e:
            logger.error(f"Text export failed: {e}")

import json
import logging
import time
import hashlib
import os
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

try:
    import ollama
except ImportError:
    ollama = None

try:
    import fitz
except ImportError:
    fitz = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DocumentProcessor")


class ProcessingStatus(Enum):
    SUCCESS = "success"
    LLM_FAILED = "llm_failed"
    FALLBACK_ONLY = "fallback_only"
    PDF_EXTRACTION_FAILED = "pdf_extraction_failed"


@dataclass
class ProcessingMetrics:
    document_hash: str
    total_duration: float
    llm_duration: float = 0.0
    pdf_extraction_duration: float = 0.0
    token_count: int = 0
    status: ProcessingStatus = ProcessingStatus.SUCCESS
    errors: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    processed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "confidence": round(self.confidence_score, 3),
            "total_time_ms": round(self.total_duration * 1000, 2),
            "llm_time_ms": round(self.llm_duration * 1000, 2),
            "pdf_time_ms": round(self.pdf_extraction_duration * 1000, 2),
            "tokens": self.token_count,
            "errors": self.errors,
            "hash": self.document_hash,
        }


@dataclass
class DocumentUnderstanding:
    title: str
    main_concepts: List[str]
    structure: Dict[str, List[str]]
    document_type: str = "unknown"
    language: str = "fr"
    summary: str = ""
    raw_text: str = ""
    detected_headings: List[str] = field(default_factory=list)
    metrics: Optional[ProcessingMetrics] = None

    @property
    def concept_count(self) -> int:
        return len(self.main_concepts)

    @property
    def section_count(self) -> int:
        return len(self.structure)


class IntelligentDocumentProcessor:
    MAX_PROMPT_CHARS = 2000
    MIN_CONTENT_LENGTH = 150

    def __init__(self, model: str = "phi3:mini", enable_cache: bool = True):
        if ollama is None:
            raise RuntimeError("Ollama non installé: pip install ollama")

        self.model = model
        self.enable_cache = enable_cache
        self._cache: Dict[str, DocumentUnderstanding] = {}

        logger.info(f"Processor initialisé | Modèle: {self.model}")

    def _generate_document_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def _extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, float]:
        if fitz is None:
            raise RuntimeError("PyMuPDF manquant: pip install pymupdf")

        start = time.time()
        try:
            doc = fitz.open(pdf_path)
            text = "\n\n".join(page.get_text() for page in doc)
            doc.close()
            duration = time.time() - start
            return text, duration
        except Exception as e:
            raise RuntimeError(f"Échec extraction PDF: {e}") from e

    def _extract_headings_from_text(self, text: str) -> List[str]:
        headings = []
        seen = set()

        for line in text.split("\n")[:200]:
            line = line.strip()

            if not line or len(line) > 100:
                continue

            is_numbered = bool(re.match(r"^(\d+\.|\d+\.\d+|[IVX]+\.)\s+", line))
            is_uppercase = line.isupper() and 3 <= len(line.split()) <= 8
            is_colon = len(line) < 60 and line.endswith(":")
            is_keyword = any(
                line.lower().startswith(kw)
                for kw in [
                    "chapitre",
                    "section",
                    "partie",
                    "introduction",
                    "conclusion",
                    "annexe",
                    "résumé",
                    "abstract",
                ]
            )

            if is_numbered or is_uppercase or is_colon or is_keyword:
                cleaned = line[:80].rstrip(".:-")
                if cleaned not in seen and len(cleaned) > 3:
                    headings.append(cleaned)
                    seen.add(cleaned)

        return headings[:15]

    def _detect_language(self, text: str) -> str:
        sample = text[:500].lower()
        fr_count = sum(sample.count(w) for w in [" le ", " la ", " les ", " un ", " une ", " est "])
        en_count = sum(sample.count(w) for w in [" the ", " a ", " an ", " is ", " in "])
        return "fr" if fr_count > en_count else "en"

    def _detect_document_type(self, text: str) -> str:
        text_lower = text.lower()
        scores = {
            "scientific": sum(2 for kw in ["abstract", "methodology", "results", "résumé"] if kw in text_lower),
            "technical": sum(2 for kw in ["api", "configuration", "implementation"] if kw in text_lower),
            "cours": sum(2 for kw in ["cours", "chapitre", "exercice", "tp"] if kw in text_lower),
        }
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"

    def _build_optimized_prompt(self, text: str, headings: List[str], doc_type: str) -> str:
        preview = text[: self.MAX_PROMPT_CHARS]
        headings_str = "\n".join(f"- {h}" for h in headings[:10])

        return f"""Analyse ce document {doc_type}. Retourne JSON strict (pas de texte avant/après):

{{"title": "titre du document", "main_concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"]}}

DÉBUT DU DOCUMENT ({len(preview)} chars):
{preview}

TITRES DÉTECTÉS:
{headings_str}

Règles:
- main_concepts: 5-8 concepts techniques spécifiques
- title: max 100 caractères
- JSON uniquement"""

    def _call_llm_once(self, prompt: str) -> Tuple[Optional[Dict], float]:
        start = time.time()
        try:
            try:
                ollama.show(self.model)
            except Exception:
                ollama.pull(self.model)

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Expert en analyse documentaire. "
                            "Réponds uniquement avec du JSON valide au format "
                            '{"title": "...", "main_concepts": [...]}'
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                options={
                    "temperature": 0.1,
                    "num_predict": 400,
                    "top_p": 0.9,
                },
            )

            duration = time.time() - start
            content = response.get("message", {}).get("content", "").strip()

            if not content:
                return None, duration

            clean = re.sub(r"```(?:json)?\s*|\s*```", "", content, flags=re.IGNORECASE)
            start_idx = clean.find("{")
            end_idx = clean.rfind("}")

            if start_idx == -1 or end_idx == -1:
                return None, duration

            data = json.loads(clean[start_idx : end_idx + 1])
            return data, duration

        except Exception:
            return None, time.time() - start

    def _extract_title_fallback(self, text: str, headings: List[str]) -> str:
        if headings:
            return headings[0][:100]

        lines = [l.strip() for l in text.split("\n") if 15 <= len(l.strip()) <= 120]
        return lines[0][:100] if lines else "Document sans titre"

    def _extract_concepts_fallback(self, text: str) -> List[str]:
        pattern = r"\b[A-ZÀ-Ÿ][a-zà-ÿ]{3,}(?:[\s-][A-ZÀ-Ÿ][a-zà-ÿ]{2,}){0,2}\b"
        matches = re.findall(pattern, text[:5000])

        counts = {}
        for m in matches:
            word = m.strip().lower()
            if len(word) > 4:
                counts[word] = counts.get(word, 0) + 1

        sorted_concepts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [c.title() for c, _ in sorted_concepts[:8]] or ["Concept"]

    def _build_structure_from_headings(self, headings: List[str]) -> Dict[str, List[str]]:
        if not headings:
            return {"Document": ["Contenu"]}

        return {heading: ["Sous-section"] for heading in headings[:8]}

    def _validate_and_enrich(
        self,
        llm_data: Optional[Dict],
        text: str,
        headings: List[str],
        language: str,
    ) -> Tuple[Dict, float]:
        confidence = 1.0

        if llm_data and llm_data.get("title"):
            title = str(llm_data["title"]).strip()[:100]
        else:
            title = self._extract_title_fallback(text, headings)
            confidence *= 0.7

        if llm_data and isinstance(llm_data.get("main_concepts"), list):
            concepts = [
                c
                for c in llm_data["main_concepts"]
                if len(str(c)) > 3
            ][:8]
        else:
            concepts = []
            confidence *= 0.6

        if len(concepts) < 3:
            concepts = self._extract_concepts_fallback(text)
            confidence *= 0.8

        structure = self._build_structure_from_headings(headings)

        return {
            "title": title,
            "main_concepts": concepts,
            "structure": structure,
        }, max(0.3, confidence)

    def process_pdf(self, pdf_path: str) -> DocumentUnderstanding:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF introuvable: {pdf_path}")

        total_start = time.time()
        doc_hash = None
        pdf_duration = 0.0
        llm_duration = 0.0

        try:
            raw_text, pdf_duration = self._extract_text_from_pdf(pdf_path)
            doc_hash = self._generate_document_hash(raw_text)

            if self.enable_cache and doc_hash in self._cache:
                cached = self._cache[doc_hash]
                cached.metrics.total_duration = time.time() - total_start
                return cached

            if len(raw_text.strip()) < self.MIN_CONTENT_LENGTH:
                raise ValueError("Contenu trop court")

            language = self._detect_language(raw_text)
            doc_type = self._detect_document_type(raw_text)
            headings = self._extract_headings_from_text(raw_text)

            prompt = self._build_optimized_prompt(raw_text, headings, doc_type)
            llm_data, llm_duration = self._call_llm_once(prompt)

            validated_data, confidence = self._validate_and_enrich(
                llm_data, raw_text, headings, language
            )

            status = ProcessingStatus.SUCCESS if llm_data else ProcessingStatus.FALLBACK_ONLY
            metrics = ProcessingMetrics(
                document_hash=doc_hash,
                total_duration=time.time() - total_start,
                llm_duration=llm_duration,
                pdf_extraction_duration=pdf_duration,
                token_count=len(raw_text.split()),
                status=status,
                confidence_score=confidence,
            )

            understanding = DocumentUnderstanding(
                title=validated_data["title"],
                main_concepts=validated_data["main_concepts"],
                structure=validated_data["structure"],
                document_type=doc_type,
                language=language,
                summary=f"Document {doc_type} sur {', '.join(validated_data['main_concepts'][:3])}",
                raw_text=raw_text,
                detected_headings=headings,
                metrics=metrics,
            )

            if self.enable_cache:
                self._cache[doc_hash] = understanding

            return understanding

        except Exception as e:
            metrics = ProcessingMetrics(
                document_hash=doc_hash or "unknown",
                total_duration=time.time() - total_start,
                pdf_extraction_duration=pdf_duration,
                llm_duration=llm_duration,
                status=ProcessingStatus.PDF_EXTRACTION_FAILED,
                errors=[str(e)],
                confidence_score=0.1,
            )

            return DocumentUnderstanding(
                title="Erreur d'analyse",
                main_concepts=["erreur"],
                structure={"Erreur": [str(e)[:100]]},
                raw_text="",
                metrics=metrics,
            )


if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "Data", "cours_.pdf")

    if os.path.exists(pdf_path):
        processor = IntelligentDocumentProcessor(model="phi3:mini")
        result = processor.process_pdf(pdf_path)

        print(result.title)
        print(", ".join(result.main_concepts[:5]))
        print(len(result.structure))
        print(f"{result.metrics.total_duration:.2f}s")
    else:
        print(f"PDF introuvable: {pdf_path}")

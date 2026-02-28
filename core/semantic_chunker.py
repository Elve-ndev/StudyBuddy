from typing import List, Dict
from dataclasses import dataclass
import re


@dataclass
class SemanticChunk:
    content: str
    section: str
    main_concept: str
    matched_concepts: List[str]
    chunk_id: int
    word_count: int
    char_start: int = 0


class RobustPDFChunker:
    """
    Simple, stable and CPU-friendly chunker for technical PDFs.
    Splits text into logical units and groups them into size-controlled chunks.
    """

    def __init__(self, max_words: int = 200, overlap: int = 30):
        self.max_words = max_words
        self.overlap = overlap

    # ---------------------------------------------------
    # STEP 1 — Split text into logical units
    # ---------------------------------------------------
    def _split_into_units(self, text: str) -> List[str]:
        # Prefer paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            return paragraphs

        # Fallback: lines
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if len(lines) > 3:
            return lines

        # Fallback: sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    # ---------------------------------------------------
    # STEP 2 — Group units into chunks
    # ---------------------------------------------------
    def _window_chunk(self, units: List[str]) -> List[List[str]]:
        chunks = []
        current_chunk = []
        current_word_count = 0

        for unit in units:
            unit_word_count = len(unit.split())

            # If adding this unit exceeds max_words → close current chunk
            if current_word_count + unit_word_count > self.max_words and current_chunk:
                chunks.append(current_chunk)

                # Overlap handling
                if self.overlap > 0:
                    overlap_words = 0
                    overlap_units = []

                    for u in reversed(current_chunk):
                        overlap_words += len(u.split())
                        overlap_units.insert(0, u)
                        if overlap_words >= self.overlap:
                            break

                    current_chunk = overlap_units
                    current_word_count = sum(len(u.split()) for u in current_chunk)
                else:
                    current_chunk = []
                    current_word_count = 0

            current_chunk.append(unit)
            current_word_count += unit_word_count

        # Add last chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    # ---------------------------------------------------
    # STEP 3 — Build SemanticChunk objects
    # ---------------------------------------------------
    def _create_chunk(
        self,
        units: List[str],
        section: str,
        chunk_id: int,
        concepts: List[str],
        char_start: int
    ) -> SemanticChunk:

        content = "\n\n".join(units)
        word_count = len(content.split())

        matched = [c for c in concepts if c.lower() in content.lower()]
        main_concept = matched[0] if matched else content.split()[:5]
        if isinstance(main_concept, list):
            main_concept = " ".join(main_concept) + "..."

        return SemanticChunk(
            content=content,
            section=section,
            main_concept=main_concept,
            matched_concepts=matched,
            chunk_id=chunk_id,
            word_count=word_count,
            char_start=char_start
        )

    # ---------------------------------------------------
    # MAIN FUNCTION
    # ---------------------------------------------------
    def chunk_document(
        self,
        raw_text: str,
        headings: List[str] = None,
        structure: Dict[str, List[str]] = None,
        concepts: List[str] = None
    ) -> List[SemanticChunk]:

        if not raw_text.strip():
            return []

        if headings is None:
            headings = []
        if structure is None:
            structure = {}
        if concepts is None:
            concepts = []

        sections = {"Document": raw_text}

        all_chunks = []
        chunk_id = 0

        for section_name, text in sections.items():
            if not text.strip():
                continue

            units = self._split_into_units(text)
            window_chunks = self._window_chunk(units)

            char_pos = 0

            for window in window_chunks:
                chunk = self._create_chunk(
                    window,
                    section_name,
                    chunk_id,
                    concepts,
                    char_pos
                )
                all_chunks.append(chunk)

                char_pos += len("\n\n".join(window))
                chunk_id += 1

        return all_chunks

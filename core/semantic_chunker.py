from typing import List, Dict, Tuple
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


class SemanticChunker:
    def __init__(self, min_words: int = 80, max_words: int = 300, fuzzy_threshold: float = 0.6):
        self.min_words = min_words
        self.max_words = max_words
        self.fuzzy_threshold = fuzzy_threshold

    def _fuzzy_match(self, text: str, pattern: str) -> float:
        text_clean = re.sub(r'[^\w\s]', '', text.lower())
        pattern_clean = re.sub(r'[^\w\s]', '', pattern.lower())

        if pattern_clean in text_clean:
            return 1.0

        text_words = set(text_clean.split())
        pattern_words = set(pattern_clean.split())

        if not pattern_words:
            return 0.0

        common = len(text_words & pattern_words)
        score = common / len(pattern_words)

        return score

    def _find_sections_flexible(
        self,
        text: str,
        headings: List[str],
        structure: Dict[str, List[str]]
    ) -> Dict[str, str]:

        if not headings and not structure:
            return {"Document": text}

        section_patterns = headings if headings else list(structure.keys())

        sections = {}
        lines = text.split('\n')

        current_section = section_patterns[0] if section_patterns else "Introduction"
        current_content = []

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                current_content.append(line)
                continue

            best_match = None
            best_score = 0.0

            for pattern in section_patterns:
                score = self._fuzzy_match(line_stripped, pattern)
                if score > best_score and score >= self.fuzzy_threshold:
                    best_score = score
                    best_match = pattern

            if best_match:
                if current_content:
                    content_text = '\n'.join(current_content)
                    if len(content_text.split()) >= self.min_words // 2:
                        sections[current_section] = content_text

                current_section = best_match
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = '\n'.join(current_content)

        if not sections:
            sections = {"Document": text}

        return sections

    def _split_into_units(self, text: str) -> List[str]:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if paragraphs and len(paragraphs) > 1:
            return paragraphs

        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines and len(lines) > 3:
            return lines

        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        return sentences if sentences else [text]

    def _chunk_section(
        self,
        text: str,
        section_name: str,
        concepts: List[str]
    ) -> List[SemanticChunk]:

        chunks = []
        units = self._split_into_units(text)

        if not units:
            return chunks

        current_units = []
        current_word_count = 0
        char_position = 0

        for unit in units:
            unit_word_count = len(unit.split())

            if current_word_count + unit_word_count > self.max_words and current_units:
                chunk = self._create_chunk(
                    current_units, section_name, concepts, len(chunks), char_position
                )
                chunks.append(chunk)

                char_position += len('\n\n'.join(current_units))
                current_units = [unit]
                current_word_count = unit_word_count
            else:
                current_units.append(unit)
                current_word_count += unit_word_count

        if current_units and current_word_count >= self.min_words // 2:
            chunk = self._create_chunk(
                current_units, section_name, concepts, len(chunks), char_position
            )
            chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        units: List[str],
        section_name: str,
        concepts: List[str],
        chunk_id: int,
        char_start: int
    ) -> SemanticChunk:

        content = '\n\n'.join(units)
        word_count = len(content.split())

        matched_concepts = self._find_matched_concepts(content, concepts)

        main_concept = matched_concepts[0] if matched_concepts else content.split()[:5]
        if isinstance(main_concept, list):
            main_concept = ' '.join(main_concept) + "..."

        return SemanticChunk(
            content=content,
            section=section_name,
            main_concept=main_concept,
            matched_concepts=matched_concepts,
            chunk_id=chunk_id,
            word_count=word_count,
            char_start=char_start
        )

    def _find_matched_concepts(self, content: str, concepts: List[str]) -> List[str]:
        matched = []
        content_lower = content.lower()

        for concept in concepts:
            if concept.lower() in content_lower:
                matched.append(concept)

        return matched

    def chunk_document(self, document_understanding) -> List[Dict]:
        print("Debut du chunking...")

        raw_text = document_understanding.raw_text
        headings = document_understanding.detected_headings
        structure = document_understanding.structure
        concepts = document_understanding.main_concepts

        sections = self._find_sections_flexible(raw_text, headings, structure)
        print(f"Sections trouvees: {len(sections)}")

        all_chunks = []
        chunk_id = 0

        for section_name, section_text in sections.items():
            print(f"Traitement: '{section_name[:50]}...'")

            section_chunks = self._chunk_section(section_text, section_name, concepts)

            for chunk in section_chunks:
                chunk.chunk_id = chunk_id
                chunk_id += 1
                all_chunks.append(chunk)

        result = [self._chunk_to_dict(chunk) for chunk in all_chunks]

        print(f"Chunking termine: {len(result)} chunks crees")
        return result

    def _chunk_to_dict(self, chunk: SemanticChunk) -> Dict:
        return {
            "chunk_id": chunk.chunk_id,
            "section": chunk.section,
            "main_concept": chunk.main_concept,
            "matched_concepts": chunk.matched_concepts,
            "content": chunk.content,
            "word_count": chunk.word_count,
            "char_start": chunk.char_start
        }


if __name__ == "__main__":
    from dataclasses import dataclass

    @dataclass
    class FakeUnderstanding:
        raw_text: str
        detected_headings: List[str]
        structure: Dict[str, List[str]]
        main_concepts: List[str]

    text = """
    COURS DE SOUDAGE

    3.1. Définition
    Le soudage est un procédé d'assemblage permanent.
    Il permet de réunir deux pièces métalliques.

    3.2. Principe du soudage
    Le principe repose sur la fusion localisée.
    On chauffe le métal jusqu'à fusion.
    Un joint solide se forme au refroidissement.
    """

    understanding = FakeUnderstanding(
        raw_text=text,
        detected_headings=["3.1. Définition", "3.2. Principe du soudage"],
        structure={"Définition": [], "Principe": []},
        main_concepts=["soudage", "assemblage", "fusion", "métal"]
    )

    chunker = SemanticChunker(min_words=20, max_words=100)
    chunks = chunker.chunk_document(understanding)

    print(f"{len(chunks)} chunks crees:")
    for chunk in chunks:
        print(f"\nChunk {chunk['chunk_id']}:")
        print(f"Section: {chunk['section']}")
        print(f"Mots: {chunk['word_count']}")
        print(f"Concepts: {', '.join(chunk['matched_concepts'])}")
        print(f"Apercu: {chunk['content'][:80]}...")

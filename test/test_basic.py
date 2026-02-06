import time
import sys
from core.intelligent_processor import IntelligentDocumentProcessor, DocumentUnderstanding

"""
Suite de tests + benchmark pour IntelligentDocumentProcessor
Mesure précise du temps de traitement pour chaque test
"""


# =========================
# Helpers
# =========================

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def timed_test(test_func):
    """Décorateur simple pour mesurer le temps d'un test"""
    start = time.perf_counter()
    result = test_func()
    elapsed = time.perf_counter() - start
    print(f"\n Temps total du test : {elapsed:.4f} s")
    return result, elapsed


# =========================
# Tests
# =========================

def test_simple_math_course():
    print_section("TEST 1 : Mathématiques - Dérivées")

    text = """
    Analyse Mathématique - Les Dérivées
    1. Définition de la dérivée
    2. Formules de dérivation
    3. Applications
    """

    processor = IntelligentDocumentProcessor(model="llama3.2")

    start = time.perf_counter()
    understanding = processor.understand_document(text)
    elapsed = time.perf_counter() - start

    print(f" Titre : {understanding.title}")
    print(f" Concepts : {understanding.main_concepts}")
    print(f" Sections : {list(understanding.structure.keys())}")
    print(f" Temps compréhension : {elapsed:.4f} s")

    assert understanding.title
    assert understanding.main_concepts
    assert understanding.structure

    return understanding, elapsed


def test_physics_course():
    print_section("TEST 2 : Physique - Mécanique")

    text = """
    Mécanique Classique
    Cinématique
    Dynamique
    Énergie
    """

    processor = IntelligentDocumentProcessor(model="llama3.2")

    start = time.perf_counter()
    understanding = processor.understand_document(text)
    elapsed = time.perf_counter() - start

    print(f"Titre : {understanding.title}")
    print(f" Concepts : {understanding.main_concepts[:5]}")
    print(f" Temps compréhension : {elapsed:.4f} s")

    assert len(understanding.main_concepts) >= 2

    return understanding, elapsed


def test_complex_document():
    print_section("TEST 3 : Document Complexe")

    text = """
    Méthodes Numériques pour les Équations Différentielles
    I. Introduction
    II. Méthode d'Euler
    III. Runge-Kutta
    IV. Stabilité
    """

    processor = IntelligentDocumentProcessor(model="llama3.2")

    start = time.perf_counter()
    understanding = processor.understand_document(text)
    elapsed = time.perf_counter() - start

    print(f" Titre : {understanding.title}")
    print(f" Concepts : {len(understanding.main_concepts)}")
    print(f" Sections : {len(understanding.structure)}")
    print(f" Temps compréhension : {elapsed:.4f} s")

    assert len(understanding.structure) >= 2

    return understanding, elapsed


def test_fallback_mode():
    print_section("TEST 4 : Mode Fallback")

    text = """
    Systèmes Linéaires
    Forme matricielle Ax=b
    Élimination de Gauss
    """

    processor = IntelligentDocumentProcessor(model="llama3.2")

    start = time.perf_counter()
    understanding = processor._simple_understanding(text)
    elapsed = time.perf_counter() - start

    print(f" Titre : {understanding.title}")
    print(f" Concepts : {understanding.main_concepts}")
    print(f" Temps fallback : {elapsed:.6f} s")

    assert understanding.title

    return understanding, elapsed


def test_keyword_extraction():
    print_section("TEST 5 : Extraction de mots-clés")

    text = """
    dérivées intégrales matrices vecteurs théorème
    """

    processor = IntelligentDocumentProcessor()

    start = time.perf_counter()
    keywords = processor._extract_keywords(text)
    elapsed = time.perf_counter() - start

    print(f" Mots-clés : {keywords}")
    print(f" Temps extraction : {elapsed:.6f} s")

    assert len(keywords) > 0

    return elapsed


def test_structure_extraction():
    print_section("TEST 6 : Extraction de structure")

    text = """
    Introduction
    1. Partie A
    2. Partie B
    Conclusion
    """

    processor = IntelligentDocumentProcessor()

    start = time.perf_counter()
    structure = processor._extract_structure(text)
    elapsed = time.perf_counter() - start

    print(f"📋 Sections : {list(structure.keys())}")
    print(f"⏱️ Temps extraction : {elapsed:.6f} s")

    assert len(structure) >= 2

    return elapsed




def run_all_tests():
    print("\n SUITE DE TESTS + BENCHMARK IntelligentDocumentProcessor 🧪")

    times = []

    try:
        for test in [
            test_simple_math_course,
            test_physics_course,
            test_complex_document,
            test_fallback_mode,
        ]:
            _, t = timed_test(test)
            times.append(t)

        times.append(test_keyword_extraction())
        times.append(test_structure_extraction())

        print_section("RÉSUMÉ DES PERFORMANCES")

        print(f"• Nombre de tests : {len(times)}")
        print(f"• Temps total     : {sum(times):.4f} s")
        print(f"• Temps moyen     : {sum(times)/len(times):.4f} s")
        print(f"• Temps min       : {min(times):.6f} s")
        print(f"• Temps max       : {max(times):.4f} s")

        print("\n IntelligentDocumentProcessor BENCHMARKÉ AVEC SUCCÈS")

    except AssertionError as e:
        print(f"\n ÉCHEC : {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n ERREUR INATTENDUE : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

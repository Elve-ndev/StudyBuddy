"""
Wrapper script pour lancer le générateur de quiz facilement
Usage: python scripts/generate_quiz.py [arguments]
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.quiz_generator import run_quiz_pipeline, QUESTION_TYPES, DIFFICULTY_LEVELS
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="🎯 Générateur de Quiz Créatif depuis PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  
  # Quiz basique (10 questions, difficulté moyenne, format HTML)
  python scripts/generate_quiz.py
  
  # Quiz difficile avec 15 questions
  python scripts/generate_quiz.py --num 15 --difficulty difficile
  
  # Quiz focalisé sur un sujet spécifique
  python scripts/generate_quiz.py --topic "brasure" --num 8
  
  # Questions spécifiques (QCM et Vrai/Faux uniquement)
  python scripts/generate_quiz.py --types multiple_choice true_false --num 12
  
  # Export en Markdown
  python scripts/generate_quiz.py --format markdown --num 20
  
  # Quiz avancé avec scénarios
  python scripts/generate_quiz.py --types scenario short_answer error_detection --difficulty difficile

Types de questions disponibles:
  - multiple_choice: Questions à choix multiples (4 options)
  - true_false: Vrai/Faux avec justification
  - fill_blank: Compléter les blancs
  - matching: Associer les concepts
  - short_answer: Réponse courte (2-3 phrases)
  - scenario: Étude de cas / Scénario pratique
  - error_detection: Trouver l'erreur dans l'affirmation
  - ranking: Classer par ordre (chronologique, importance, etc.)
        """
    )
    
    parser.add_argument(
        "--pdf",
        type=str,
        default="Data/cours_.pdf",
        help="Chemin du fichier PDF (défaut: Data/cours_.pdf)"
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Sujet spécifique pour filtrer les questions (optionnel)"
    )
    
    parser.add_argument(
        "--num",
        type=int,
        default=10,
        help="Nombre de questions à générer (défaut: 10)"
    )
    
    parser.add_argument(
        "--difficulty",
        type=str,
        default="moyen",
        choices=["facile", "moyen", "difficile"],
        help="Niveau de difficulté (défaut: moyen)"
    )
    
    parser.add_argument(
        "--types",
        type=str,
        nargs="+",
        choices=list(QUESTION_TYPES.keys()),
        default=None,
        help="Types de questions à inclure (défaut: tous types mélangés)"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        default="html",
        choices=["json", "html", "markdown"],
        help="Format de sortie (défaut: html)"
    )
    
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="Afficher tous les types de questions disponibles"
    )
    
    args = parser.parse_args()
    
    # Show question types if requested
    if args.list_types:
        print("\n" + "="*70)
        print("📝 TYPES DE QUESTIONS DISPONIBLES")
        print("="*70)
        for q_type, description in QUESTION_TYPES.items():
            print(f"\n{q_type:20} : {description}")
        print("\n" + "="*70)
        print("\n💡 NIVEAUX DE DIFFICULTÉ")
        print("="*70)
        for level, description in DIFFICULTY_LEVELS.items():
            print(f"\n{level:20} : {description}")
        print("\n" + "="*70 + "\n")
        return
    
    # Validate PDF path
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        logger.error(f"❌ PDF introuvable: {pdf_path}")
        logger.info("💡 Vérifiez le chemin ou utilisez --pdf pour spécifier un autre fichier")
        sys.exit(1)
    
    # Display configuration
    print("\n" + "="*70)
    print("🎯 CONFIGURATION DU QUIZ")
    print("="*70)
    print(f"📄 PDF: {pdf_path}")
    print(f"📚 Sujet: {args.topic or 'Tout le contenu'}")
    print(f"📝 Questions: {args.num}")
    print(f"⚡ Difficulté: {args.difficulty}")
    print(f"🎲 Types: {', '.join(args.types) if args.types else 'Tous (mélangés)'}")
    print(f"💾 Format: {args.format.upper()}")
    print("="*70 + "\n")
    
    # Generate quiz
    try:
        quiz_data, output_file = run_quiz_pipeline(
            pdf_path=pdf_path,
            topic=args.topic,
            num_questions=args.num,
            difficulty=args.difficulty,
            question_types=args.types,
            output_format=args.format
        )
        
        print(f"\n✅ SUCCÈS! Quiz généré et sauvegardé")
        print(f"📂 Fichier: {output_file}")
        
        if args.format == "html":
            print(f"\n🌐 Pour visualiser: Ouvrez {output_file} dans votre navigateur")
        elif args.format == "json":
            print(f"\n📊 Pour utiliser: Importez le JSON dans votre application")
        else:
            print(f"\n📖 Pour lire: Ouvrez {output_file} dans un éditeur de texte")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
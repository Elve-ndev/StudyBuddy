#!/usr/bin/env python3
"""
Quick test script for your PDF: Data/cours.pdf
"""

import sys
from pathlib import Path

def check_pdf():
    """Check if PDF exists"""
    pdf_path = Path("./Data/cours_.pdf")
    
    print("=" * 60)
    print("Vérification du fichier PDF")
    print("=" * 60)
    
    if pdf_path.exists():
        print(f"✓ PDF trouvé: {pdf_path}")
        print(f"  Taille: {pdf_path.stat().st_size / 1024:.2f} KB")
        return True
    else:
        print(f"✗ PDF non trouvé: {pdf_path}")
        print("\nAssurez-vous que le fichier existe dans:")
        print(f"  {pdf_path.absolute()}")
        return False

def test_extraction():
    """Test PDF extraction"""
    print("\n" + "=" * 60)
    print("Test d'extraction du PDF")
    print("=" * 60)
    
    try:
        # Try pdfplumber first
        try:
            import pdfplumber
            pdf_path = Path("./Data/cours_.pdf")
            
            with pdfplumber.open(pdf_path) as pdf:
                num_pages = len(pdf.pages)
                print(f"✓ pdfplumber: {num_pages} pages détectées")
                
                # Extract first page as sample
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    preview = first_page_text[:200].replace('\n', ' ')
                    print(f"\n  Aperçu du contenu:")
                    print(f"  {preview}...")
                    return True
                else:
                    print("⚠ Aucun texte extrait de la première page")
                    return False
                    
        except ImportError:
            print("⚠ pdfplumber non installé, tentative avec PyPDF2...")
            
            import PyPDF2
            pdf_path = Path("./Data/cours_.pdf")
            
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                print(f"✓ PyPDF2: {num_pages} pages détectées")
                
                first_page_text = pdf_reader.pages[0].extract_text()
                if first_page_text:
                    preview = first_page_text[:200].replace('\n', ' ')
                    print(f"\n  Aperçu du contenu:")
                    print(f"  {preview}...")
                    return True
                else:
                    print("⚠ Aucun texte extrait de la première page")
                    return False
                    
    except Exception as e:
        print(f"✗ Erreur lors de l'extraction: {e}")
        return False

def main():
    """Run quick tests"""
    print("\n🔍 Test rapide du PDF Data/cours.pdf\n")
    
    # Check if PDF exists
    if not check_pdf():
        print("\n❌ Le fichier PDF n'existe pas. Vérifiez le chemin.")
        return 1
    
    # Test extraction
    if not test_extraction():
        print("\n⚠️  Le PDF existe mais l'extraction a échoué.")
        print("Installez pdfplumber: pip install pdfplumber")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ Le PDF est prêt à être utilisé!")
    print("=" * 60)
    print("\nCommandes pour tester le pipeline RAG:")
    print("\n1. Question simple:")
    print("   python rag_pipeline.py --query \"Qu'est-ce que la brasure ?\"")
    print("\n2. Mode interactif:")
    print("   python rag_pipeline.py --interactive")
    print("\n3. Avec votre propre PDF:")
    print("   python rag_pipeline.py --pdf ./Data/cours_.pdf --query \"votre question\"")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
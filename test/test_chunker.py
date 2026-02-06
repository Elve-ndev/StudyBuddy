"""
test_semantic_chunker.py - Test complet avec mesures de performance
"""
import time
import sys
from pathlib import Path

# Ajouter le chemin pour pouvoir importer
sys.path.append(str(Path(__file__).parent))

def print_header(title):
    """Affiche un en-tête stylisé"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_result(success, message):
    """Affiche un résultat stylisé"""
    if success:
        print(f" {message}")
    else:
        print(f" {message}")

def mesure_temps(func):
    """Décorateur pour mesurer le temps d'exécution"""
    def wrapper(*args, **kwargs):
        debut = time.time()
        result = func(*args, **kwargs)
        fin = time.time()
        temps_ecoule = fin - debut
        
        # Formater le temps
        if temps_ecoule < 1:
            temps_str = f"{temps_ecoule*1000:.2f} ms"
        elif temps_ecoule < 60:
            temps_str = f"{temps_ecoule:.2f} secondes"
        else:
            minutes = int(temps_ecoule // 60)
            secondes = temps_ecoule % 60
            temps_str = f"{minutes}min {secondes:.1f}s"
        
        return result, temps_ecoule, temps_str
    return wrapper

@mesure_temps
def test_1_texte_court():
    """Test 1 : Texte très court"""
    print_header("TEST 1 - Texte très court (50 mots)")
    
    from semantic_chunker import SemanticChunker, DocumentUnderstanding
    
    texte = """
    La photosynthèse est le processus par lequel les plantes convertissent la lumière en énergie.
    Ce processus produit de l'oxygène.
    Il est essentiel à la vie sur Terre.
    """
    
    comprehension = DocumentUnderstanding(
        title="La Photosynthèse",
        main_concepts=["photosynthèse", "plantes", "lumière", "énergie", "oxygène"],
        structure={
            "Introduction": ["définition", "importance"]
        }
    )
    
    chunker = SemanticChunker(min_words=10, max_words=50)
    chunks = chunker.chunk_document(texte, comprehension)
    
    print(f" Texte de {len(texte.split())} mots")
    print(f" {len(chunks)} chunk(s) créé(s)")
    
    for chunk in chunks:
        print(f"   • Chunk {chunk['chunk_id']}: {chunk['word_count']} mots | Section: {chunk['section']}")
    
    return len(chunks) > 0

@mesure_temps  
def test_2_cours_mathematiques():
    """Test 2 : Cours de mathématiques complet"""
    print_header("TEST 2 - Cours de mathématiques (200 mots)")
    
    from semantic_chunker import SemanticChunker, DocumentUnderstanding
    
    texte = """
    COURS DE MATHÉMATIQUES - NIVEAU LYCÉE

    Chapitre 1 : Les Fonctions
    
    Une fonction est une relation qui associe à chaque élément d'un ensemble de départ un élément d'un ensemble d'arrivée.
    On note généralement f(x) la valeur de la fonction f au point x.
    
    Exemple : La fonction carré f(x) = x² associe à tout nombre son carré.
    Pour x = 3, f(3) = 9.
    Pour x = -2, f(-2) = 4.
    
    Chapitre 2 : Les Dérivées
    
    La dérivée d'une fonction mesure son taux de variation instantané.
    Elle est notée f'(x) ou df/dx.
    
    Définition formelle : f'(x) = lim(h→0) [f(x+h) - f(x)] / h
    
    Propriétés importantes :
    1. Dérivée d'une constante : si f(x) = c, alors f'(x) = 0
    2. Dérivée de x^n : si f(x) = x^n, alors f'(x) = n*x^(n-1)
    3. Dérivée d'une somme : (f+g)'(x) = f'(x) + g'(x)
    
    Applications :
    - Trouver les tangentes
    - Étudier les variations
    - Optimiser des fonctions
    """
    
    comprehension = DocumentUnderstanding(
        title="Cours de Mathématiques - Fonctions et Dérivées",
        main_concepts=["fonctions", "dérivées", "limites", "tangentes", "optimisation", "mathématiques"],
        structure={
            "Chapitre 1 : Les Fonctions": ["définition", "exemple", "carré"],
            "Chapitre 2 : Les Dérivées": ["définition", "propriétés", "applications"]
        }
    )
    
    chunker = SemanticChunker(min_words=50, max_words=150)
    chunks = chunker.chunk_document(texte, comprehension)
    
    mots_totaux = sum(chunk['word_count'] for chunk in chunks)
    
    print(f" Statistiques :")
    print(f"   • Texte original : {len(texte.split())} mots")
    print(f"   • Chunks créés : {len(chunks)}")
    print(f"   • Mots totaux dans chunks : {mots_totaux}")
    print(f"   • Moyenne mots/chunk : {mots_totaux/len(chunks):.1f}" if chunks else "N/A")
    
    print(f"\n Détail des chunks :")
    for chunk in chunks[:5]:  # Afficher seulement les 5 premiers
        concepts = ', '.join(chunk['matched_concepts'][:3])
        if len(chunk['matched_concepts']) > 3:
            concepts += f"... (+{len(chunk['matched_concepts'])-3})"
        
        apercu = chunk['content'][:60].replace('\n', ' ')
        print(f"   • Chunk {chunk['chunk_id']}: {chunk['section'][:20]:20} | {chunk['word_count']:3} mots | Concepts: {concepts}")
        print(f"     Aperçu: {apercu}...")
    
    if len(chunks) > 5:
        print(f"   ... et {len(chunks)-5} autres chunks")
    
    return len(chunks) >= 2

@mesure_temps
def test_3_document_long():
    """Test 3 : Document long avec plusieurs sections"""
    print_header("TEST 3 - Document long scientifique (500+ mots)")
    
    from semantic_chunker import SemanticChunker, DocumentUnderstanding
    
    texte = """
    MÉMOIRE SCIENTIFIQUE SUR L'INTELLIGENCE ARTIFICIELLE
    
    RÉSUMÉ
    Ce mémoire explore les avancées récentes en intelligence artificielle, 
    particulièrement dans le domaine de l'apprentissage profond.
    
    INTRODUCTION
    L'intelligence artificielle (IA) est un domaine en pleine expansion.
    Depuis les années 2010, l'apprentissage profond a révolutionné le domaine.
    
    CHAPITRE 1 : HISTORIQUE DE L'IA
    1.1 Les débuts (1950-1980)
    Les premiers travaux sur l'IA remontent aux années 1950 avec Alan Turing.
    Le test de Turing proposé en 1950 reste une référence.
    
    1.2 L'hiver de l'IA (1980-1990)
    Période de scepticisme et de réductions de financement.
    Les limites des systèmes experts deviennent apparentes.
    
    1.3 Renaissance (2000-présent)
    Retour en grâce grâce aux données massives et à la puissance de calcul.
    Le deep learning permet des avancées spectaculaires.
    
    CHAPITRE 2 : APPRENTISSAGE PROFOND
    2.1 Réseaux de neurones
    Inspirés du cerveau humain, composés de neurones artificiels.
    Chaque neurone effectue une transformation mathématique simple.
    
    2.2 Apprentissage par rétropropagation
    Algorithme clé pour entraîner les réseaux de neurones.
    Ajuste les poids en minimisant une fonction de coût.
    
    2.3 Architectures spécialisées
    - CNN (Convolutional Neural Networks) pour l'image
    - RNN (Recurrent Neural Networks) pour les séquences
    - Transformers pour le traitement du langage
    
    CHAPITRE 3 : APPLICATIONS
    3.1 Vision par ordinateur
    Reconnaissance d'images, détection d'objets, segmentation.
    
    3.2 Traitement du langage naturel
    Traduction automatique, analyse de sentiments, chatbots.
    
    3.3 Robotique
    Navigation autonome, manipulation d'objets.
    
    CONCLUSION
    L'IA continue d'évoluer rapidement.
    Des défis éthiques et techniques persistent.
    
    BIBLIOGRAPHIE
    [1] Goodfellow et al., Deep Learning, 2016
    [2] LeCun et al., Gradient-Based Learning, 1998
    """
    
    comprehension = DocumentUnderstanding(
        title="Mémoire sur l'Intelligence Artificielle",
        main_concepts=[
            "intelligence artificielle", "apprentissage profond", "réseaux de neurones",
            "machine learning", "deep learning", "algorithmes", "données",
            "entraînement", "modèles", "prédiction"
        ],
        structure={
            "INTRODUCTION": ["définition", "importance"],
            "CHAPITRE 1 : HISTORIQUE DE L'IA": ["débuts", "hiver", "renaissance"],
            "CHAPITRE 2 : APPRENTISSAGE PROFOND": ["réseaux", "rétropropagation", "architectures"],
            "CHAPITRE 3 : APPLICATIONS": ["vision", "langage", "robotique"],
            "CONCLUSION": ["perspectives", "défis"]
        }
    )
    
    chunker = SemanticChunker(min_words=80, max_words=250)
    chunks = chunker.chunk_document(texte, comprehension)
    
    # Analyse des résultats
    sections_trouvees = set(chunk['section'] for chunk in chunks)
    concepts_couverts = set()
    for chunk in chunks:
        concepts_couverts.update(chunk['matched_concepts'])
    
    print(f" Analyse approfondie :")
    print(f"   • Chunks totaux : {len(chunks)}")
    print(f"   • Sections détectées : {len(sections_trouvees)}")
    print(f"   • Concepts couverts : {len(concepts_couverts)}/{len(comprehension.main_concepts)}")
    print(f"   • Taux de couverture : {len(concepts_couverts)/len(comprehension.main_concepts)*100:.1f}%")
    
    print(f"\n  Sections identifiées :")
    for section in sorted(sections_trouvees):
        chunks_dans_section = sum(1 for c in chunks if c['section'] == section)
        print(f"   • {section[:30]:30} : {chunks_dans_section} chunk(s)")
    
    return len(chunks) >= 4

@mesure_temps
def test_4_matching_concepts():
    """Test 4 : Précision du matching de concepts"""
    print_header("TEST 4 - Précision du matching de concepts")
    
    from semantic_chunker import SemanticChunker, DocumentUnderstanding
    
    # Texte ciblé avec des concepts spécifiques
    texte = """
    Le machine learning utilise des algorithmes pour apprendre à partir de données.
    Le deep learning est un sous-domaine utilisant des réseaux de neurones profonds.
    Les données sont essentielles pour l'entraînement des modèles.
    La prédiction est l'objectif final de ces systèmes.
    """
    
    comprehension = DocumentUnderstanding(
        title="Test de Matching",
        main_concepts=[
            "machine learning", "deep learning", "algorithmes", 
            "données", "réseaux de neurones", "entraînement", 
            "modèles", "prédiction", "systèmes"
        ],
        structure={"Test": []}
    )
    
    chunker = SemanticChunker(min_words=20, max_words=100)
    chunks = chunker.chunk_document(texte, comprehension)
    
    print(f" Analyse du matching :")
    
    toutes_bonnes = True
    for chunk in chunks:
        print(f"\n Chunk {chunk['chunk_id']} :")
        print(f"   Concepts trouvés : {chunk['matched_concepts']}")
        
        # Vérification manuelle
        contenu = chunk['content'].lower()
        concepts_attendus = []
        
        for concept in comprehension.main_concepts:
            if concept in contenu:
                concepts_attendus.append(concept)
        
        concepts_trouves = set(chunk['matched_concepts'])
        concepts_attendus_set = set(concepts_attendus)
        
        if concepts_trouves == concepts_attendus_set:
            print(f"    Matching parfait !")
        else:
            print(f"     Problème de matching")
            print(f"      Attendu : {concepts_attendus}")
            print(f"      Manquant : {concepts_attendus_set - concepts_trouves}")
            print(f"      Supplémentaires : {concepts_trouves - concepts_attendus_set}")
            toutes_bonnes = False
    
    return toutes_bonnes

@mesure_temps
def test_5_performance():
    """Test 5 : Performance avec différents paramètres"""
    print_header("TEST 5 - Performance avec différents paramètres")
    
    from semantic_chunker import SemanticChunker, DocumentUnderstanding
    
    # Générer un texte long
    texte = "\n".join([f"Paragraphe {i}: " + " ".join(["mot"] * 20) for i in range(50)])
    
    comprehension = DocumentUnderstanding(
        title="Test Performance",
        main_concepts=["mot", "paragraphe", "test"],
        structure={"Performance": []}
    )
    
    resultats = []
    
    # Tester différentes configurations
    configurations = [
        ("Petits chunks", 30, 80),
        ("Chunks moyens", 80, 200),
        ("Gros chunks", 150, 400)
    ]
    
    for nom, min_w, max_w in configurations:
        debut = time.time()
        chunker = SemanticChunker(min_words=min_w, max_words=max_w)
        chunks = chunker.chunk_document(texte, comprehension)
        fin = time.time()
        
        temps = fin - debut
        vitesse = len(texte.split()) / temps if temps > 0 else 0
        
        resultats.append({
            "nom": nom,
            "chunks": len(chunks),
            "temps": temps,
            "vitesse": vitesse,
            "moyenne_mots": sum(c['word_count'] for c in chunks)/len(chunks) if chunks else 0
        })
    
    print(f"⚡ Comparaison des performances :")
    for res in resultats:
        print(f"\n   {res['nom']}:")
        print(f"     • Chunks créés : {res['chunks']}")
        print(f"     • Temps : {res['temps']:.3f}s")
        print(f"     • Vitesse : {res['vitesse']:.0f} mots/s")
        print(f"     • Moyenne mots/chunk : {res['moyenne_mots']:.1f}")
    
    return len(resultats) == 3

def test_6_integration():
    """Test 6 : Test d'intégration complet"""
    print_header("TEST 6 - Intégration complète (simulée)")
    
    print(" Simulation du pipeline complet :")
    print("   1.  Document texte")
    print("   2.  Analyse avec IntelligentProcessor")
    print("   3.  Décopage avec SemanticChunker")
    print("   4. Analyse des résultats")
    
    # Simuler le pipeline
    from semantic_chunker import SemanticChunker, DocumentUnderstanding
    
    # Étape 1 : Texte
    texte = "L'intelligence artificielle transforme notre société."
    
    # Étape 2 : Analyse simulée
    comprehension = DocumentUnderstanding(
        title="Impact de l'IA",
        main_concepts=["intelligence artificielle", "société", "transformation"],
        structure={"Impact": []}
    )
    
    # Étape 3 : Chunking
    chunker = SemanticChunker()
    chunks = chunker.chunk_document(texte, comprehension)
    
    # Étape 4 : Résultats
    print(f"\n Résultats du pipeline :")
    print(f"   • Chunks créés : {len(chunks)}")
    print(f"   • Concept principal : {chunks[0]['main_concept'] if chunks else 'Aucun'}")
    print(f"   • Concepts matchés : {chunks[0]['matched_concepts'] if chunks else []}")
    
    print("\n Pipeline simulé avec succès !")
    return len(chunks) == 1

def main():
    """Fonction principale exécutant tous les tests"""
    print("\n" + "" * 35)
    print("          TEST COMPLET DU SEMANTIC CHUNKER")
    print("          avec mesures de performance précises")
    print("" * 35)
    
    # Liste des tests à exécuter
    tests = [
        ("Test 1 - Texte court", test_1_texte_court),
        ("Test 2 - Cours mathématiques", test_2_cours_mathematiques),
        ("Test 3 - Document long", test_3_document_long),
        ("Test 4 - Matching concepts", test_4_matching_concepts),
        ("Test 5 - Performance", test_5_performance),
        ("Test 6 - Intégration", test_6_integration)
    ]
    
    resultats = []
    temps_total = 0
    
    print(f"\n {len(tests)} tests vont être exécutés...\n")
    
    # Exécuter chaque test
    for nom_test, fonction_test in tests:
        print(f"\n  Exécution : {nom_test}")
        
        try:
            resultat, temps, temps_str = fonction_test()
            temps_total += temps
            
            resultats.append({
                "nom": nom_test,
                "succes": resultat,
                "temps": temps,
                "temps_str": temps_str
            })
            
            if resultat:
                print_result(True, f"{nom_test} : RÉUSSI en {temps_str}")
            else:
                print_result(False, f"{nom_test} : ÉCHEC en {temps_str}")
                
        except Exception as e:
            print_result(False, f"{nom_test} : ERREUR - {str(e)}")
            resultats.append({
                "nom": nom_test,
                "succes": False,
                "temps": 0,
                "temps_str": "ERREUR"
            })
    
    # Afficher le rapport final
    print("\n" + "📊" * 35)
    print("          RAPPORT FINAL DES TESTS")
    print("📊" * 35)
    
    tests_reussis = sum(1 for r in resultats if r["succes"])
    tests_totaux = len(resultats)
    
    print(f"\n Statistiques globales :")
    print(f"   • Tests exécutés : {tests_totaux}")
    print(f"   • Tests réussis : {tests_reussis}")
    print(f"   • Taux de succès : {tests_reussis/tests_totaux*100:.1f}%")
    print(f"   • Temps total d'exécution : {temps_total:.2f}s")
    print(f"   • Temps moyen par test : {temps_total/tests_totaux:.2f}s")
    
    print(f"\n  Détail par test :")
    for res in resultats:
        statut = "" if res["succes"] else "❌"
        print(f"   {statut} {res['nom']:30} : {res['temps_str']}")
    
    print(f"\n Performance du SemanticChunker :")
    
    if tests_reussis == tests_totaux:
        print(" TOUS LES TESTS SONT RÉUSSIS !")
        print(" Le SemanticChunker est parfaitement fonctionnel !")
    elif tests_reussis >= tests_totaux * 0.7:
        print(" La plupart des tests sont réussis.")
        print(" Quelques ajustements mineurs sont nécessaires.")
    else:
        print("  Plusieurs tests ont échoué.")
        print(" Des corrections importantes sont nécessaires.")
    
    # Recommandations
    print(f"\n Recommandations :")
    if tests_reussis == tests_totaux:
        print("   • Le chunker est prêt pour la production")
        print("   • Vous pouvez l'intégrer à votre pipeline RAG")
        print("   • Testez avec des documents réels pour validation finale")
    else:
        print("   • Corrigez les tests qui ont échoué")
        print("   • Vérifiez la logique de découpage par sections")
        print("   • Testez avec plus de variétés de documents")
    
    print("\n" + "" * 35)
    print("          FIN DU TEST - SemanticChunker")
    print("" * 35)

if __name__ == "__main__":
    """
    INSTRUCTIONS POUR EXÉCUTER CE TEST :
    
    1. Sauvegarde ce fichier comme 'test_semantic_chunker.py'
    2. Place-le dans le même dossier que semantic_chunker.py
    3. Ouvre un terminal VS Code (Ctrl + ù)
    4. Tape : python test_semantic_chunker.py
    5. Regarde les résultats !
    
    Le test va :
    - Mesurer le temps pour chaque test
    - Vérifier la précision du chunking
    - Tester différentes tailles de documents
    - Analyser la performance
    - Donner un rapport complet
    """
    
    try:
        # Vérifier que semantic_chunker.py existe
        from pathlib import Path
        if not Path("semantic_chunker.py").exists():
            print(" ERREUR : semantic_chunker.py n'est pas dans ce dossier")
            print(" Place ce fichier de test dans le même dossier que semantic_chunker.py")
            exit(1)
        
        # Exécuter les tests
        main()
        
    except KeyboardInterrupt:
        print("\n\n  Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n ERREUR CRITIQUE : {e}")
        import traceback
        traceback.print_exc()
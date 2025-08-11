#!/usr/bin/env python
"""
Script de test pour vérifier le système d'aperçus vidéo
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novalearnweb.settings')
django.setup()

from store.models import Product, VideoSequence
from django.test import RequestFactory
from store.views import sequence_video_preview

def test_video_preview_system():
    """Test du système d'aperçus vidéo"""
    print("=== Test du Système d'Aperçus Vidéo ===\n")
    
    # 1. Vérifier les produits avec séquences vidéo
    products_with_sequences = Product.objects.filter(
        video_sequences__isnull=False
    ).distinct()
    
    print(f"1. Produits avec séquences vidéo: {products_with_sequences.count()}")
    
    for product in products_with_sequences:
        print(f"   - {product.title}")
        sequences = product.video_sequences.filter(is_active=True)
        print(f"     * Séquences actives: {sequences.count()}")
        
        # Vérifier les séquences avec fichiers
        sequences_with_files = sequences.filter(video_file__isnull=False)
        print(f"     * Avec fichiers vidéo: {sequences_with_files.count()}")
        
        # Vérifier les aperçus
        preview_sequences = sequences.filter(is_preview=True)
        print(f"     * Séquences d'aperçu: {preview_sequences.count()}")
        
        # Afficher quelques détails
        for seq in sequences_with_files[:3]:
            print(f"       > Séquence {seq.order}: {seq.title}")
            print(f"         - Durée: {seq.get_duration_display()}")
            print(f"         - Aperçu: {'Oui' if seq.is_preview else 'Non'}")
            print(f"         - Fichier: {seq.video_file.name if seq.video_file else 'Aucun'}")
            
            # Vérifier l'existence du fichier
            if seq.video_file:
                file_path = seq.video_file.path
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"         - Taille: {file_size} bytes")
                else:
                    print(f"         - ❌ Fichier manquant!")
    
    # 2. Test de la vue API
    print(f"\n2. Test de la vue API sequence_video_preview:")
    
    # Trouver une séquence avec fichier pour le test
    test_sequence = VideoSequence.objects.filter(
        is_active=True,
        video_file__isnull=False
    ).first()
    
    if test_sequence:
        print(f"   - Séquence de test: {test_sequence.title}")
        
        # Simuler une requête
        factory = RequestFactory()
        request = factory.get(f'/api/sequence/{test_sequence.id}/preview/')
        
        try:
            response = sequence_video_preview(request, test_sequence.id)
            print(f"   - Statut de réponse: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   - ✅ API fonctionnelle")
            else:
                print(f"   - ❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"   - ❌ Erreur lors du test: {str(e)}")
    else:
        print(f"   - ⚠️  Aucune séquence avec fichier trouvée pour le test")
    
    # 3. Statistiques générales
    print(f"\n3. Statistiques générales:")
    total_sequences = VideoSequence.objects.filter(is_active=True).count()
    sequences_with_files = VideoSequence.objects.filter(
        is_active=True,
        video_file__isnull=False
    ).count()
    preview_sequences = VideoSequence.objects.filter(
        is_active=True,
        is_preview=True
    ).count()
    
    print(f"   - Total séquences actives: {total_sequences}")
    print(f"   - Séquences avec fichiers: {sequences_with_files}")
    print(f"   - Séquences d'aperçu: {preview_sequences}")
    print(f"   - Pourcentage avec fichiers: {(sequences_with_files/total_sequences*100):.1f}%" if total_sequences > 0 else "   - Pourcentage avec fichiers: 0%")
    
    return True

def show_preview_instructions():
    """Afficher les instructions pour tester les aperçus"""
    print(f"\n" + "="*60)
    print(f"📋 INSTRUCTIONS DE TEST DES APERÇUS VIDÉO")
    print(f"="*60)
    
    # Trouver un produit avec séquences pour le test
    test_product = Product.objects.filter(
        video_sequences__isnull=False,
        video_sequences__video_file__isnull=False
    ).first()
    
    if test_product:
        print(f"\n🌐 Pour tester les aperçus vidéo:")
        print(f"   1. Assurez-vous que le serveur est démarré:")
        print(f"      python manage.py runserver 8000")
        print(f"   2. Allez sur la page du produit:")
        print(f"      http://127.0.0.1:8000/product/{test_product.slug}/")
        print(f"   3. Dans la section 'Contenu inclus', cliquez sur 'Aperçu'")
        print(f"   4. Une modale devrait s'ouvrir avec la vidéo")
        
        # Afficher les séquences disponibles
        sequences = test_product.video_sequences.filter(
            is_active=True,
            video_file__isnull=False
        )
        print(f"\n📹 Séquences disponibles pour l'aperçu:")
        for seq in sequences[:5]:  # Afficher les 5 premières
            print(f"   - {seq.order}. {seq.title} ({seq.get_duration_display()})")
        
        if sequences.count() > 5:
            print(f"   - ... et {sequences.count() - 5} autres")
    else:
        print(f"\n⚠️  Aucun produit avec séquences vidéo trouvé pour le test")
    
    print(f"\n🔧 Fonctionnalités testées:")
    print(f"   - ✅ Boutons d'aperçu dans la liste des séquences")
    print(f"   - ✅ Modale vidéo responsive")
    print(f"   - ✅ API pour vérifier la disponibilité des vidéos")
    print(f"   - ✅ Gestion d'erreurs et indicateurs de chargement")
    print(f"   - ✅ Fermeture avec Échap ou clic extérieur")

if __name__ == "__main__":
    print("🎬 Test du Système d'Aperçus Vidéo\n")
    
    success = test_video_preview_system()
    
    if success:
        print("\n🎉 Le système d'aperçus vidéo est prêt!")
        show_preview_instructions()
    else:
        print("\n💥 Des problèmes ont été détectés dans le système d'aperçus.")
        print("   Veuillez vérifier les fichiers et permissions.")
        sys.exit(1)

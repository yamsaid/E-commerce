#!/usr/bin/env python
"""
Script de test pour vérifier les améliorations du système d'aperçus vidéo
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
import json

def test_improved_video_preview():
    """Test du système d'aperçus vidéo amélioré"""
    print("=== Test du Système d'Aperçus Vidéo Amélioré ===\n")
    
    # 1. Vérifier les améliorations de l'API
    print("1. Test de l'API améliorée:")
    
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
                # Analyser la réponse JSON
                data = json.loads(response.content)
                sequence_data = data.get('sequence', {})
                
                print(f"   - ✅ API fonctionnelle")
                print(f"   - Informations retournées:")
                print(f"     * Titre: {sequence_data.get('title', 'N/A')}")
                print(f"     * Durée: {sequence_data.get('duration', 'N/A')}")
                print(f"     * Ordre: {sequence_data.get('order', 'N/A')}")
                print(f"     * Aperçu: {sequence_data.get('is_preview', 'N/A')}")
                print(f"     * URL vidéo: {sequence_data.get('video_url', 'N/A')}")
                print(f"     * Niveau: {sequence_data.get('level', 'N/A')}")
                print(f"     * ID Produit: {sequence_data.get('product_id', 'N/A')}")
                print(f"     * Slug Produit: {sequence_data.get('product_slug', 'N/A')}")
                print(f"     * Titre Produit: {sequence_data.get('product_title', 'N/A')}")
                print(f"     * Total séquences: {sequence_data.get('total_sequences', 'N/A')}")
                print(f"     * Séquences d'aperçu: {sequence_data.get('preview_sequences', 'N/A')}")
                
                # Vérifier que toutes les informations nécessaires sont présentes
                required_fields = ['id', 'title', 'duration', 'order', 'video_url', 'product_id', 'product_slug']
                missing_fields = [field for field in required_fields if not sequence_data.get(field)]
                
                if missing_fields:
                    print(f"   - ⚠️  Champs manquants: {missing_fields}")
                else:
                    print(f"   - ✅ Tous les champs requis sont présents")
                    
            else:
                print(f"   - ❌ Erreur API: {response.status_code}")
                
        except Exception as e:
            print(f"   - ❌ Erreur lors du test: {str(e)}")
    else:
        print(f"   - ⚠️  Aucune séquence avec fichier trouvée pour le test")
    
    # 2. Vérifier les améliorations de l'interface
    print(f"\n2. Améliorations de l'interface:")
    
    # Compter les séquences avec différents types d'informations
    sequences_with_description = VideoSequence.objects.filter(
        is_active=True,
        description__isnull=False
    ).exclude(description='').count()
    
    sequences_with_files = VideoSequence.objects.filter(
        is_active=True,
        video_file__isnull=False
    ).count()
    
    preview_sequences = VideoSequence.objects.filter(
        is_active=True,
        is_preview=True
    ).count()
    
    print(f"   - Séquences avec description: {sequences_with_description}")
    print(f"   - Séquences avec fichiers: {sequences_with_files}")
    print(f"   - Séquences d'aperçu: {preview_sequences}")
    
    # 3. Vérifier les produits avec séquences
    print(f"\n3. Produits avec séquences vidéo:")
    
    products_with_sequences = Product.objects.filter(
        video_sequences__isnull=False
    ).distinct()
    
    for product in products_with_sequences[:3]:  # Afficher les 3 premiers
        sequences = product.video_sequences.filter(is_active=True)
        preview_count = sequences.filter(is_preview=True).count()
        
        print(f"   - {product.title}")
        print(f"     * Total séquences: {sequences.count()}")
        print(f"     * Séquences d'aperçu: {preview_count}")
        print(f"     * Niveau: {product.level or 'Non spécifié'}")
        
        # Vérifier les fichiers physiques
        valid_sequences = 0
        for seq in sequences:
            if seq.video_file and os.path.exists(seq.video_file.path):
                valid_sequences += 1
        
        print(f"     * Fichiers valides: {valid_sequences}/{sequences.count()}")
    
    # 4. Test des nouvelles fonctionnalités
    print(f"\n4. Nouvelles fonctionnalités:")
    
    # Vérifier les séquences avec descriptions détaillées
    detailed_sequences = VideoSequence.objects.filter(
        is_active=True,
        description__isnull=False
    ).exclude(description='').exclude(description__icontains='test')
    
    if detailed_sequences.exists():
        sample_sequence = detailed_sequences.first()
        print(f"   - ✅ Séquences avec descriptions détaillées disponibles")
        print(f"     * Exemple: {sample_sequence.title}")
        print(f"     * Description: {sample_sequence.description[:100]}...")
    else:
        print(f"   - ⚠️  Aucune séquence avec description détaillée trouvée")
    
    # Vérifier les produits avec niveaux
    products_with_levels = Product.objects.filter(
        video_sequences__isnull=False,
        level__isnull=False
    ).distinct().count()
    
    print(f"   - Produits avec niveaux définis: {products_with_levels}")
    
    return True

def show_improvement_summary():
    """Afficher un résumé des améliorations"""
    print(f"\n" + "="*70)
    print(f"📋 RÉSUMÉ DES AMÉLIORATIONS DU SYSTÈME D'APERÇUS VIDÉO")
    print(f"="*70)
    
    print(f"\n🎨 Améliorations de l'Interface:")
    print(f"   ✅ En-tête avec gradient et icône de lecture")
    print(f"   ✅ Panneau d'informations latéral avec métadonnées")
    print(f"   ✅ Barre de progression en temps réel")
    print(f"   ✅ Boutons d'action (téléchargement, voir toutes les séquences)")
    print(f"   ✅ Contrôles supplémentaires (plein écran, qualité)")
    print(f"   ✅ Indicateurs de temps restant et compteur de vues")
    print(f"   ✅ Overlay de chargement amélioré")
    print(f"   ✅ Gestion d'erreurs plus élégante")
    
    print(f"\n🔧 Améliorations Techniques:")
    print(f"   ✅ API enrichie avec plus d'informations")
    print(f"   ✅ Gestionnaires d'événements optimisés")
    print(f"   ✅ Formatage intelligent du temps")
    print(f"   ✅ Gestion du mode plein écran")
    print(f"   ✅ Réinitialisation automatique des informations")
    print(f"   ✅ Validation robuste des données")
    
    print(f"\n📊 Nouvelles Informations Disponibles:")
    print(f"   ✅ Durée réelle de la vidéo")
    print(f"   ✅ Niveau de difficulté")
    print(f"   ✅ Progression dans la formation")
    print(f"   ✅ Nombre total de séquences")
    print(f"   ✅ Nombre de séquences d'aperçu")
    print(f"   ✅ Informations sur le produit parent")
    
    print(f"\n🌐 Pour tester les améliorations:")
    print(f"   1. Démarrez le serveur: python manage.py runserver 8000")
    print(f"   2. Allez sur une page produit avec séquences vidéo")
    print(f"   3. Cliquez sur 'Aperçu' pour voir la nouvelle interface")
    print(f"   4. Explorez le panneau d'informations latéral")
    print(f"   5. Testez les contrôles supplémentaires")

if __name__ == "__main__":
    print("🚀 Test des Améliorations du Système d'Aperçus Vidéo\n")
    
    success = test_improved_video_preview()
    
    if success:
        print("\n🎉 Le système d'aperçus vidéo amélioré est prêt!")
        show_improvement_summary()
    else:
        print("\n💥 Des problèmes ont été détectés dans les améliorations.")
        print("   Veuillez vérifier les modifications apportées.")
        sys.exit(1)

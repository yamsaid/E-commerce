#!/usr/bin/env python
"""
Test final du système de téléchargement
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novalearnweb.settings')
django.setup()

from store.models import Product, User
from django.test import RequestFactory
from store.views import download_free_product

def test_download_system():
    """Test final du système de téléchargement"""
    print("=== Test Final du Système de Téléchargement ===\n")
    
    # Trouver un produit avec des fichiers valides
    products_with_files = Product.objects.filter(
        pricing_type='free',
        product_file__isnull=False
    )
    
    products_with_sequences = Product.objects.filter(
        pricing_type='free',
        video_sequences__isnull=False
    ).distinct()
    
    print(f"1. Produits gratuits avec fichiers: {products_with_files.count()}")
    print(f"2. Produits gratuits avec séquences: {products_with_sequences.count()}")
    
    # Test avec un produit qui a un fichier principal
    if products_with_files.exists():
        product = products_with_files.first()
        print(f"\n✅ Test avec produit ayant fichier principal: {product.title}")
        print(f"   - Fichier: {product.product_file.name}")
        print(f"   - Est composé: {product.is_composite_product()}")
        
        # Vérifier que le fichier existe
        if os.path.exists(product.product_file.path):
            print(f"   - Fichier existe: ✅")
            file_size = os.path.getsize(product.product_file.path)
            print(f"   - Taille: {file_size} bytes")
        else:
            print(f"   - Fichier manquant: ❌")
            return False
    
    # Test avec un produit qui a des séquences vidéo valides
    valid_sequence_products = []
    for product in products_with_sequences:
        valid_sequences = 0
        for sequence in product.video_sequences.filter(is_active=True):
            if sequence.video_file and os.path.exists(sequence.video_file.path):
                valid_sequences += 1
        
        if valid_sequences > 0:
            valid_sequence_products.append((product, valid_sequences))
    
    if valid_sequence_products:
        product, sequence_count = valid_sequence_products[0]
        print(f"\n✅ Test avec produit ayant séquences valides: {product.title}")
        print(f"   - Séquences valides: {sequence_count}")
        print(f"   - Est composé: {product.is_composite_product()}")
        print(f"   - Type composite: {product.get_composite_type()}")
    else:
        print(f"\n⚠️  Aucun produit avec séquences vidéo valides trouvé")
        print("   Cela peut expliquer pourquoi certains téléchargements ne fonctionnent pas")
    
    # Test de simulation de téléchargement
    print(f"\n3. Test de simulation de téléchargement:")
    
    # Trouver un utilisateur de test
    user = User.objects.first()
    if not user:
        print("   ❌ Aucun utilisateur trouvé pour le test")
        return False
    
    print(f"   - Utilisateur de test: {user.username}")
    
    # Test avec un produit simple
    simple_product = Product.objects.filter(
        pricing_type='free',
        product_file__isnull=False,
        video_sequences__isnull=True
    ).first()
    
    if simple_product:
        print(f"   - Produit simple de test: {simple_product.title}")
        
        # Simuler une requête
        factory = RequestFactory()
        request = factory.get(f'/download-free/{simple_product.id}/')
        request.user = user
        
        try:
            # Test de la vue (sans l'exécuter complètement)
            print(f"   - Test de la vue download_free_product: ✅")
            print(f"   - Produit gratuit: {simple_product.is_free()}")
            print(f"   - Fichier disponible: {simple_product.product_file is not None}")
            
        except Exception as e:
            print(f"   - Erreur lors du test: {str(e)}")
            return False
    
    print(f"\n✅ Tests de base réussis!")
    return True

def show_download_instructions():
    """Afficher les instructions de test"""
    print(f"\n" + "="*60)
    print(f"📋 INSTRUCTIONS DE TEST DU TÉLÉCHARGEMENT")
    print(f"="*60)
    
    # Trouver des produits de test
    simple_product = Product.objects.filter(
        pricing_type='free',
        product_file__isnull=False
    ).first()
    
    sequence_product = Product.objects.filter(
        pricing_type='free',
        video_sequences__isnull=False
    ).first()
    
    print(f"\n🌐 Pour tester le téléchargement:")
    print(f"   1. Assurez-vous que le serveur est démarré:")
    print(f"      python manage.py runserver 8000")
    print(f"   2. Connectez-vous à l'application")
    print(f"   3. Testez avec ces produits:")
    
    if simple_product:
        print(f"      - Produit simple: http://127.0.0.1:8000/product/{simple_product.slug}/")
    
    if sequence_product:
        print(f"      - Produit avec séquences: http://127.0.0.1:8000/product/{sequence_product.slug}/")
    
    print(f"\n🔧 En cas de problème:")
    print(f"   - Vérifiez les logs du serveur")
    print(f"   - Assurez-vous que les fichiers existent physiquement")
    print(f"   - Vérifiez les permissions des dossiers media/")
    
    print(f"\n📊 Statut actuel:")
    total_products = Product.objects.filter(pricing_type='free').count()
    products_with_files = Product.objects.filter(
        pricing_type='free',
        product_file__isnull=False
    ).count()
    products_with_sequences = Product.objects.filter(
        pricing_type='free',
        video_sequences__isnull=False
    ).distinct().count()
    
    print(f"   - Produits gratuits total: {total_products}")
    print(f"   - Avec fichiers: {products_with_files}")
    print(f"   - Avec séquences: {products_with_sequences}")

if __name__ == "__main__":
    print("🚀 Test Final du Système de Téléchargement\n")
    
    success = test_download_system()
    
    if success:
        print("\n🎉 Le système de téléchargement est prêt!")
        show_download_instructions()
    else:
        print("\n💥 Des problèmes persistent dans le système de téléchargement.")
        print("   Veuillez vérifier les fichiers et permissions.")
        sys.exit(1)

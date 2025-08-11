#!/usr/bin/env python
"""
Test script pour vérifier le processus d'inscription
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novalearnweb.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

def test_register_process():
    """Test du processus d'inscription"""
    client = Client(HTTP_HOST='127.0.0.1')
    
    print("=== Test du processus d'inscription ===\n")
    
    # 1. Test d'accès à la page d'inscription
    print("1. Test d'accès à la page d'inscription...")
    response = client.get('/register/')
    print(f"   Status code: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Page d'inscription accessible")
    else:
        print("   ❌ Page d'inscription non accessible")
        return False
    
    # 2. Test d'inscription avec des données valides
    print("\n2. Test d'inscription avec des données valides...")
    
    # Générer un nom d'utilisateur unique
    import time
    timestamp = int(time.time())
    test_username = f"testuser{timestamp}"
    test_email = f"test{timestamp}@example.com"
    
    register_data = {
        'username': test_username,
        'email': test_email,
        'password': 'TestPass123',
        'confirm_password': 'TestPass123',
        'terms': 'on'
    }
    
    response = client.post('/register/', register_data)
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 302:  # Redirection
        print(f"   ✅ Inscription réussie - Redirection vers: {response.url}")
        
        # Vérifier que l'utilisateur a été créé
        try:
            user = User.objects.get(username=test_username)
            print(f"   ✅ Utilisateur créé: {user.username} ({user.email})")
            print(f"   ✅ Utilisateur actif: {user.is_active}")
            print(f"   ✅ Utilisateur staff: {user.is_staff}")
        except User.DoesNotExist:
            print("   ❌ Utilisateur non trouvé en base de données")
            return False
        
        # Vérifier que la redirection va vers la page de connexion
        if 'login' in response.url:
            print("   ✅ Redirection correcte vers la page de connexion")
        else:
            print(f"   ⚠️  Redirection vers: {response.url} (attendu: page de connexion)")
            
    else:
        print("   ❌ Échec de l'inscription")
        print(f"   Contenu de la réponse: {response.content[:500]}...")
        return False
    
    # 3. Test d'inscription avec des données invalides
    print("\n3. Test d'inscription avec des données invalides...")
    
    # Test avec un nom d'utilisateur trop court
    invalid_data = {
        'username': 'ab',  # Trop court
        'email': 'invalid@example.com',
        'password': 'weak',
        'confirm_password': 'weak',
        'terms': 'on'
    }
    
    response = client.post('/register/', invalid_data)
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:  # Pas de redirection = erreur
        print("   ✅ Validation des erreurs fonctionne")
    else:
        print("   ❌ Validation des erreurs ne fonctionne pas")
    
    # 4. Test d'inscription avec un nom d'utilisateur existant
    print("\n4. Test d'inscription avec un nom d'utilisateur existant...")
    
    duplicate_data = {
        'username': test_username,  # Utilisateur déjà créé
        'email': 'another@example.com',
        'password': 'TestPass123',
        'confirm_password': 'TestPass123',
        'terms': 'on'
    }
    
    response = client.post('/register/', duplicate_data)
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:  # Pas de redirection = erreur
        print("   ✅ Détection du nom d'utilisateur en double")
    else:
        print("   ❌ Échec de la détection du nom d'utilisateur en double")
    
    # 5. Test de connexion après inscription
    print("\n5. Test de connexion après inscription...")
    
    login_data = {
        'username': test_username,
        'password': 'TestPass123'
    }
    
    response = client.post('/login/', login_data)
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 302:
        print("   ✅ Connexion réussie après inscription")
    else:
        print("   ❌ Échec de la connexion après inscription")
    
    # 6. Nettoyage - Supprimer l'utilisateur de test
    print("\n6. Nettoyage...")
    try:
        user = User.objects.get(username=test_username)
        user.delete()
        print("   ✅ Utilisateur de test supprimé")
    except User.DoesNotExist:
        print("   ⚠️  Utilisateur de test non trouvé pour suppression")
    
    return True

def show_register_instructions():
    """Afficher les instructions pour l'inscription"""
    print(f"\n" + "="*70)
    print(f"📋 INSTRUCTIONS D'UTILISATION DE L'INSCRIPTION")
    print(f"="*70)
    
    print(f"\n🔐 Processus d'inscription:")
    print(f"   1. L'utilisateur accède à /register/")
    print(f"   2. Il remplit le formulaire avec ses informations")
    print(f"   3. Validation côté client et serveur")
    print(f"   4. Création du compte en base de données")
    print(f"   5. Redirection vers la page de connexion")
    print(f"   6. Message de succès affiché")
    
    print(f"\n✅ Validations effectuées:")
    print(f"   - Nom d'utilisateur unique (min 3 caractères)")
    print(f"   - Email valide et unique")
    print(f"   - Mot de passe sécurisé (8+ caractères, majuscule, chiffre)")
    print(f"   - Confirmation du mot de passe")
    print(f"   - Acceptation des conditions d'utilisation")
    
    print(f"\n🎯 Fonctionnalités:")
    print(f"   - Validation en temps réel côté client")
    print(f"   - Messages d'erreur explicites")
    print(f"   - Indicateurs de force du mot de passe")
    print(f"   - Redirection automatique vers la connexion")
    print(f"   - Pas de connexion automatique après inscription")
    
    print(f"\n🌐 URLs:")
    print(f"   - Inscription: /register/")
    print(f"   - Connexion: /login/")
    print(f"   - Redirection après inscription: /login/")

if __name__ == '__main__':
    print("🚀 Test du processus d'inscription\n")
    
    success = test_register_process()
    
    if success:
        print("\n🎉 Le processus d'inscription fonctionne correctement!")
        show_register_instructions()
    else:
        print("\n💥 Des problèmes ont été détectés dans le processus d'inscription.")
        print("   Veuillez vérifier les vues et templates.")
        sys.exit(1)

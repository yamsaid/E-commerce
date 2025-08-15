#!/usr/bin/env python3
"""
Script pour lancer le serveur Django en mode développement
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire du projet au path Python
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration pour le développement
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novalearnweb.development')
os.environ.setdefault('DEBUG', 'True')

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    
    # Arguments pour lancer le serveur de développement
    args = ['manage.py', 'runserver', '127.0.0.1:8000']
    
    print("🚀 Démarrage du serveur Django en mode développement...")
    print("📍 URL: http://127.0.0.1:8000")
    print("🔧 Mode: DEBUG=True, HTTPS désactivé")
    print("=" * 50)
    
    execute_from_command_line(args)

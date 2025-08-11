#!/usr/bin/env python
"""
Test script to verify admin dashboard URL configuration
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
from django.urls import reverse
from django.contrib.auth.models import User

def test_admin_dashboard():
    """Test if admin dashboard is accessible"""
    client = Client(HTTP_HOST='127.0.0.1')
    
    # Test without authentication (should redirect to login)
    print("Testing admin dashboard without authentication...")
    response = client.get('/admin/dashboard/')
    print(f"Status code: {response.status_code}")
    print(f"Redirect URL: {response.url if hasattr(response, 'url') else 'None'}")
    
    # Create a test user with staff permissions
    try:
        user = User.objects.get(username='testadmin')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testadmin',
            email='testadmin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        print(f"Created test admin user: {user.username}")
    
    # Login and test
    print("\nTesting admin dashboard with authentication...")
    client.login(username='testadmin', password='testpass123')
    response = client.get('/admin/dashboard/')
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Admin dashboard is accessible!")
    else:
        print("❌ Admin dashboard is not accessible")
        print(f"Response content: {response.content[:500]}...")
    
    # Test other admin URLs
    print("\nTesting other admin URLs...")
    admin_urls = [
        '/admin/orders/',
        '/admin/analytics/',
    ]
    
    for url in admin_urls:
        response = client.get(url)
        print(f"{url}: {response.status_code}")

if __name__ == '__main__':
    test_admin_dashboard()


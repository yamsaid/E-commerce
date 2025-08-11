from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Test view
    path('test/', views.test_view, name='test'),
    
    # Pages principales
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/review/', views.add_review, name='add_review'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Collections de livres
    path('collections/', views.book_collections, name='book_collections'),
    path('collection/<slug:slug>/', views.book_collection_detail, name='book_collection_detail'),
    
    # Développement personnel
    path('developpement-personnel/', views.personal_development, name='personal_development'),
    path('developpement-personnel/<slug:slug>/', views.personal_development_section, name='personal_development_section'),
    
    # Contact et avis
    path('contact/', views.contact, name='contact'),
    
    # Panier et commandes
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    
    # Paiements
    path('payment/<str:order_number>/', views.payment, name='payment'),
    path('payment-success/<str:order_number>/', views.payment_success, name='payment_success'),
    path('payment-cancel/<str:order_number>/', views.payment_cancel, name='payment_cancel'),
    path('payment-status/<str:transaction_id>/', views.payment_status, name='payment_status'),
    
    # API Mobile Money
    path('api/check-payment-status/<str:transaction_id>/', views.check_payment_status_api, name='check_payment_status_api'),
    path('api/retry-mobile-money/<str:transaction_id>/', views.retry_mobile_money_payment, name='retry_mobile_money_payment'),
    
    # Téléchargements
    path('download/<str:token>/', views.download_file, name='download_file'),
    path('download-free/<int:product_id>/', views.download_free_product, name='download_free_product'),
    path('download-compressed/<int:product_id>/', views.download_compressed_product, name='download_compressed_product'),
    
    # Espace client
    path('account/', views.account, name='account'),
    path('account/orders/', views.my_orders, name='my_orders'),
    path('account/downloads/', views.my_downloads, name='my_downloads'),
    
    # Authentification
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # OAuth
    path('auth/google/', views.oauth_google, name='oauth_google'),
    path('auth/facebook/', views.oauth_facebook, name='oauth_facebook'),
    path('auth/callback/', views.oauth_callback, name='oauth_callback'),
    
        # API pour AJAX
    path('api/update-cart/', views.update_cart, name='update_cart'),
    path('api/product-search/', views.product_search, name='product_search'),
    
    # Vidéos et séquences
    path('product/<int:product_id>/preview/', views.video_preview, name='video_preview'),
    path('product/<int:product_id>/sequences/', views.product_video_sequences, name='product_video_sequences'),
    path('api/sequence/<int:sequence_id>/preview/', views.sequence_video_preview, name='sequence_video_preview'),
    
    # Dashboard administrateur
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/orders/<str:order_number>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
] 
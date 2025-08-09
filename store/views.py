from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
import json
from django.contrib.auth.models import User
from datetime import timedelta
import uuid
import zipfile
import io
import os
from .models import Category, Product, Order, OrderItem, Payment, Download, Review, VideoSequence, BookCollection, PersonalDevelopmentSection, Contact
from decimal import Decimal


def test_view(request):
    """Test view to check template loading"""
    return render(request, 'store/test.html')


def home(request):
    """Page d'accueil"""
    try:
        featured_products = Product.objects.filter(
            is_active=True, 
            is_featured=True
        ).select_related('category')[:6]
        
        new_products = Product.objects.filter(
            is_active=True, 
            is_new=True
        ).select_related('category')[:4]
        
        popular_products = Product.objects.filter(
            is_active=True, 
            is_popular=True
        ).select_related('category')[:4]
        
        categories = Category.objects.filter(is_active=True)[:6]
        
        context = {
            'featured_products': featured_products,
            'new_products': new_products,
            'popular_products': popular_products,
            'categories': categories,
        }
        
        return render(request, 'store/home.html', context)
    except Exception as e:
        # Fallback context if there are database issues
        context = {
            'featured_products': [],
            'new_products': [],
            'popular_products': [],
            'categories': [],
        }
        return render(request, 'store/home.html', context)


def product_list(request):
    """Liste des produits"""
    products = Product.objects.filter(is_active=True).select_related('category')
    
    # Filtres
    category = request.GET.get('category')
    if category:
        products = products.filter(category__slug=category)
    
    product_type = request.GET.get('type')
    if product_type:
        products = products.filter(product_type=product_type)
    
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    # Tri
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        products = products.order_by('price_fcfa')
    elif sort == 'price_high':
        products = products.order_by('-price_fcfa')
    elif sort == 'popular':
        products = products.order_by('-sales_count')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category,
        'current_type': product_type,
        'current_search': search,
        'current_sort': sort,
    }
    
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    """Détail d'un produit"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Incrémenter le compteur de vues
    product.views_count += 1
    product.save(update_fields=['views_count'])
    
    # Produits similaires
    similar_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Avis approuvés
    reviews = Review.objects.filter(
        product=product,
        is_approved=True
    ).select_related('user')[:10]
    
    context = {
        'product': product,
        'similar_products': similar_products,
        'reviews': reviews,
    }
    
    return render(request, 'store/product_detail.html', context)


def category_detail(request, slug):
    """Détail d'une catégorie"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(
        category=category,
        is_active=True
    ).select_related('category')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    
    return render(request, 'store/category_detail.html', context)


def cart(request):
    """Panier"""
    cart_data = request.session.get('cart', {})
    cart_items = []
    total_fcfa = 0
    total_eur = 0
    
    for product_id, quantity in cart_data.items():
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Supprimer les produits gratuits du panier
            if product.is_free():
                del cart_data[product_id]
                messages.warning(request, f'{product.title} a été retiré du panier car il est gratuit.')
                continue
            
            item_total_fcfa = product.price_fcfa * quantity
            item_total_eur = product.price_eur * quantity
            
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_fcfa': item_total_fcfa,
                'total_eur': item_total_eur,
            })
            
            total_fcfa += item_total_fcfa
            total_eur += item_total_eur
            
        except Product.DoesNotExist:
            # Supprimer le produit invalide du panier
            del cart_data[product_id]
    
    request.session['cart'] = cart_data
    request.session.modified = True
    
    # Calculer la TVA (18%) et le total avec TVA
    tax_fcfa = total_fcfa * Decimal('0.18')
    tax_eur = total_eur * Decimal('0.18')
    total_with_tax_fcfa = total_fcfa + tax_fcfa
    total_with_tax_eur = total_eur + tax_eur
    
    context = {
        'cart_items': cart_items,
        'total_fcfa': total_fcfa,
        'total_eur': total_eur,
        'tax_fcfa': tax_fcfa,
        'tax_eur': tax_eur,
        'total_with_tax_fcfa': total_with_tax_fcfa,
        'total_with_tax_eur': total_with_tax_eur,
    }
    
    return render(request, 'store/cart.html', context)


def add_to_cart(request, product_id):
    """Ajouter au panier"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Empêcher l'ajout de produits gratuits au panier
        if product.is_free():
            messages.warning(request, f'{product.title} est gratuit. Vous pouvez le télécharger directement.')
            return redirect('store:product_detail', slug=product.slug)
        
        quantity = int(request.POST.get('quantity', 1))
        
        cart_data = request.session.get('cart', {})
        cart_data[str(product_id)] = cart_data.get(str(product_id), 0) + quantity
        request.session['cart'] = cart_data
        request.session.modified = True
        
        messages.success(request, f'{product.title} ajouté au panier.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('store:cart')
    
    return redirect('store:product_detail', slug=product.slug)


def remove_from_cart(request, product_id):
    """Retirer du panier"""
    cart_data = request.session.get('cart', {})
    if str(product_id) in cart_data:
        del cart_data[str(product_id)]
        request.session['cart'] = cart_data
        request.session.modified = True
        messages.success(request, 'Produit retiré du panier.')
    
    return redirect('store:cart')


@login_required
def checkout(request):
    """Finaliser la commande"""
    cart_data = request.session.get('cart', {})
    
    if not cart_data:
        messages.warning(request, 'Votre panier est vide.')
        return redirect('store:product_list')
    
    cart_items = []
    total_fcfa = 0
    total_eur = 0
    
    for product_id, quantity in cart_data.items():
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Supprimer les produits gratuits du panier
            if product.is_free():
                del cart_data[product_id]
                messages.warning(request, f'{product.title} a été retiré du panier car il est gratuit.')
                continue
            
            item_total_fcfa = product.price_fcfa * quantity
            item_total_eur = product.price_eur * quantity
            
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_fcfa': item_total_fcfa,
                'total_eur': item_total_eur,
            })
            
            total_fcfa += item_total_fcfa
            total_eur += item_total_eur
            
        except Product.DoesNotExist:
            del cart_data[product_id]
    
    # Calculer la TVA (18%) et le total avec TVA
    tax_fcfa = total_fcfa * Decimal('0.18')
    tax_eur = total_eur * Decimal('0.18')
    total_with_tax_fcfa = total_fcfa + tax_fcfa
    total_with_tax_eur = total_eur + tax_eur
    
    if request.method == 'POST':
        # Créer la commande
        order = Order.objects.create(
            user=request.user,
            customer_name=request.POST.get('customer_name'),
            customer_email=request.POST.get('customer_email'),
            customer_phone=request.POST.get('customer_phone'),
            subtotal_fcfa=total_fcfa,
            subtotal_eur=total_eur,
            total_fcfa=total_with_tax_fcfa,
            total_eur=total_with_tax_eur,
        )
        
        # Ajouter les produits à la commande
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price_fcfa=item['product'].price_fcfa,
                price_eur=item['product'].price_eur,
            )
        
        # Vider le panier
        request.session['cart'] = {}
        request.session.modified = True
        
        return redirect('store:payment', order_number=order.order_number)
    
    context = {
        'cart_items': cart_items,
        'total_fcfa': total_fcfa,
        'total_eur': total_eur,
        'tax_fcfa': tax_fcfa,
        'tax_eur': tax_eur,
        'total_with_tax_fcfa': total_with_tax_fcfa,
        'total_with_tax_eur': total_with_tax_eur,
    }
    
    return render(request, 'store/checkout.html', context)


@login_required
def payment(request, order_number):
    """Page de paiement"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.status != 'pending':
        messages.warning(request, 'Cette commande ne peut plus être payée.')
        return redirect('store:order_detail', order_number=order_number)
    
    # Calculer la TVA
    tax_fcfa = order.subtotal_fcfa * Decimal('0.18')
    tax_eur = order.subtotal_eur * Decimal('0.18')
    
    context = {
        'order': order,
        'tax_fcfa': tax_fcfa,
        'tax_eur': tax_eur,
    }
    
    return render(request, 'store/payment.html', context)


@login_required
def payment_success(request, order_number):
    """Succès du paiement"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Mettre à jour le statut de la commande
    order.status = 'paid'
    order.paid_at = timezone.now()
    order.save()
    
    # Créer les liens de téléchargement
    for item in order.items.all():
        download = Download.objects.create(
            user=request.user,
            product=item.product,
            order=order,
            download_url=f'/media/{item.product.product_file.name}',
            expires_at=timezone.now() + timezone.timedelta(days=30),
        )
    
    messages.success(request, 'Paiement effectué avec succès ! Vous pouvez maintenant télécharger vos produits.')
    
    return redirect('store:order_detail', order_number=order_number)


@login_required
def payment_cancel(request, order_number):
    """Annulation du paiement"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    messages.warning(request, 'Paiement annulé. Vous pouvez réessayer plus tard.')
    
    return redirect('store:order_detail', order_number=order_number)


@login_required
def order_detail(request, order_number):
    """Détail d'une commande"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Calculer la TVA
    tax_fcfa = order.subtotal_fcfa * Decimal('0.18')
    tax_eur = order.subtotal_eur * Decimal('0.18')
    
    context = {
        'order': order,
        'tax_fcfa': tax_fcfa,
        'tax_eur': tax_eur,
    }
    
    return render(request, 'store/order_detail.html', context)


@login_required
def download_file(request, token):
    """Téléchargement de fichier"""
    try:
        download = Download.objects.get(
            download_token=token,
            user=request.user,
            is_active=True
        )
        
        # Vérifier si le téléchargement n'a pas expiré
        if download.expires_at < timezone.now():
            messages.error(request, "Le lien de téléchargement a expiré.")
            return redirect('store:my_downloads')
        
        # Vérifier si le nombre max de téléchargements n'est pas dépassé
        if download.downloads_count >= download.max_downloads:
            messages.error(request, "Vous avez atteint le nombre maximum de téléchargements.")
            return redirect('store:my_downloads')
        
        # Incrémenter le compteur de téléchargements du produit
        download.product.increment_downloads()
        
        # Vérifier si le produit a des séquences vidéo (formation avec plusieurs fichiers)
        if download.product.product_type in ['formation', 'video'] and download.product.video_sequences.exists():
            return download_compressed_product(request, download.product, download)
        else:
            # Incrémenter le compteur de téléchargements de l'instance Download
            download.downloads_count += 1
            download.last_download_at = timezone.now()
            download.save()
            
            # Retourner le fichier simple
            response = HttpResponse(download.product.product_file, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{download.product.product_file.name.split("/")[-1]}"'
            return response
        
    except Download.DoesNotExist:
        messages.error(request, "Lien de téléchargement invalide.")
        return redirect('store:my_downloads')


@login_required
def account(request):
    """Espace client"""
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    user_downloads = Download.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'user_orders': user_orders,
        'user_downloads': user_downloads,
    }
    
    return render(request, 'store/account.html', context)


@login_required
def my_orders(request):
    """Mes commandes"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'store/my_orders.html', context)


@login_required
def my_downloads(request):
    """Mes téléchargements"""
    downloads = Download.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'downloads': downloads,
    }
    
    return render(request, 'store/my_downloads.html', context)


def login_view(request):
    """Connexion"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Connexion réussie.')
            return redirect('store:home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'store/login.html')


def register_view(request):
    """Inscription"""
    if request.method == 'POST':
        # Logique d'inscription simplifiée
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Cette adresse email existe déjà.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, 'Compte créé avec succès.')
            return redirect('store:home')
    
    return render(request, 'store/register.html')


def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté.')
    return redirect('store:home')


def update_cart(request):
    """Mettre à jour le panier via AJAX"""
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        cart_data = request.session.get('cart', {})
        
        if quantity > 0:
            cart_data[str(product_id)] = quantity
        else:
            cart_data.pop(str(product_id), None)
        
        request.session['cart'] = cart_data
        request.session.modified = True
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


def product_search(request):
    """Recherche de produits via AJAX"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    products = Product.objects.filter(
        is_active=True,
        title__icontains=query
    ).select_related('category')[:10]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'title': product.title,
            'price_fcfa': float(product.price_fcfa),
            'price_eur': float(product.price_eur),
            'image_url': product.cover_image.url if product.cover_image else '',
            'url': product.get_absolute_url(),
        })
    
    return JsonResponse({'products': results})


def video_preview(request, product_id):
    """Aperçu vidéo d'une formation"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Trouver la première séquence d'aperçu ou la première séquence
    preview_sequence = product.video_sequences.filter(
        is_preview=True, 
        is_active=True
    ).first()
    
    if not preview_sequence:
        preview_sequence = product.video_sequences.filter(is_active=True).first()
    
    context = {
        'product': product,
        'preview_sequence': preview_sequence,
    }
    
    return render(request, 'store/video_preview.html', context)


def product_video_sequences(request, product_id):
    """Afficher les séquences vidéo d'une formation"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Vérifier si l'utilisateur a acheté ce produit
    if not request.user.is_authenticated:
        messages.error(request, 'Vous devez être connecté pour accéder à cette page.')
        return redirect('store:login')
    
    has_purchased = False
    for order in request.user.orders.all():
        if order.status == 'paid':
            for item in order.items.all():
                if item.product == product:
                    has_purchased = True
                    break
        if has_purchased:
            break
    
    if not has_purchased:
        messages.error(request, 'Vous devez avoir acheté cette formation pour y accéder.')
        return redirect('store:product_detail', slug=product.slug)
    
    sequences = product.video_sequences.filter(is_active=True).order_by('order')
    
    context = {
        'product': product,
        'sequences': sequences,
    }
    
    return render(request, 'store/product_video_sequences.html', context)


def book_collections(request):
    """Liste des collections de livres"""
    collections = BookCollection.objects.filter(is_active=True).prefetch_related('books')
    
    context = {
        'collections': collections,
    }
    return render(request, 'store/book_collections.html', context)


def book_collection_detail(request, slug):
    """Détail d'une collection de livres"""
    collection = get_object_or_404(BookCollection, slug=slug, is_active=True)
    books = collection.books.filter(is_active=True)
    
    context = {
        'collection': collection,
        'books': books,
    }
    return render(request, 'store/book_collection_detail.html', context)


def personal_development(request):
    """Page développement personnel"""
    sections = PersonalDevelopmentSection.objects.filter(is_active=True).prefetch_related('books')
    
    # Livres populaires en développement personnel
    popular_books = Product.objects.filter(
        product_type__in=['livre', 'ebook'],
        personal_development_section__isnull=False,
        is_active=True
    ).order_by('-sales_count')[:6]
    
    context = {
        'sections': sections,
        'popular_books': popular_books,
    }
    return render(request, 'store/personal_development.html', context)


def personal_development_section(request, slug):
    """Détail d'une section développement personnel"""
    section = get_object_or_404(PersonalDevelopmentSection, slug=slug, is_active=True)
    books = section.books.filter(is_active=True)
    
    context = {
        'section': section,
        'books': books,
    }
    return render(request, 'store/personal_development_section.html', context)


def contact(request):
    """Page de contact"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        contact_type = request.POST.get('contact_type', 'general')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and subject and message:
            Contact.objects.create(
                name=name,
                email=email,
                phone=phone,
                contact_type=contact_type,
                subject=subject,
                message=message
            )
            messages.success(request, "Votre message a été envoyé avec succès. Nous vous répondrons dans les plus brefs délais.")
            return redirect('store:contact')
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
    
    context = {
        'contact_types': Contact.CONTACT_TYPES,
    }
    return render(request, 'store/contact.html', context)

def reviews(request):
    """Page des avis et commentaires"""
    # Récupérer les avis approuvés
    approved_reviews = Review.objects.filter(
        is_approved=True
    ).select_related('user', 'product').order_by('-created_at')[:20]
    
    # Récupérer les produits populaires pour afficher leurs avis
    popular_products = Product.objects.filter(
        is_active=True,
        rating_count__gt=0
    ).order_by('-rating')[:6]
    
    context = {
        'reviews': approved_reviews,
        'popular_products': popular_products,
    }
    return render(request, 'store/reviews.html', context)


@login_required
def download_free_product(request, product_id):
    """Téléchargement direct d'un produit gratuit"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Vérifier que le produit est gratuit
        if not product.is_free():
            messages.error(request, "Ce produit n'est pas gratuit.")
            return redirect('store:product_detail', slug=product.slug)
        
        # Incrémenter le compteur de téléchargements du produit
        product.increment_downloads()
        
        # Créer un enregistrement de téléchargement pour le suivi
        download = Download.objects.create(
            user=request.user,
            product=product,
            order=None,  # Pas d'ordre pour les produits gratuits
            download_url=product.product_file.url,
            download_token=uuid.uuid4().hex,
            max_downloads=10,  # Plus de téléchargements pour les produits gratuits
            expires_at=timezone.now() + timedelta(days=365),  # Expire dans 1 an
            is_active=True
        )
        
        # Vérifier si le produit a des séquences vidéo (formation avec plusieurs fichiers)
        if product.product_type in ['formation', 'video'] and product.video_sequences.exists():
            return download_compressed_product(request, product, download)
        else:
            # Retourner le fichier simple
            response = HttpResponse(product.product_file, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{product.product_file.name.split("/")[-1]}"'
            return response
        
    except Exception as e:
        messages.error(request, "Erreur lors du téléchargement.")
        return redirect('store:product_detail', slug=product.slug)


@login_required
def download_compressed_product(request, product_id=None, product=None, download=None):
    """Téléchargement compressé d'un produit avec plusieurs fichiers"""
    try:
        # Si product_id est fourni, récupérer le produit
        if product_id and not product:
            product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Vérifier que l'utilisateur a le droit de télécharger ce produit
        if not product:
            messages.error(request, "Produit non trouvé.")
            return redirect('store:home')
        
        # Vérifier les droits d'accès
        has_access = False
        
        # Produit gratuit
        if product.is_free():
            has_access = True
        else:
            # Vérifier si l'utilisateur a acheté ce produit
            user_orders = Order.objects.filter(
                user=request.user,
                status='paid',
                items__product=product
            )
            has_access = user_orders.exists()
        
        if not has_access:
            messages.error(request, "Vous n'avez pas accès à ce produit.")
            return redirect('store:product_detail', slug=product.slug)
        
        # Créer un buffer en mémoire pour le fichier ZIP
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Ajouter le fichier principal du produit
            if product.product_file:
                main_filename = os.path.basename(product.product_file.name)
                zip_file.writestr(f"{product.title}/{main_filename}", product.product_file.read())
            
            # Ajouter les séquences vidéo si elles existent
            video_sequences = product.video_sequences.filter(is_active=True).order_by('order')
            if video_sequences.exists():
                for sequence in video_sequences:
                    if sequence.video_file:
                        # Créer un nom de fichier sécurisé
                        safe_title = "".join(c for c in sequence.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        sequence_filename = f"{sequence.order:02d}_{safe_title}{os.path.splitext(sequence.video_file.name)[1]}"
                        zip_file.writestr(f"{product.title}/sequences/{sequence_filename}", sequence.video_file.read())
            
            # Ajouter un fichier README avec les informations du produit
            readme_content = f"""FORMATION: {product.title}

Description: {product.description}

Informations:
- Type: {product.get_product_type_display()}
- Niveau: {product.level}
- Langue: {product.language}
- Durée: {product.duration}

Séquences vidéo incluses:
"""
            for sequence in video_sequences:
                readme_content += f"- {sequence.order:02d}. {sequence.title} ({sequence.get_duration_display()})\n"
            
            zip_file.writestr(f"{product.title}/README.txt", readme_content)
        
        # Préparer la réponse
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{product.title.replace(" ", "_")}.zip"'
        
        # Incrémenter le compteur de téléchargements si un objet download est fourni
        if download:
            download.downloads_count += 1
            download.last_download_at = timezone.now()
            download.save()
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la création de l'archive: {str(e)}")
        return redirect('store:product_detail', slug=product.slug)

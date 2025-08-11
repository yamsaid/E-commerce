from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q, Avg
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
from .forms import ReviewForm
from decimal import Decimal
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate, TruncMonth
from datetime import datetime, timedelta
from django.utils import timezone


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
        
        # Récupérer les avis approuvés pour la page d'accueil
        approved_reviews = Review.objects.filter(
            is_approved=True
        ).select_related('user', 'product').order_by('-created_at')[:6]
        
        # Récupérer les produits populaires avec avis
        products_with_reviews = Product.objects.filter(
            is_active=True,
            rating_count__gt=0
        ).order_by('-rating')[:4]
        
        context = {
            'featured_products': featured_products,
            'new_products': new_products,
            'popular_products': popular_products,
            'categories': categories,
            'reviews': approved_reviews,
            'products_with_reviews': products_with_reviews,
        }
        
        return render(request, 'store/home.html', context)
    except Exception as e:
        # Fallback context if there are database issues
        context = {
            'featured_products': [],
            'new_products': [],
            'popular_products': [],
            'categories': [],
            'reviews': [],
            'products_with_reviews': [],
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


@login_required
def add_review(request, slug):
    """Créer ou mettre à jour un avis utilisateur pour un produit"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if request.method != 'POST':
        return redirect('store:product_detail', slug=slug)

    form = ReviewForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        # Un avis par user/prod (hors commande spécifique)
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            order=None,
            defaults={
                'rating': data['rating'],
                'title': data['title'],
                'comment': data['comment'],
                'is_approved': True,  # basculer à False si modération requise
            },
        )

        # Recalcule la note moyenne et le nombre d'avis
        approved_qs = product.reviews.filter(is_approved=True)
        product.rating_count = approved_qs.count()
        product.rating = approved_qs.aggregate(avg=Avg('rating'))['avg'] or 0
        product.save(update_fields=['rating', 'rating_count'])

        messages.success(request, 'Merci pour votre avis !')
    else:
        messages.error(request, "Formulaire invalide. Veuillez corriger les champs.")
    return redirect('store:product_detail', slug=slug)


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
    
    # Traitement des paiements Mobile Money
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_type = data.get('payment_type')
            
            if payment_type == 'mobile_money':
                from .services import MobileMoneyService
                
                operator = data.get('operator')
                phone_number = data.get('phone_number')
                
                if not operator or not phone_number:
                    return JsonResponse({
                        'success': False,
                        'error': 'Opérateur et numéro de téléphone requis'
                    })
                
                # Valider le numéro de téléphone
                if not phone_number.startswith('+225') and not phone_number.startswith('225'):
                    phone_number = '+225' + phone_number.lstrip('0')
                
                # Initier le paiement Mobile Money
                mobile_money_service = MobileMoneyService()
                result = mobile_money_service.initiate_payment(
                    order=order,
                    operator=operator,
                    phone_number=phone_number,
                    amount_fcfa=order.total_fcfa
                )
                
                if result['success']:
                    return JsonResponse({
                        'success': True,
                        'transaction_id': result['transaction_id'],
                        'message': result['message'],
                        'redirect_url': f'/payment-status/{result["transaction_id"]}/'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': result['error']
                    })
            
            elif payment_type == 'stripe':
                # Logique Stripe existante (à implémenter)
                return JsonResponse({
                    'success': False,
                    'error': 'Paiement Stripe en cours de développement'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Type de paiement non supporté'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données invalides'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
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
def payment_status(request, transaction_id):
    """Page de statut du paiement Mobile Money"""
    try:
        from .models import MobileMoneyTransaction
        from .services import MobileMoneyService
        
        transaction = MobileMoneyTransaction.objects.get(
            transaction_id=transaction_id,
            order__user=request.user
        )
        
        # Vérifier le statut actuel
        mobile_money_service = MobileMoneyService()
        status_result = mobile_money_service.check_payment_status(transaction_id)
        
        context = {
            'transaction': transaction,
            'status_result': status_result,
            'order': transaction.order
        }
        
        return render(request, 'store/payment_status.html', context)
        
    except MobileMoneyTransaction.DoesNotExist:
        messages.error(request, 'Transaction non trouvée.')
        return redirect('store:my_orders')


@login_required
def check_payment_status_api(request, transaction_id):
    """API pour vérifier le statut d'un paiement"""
    try:
        from .models import MobileMoneyTransaction
        from .services import MobileMoneyService
        
        transaction = MobileMoneyTransaction.objects.get(
            transaction_id=transaction_id,
            order__user=request.user
        )
        
        mobile_money_service = MobileMoneyService()
        status_result = mobile_money_service.check_payment_status(transaction_id)
        
        return JsonResponse(status_result)
        
    except MobileMoneyTransaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transaction non trouvée'
        })


@login_required
def retry_mobile_money_payment(request, transaction_id):
    """Réessayer un paiement Mobile Money échoué"""
    try:
        from .models import MobileMoneyTransaction
        from .services import MobileMoneyService
        
        transaction = MobileMoneyTransaction.objects.get(
            transaction_id=transaction_id,
            order__user=request.user
        )
        
        if not transaction.can_retry():
            return JsonResponse({
                'success': False,
                'error': 'Cette transaction ne peut pas être relancée'
            })
        
        # Créer une nouvelle transaction
        mobile_money_service = MobileMoneyService()
        result = mobile_money_service.initiate_payment(
            order=transaction.order,
            operator=transaction.operator,
            phone_number=transaction.phone_number,
            amount_fcfa=transaction.amount_fcfa
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'transaction_id': result['transaction_id'],
                'message': result['message'],
                'redirect_url': f'/payment-status/{result["transaction_id"]}/'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except MobileMoneyTransaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transaction non trouvée'
        })


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
        
        # Vérifier si le produit est composé de plusieurs éléments
        if download.product.is_composite_product():
            return download_compressed_product(request, download.product, download)
        else:
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
        identifier = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        # Permettre la connexion via email ou nom d'utilisateur
        user = None
        if identifier:
            if '@' in identifier:
                try:
                    user_obj = User.objects.get(email__iexact=identifier)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            else:
                user = authenticate(request, username=identifier, password=password)
        
        if user is not None:
            login(request, user)
            # Gérer la persistance de session si "Se souvenir de moi" est coché
            if remember_me:
                # 14 jours
                request.session.set_expiry(1209600)
            else:
                # Session navigateur
                request.session.set_expiry(0)
            messages.success(request, 'Connexion réussie.')
            return redirect('store:home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'store/login.html')


def register_view(request):
    """Inscription"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        terms = request.POST.get('terms')

        # Validations côté serveur
        if not username or len(username) < 3:
            messages.error(request, "Le nom d'utilisateur doit contenir au moins 3 caractères.")
        elif not email:
            messages.error(request, "L'adresse email est obligatoire.")
        elif password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        elif len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
            messages.error(request, "Le mot de passe doit faire au moins 8 caractères, contenir une majuscule et un chiffre.")
        elif not terms:
            messages.error(request, "Vous devez accepter les conditions d'utilisation.")
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Cette adresse email existe déjà.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Compte créé avec succès. Vous pouvez maintenant vous connecter.')
            return redirect('store:login')
    
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


def sequence_video_preview(request, sequence_id):
    """API pour servir l'aperçu vidéo d'une séquence spécifique"""
    try:
        sequence = get_object_or_404(VideoSequence, id=sequence_id, is_active=True)
        
        # Vérifier que la séquence a un fichier vidéo
        if not sequence.video_file:
            return JsonResponse({
                'error': 'Aucun fichier vidéo disponible pour cette séquence'
            }, status=404)
        
        # Vérifier que le fichier existe physiquement
        if not os.path.exists(sequence.video_file.path):
            return JsonResponse({
                'error': 'Fichier vidéo introuvable'
            }, status=404)
        
        # Récupérer les informations du produit associé
        product = sequence.product
        total_sequences = product.video_sequences.filter(is_active=True).count()
        
        # Retourner les informations de la séquence
        return JsonResponse({
            'success': True,
            'sequence': {
                'id': sequence.id,
                'title': sequence.title,
                'description': sequence.description or '',
                'duration': sequence.get_duration_display(),
                'order': sequence.order,
                'is_preview': sequence.is_preview,
                'video_url': sequence.video_file.url,
                'level': getattr(product, 'level', None),
                'product_id': product.id,
                'product_slug': product.slug,
                'product_title': product.title,
                'total_sequences': total_sequences,
                'preview_sequences': product.video_sequences.filter(is_active=True, is_preview=True).count(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur lors de la récupération de la séquence: {str(e)}'
        }, status=500)


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

@login_required
def download_free_product(request, product_id):
    """Téléchargement direct d'un produit gratuit"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Vérifier que le produit est gratuit
        if not product.is_free():
            messages.error(request, "Ce produit n'est pas gratuit.")
            return redirect('store:product_detail', slug=product.slug)
        
        # Vérifier que le fichier existe
        if not product.product_file:
            messages.error(request, "Le fichier de ce produit n'est pas disponible.")
            return redirect('store:product_detail', slug=product.slug)
        
        # Incrémenter le compteur de téléchargements du produit
        product.increment_downloads()
        
        # Créer un enregistrement de téléchargement pour le suivi
        download = Download.objects.create(
            user=request.user,
            product=product,
            order=None,  # Pas d'ordre pour les produits gratuits
            download_url=product.product_file.url if product.product_file else "",
            download_token=uuid.uuid4().hex,
            max_downloads=10,  # Plus de téléchargements pour les produits gratuits
            expires_at=timezone.now() + timedelta(days=365),  # Expire dans 1 an
            is_active=True
        )
        
        # Vérifier si le produit est composé de plusieurs éléments
        if product.is_composite_product():
            return download_compressed_product(request, product=product, download=download)
        else:
            # Retourner le fichier simple
            try:
                # Ouvrir le fichier en mode binaire
                with open(product.product_file.path, 'rb') as file:
                    file_content = file.read()
                
                # Créer la réponse HTTP
                response = HttpResponse(file_content, content_type='application/octet-stream')
                filename = os.path.basename(product.product_file.name)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Content-Length'] = len(file_content)
                return response
                
            except (IOError, OSError) as e:
                messages.error(request, "Erreur lors de l'accès au fichier.")
                return redirect('store:product_detail', slug=product.slug)
        
    except Product.DoesNotExist:
        messages.error(request, "Produit non trouvé.")
        return redirect('store:home')
    except Exception as e:
        messages.error(request, f"Erreur lors du téléchargement: {str(e)}")
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
        
        # Vérifier qu'il y a du contenu à télécharger
        has_content = False
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Ajouter le fichier principal du produit
            if product.product_file:
                try:
                    main_filename = os.path.basename(product.product_file.name)
                    zip_file.writestr(f"{product.title}/{main_filename}", product.product_file.read())
                    has_content = True
                except Exception as e:
                    print(f"Erreur lors de l'ajout du fichier principal: {e}")
            
            # Ajouter les séquences vidéo si elles existent
            video_sequences = product.video_sequences.filter(is_active=True).order_by('order')
            if video_sequences.exists():
                valid_sequences = 0
                for sequence in video_sequences:
                    if sequence.video_file:
                        try:
                            # Vérifier que le fichier existe physiquement
                            if os.path.exists(sequence.video_file.path):
                                # Créer un nom de fichier sécurisé
                                safe_title = "".join(c for c in sequence.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                                sequence_filename = f"{sequence.order:02d}_{safe_title}{os.path.splitext(sequence.video_file.name)[1]}"
                                zip_file.writestr(f"{product.title}/sequences/{sequence_filename}", sequence.video_file.read())
                                valid_sequences += 1
                            else:
                                print(f"Fichier manquant pour la séquence: {sequence.title}")
                        except Exception as e:
                            print(f"Erreur lors de l'ajout de la séquence {sequence.title}: {e}")
                
                if valid_sequences > 0:
                    has_content = True
                    # Créer le dossier sequences seulement s'il y a des fichiers valides
                    zip_file.writestr(f"{product.title}/sequences/", "")
                else:
                    # Aucune séquence valide trouvée
                    messages.warning(request, f"Attention: Aucune séquence vidéo valide trouvée pour {product.title}")
            
            # Ajouter les livres de la collection si c'est une collection
            if product.collection:
                collection = product.collection
                collection_books = collection.books.filter(is_active=True)
                if collection_books.exists():
                    valid_books = 0
                    for book in collection_books:
                        if book.product_file:
                            try:
                                if os.path.exists(book.product_file.path):
                                    book_filename = os.path.basename(book.product_file.name)
                                    zip_file.writestr(f"{product.title}/collection_{collection.slug}/{book_filename}", book.product_file.read())
                                    valid_books += 1
                            except Exception as e:
                                print(f"Erreur lors de l'ajout du livre {book.title}: {e}")
                    
                    if valid_books > 0:
                        has_content = True
                        zip_file.writestr(f"{product.title}/collection_{collection.slug}/", "")
            
            # Ajouter les livres de la section développement personnel si applicable
            if product.personal_development_section:
                section = product.personal_development_section
                section_books = section.books.filter(is_active=True)
                if section_books.exists():
                    valid_books = 0
                    for book in section_books:
                        if book.product_file:
                            try:
                                if os.path.exists(book.product_file.path):
                                    book_filename = os.path.basename(book.product_file.name)
                                    zip_file.writestr(f"{product.title}/section_{section.slug}/{book_filename}", book.product_file.read())
                                    valid_books += 1
                            except Exception as e:
                                print(f"Erreur lors de l'ajout du livre {book.title}: {e}")
                    
                    if valid_books > 0:
                        has_content = True
                        zip_file.writestr(f"{product.title}/section_{section.slug}/", "")
            
            # Vérifier s'il y a du contenu à télécharger
            if not has_content:
                messages.error(request, f"Aucun contenu téléchargeable trouvé pour {product.title}. Veuillez contacter l'administrateur.")
                return redirect('store:product_detail', slug=product.slug)
            
            # Ajouter un fichier README avec les informations du produit
            readme_content = f"""PRODUIT: {product.title}

Description: {product.description}

Informations:
- Type: {product.get_product_type_display()}
- Niveau: {product.level or 'Non spécifié'}
- Langue: {product.language}
- Durée: {product.duration or 'Non spécifiée'}
- Catégorie: {product.category.name}

"""
            
            # Ajouter les informations sur les séquences vidéo
            if video_sequences.exists():
                valid_sequences = [seq for seq in video_sequences if seq.video_file and os.path.exists(seq.video_file.path)]
                readme_content += f"\nSÉQUENCES VIDÉO INCLUSES ({len(valid_sequences)} séquences):\n"
                for sequence in valid_sequences:
                    readme_content += f"- {sequence.order:02d}. {sequence.title} ({sequence.get_duration_display()})\n"
                    if sequence.description:
                        readme_content += f"  Description: {sequence.description}\n"
            
            # Ajouter les informations sur la collection
            if product.collection:
                collection = product.collection
                collection_books = collection.books.filter(is_active=True)
                valid_books = [book for book in collection_books if book.product_file and os.path.exists(book.product_file.path)]
                readme_content += f"\nCOLLECTION: {collection.title}\n"
                readme_content += f"Description: {collection.description}\n"
                readme_content += f"Livres inclus ({len(valid_books)} livres):\n"
                for book in valid_books:
                    readme_content += f"- {book.title}\n"
                    if book.short_description:
                        readme_content += f"  Description: {book.short_description}\n"
            
            # Ajouter les informations sur la section développement personnel
            if product.personal_development_section:
                section = product.personal_development_section
                section_books = section.books.filter(is_active=True)
                valid_books = [book for book in section_books if book.product_file and os.path.exists(book.product_file.path)]
                readme_content += f"\nSECTION DÉVELOPPEMENT PERSONNEL: {section.name}\n"
                readme_content += f"Description: {section.description}\n"
                readme_content += f"Livres inclus ({len(valid_books)} livres):\n"
                for book in valid_books:
                    readme_content += f"- {book.title}\n"
                    if book.short_description:
                        readme_content += f"  Description: {book.short_description}\n"
            
            # Ajouter les informations légales
            readme_content += f"""

INFORMATIONS LÉGALES:
- Ce produit est fourni par NovaLearn
- Utilisation personnelle uniquement
- Tous droits réservés
- Date de téléchargement: {timezone.now().strftime('%d/%m/%Y à %H:%M')}

Pour toute question, contactez-nous via notre site web.
"""
            
            # Ajouter le README à l'archive
            zip_file.writestr(f"{product.title}/README.txt", readme_content)
        
        # Préparer la réponse
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{product.title.replace(" ", "_")}.zip"'
        
        # Incrémenter le compteur de téléchargements
        if download:
            download.downloads_count += 1
            download.last_download_at = timezone.now()
            download.save()
        
        product.increment_downloads()
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la création de l'archive: {str(e)}")
        return redirect('store:product_detail', slug=product.slug)

def oauth_google(request):
    """Redirection vers l'authentification Google OAuth"""
    try:
        from social_django.utils import load_strategy, load_backend
        from social_core.exceptions import AuthException
        
        strategy = load_strategy(request)
        backend = load_backend(strategy=strategy, name='google-oauth2', redirect_uri=None)
        
        # Rediriger vers l'authentification Google
        return backend.start()
    except Exception as e:
        messages.error(request, f'Erreur lors de la connexion avec Google: {str(e)}')
        return redirect('store:login')

def oauth_facebook(request):
    """Redirection vers l'authentification Facebook OAuth"""
    try:
        from social_django.utils import load_strategy, load_backend
        from social_core.exceptions import AuthException
        
        strategy = load_strategy(request)
        backend = load_backend(strategy=strategy, name='facebook', redirect_uri=None)
        
        # Rediriger vers l'authentification Facebook
        return backend.start()
    except Exception as e:
        messages.error(request, f'Erreur lors de la connexion avec Facebook: {str(e)}')
        return redirect('store:login')

def oauth_callback(request):
    """Gestion du callback OAuth"""
    try:
        from social_django.utils import load_strategy, load_backend
        from social_core.exceptions import AuthException
        
        strategy = load_strategy(request)
        backend = load_backend(strategy=strategy, name=request.GET.get('backend'), redirect_uri=None)
        
        # Traiter la réponse OAuth
        user = backend.complete(user=request.user)
        
        if user and user.is_active:
            login(request, user)
            messages.success(request, f'Connexion réussie avec {backend.name.title()}.')
            return redirect('store:home')
        else:
            messages.error(request, 'Échec de l\'authentification OAuth.')
            return redirect('store:login')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'authentification OAuth: {str(e)}')
        return redirect('store:login')


@staff_member_required
def admin_dashboard(request):
    """Dashboard administrateur pour suivre l'état des achats"""
    
    # Période de référence (30 derniers jours par défaut)
    days = request.GET.get('days', 30)
    try:
        days = int(days)
    except ValueError:
        days = 30
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Statistiques générales
    total_orders = Order.objects.filter(created_at__gte=start_date).count()
    total_revenue = Order.objects.filter(
        status='paid',
        created_at__gte=start_date
    ).aggregate(total=Sum('total_eur'))['total'] or 0
    
    # Statistiques par statut
    orders_by_status = Order.objects.filter(
        created_at__gte=start_date
    ).values('status').annotate(
        count=Count('id'),
        total_amount=Sum('total_eur')
    ).order_by('status')
    
    # Produits les plus vendus
    top_products = OrderItem.objects.filter(
        order__status='paid',
        order__created_at__gte=start_date
    ).values(
        'product__title'
    ).annotate(
        total_sales=Count('id'),
        total_revenue=Sum('price_eur')
    ).order_by('-total_sales')[:10]
    
    # Évolution des ventes (par jour)
    daily_sales = Order.objects.filter(
        status='paid',
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        orders=Count('id'),
        revenue=Sum('total_eur')
    ).order_by('date')
    
    # Taux de conversion
    total_cart_abandoned = Order.objects.filter(
        status='pending',
        created_at__gte=start_date
    ).count()
    
    conversion_rate = 0
    if total_orders > 0:
        conversion_rate = ((total_orders - total_cart_abandoned) / total_orders) * 100
    
    # Statistiques des téléchargements
    total_downloads = Download.objects.filter(
        created_at__gte=start_date
    ).count()
    
    downloads_by_product = Download.objects.filter(
        created_at__gte=start_date
    ).values(
        'product__title'
    ).annotate(
        downloads=Count('id')
    ).order_by('-downloads')[:10]
    
    # Produits gratuits populaires
    free_downloads = Download.objects.filter(
        product__pricing_type='free',
        created_at__gte=start_date
    ).values(
        'product__title'
    ).annotate(
        downloads=Count('id')
    ).order_by('-downloads')[:5]
    
    # Utilisateurs actifs
    active_users = User.objects.filter(
        orders__created_at__gte=start_date
    ).distinct().count()
    
    # Nouveaux utilisateurs
    new_users = User.objects.filter(
        date_joined__gte=start_date
    ).count()
    
    context = {
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        
        # Statistiques générales
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'conversion_rate': round(conversion_rate, 2),
        'total_downloads': total_downloads,
        'active_users': active_users,
        'new_users': new_users,
        
        # Données détaillées
        'orders_by_status': orders_by_status,
        'top_products': top_products,
        'daily_sales': list(daily_sales),
        'downloads_by_product': downloads_by_product,
        'free_downloads': free_downloads,
        
        # Calculs pour les graphiques
        'chart_labels': [item['date'].strftime('%d/%m') for item in daily_sales],
        'chart_orders': [item['orders'] for item in daily_sales],
        'chart_revenue': [float(item['revenue'] or 0) for item in daily_sales],
    }
    
    return render(request, 'store/admin/dashboard.html', context)


@staff_member_required
def admin_orders(request):
    """Vue détaillée des commandes pour l'administrateur"""
    
    # Filtres
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    orders = Order.objects.all().order_by('-created_at')
    
    # Appliquer les filtres
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            orders = orders.filter(created_at__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            orders = orders.filter(created_at__lte=date_to)
        except ValueError:
            pass
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(items__product__title__icontains=search)
        ).distinct()
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'store/admin/orders.html', context)


@staff_member_required
def admin_order_detail(request, order_number):
    """Détail d'une commande pour l'administrateur"""
    
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        # Mise à jour du statut
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Envoyer un email de notification si le statut change
            if old_status != new_status:
                messages.success(request, f'Statut de la commande mis à jour vers {new_status}')
    
    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'store/admin/order_detail.html', context)


@staff_member_required
def admin_analytics(request):
    """Analytics détaillés pour l'administrateur"""
    
    # Période
    period = request.GET.get('period', 'month')
    if period == 'week':
        start_date = timezone.now() - timedelta(days=7)
    elif period == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif period == 'quarter':
        start_date = timezone.now() - timedelta(days=90)
    else:
        start_date = timezone.now() - timedelta(days=365)
    
    # Revenus par mois
    monthly_revenue = Order.objects.filter(
        status='paid',
        created_at__gte=start_date
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_eur'),
        orders=Count('id')
    ).order_by('month')
    
    # Top catégories
    top_categories = OrderItem.objects.filter(
        order__status='paid',
        order__created_at__gte=start_date
    ).values(
        'product__category__name'
    ).annotate(
        sales=Count('id'),
        revenue=Sum('price_eur')
    ).order_by('-revenue')[:10]
    
    # Performance des produits
    product_performance = Product.objects.filter(
        orderitem__order__status='paid',
        orderitem__order__created_at__gte=start_date
    ).annotate(
        total_sales=Count('orderitem'),
        total_revenue=Sum('orderitem__price_eur'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-total_revenue')[:20]
    
    # Taux de conversion par produit
    conversion_by_product = []
    for product in Product.objects.filter(is_active=True)[:20]:
        views = product.views_count or 0
        sales = OrderItem.objects.filter(
            product=product,
            order__status='paid',
            order__created_at__gte=start_date
        ).count()
        
        conversion = 0
        if views > 0:
            conversion = (sales / views) * 100
        
        conversion_by_product.append({
            'product': product,
            'views': views,
            'sales': sales,
            'conversion': round(conversion, 2)
        })
    
    conversion_by_product.sort(key=lambda x: x['conversion'], reverse=True)
    
    context = {
        'period': period,
        'start_date': start_date,
        'monthly_revenue': list(monthly_revenue),
        'top_categories': top_categories,
        'product_performance': product_performance,
        'conversion_by_product': conversion_by_product[:10],
    }
    
    return render(request, 'store/admin/analytics.html', context)

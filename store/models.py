from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import os
from datetime import timedelta


def product_image_path(instance, filename):
    """Génère le chemin pour les images de produits"""
    ext = filename.split('.')[-1]
    filename = f"{instance.id}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('products', filename)


def product_file_path(instance, filename):
    """Génère le chemin pour les fichiers de produits"""
    ext = filename.split('.')[-1]
    filename = f"{instance.id}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('product_files', filename)


class Category(models.Model):
    """Catégorie de produits"""
    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Image")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Produit (formation ou livre)"""
    PRODUCT_TYPES = [
        ('formation', 'Formation'),
        ('livre', 'Livre'),
        ('ebook', 'E-book'),
        ('video', 'Vidéo'),
    ]
    
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('zip', 'ZIP'),
        ('mp4', 'MP4'),
        ('mov', 'MOV'),
        ('avi', 'AVI'),
    ]

    # Informations de base
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Description")
    short_description = models.CharField(max_length=300, verbose_name="Description courte")
    
    # Catégorisation
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Catégorie")
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='formation', verbose_name="Type de produit")
    
    # Prix
    price_fcfa = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (FCFA)")
    price_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (EUR)")
    
    # Fichiers et médias
    cover_image = models.ImageField(upload_to=product_image_path, verbose_name="Image de couverture")
    product_file = models.FileField(upload_to=product_file_path, verbose_name="Fichier produit")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='pdf', verbose_name="Type de fichier")
    file_size = models.CharField(max_length=20, blank=True, verbose_name="Taille du fichier")
    
    # Métadonnées
    duration = models.CharField(max_length=50, blank=True, verbose_name="Durée")
    level = models.CharField(max_length=50, blank=True, verbose_name="Niveau")
    language = models.CharField(max_length=50, default='Français', verbose_name="Langue")
    
    # Collections et sections
    collection = models.ForeignKey(
        'BookCollection', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='books',
        verbose_name="Collection"
    )
    personal_development_section = models.ForeignKey(
        'PersonalDevelopmentSection', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='books',
        verbose_name="Section développement personnel"
    )
    
    # Type de produit (gratuit/payant)
    PRICING_CHOICES = [
        ('free', 'Gratuit'),
        ('paid', 'Payant'),
    ]
    pricing_type = models.CharField(
        max_length=10, 
        choices=PRICING_CHOICES, 
        default='paid', 
        verbose_name="Type de tarification"
    )
    
    # Statut et visibilité
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    is_new = models.BooleanField(default=False, verbose_name="Nouveau")
    is_popular = models.BooleanField(default=False, verbose_name="Populaire")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Statistiques
    views_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")
    sales_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de ventes")
    downloads_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de téléchargements")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name="Note moyenne")
    rating_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'avis")
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Titre SEO")
    meta_description = models.TextField(blank=True, verbose_name="Description SEO")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f'/product/{self.slug}/'

    def get_price_display(self):
        return f"{self.price_fcfa} FCFA / {self.price_eur} EUR"

    def get_total_video_count(self):
        """Retourne le nombre total de séquences vidéo"""
        return self.video_sequences.filter(is_active=True).count()

    def get_total_duration(self):
        """Retourne la durée totale de la formation"""
        total_minutes = self.video_sequences.filter(is_active=True).aggregate(
            total=models.Sum('duration')
        )['total'] or 0
        return total_minutes

    def get_total_duration_display(self):
        """Retourne la durée totale formatée"""
        total_minutes = self.get_total_duration()
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}min"
        return f"{minutes}min"

    def has_preview_sequence(self):
        """Vérifie si la formation a une séquence d'aperçu"""
        return self.video_sequences.filter(is_preview=True, is_active=True).exists()
    
    def increment_downloads(self):
        """Incrémente le nombre de téléchargements"""
        self.downloads_count += 1
        self.save(update_fields=['downloads_count'])
    
    def is_free(self):
        """Vérifier si le produit est gratuit"""
        return self.pricing_type == 'free' or self.price_fcfa == 0
    
    def get_price_display_for_free_products(self):
        """Obtenir l'affichage du prix pour les produits gratuits"""
        if self.is_free():
            return "Gratuit"
        else:
            return f"{self.price_fcfa} FCFA"
    
    def is_composite_product(self):
        """Vérifier si le produit est composé de plusieurs éléments"""
        return (
            self.video_sequences.exists() or 
            self.collection is not None or 
            self.personal_development_section is not None
        )
    
    def get_composite_type(self):
        """Obtenir le type de produit composé"""
        if self.video_sequences.exists():
            return "video_sequences"
        elif self.collection:
            return "collection"
        elif self.personal_development_section:
            return "personal_development"
        else:
            return "simple"


class Order(models.Model):
    """Commande"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payée'),
        ('processing', 'En traitement'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée'),
    ]

    # Informations de base
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Numéro de commande")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Utilisateur")
    
    # Produits
    products = models.ManyToManyField(Product, through='OrderItem', verbose_name="Produits")
    
    # Montants
    subtotal_fcfa = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sous-total (FCFA)")
    subtotal_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sous-total (EUR)")
    total_fcfa = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total (FCFA)")
    total_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total (EUR)")
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    
    # Informations client
    customer_email = models.EmailField(verbose_name="Email client")
    customer_name = models.CharField(max_length=200, verbose_name="Nom client")
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone client")
    
    # Notes
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="Payé le")

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Élément de commande"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Commande")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produit")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    price_fcfa = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (FCFA)")
    price_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (EUR)")

    class Meta:
        verbose_name = "Élément de commande"
        verbose_name_plural = "Éléments de commande"

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"


class Payment(models.Model):
    """Paiement"""
    PAYMENT_METHODS = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),

        ('wave', 'Wave'),
        ('cinetpay', 'CinetPay'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En traitement'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]

    # Informations de base
    payment_id = models.CharField(max_length=100, unique=True, verbose_name="ID de paiement")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name="Commande")
    
    # Méthode et montant
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name="Méthode de paiement")
    amount_fcfa = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (FCFA)")
    amount_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (EUR)")
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    
    # Informations de transaction
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name="ID de transaction")
    gateway_response = models.JSONField(blank=True, null=True, verbose_name="Réponse de la passerelle")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Terminé le")

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement {self.payment_id}"


class Download(models.Model):
    """Téléchargement"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloads', verbose_name="Utilisateur")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='downloads', verbose_name="Produit")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='downloads', verbose_name="Commande", null=True, blank=True)
    
    # Lien de téléchargement
    download_url = models.URLField(verbose_name="URL de téléchargement")
    download_token = models.CharField(max_length=100, unique=True, verbose_name="Token de téléchargement")
    
    # Limites
    max_downloads = models.PositiveIntegerField(default=3, verbose_name="Nombre max de téléchargements")
    downloads_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de téléchargements")
    
    # Expiration
    expires_at = models.DateTimeField(verbose_name="Expire le")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    last_download_at = models.DateTimeField(blank=True, null=True, verbose_name="Dernier téléchargement")

    class Meta:
        verbose_name = "Téléchargement"
        verbose_name_plural = "Téléchargements"
        ordering = ['-created_at']

    def __str__(self):
        return f"Téléchargement {self.product.title} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.download_token:
            self.download_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def can_download(self):
        return (
            self.is_active and 
            self.downloads_count < self.max_downloads and 
            timezone.now() < self.expires_at
        )


class Review(models.Model):
    """Avis client"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Produit")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Utilisateur")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews', verbose_name="Commande", null=True, blank=True)
    
    # Évaluation
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note"
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    comment = models.TextField(verbose_name="Commentaire")
    
    # Statut
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé")
    is_verified_purchase = models.BooleanField(default=True, verbose_name="Achat vérifié")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']
        unique_together = ['product', 'user', 'order']

    def __str__(self):
        return f"Avis de {self.user.username} sur {self.product.title}"


class VideoSequence(models.Model):
    """Séquence vidéo d'une formation"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='video_sequences', verbose_name="Formation")
    title = models.CharField(max_length=200, verbose_name="Titre de la séquence")
    description = models.TextField(blank=True, verbose_name="Description")
    video_file = models.FileField(upload_to='video_sequences/', verbose_name="Fichier vidéo")
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True, verbose_name="Aperçu")
    duration = models.PositiveIntegerField(default=0, verbose_name="Durée (minutes)")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    is_preview = models.BooleanField(default=False, verbose_name="Aperçu gratuit")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Séquence vidéo"
        verbose_name_plural = "Séquences vidéo"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.product.title} - {self.title}"

    def get_duration_display(self):
        """Retourne la durée formatée"""
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours > 0:
            return f"{hours}h {minutes}min"
        return f"{minutes}min"


class BookCollection(models.Model):
    """Collection de livres"""
    title = models.CharField(max_length=200, verbose_name="Titre de la collection")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Description")
    cover_image = models.ImageField(upload_to='collections/', verbose_name="Image de couverture")
    
    # Prix de la collection (peut être différent de la somme des livres individuels)
    price_fcfa = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix collection (FCFA)")
    price_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix collection (EUR)")
    
    # Réduction appliquée par rapport à l'achat individuel
    discount_percentage = models.PositiveIntegerField(default=0, verbose_name="Réduction (%)")
    
    # Métadonnées
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Collection de livres"
        verbose_name_plural = "Collections de livres"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_books_count(self):
        return self.books.count()
    
    def get_total_individual_price_fcfa(self):
        return sum(book.price_fcfa for book in self.books.all())
    
    def get_total_individual_price_eur(self):
        return sum(book.price_eur for book in self.books.all())
    
    def get_savings_fcfa(self):
        return self.get_total_individual_price_fcfa() - self.price_fcfa
    
    def get_savings_eur(self):
        return self.get_total_individual_price_eur() - self.price_eur


class PersonalDevelopmentSection(models.Model):
    """Section développement personnel"""
    name = models.CharField(max_length=100, verbose_name="Nom de la section")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Description")
    image = models.ImageField(upload_to='sections/', blank=True, null=True, verbose_name="Image")
    
    # Sous-sections thématiques
    SUB_SECTIONS = [
        ('motivation', 'Motivation et Productivité'),
        ('leadership', 'Leadership et Management'),
        ('communication', 'Communication et Relations'),
        ('bien_etre', 'Bien-être et Équilibre'),
        ('finance', 'Finance personnelle'),
        ('carriere', 'Carrière et Développement professionnel'),
    ]
    sub_section = models.CharField(max_length=20, choices=SUB_SECTIONS, verbose_name="Sous-section")
    
    # Visibilité
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Section développement personnel"
        verbose_name_plural = "Sections développement personnel"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_books_count(self):
        return self.books.count()


class Contact(models.Model):
    """Formulaire de contact"""
    CONTACT_TYPES = [
        ('general', 'Question générale'),
        ('support', 'Support technique'),
        ('billing', 'Facturation'),
        ('partnership', 'Partenariat'),
        ('other', 'Autre'),
    ]
    
    # Informations de base
    name = models.CharField(max_length=200, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    
    # Sujet et message
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES, default='general', verbose_name="Type de contact")
    subject = models.CharField(max_length=200, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    
    # Statut
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    is_responded = models.BooleanField(default=False, verbose_name="Répondu")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"





class CinetPayTransaction(models.Model):
    """Transaction CinetPay"""
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('PENDING', 'En attente'),
        ('SUCCESS', 'Succès'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
        ('EXPIRED', 'Expiré'),
    ]
    
    # Informations de base
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name="ID de transaction")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='cinetpay_transactions', verbose_name="Commande")
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='cinetpay_transactions', verbose_name="Paiement")
    
    # Informations CinetPay
    cinetpay_transaction_id = models.CharField(max_length=100, blank=True, verbose_name="ID transaction CinetPay")
    payment_token = models.CharField(max_length=255, blank=True, verbose_name="Token de paiement")
    
    # Montants
    amount_fcfa = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (FCFA)")
    amount_eur = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (EUR)")
    
    # Informations client
    customer_name = models.CharField(max_length=200, verbose_name="Nom du client")
    customer_email = models.EmailField(verbose_name="Email du client")
    customer_phone = models.CharField(max_length=20, verbose_name="Téléphone du client")
    
    # Statut et métadonnées
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED', verbose_name="Statut")
    gateway_response = models.JSONField(blank=True, null=True, verbose_name="Réponse de la passerelle")
    
    # Informations de suivi
    initiated_at = models.DateTimeField(blank=True, null=True, verbose_name="Initiated le")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Terminé le")
    expires_at = models.DateTimeField(verbose_name="Expire le")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Transaction CinetPay"
        verbose_name_plural = "Transactions CinetPay"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"CinetPay - {self.customer_name} - {self.amount_fcfa} FCFA"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"CP_{uuid.uuid4().hex[:16].upper()}"
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def can_retry(self):
        return self.status in ['FAILED', 'EXPIRED', 'CANCELLED']
    
    def get_status_display_color(self):
        status_colors = {
            'INITIATED': 'text-blue-600',
            'PENDING': 'text-yellow-600',
            'SUCCESS': 'text-green-600',
            'FAILED': 'text-red-600',
            'CANCELLED': 'text-gray-600',
            'EXPIRED': 'text-orange-600',
        }
        return status_colors.get(self.status, 'text-gray-600')

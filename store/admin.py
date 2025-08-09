from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Category, Product, Order, OrderItem, Payment, Download, Review, VideoSequence, BookCollection, PersonalDevelopmentSection, Contact


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at', 'product_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Nombre de produits"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price_fcfa', 'price_eur']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['payment_id', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer_name', 'customer_email', 
        'total_fcfa', 'total_eur', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'paid_at']
    search_fields = ['order_number', 'customer_name', 'customer_email']
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 'paid_at',
        'subtotal_fcfa', 'subtotal_eur', 'total_fcfa', 'total_eur'
    ]
    inlines = [OrderItemInline, PaymentInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Informations client', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Montants', {
            'fields': ('subtotal_fcfa', 'subtotal_eur', 'total_fcfa', 'total_eur'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'product_type', 'pricing_type', 'price_fcfa', 
        'price_eur', 'downloads_count', 'is_active', 'is_featured', 'views_count', 'sales_count'
    ]
    list_filter = [
        'category', 'product_type', 'pricing_type', 'is_active', 'is_featured', 
        'is_new', 'is_popular', 'created_at'
    ]
    search_fields = ['title', 'description', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'views_count', 'sales_count', 'downloads_count', 'rating', 'rating_count',
        'created_at', 'updated_at', 'cover_image_preview'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'slug', 'description', 'short_description')
        }),
        ('Catégorisation', {
            'fields': ('category', 'product_type')
        }),
        ('Tarification', {
            'fields': ('pricing_type', 'price_fcfa', 'price_eur')
        }),
        ('Collections et sections', {
            'fields': ('collection', 'personal_development_section'),
            'classes': ('collapse',)
        }),
        ('Fichiers et médias', {
            'fields': ('cover_image', 'cover_image_preview', 'product_file', 'file_type', 'file_size')
        }),
        ('Métadonnées', {
            'fields': ('duration', 'level', 'language'),
            'classes': ('collapse',)
        }),
        ('Statut et visibilité', {
            'fields': ('is_featured', 'is_new', 'is_popular', 'is_active')
        }),
        ('Statistiques', {
            'fields': ('views_count', 'sales_count', 'downloads_count', 'rating', 'rating_count'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.cover_image.url
            )
        return "Aucune image"
    cover_image_preview.short_description = "Aperçu de l'image"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_id', 'order', 'payment_method', 'amount_fcfa', 
        'amount_eur', 'status', 'created_at'
    ]
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['payment_id', 'transaction_id', 'order__order_number']
    readonly_fields = [
        'payment_id', 'created_at', 'updated_at', 'completed_at'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('payment_id', 'order', 'payment_method')
        }),
        ('Montants', {
            'fields': ('amount_fcfa', 'amount_eur')
        }),
        ('Statut', {
            'fields': ('status',)
        }),
        ('Informations de transaction', {
            'fields': ('transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'product', 'downloads_count', 'max_downloads', 
        'is_active', 'expires_at', 'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__username', 'product__title', 'download_token']
    readonly_fields = [
        'download_token', 'downloads_count', 'created_at', 'last_download_at'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'product', 'order')
        }),
        ('Lien de téléchargement', {
            'fields': ('download_url', 'download_token')
        }),
        ('Limites', {
            'fields': ('max_downloads', 'downloads_count')
        }),
        ('Expiration', {
            'fields': ('expires_at', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_download_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product', 'order')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'product', 'rating', 'title', 'is_approved', 
        'is_verified_purchase', 'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'is_verified_purchase', 'created_at']
    search_fields = ['user__username', 'product__title', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'product', 'order')
        }),
        ('Évaluation', {
            'fields': ('rating', 'title', 'comment')
        }),
        ('Statut', {
            'fields': ('is_approved', 'is_verified_purchase')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product', 'order')


@admin.register(VideoSequence)
class VideoSequenceAdmin(admin.ModelAdmin):
    list_display = ['product', 'title', 'order', 'duration', 'is_preview', 'is_active']
    list_filter = ['is_preview', 'is_active', 'product']
    search_fields = ['title', 'product__title']
    ordering = ['product', 'order']
    list_editable = ['order', 'is_preview', 'is_active']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('product', 'title', 'description')
        }),
        ('Fichiers vidéo', {
            'fields': ('video_file', 'thumbnail')
        }),
        ('Métadonnées', {
            'fields': ('duration', 'order')
        }),
        ('Statut', {
            'fields': ('is_preview', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(BookCollection)
class BookCollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_books_count', 'price_fcfa', 'discount_percentage', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_featured', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'slug', 'description')
        }),
        ('Image', {
            'fields': ('cover_image',)
        }),
        ('Prix', {
            'fields': ('price_fcfa', 'price_eur', 'discount_percentage')
        }),
        ('Statut', {
            'fields': ('is_featured', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_books_count(self, obj):
        return obj.get_books_count()
    get_books_count.short_description = "Nombre de livres"


@admin.register(PersonalDevelopmentSection)
class PersonalDevelopmentSectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'sub_section', 'get_books_count', 'order', 'is_active']
    list_filter = ['is_active', 'sub_section', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Image', {
            'fields': ('image',)
        }),
        ('Catégorisation', {
            'fields': ('sub_section',)
        }),
        ('Affichage', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_books_count(self, obj):
        return obj.get_books_count()
    get_books_count.short_description = "Nombre de livres"


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'contact_type', 'subject', 'is_read', 
        'is_responded', 'created_at'
    ]
    list_filter = ['contact_type', 'is_read', 'is_responded', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_read', 'is_responded']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('contact_type', 'subject', 'message')
        }),
        ('Statut', {
            'fields': ('is_read', 'is_responded')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


# Configuration de l'interface d'administration
admin.site.site_header = "NovaLearn - Administration"
admin.site.site_title = "NovaLearn Admin"
admin.site.index_title = "Tableau de bord NovaLearn"

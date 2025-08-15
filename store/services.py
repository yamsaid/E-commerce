import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from .models import Payment, Order, Download
from decimal import Decimal

logger = logging.getLogger(__name__)

class CinetPayService:
    """Service pour gérer les paiements CinetPay"""
    
    def __init__(self):
        # Configuration CinetPay
        self.api_url = getattr(settings, 'CINETPAY_API_URL', 'https://api-checkout.cinetpay.com/v2/payment')
        self.site_id = getattr(settings, 'CINETPAY_SITE_ID', '')
        self.api_key = getattr(settings, 'CINETPAY_API_KEY', '')
        self.environment = getattr(settings, 'CINETPAY_ENVIRONMENT', 'TEST')  # TEST ou PROD
        self.return_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        self.cancel_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        self.notify_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    def initiate_payment(self, order, customer_data):
        """
        Initie un paiement CinetPay
        
        Args:
            order: Instance de Order
            customer_data: dict avec name, email, phone
            
        Returns:
            dict: Réponse de l'API avec statut et détails
        """
        try:
            from .models import CinetPayTransaction
            
            # Créer le paiement
            payment = Payment.objects.create(
                payment_id=f"PAY_{order.order_number}_{int(timezone.now().timestamp())}",
                order=order,
                payment_method='cinetpay',
                amount_fcfa=order.total_fcfa,
                amount_eur=order.total_eur,
                status='pending'
            )
            
            # Créer la transaction CinetPay
            transaction = CinetPayTransaction.objects.create(
                order=order,
                payment=payment,
                amount_fcfa=order.total_fcfa,
                amount_eur=order.total_eur,
                customer_name=customer_data.get('name', ''),
                customer_email=customer_data.get('email', ''),
                customer_phone=customer_data.get('phone', ''),
                status='INITIATED',
                initiated_at=timezone.now()
            )
            
            # Préparer les données pour CinetPay
            payload = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': transaction.transaction_id,
                'amount': int(order.total_fcfa),  # Montant en FCFA (entier)
                'currency': 'XOF',
                'description': f'Commande {order.order_number} - {order.items.count()} produit(s)',
                'return_url': f"{self.return_url}/payment-success/{order.order_number}/",
                'cancel_url': f"{self.cancel_url}/payment-cancel/{order.order_number}/",
                'notify_url': f"{self.notify_url}/api/cinetpay/webhook/",
                'customer_name': customer_data.get('name', ''),
                'customer_email': customer_data.get('email', ''),
                'customer_phone': customer_data.get('phone', ''),
                'customer_address': '',
                'customer_city': '',
                'customer_country': 'CI',
                'customer_state': '',
                'customer_zip_code': '',
                'channels': 'ALL',  # Tous les canaux de paiement
                'lang': 'FR',
                'invoice_data': {
                    'items': [
                        {
                            'name': item.product.title,
                            'quantity': item.quantity,
                            'unit_price': int(item.price_fcfa),
                            'total_price': int(item.price_fcfa * item.quantity),
                            'description': item.product.short_description
                        }
                        for item in order.items.all()
                    ]
                }
            }
            
            # Appeler l'API CinetPay
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('code') == '201':
                # Succès - mise à jour de la transaction
                transaction.cinetpay_transaction_id = response_data.get('data', {}).get('transaction_id', '')
                transaction.payment_token = response_data.get('data', {}).get('payment_token', '')
                transaction.status = 'PENDING'
                transaction.gateway_response = response_data
                transaction.save()
                
                # Mettre à jour le paiement
                payment.transaction_id = transaction.cinetpay_transaction_id
                payment.gateway_response = response_data
                payment.save()
                
                return {
                    'success': True,
                    'transaction_id': transaction.transaction_id,
                    'cinetpay_transaction_id': transaction.cinetpay_transaction_id,
                    'payment_url': response_data.get('data', {}).get('payment_url', ''),
                    'message': 'Paiement initié avec succès. Redirection vers CinetPay...',
                    'status': 'PENDING'
                }
            else:
                # Erreur
                transaction.status = 'FAILED'
                transaction.gateway_response = response_data
                transaction.save()
                
                error_message = response_data.get('message', 'Erreur lors de l\'initiation du paiement')
                logger.error(f"Erreur CinetPay: {error_message}")
                
                return {
                    'success': False,
                    'error': error_message,
                    'transaction_id': transaction.transaction_id
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du paiement CinetPay: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transaction_id': None
            }
    
    def check_payment_status(self, transaction_id):
        """
        Vérifie le statut d'un paiement CinetPay
        
        Args:
            transaction_id: ID de la transaction
            
        Returns:
            dict: Statut du paiement
        """
        try:
            from .models import CinetPayTransaction
            
            transaction = CinetPayTransaction.objects.get(transaction_id=transaction_id)
            
            if transaction.status == 'SUCCESS':
                return {
                    'success': True,
                    'status': 'SUCCESS',
                    'message': 'Paiement confirmé avec succès'
                }
            
            if transaction.is_expired():
                transaction.status = 'EXPIRED'
                transaction.save()
                return {
                    'success': False,
                    'status': 'EXPIRED',
                    'message': 'La transaction a expiré'
                }
            
            # Vérifier le statut auprès de CinetPay
            if transaction.cinetpay_transaction_id:
                return self._check_cinetpay_status(transaction)
            
            return {
                'success': False,
                'status': transaction.status,
                'message': 'Statut en attente'
            }
            
        except CinetPayTransaction.DoesNotExist:
            return {
                'success': False,
                'error': 'Transaction non trouvée'
            }
    
    def _check_cinetpay_status(self, transaction):
        """Vérifie le statut auprès de l'API CinetPay"""
        try:
            # URL de vérification du statut
            status_url = 'https://api-checkout.cinetpay.com/v2/payment/check'
            
            payload = {
                'apikey': self.api_key,
                'site_id': self.site_id,
                'transaction_id': transaction.cinetpay_transaction_id
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(status_url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200:
                # Mettre à jour le statut selon la réponse
                cinetpay_status = response_data.get('data', {}).get('status')
                
                if cinetpay_status == 'SUCCESS':
                    transaction.status = 'SUCCESS'
                    transaction.completed_at = timezone.now()
                    # Mettre à jour le paiement
                    transaction.payment.status = 'completed'
                    transaction.payment.completed_at = timezone.now()
                    transaction.payment.save()
                elif cinetpay_status == 'FAILED':
                    transaction.status = 'FAILED'
                elif cinetpay_status == 'PENDING':
                    transaction.status = 'PENDING'
                elif cinetpay_status == 'CANCELLED':
                    transaction.status = 'CANCELLED'
                
                transaction.gateway_response = response_data
                transaction.save()
                
                return {
                    'success': True,
                    'status': transaction.status,
                    'message': response_data.get('message', 'Statut mis à jour')
                }
            
            return {
                'success': False,
                'error': 'Erreur lors de la vérification du statut'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la vérification du statut CinetPay: {str(e)}")
            return {
                'success': False,
                'error': 'Erreur de connexion'
            }
    
    def process_webhook(self, webhook_data):
        """
        Traite les webhooks CinetPay
        
        Args:
            webhook_data: Données du webhook
            
        Returns:
            dict: Résultat du traitement
        """
        try:
            from .models import CinetPayTransaction
            
            # Extraire les données du webhook
            transaction_id = webhook_data.get('transaction_id')
            cinetpay_transaction_id = webhook_data.get('cinetpay_transaction_id')
            status = webhook_data.get('status')
            amount = webhook_data.get('amount')
            
            # Vérifier la signature (à implémenter selon la documentation CinetPay)
            # if not self._verify_signature(webhook_data):
            #     return {'success': False, 'error': 'Signature invalide'}
            
            # Trouver la transaction
            try:
                if transaction_id:
                    transaction = CinetPayTransaction.objects.get(transaction_id=transaction_id)
                elif cinetpay_transaction_id:
                    transaction = CinetPayTransaction.objects.get(cinetpay_transaction_id=cinetpay_transaction_id)
                else:
                    return {'success': False, 'error': 'Transaction ID manquant'}
            except CinetPayTransaction.DoesNotExist:
                return {'success': False, 'error': 'Transaction non trouvée'}
            
            # Mettre à jour le statut
            if status == 'SUCCESS':
                transaction.status = 'SUCCESS'
                transaction.completed_at = timezone.now()
                # Mettre à jour le paiement
                transaction.payment.status = 'completed'
                transaction.payment.completed_at = timezone.now()
                transaction.payment.save()
                
                # Mettre à jour la commande
                order = transaction.order
                order.status = 'paid'
                order.paid_at = timezone.now()
                order.save()
                
                # Créer les liens de téléchargement
                self._create_download_links(order)
                
            elif status == 'FAILED':
                transaction.status = 'FAILED'
            elif status == 'CANCELLED':
                transaction.status = 'CANCELLED'
            
            transaction.gateway_response = webhook_data
            transaction.save()
            
            return {
                'success': True,
                'message': f'Webhook traité avec succès. Statut: {status}'
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook CinetPay: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_download_links(self, order):
        """Crée les liens de téléchargement pour une commande payée"""
        try:
            for item in order.items.all():
                # Vérifier si un lien de téléchargement existe déjà
                existing_download = Download.objects.filter(
                    user=order.user,
                    product=item.product,
                    order=order
                ).first()
                
                if not existing_download:
                    Download.objects.create(
                        user=order.user,
                        product=item.product,
                        order=order,
                        download_url=f'/media/{item.product.product_file.name}',
                        expires_at=timezone.now() + timezone.timedelta(days=30),
                    )
                    
                    # Incrémenter le compteur de téléchargements du produit
                    item.product.increment_downloads()
                    
        except Exception as e:
            logger.error(f"Erreur lors de la création des liens de téléchargement: {str(e)}")
    
    def _verify_signature(self, webhook_data):
        """Vérifie la signature du webhook CinetPay (à implémenter)"""
        # Cette méthode doit être implémentée selon la documentation CinetPay
        # pour vérifier l'authenticité du webhook
        return True  # Temporaire

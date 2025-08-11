import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from .models import MobileMoneyTransaction, Payment, Order
from decimal import Decimal

logger = logging.getLogger(__name__)

class MobileMoneyService:
    """Service pour gérer les paiements Mobile Money"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'MOBILE_MONEY_BASE_URL', 'https://api.mobilemoney.com')
        self.api_key = getattr(settings, 'MOBILE_MONEY_API_KEY', '')
        self.merchant_id = getattr(settings, 'MOBILE_MONEY_MERCHANT_ID', '')
        self.secret_key = getattr(settings, 'MOBILE_MONEY_SECRET_KEY', '')
    
    def initiate_payment(self, order, operator, phone_number, amount_fcfa):
        """
        Initie un paiement Mobile Money
        
        Args:
            order: Instance de Order
            operator: Opérateur (orange, mtn, moov, wave)
            phone_number: Numéro de téléphone
            amount_fcfa: Montant en FCFA
        
        Returns:
            dict: Réponse de l'API avec statut et détails
        """
        try:
            # Créer le paiement
            payment = Payment.objects.create(
                payment_id=f"PAY_{order.order_number}_{int(timezone.now().timestamp())}",
                order=order,
                payment_method='mobile_money',
                amount_fcfa=amount_fcfa,
                amount_eur=order.total_eur,
                status='pending'
            )
            
            # Créer la transaction Mobile Money
            transaction = MobileMoneyTransaction.objects.create(
                order=order,
                payment=payment,
                operator=operator,
                phone_number=phone_number,
                amount_fcfa=amount_fcfa,
                amount_eur=order.total_eur,
                status='pending'
            )
            
            # Appeler l'API de l'opérateur selon le type
            if operator == 'orange':
                return self._initiate_orange_payment(transaction)
            elif operator == 'mtn':
                return self._initiate_mtn_payment(transaction)
            elif operator == 'moov':
                return self._initiate_moov_payment(transaction)
            elif operator == 'wave':
                return self._initiate_wave_payment(transaction)
            else:
                raise ValueError(f"Opérateur non supporté: {operator}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initiation du paiement Mobile Money: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transaction_id': None
            }
    
    def _initiate_orange_payment(self, transaction):
        """Initie un paiement Orange Money"""
        try:
            # URL de l'API Orange Money (à adapter selon la documentation officielle)
            url = f"{self.base_url}/orange/initiate"
            
            payload = {
                'merchant_id': self.merchant_id,
                'amount': str(transaction.amount_fcfa),
                'currency': 'XOF',
                'phone_number': transaction.phone_number,
                'reference': transaction.transaction_id,
                'callback_url': f"{settings.SITE_URL}/api/mobile-money/webhook/orange/",
                'return_url': f"{settings.SITE_URL}/payment-status/{transaction.transaction_id}/"
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                # Mettre à jour la transaction
                transaction.status = 'initiated'
                transaction.gateway_transaction_id = response_data.get('transaction_id')
                transaction.gateway_response = response_data
                transaction.initiated_at = timezone.now()
                transaction.save()
                
                return {
                    'success': True,
                    'transaction_id': transaction.transaction_id,
                    'gateway_transaction_id': response_data.get('transaction_id'),
                    'message': 'Paiement initié avec succès. Vérifiez votre téléphone pour confirmer.',
                    'status': 'initiated'
                }
            else:
                # Mettre à jour la transaction avec l'erreur
                transaction.status = 'failed'
                transaction.gateway_response = response_data
                transaction.save()
                
                return {
                    'success': False,
                    'error': response_data.get('message', 'Erreur lors de l\'initiation du paiement'),
                    'transaction_id': transaction.transaction_id
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion à l'API Orange Money: {str(e)}")
            transaction.status = 'failed'
            transaction.gateway_response = {'error': str(e)}
            transaction.save()
            
            return {
                'success': False,
                'error': 'Erreur de connexion au service de paiement',
                'transaction_id': transaction.transaction_id
            }
    
    def _initiate_mtn_payment(self, transaction):
        """Initie un paiement MTN Money"""
        try:
            url = f"{self.base_url}/mtn/initiate"
            
            payload = {
                'merchant_id': self.merchant_id,
                'amount': str(transaction.amount_fcfa),
                'currency': 'XOF',
                'phone_number': transaction.phone_number,
                'reference': transaction.transaction_id,
                'callback_url': f"{settings.SITE_URL}/api/mobile-money/webhook/mtn/",
                'return_url': f"{settings.SITE_URL}/payment-status/{transaction.transaction_id}/"
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                transaction.status = 'initiated'
                transaction.gateway_transaction_id = response_data.get('transaction_id')
                transaction.gateway_response = response_data
                transaction.initiated_at = timezone.now()
                transaction.save()
                
                return {
                    'success': True,
                    'transaction_id': transaction.transaction_id,
                    'gateway_transaction_id': response_data.get('transaction_id'),
                    'message': 'Paiement MTN initié avec succès. Vérifiez votre téléphone pour confirmer.',
                    'status': 'initiated'
                }
            else:
                transaction.status = 'failed'
                transaction.gateway_response = response_data
                transaction.save()
                
                return {
                    'success': False,
                    'error': response_data.get('message', 'Erreur lors de l\'initiation du paiement MTN'),
                    'transaction_id': transaction.transaction_id
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion à l'API MTN Money: {str(e)}")
            transaction.status = 'failed'
            transaction.gateway_response = {'error': str(e)}
            transaction.save()
            
            return {
                'success': False,
                'error': 'Erreur de connexion au service de paiement MTN',
                'transaction_id': transaction.transaction_id
            }
    
    def _initiate_moov_payment(self, transaction):
        """Initie un paiement Moov Money"""
        try:
            url = f"{self.base_url}/moov/initiate"
            
            payload = {
                'merchant_id': self.merchant_id,
                'amount': str(transaction.amount_fcfa),
                'currency': 'XOF',
                'phone_number': transaction.phone_number,
                'reference': transaction.transaction_id,
                'callback_url': f"{settings.SITE_URL}/api/mobile-money/webhook/moov/",
                'return_url': f"{settings.SITE_URL}/payment-status/{transaction.transaction_id}/"
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                transaction.status = 'initiated'
                transaction.gateway_transaction_id = response_data.get('transaction_id')
                transaction.gateway_response = response_data
                transaction.initiated_at = timezone.now()
                transaction.save()
                
                return {
                    'success': True,
                    'transaction_id': transaction.transaction_id,
                    'gateway_transaction_id': response_data.get('transaction_id'),
                    'message': 'Paiement Moov initié avec succès. Vérifiez votre téléphone pour confirmer.',
                    'status': 'initiated'
                }
            else:
                transaction.status = 'failed'
                transaction.gateway_response = response_data
                transaction.save()
                
                return {
                    'success': False,
                    'error': response_data.get('message', 'Erreur lors de l\'initiation du paiement Moov'),
                    'transaction_id': transaction.transaction_id
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion à l'API Moov Money: {str(e)}")
            transaction.status = 'failed'
            transaction.gateway_response = {'error': str(e)}
            transaction.save()
            
            return {
                'success': False,
                'error': 'Erreur de connexion au service de paiement Moov',
                'transaction_id': transaction.transaction_id
            }
    
    def _initiate_wave_payment(self, transaction):
        """Initie un paiement Wave"""
        try:
            url = f"{self.base_url}/wave/initiate"
            
            payload = {
                'merchant_id': self.merchant_id,
                'amount': str(transaction.amount_fcfa),
                'currency': 'XOF',
                'phone_number': transaction.phone_number,
                'reference': transaction.transaction_id,
                'callback_url': f"{settings.SITE_URL}/api/mobile-money/webhook/wave/",
                'return_url': f"{settings.SITE_URL}/payment-status/{transaction.transaction_id}/"
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                transaction.status = 'initiated'
                transaction.gateway_transaction_id = response_data.get('transaction_id')
                transaction.gateway_response = response_data
                transaction.initiated_at = timezone.now()
                transaction.save()
                
                return {
                    'success': True,
                    'transaction_id': transaction.transaction_id,
                    'gateway_transaction_id': response_data.get('transaction_id'),
                    'message': 'Paiement Wave initié avec succès. Vérifiez votre téléphone pour confirmer.',
                    'status': 'initiated'
                }
            else:
                transaction.status = 'failed'
                transaction.gateway_response = response_data
                transaction.save()
                
                return {
                    'success': False,
                    'error': response_data.get('message', 'Erreur lors de l\'initiation du paiement Wave'),
                    'transaction_id': transaction.transaction_id
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion à l'API Wave: {str(e)}")
            transaction.status = 'failed'
            transaction.gateway_response = {'error': str(e)}
            transaction.save()
            
            return {
                'success': False,
                'error': 'Erreur de connexion au service de paiement Wave',
                'transaction_id': transaction.transaction_id
            }
    
    def check_payment_status(self, transaction_id):
        """
        Vérifie le statut d'un paiement
        
        Args:
            transaction_id: ID de la transaction
            
        Returns:
            dict: Statut du paiement
        """
        try:
            transaction = MobileMoneyTransaction.objects.get(transaction_id=transaction_id)
            
            if transaction.status == 'success':
                return {
                    'success': True,
                    'status': 'success',
                    'message': 'Paiement confirmé avec succès'
                }
            
            if transaction.is_expired():
                transaction.status = 'expired'
                transaction.save()
                return {
                    'success': False,
                    'status': 'expired',
                    'message': 'La transaction a expiré'
                }
            
            # Vérifier le statut auprès de la passerelle
            if transaction.gateway_transaction_id:
                return self._check_gateway_status(transaction)
            
            return {
                'success': False,
                'status': transaction.status,
                'message': 'Statut en attente'
            }
            
        except MobileMoneyTransaction.DoesNotExist:
            return {
                'success': False,
                'error': 'Transaction non trouvée'
            }
    
    def _check_gateway_status(self, transaction):
        """Vérifie le statut auprès de la passerelle de paiement"""
        try:
            if transaction.operator == 'orange':
                url = f"{self.base_url}/orange/status/{transaction.gateway_transaction_id}"
            elif transaction.operator == 'mtn':
                url = f"{self.base_url}/mtn/status/{transaction.gateway_transaction_id}"
            elif transaction.operator == 'moov':
                url = f"{self.base_url}/moov/status/{transaction.gateway_transaction_id}"
            elif transaction.operator == 'wave':
                url = f"{self.base_url}/wave/status/{transaction.gateway_transaction_id}"
            else:
                return {
                    'success': False,
                    'error': 'Opérateur non supporté'
                }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200:
                # Mettre à jour le statut selon la réponse
                gateway_status = response_data.get('status')
                
                if gateway_status == 'success':
                    transaction.status = 'success'
                    transaction.completed_at = timezone.now()
                    # Mettre à jour le paiement
                    transaction.payment.status = 'completed'
                    transaction.payment.save()
                elif gateway_status == 'failed':
                    transaction.status = 'failed'
                elif gateway_status == 'processing':
                    transaction.status = 'processing'
                
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
            logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
            return {
                'success': False,
                'error': 'Erreur de connexion'
            }

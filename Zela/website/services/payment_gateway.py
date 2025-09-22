"""
Payment Gateway Integration Service
Handles payment processing for the booking flow
"""
from typing import Dict, Optional, Tuple
from decimal import Decimal
from django.conf import settings
import uuid
import logging

logger = logging.getLogger(__name__)


class PaymentGateway:
    """Base payment gateway interface."""
    
    def process_payment(self, amount: Decimal, booking_id: int, payment_method: str, **kwargs) -> Tuple[bool, Dict]:
        """
        Process a payment transaction.
        
        Args:
            amount: Payment amount in Kz
            booking_id: Associated booking ID
            payment_method: Payment method (cash, card, transfer)
            **kwargs: Additional payment data
            
        Returns:
            Tuple of (success: bool, response: dict)
        """
        raise NotImplementedError("Subclasses must implement process_payment")
    
    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> Tuple[bool, Dict]:
        """
        Refund a payment transaction.
        
        Args:
            transaction_id: Original transaction ID
            amount: Optional partial refund amount
            
        Returns:
            Tuple of (success: bool, response: dict)
        """
        raise NotImplementedError("Subclasses must implement refund_payment")
    
    def get_transaction_status(self, transaction_id: str) -> Dict:
        """Get the status of a transaction."""
        raise NotImplementedError("Subclasses must implement get_transaction_status")


class MockPaymentGateway(PaymentGateway):
    """Mock payment gateway for development/testing."""
    
    def process_payment(self, amount: Decimal, booking_id: int, payment_method: str, **kwargs) -> Tuple[bool, Dict]:
        """Simulate payment processing."""
        transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        
        # Simulate payment processing
        logger.info(f"Processing mock payment: {amount} Kz for booking {booking_id}")
        
        # Simulate different outcomes based on amount
        if amount == Decimal('0.01'):
            # Test failure case
            return False, {
                'transaction_id': transaction_id,
                'status': 'failed',
                'error': 'Insufficient funds',
                'amount': str(amount),
                'booking_id': booking_id
            }
        
        # Successful payment
        return True, {
            'transaction_id': transaction_id,
            'status': 'completed',
            'amount': str(amount),
            'booking_id': booking_id,
            'payment_method': payment_method,
            'gateway': 'mock'
        }
    
    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> Tuple[bool, Dict]:
        """Simulate payment refund."""
        refund_id = f"REF_{uuid.uuid4().hex[:12].upper()}"
        
        logger.info(f"Processing mock refund for transaction {transaction_id}")
        
        return True, {
            'refund_id': refund_id,
            'original_transaction_id': transaction_id,
            'status': 'refunded',
            'amount': str(amount) if amount else 'full'
        }
    
    def get_transaction_status(self, transaction_id: str) -> Dict:
        """Get mock transaction status."""
        return {
            'transaction_id': transaction_id,
            'status': 'completed',
            'gateway': 'mock'
        }


class StripePaymentGateway(PaymentGateway):
    """Stripe payment gateway integration."""
    
    def __init__(self):
        """Initialize Stripe with API keys."""
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self.stripe = stripe
        except ImportError:
            logger.error("Stripe library not installed. Run: pip install stripe")
            raise
    
    def process_payment(self, amount: Decimal, booking_id: int, payment_method: str, **kwargs) -> Tuple[bool, Dict]:
        """Process payment via Stripe."""
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            # Create payment intent
            intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='aoa',  # Angolan Kwanza
                metadata={
                    'booking_id': str(booking_id),
                    'payment_method': payment_method
                },
                description=f"Payment for booking #{booking_id}"
            )
            
            return True, {
                'transaction_id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status,
                'amount': str(amount),
                'booking_id': booking_id,
                'gateway': 'stripe'
            }
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return False, {
                'error': str(e),
                'status': 'failed',
                'gateway': 'stripe'
            }
    
    def refund_payment(self, transaction_id: str, amount: Optional[Decimal] = None) -> Tuple[bool, Dict]:
        """Refund via Stripe."""
        try:
            refund_data = {'payment_intent': transaction_id}
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            refund = self.stripe.Refund.create(**refund_data)
            
            return True, {
                'refund_id': refund.id,
                'original_transaction_id': transaction_id,
                'status': refund.status,
                'amount': str(Decimal(refund.amount) / 100),
                'gateway': 'stripe'
            }
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {str(e)}")
            return False, {
                'error': str(e),
                'status': 'failed',
                'gateway': 'stripe'
            }
    
    def get_transaction_status(self, transaction_id: str) -> Dict:
        """Get Stripe payment status."""
        try:
            intent = self.stripe.PaymentIntent.retrieve(transaction_id)
            return {
                'transaction_id': transaction_id,
                'status': intent.status,
                'amount': str(Decimal(intent.amount) / 100),
                'gateway': 'stripe'
            }
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe status error: {str(e)}")
            return {
                'transaction_id': transaction_id,
                'status': 'unknown',
                'error': str(e),
                'gateway': 'stripe'
            }


class PaymentService:
    """Service for handling payments in the booking flow."""
    
    @staticmethod
    def get_gateway(gateway_type: Optional[str] = None) -> PaymentGateway:
        """
        Get the appropriate payment gateway.
        
        Args:
            gateway_type: Optional gateway type override
            
        Returns:
            PaymentGateway instance
        """
        if not gateway_type:
            gateway_type = getattr(settings, 'PAYMENT_GATEWAY', 'mock')
        
        if gateway_type == 'stripe':
            return StripePaymentGateway()
        else:
            return MockPaymentGateway()
    
    @classmethod
    def process_booking_payment(cls, booking, payment_method: str) -> Tuple[bool, Dict]:
        """
        Process payment for a booking.
        
        Args:
            booking: Booking instance
            payment_method: Payment method chosen
            
        Returns:
            Tuple of (success, transaction_data)
        """
        gateway = cls.get_gateway()
        
        # For cash payments, just mark as pending
        if payment_method == 'cash':
            return True, {
                'transaction_id': f"CASH_{booking.id}",
                'status': 'pending_cash_payment',
                'payment_method': 'cash',
                'amount': str(booking.total_price)
            }
        
        # Process electronic payment
        success, response = gateway.process_payment(
            amount=Decimal(str(booking.total_price)),
            booking_id=booking.id,
            payment_method=payment_method
        )
        
        if success:
            # Update booking payment status
            booking.payment_status = 'processing'
            booking.payment_transaction_id = response.get('transaction_id')
            booking.save(update_fields=['payment_status', 'payment_transaction_id'])
        
        return success, response
    
    @classmethod
    def refund_booking(cls, booking, amount: Optional[Decimal] = None) -> Tuple[bool, Dict]:
        """
        Refund a booking payment.
        
        Args:
            booking: Booking instance
            amount: Optional partial refund amount
            
        Returns:
            Tuple of (success, refund_data)
        """
        if not booking.payment_transaction_id:
            return False, {'error': 'No payment transaction found'}
        
        gateway = cls.get_gateway()
        success, response = gateway.refund_payment(
            transaction_id=booking.payment_transaction_id,
            amount=amount
        )
        
        if success:
            booking.payment_status = 'refunded'
            booking.save(update_fields=['payment_status'])
        
        return success, response
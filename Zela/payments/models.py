from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from bookings.models import Booking
import uuid

User = get_user_model()


class Payment(models.Model):
    """Payment records for bookings."""
    
    GATEWAY_CHOICES = [
        ("paystack", "Paystack"),
        ("paypal", "PayPal"),
        ("stripe", "Stripe"),
        ("bank_transfer", "Bank Transfer"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
        ("partial_refund", "Partial Refund"),
    ]
    
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        help_text="Booking this payment is for"
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Provider who will receive payment"
    )
    reference = models.CharField(
        max_length=120,
        unique=True,
        help_text="Payment gateway reference ID"
    )
    amount = models.PositiveIntegerField(
        help_text="Payment amount in AOA"
    )
    gateway = models.CharField(
        max_length=20,
        choices=GATEWAY_CHOICES,
        help_text="Payment gateway used"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current payment status"
    )
    gateway_response = models.JSONField(
        default=dict,
        help_text="Raw response from payment gateway"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Generate unique reference if not provided."""
        if not self.reference:
            self.reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"Payment {self.reference} - {self.get_status_display()}"
    
    @property
    def amount_display(self) -> str:
        """Return formatted amount."""
        return f"AOA {self.amount:,}"
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == "success"
    
    @property
    def is_refunded(self) -> bool:
        """Check if payment was refunded."""
        return self.status in ["refunded", "partial_refund"]
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']


class Payout(models.Model):
    """Weekly payouts to providers."""
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payouts",
        help_text="Provider receiving the payout"
    )
    week_start = models.DateField(
        help_text="Start date of the week being paid out"
    )
    week_end = models.DateField(
        help_text="End date of the week being paid out"
    )
    amount = models.PositiveIntegerField(
        help_text="Payout amount in AOA"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.15,
        help_text="Platform commission rate (e.g., 0.15 for 15%)"
    )
    commission_amount = models.PositiveIntegerField(
        help_text="Commission amount deducted"
    )
    net_amount = models.PositiveIntegerField(
        help_text="Net amount paid to provider"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Payout status"
    )
    is_disbursed = models.BooleanField(
        default=False,
        help_text="Whether payout has been disbursed"
    )
    disbursement_reference = models.CharField(
        max_length=120,
        blank=True,
        help_text="Bank transfer reference"
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about the payout"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    disbursed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the payout was disbursed"
    )
    
    def save(self, *args, **kwargs):
        """Calculate net amount and week end date."""
        if not self.week_end:
            # Calculate week end (6 days after start)
            self.week_end = self.week_start + timezone.timedelta(days=6)
        
        if not self.commission_amount:
            self.commission_amount = int(self.amount * self.commission_rate)
        
        if not self.net_amount:
            self.net_amount = self.amount - self.commission_amount
        
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"Payout {self.provider.get_full_name()} - {self.week_start}"
    
    @property
    def amount_display(self) -> str:
        """Return formatted amount."""
        return f"AOA {self.amount:,}"
    
    @property
    def net_amount_display(self) -> str:
        """Return formatted net amount."""
        return f"AOA {self.net_amount:,}"
    
    @property
    def week_display(self) -> str:
        """Return formatted week range."""
        return f"{self.week_start} - {self.week_end}"
    
    class Meta:
        verbose_name = 'Payout'
        verbose_name_plural = 'Payouts'
        ordering = ['-week_start']
        unique_together = ['provider', 'week_start']

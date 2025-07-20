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


class ProviderWallet(models.Model):
    """Wallet for tracking provider balances and earnings."""
    
    provider = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="wallet",
        help_text="Provider who owns this wallet"
    )
    available_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Balance available for withdrawal"
    )
    pending_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Balance pending from recent jobs"
    )
    total_withdrawn = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total amount withdrawn all time"
    )
    last_payout_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of last payout"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Wallet - {self.provider.get_full_name()}"
    
    @property
    def total_balance(self):
        """Get total balance (available + pending)."""
        return self.available_balance + self.pending_balance
    
    class Meta:
        verbose_name = 'Provider Wallet'
        verbose_name_plural = 'Provider Wallets'


class EarningsHistory(models.Model):
    """Track daily earnings for providers."""
    
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="earnings_history",
        help_text="Provider who earned this"
    )
    date = models.DateField(
        help_text="Date of earnings"
    )
    jobs_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of jobs completed"
    )
    gross_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total earnings before commission"
    )
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Platform commission"
    )
    tips_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Tips received"
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Net earnings after commission"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Calculate net amount."""
        self.net_amount = self.gross_amount - self.commission_amount + self.tips_amount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.provider.get_full_name()} - {self.date}"
    
    class Meta:
        verbose_name = 'Earnings History'
        verbose_name_plural = 'Earnings Histories'
        unique_together = ['provider', 'date']
        ordering = ['-date']


class PayoutRequest(models.Model):
    """Payout requests from providers."""
    
    TYPE_CHOICES = [
        ("instant", "Instant Payout"),
        ("standard", "Standard Payout"),
    ]
    
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
        related_name="payout_requests",
        help_text="Provider requesting payout"
    )
    payout_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text="Type of payout"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Requested amount"
    )
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Fee for instant payout"
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount after fees"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Request status"
    )
    reference = models.CharField(
        max_length=120,
        unique=True,
        help_text="Unique payout reference"
    )
    bank_reference = models.CharField(
        max_length=120,
        blank=True,
        help_text="Bank transfer reference"
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payout was processed"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payout was completed"
    )
    
    def save(self, *args, **kwargs):
        """Generate reference and calculate fees."""
        if not self.reference:
            self.reference = f"PO-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate fees for instant payout (1.5%)
        if self.payout_type == "instant" and not self.fee_amount:
            self.fee_amount = self.amount * 0.015
        
        # Calculate net amount
        self.net_amount = self.amount - self.fee_amount
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.reference} - {self.provider.get_full_name()}"
    
    class Meta:
        verbose_name = 'Payout Request'
        verbose_name_plural = 'Payout Requests'
        ordering = ['-requested_at']


class RecentTransaction(models.Model):
    """Unified transaction history for users."""
    
    TRANSACTION_TYPE_CHOICES = [
        ("payment", "Payment"),
        ("payout", "Payout"),
        ("refund", "Refund"),
        ("commission", "Commission"),
        ("adjustment", "Adjustment"),
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("earning", "Earning"),
        ("tip", "Tip"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recent_transactions",
        help_text="User associated with this transaction"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction"
    )
    reference = models.CharField(
        max_length=120,
        unique=True,
        help_text="Unique transaction reference"
    )
    amount = models.PositiveIntegerField(
        help_text="Transaction amount in AOA"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Transaction status"
    )
    description = models.CharField(
        max_length=255,
        help_text="Transaction description"
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Related payment record"
    )
    payout = models.ForeignKey(
        Payout,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Related payout record"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional transaction data"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Generate unique reference if not provided."""
        if not self.reference:
            prefix = self.transaction_type[:3].upper()
            self.reference = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} {self.reference} - {self.user.get_full_name()}"
    
    @property
    def amount_display(self) -> str:
        """Return formatted amount."""
        return f"AOA {self.amount:,}"
    
    @property
    def is_credit(self) -> bool:
        """Check if transaction adds money to user's account."""
        return self.transaction_type in ["earning", "tip", "refund", "deposit"]
    
    @property
    def is_debit(self) -> bool:
        """Check if transaction removes money from user's account."""
        return self.transaction_type in ["payout", "payment", "commission", "withdrawal"]
    
    class Meta:
        verbose_name = 'Recent Transaction'
        verbose_name_plural = 'Recent Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
        ]

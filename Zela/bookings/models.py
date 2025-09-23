from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from services.models import ServiceTask
from decimal import Decimal

User = get_user_model()


class Booking(models.Model):
    """Customer bookings for services."""
    
    STATUS_CHOICES = [
        ("pending_confirmation", "Pending Confirmation"),
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings",
        help_text="Customer who made the booking"
    )
    worker = models.ForeignKey(
        'workers.Worker',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        help_text="Worker assigned to this booking"
    )
    service_task = models.ForeignKey(
        ServiceTask,
        on_delete=models.PROTECT,
        help_text="Main service task for this booking"
    )
    extras = models.ManyToManyField(
        ServiceTask,
        related_name="bookings_extras",
        blank=True,
        help_text="Additional services/add-ons"
    )
    
    # Property and unit information for pricing
    property_typology = models.ForeignKey(
        'workers.PropertyTypology',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Property type for typology-based pricing"
    )
    unit_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of units (e.g., AC units)"
    )
    
    # Time tracking
    start_at = models.DateTimeField(
        help_text="When the service should start"
    )
    end_at = models.DateTimeField(
        help_text="When the service should end"
    )
    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual hours worked (for hourly services)"
    )
    
    # Location
    address = models.CharField(
        max_length=255,
        help_text="Service address"
    )
    notes = models.TextField(
        blank=True,
        help_text="Special instructions for the provider"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current booking status"
    )
    
    # Package/credit tracking
    package_used = models.ForeignKey(
        'workers.ServicePackage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        help_text="Package used for this booking"
    )
    credits_consumed = models.PositiveIntegerField(
        default=1,
        help_text="Number of package credits consumed"
    )
    
    # Payment information
    total_price = models.PositiveIntegerField(
        help_text="Total price in AOA including extras"
    )
    amount_prepaid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount paid at booking time"
    )
    amount_pending = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount pending after service"
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final amount after service completion"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"Booking #{self.pk} - {self.customer.get_full_name() or self.customer.username}"
    
    @property
    def is_upcoming(self) -> bool:
        """Check if booking is in the future."""
        return self.start_at > timezone.now()
    
    @property
    def is_past(self) -> bool:
        """Check if booking is in the past."""
        return self.end_at < timezone.now()
    
    @property
    def can_be_cancelled(self) -> bool:
        """Check if booking can still be cancelled."""
        return self.status in ['pending', 'accepted'] and self.is_upcoming
    
    @property
    def can_be_rated(self) -> bool:
        """Check if booking can be rated."""
        return self.status == 'completed' and not hasattr(self, 'rating')
    
    @property
    def duration_hours(self) -> float:
        """Calculate booking duration in hours."""
        if self.start_at and self.end_at:
            delta = self.end_at - self.start_at
            return delta.total_seconds() / 3600
        return 0
    
    @property
    def total_price_display(self) -> str:
        """Return formatted total price."""
        return f"AOA {self.total_price:,}"
    
    @property
    def provider(self):
        """Get provider user from worker for backward compatibility."""
        return self.worker.user if self.worker else None
    
    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']


class Rating(models.Model):
    """Customer ratings for completed bookings."""
    
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        help_text="Booking being rated"
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating score from 1 to 5"
    )
    comment = models.TextField(
        blank=True,
        help_text="Optional comment about the service"
    )
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return f"Rating {self.score}/5 for Booking #{self.booking.pk}"
    
    @property
    def stars_display(self) -> str:
        """Return star representation of rating."""
        return "★" * self.score + "☆" * (5 - self.score)
    
    class Meta:
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        ordering = ['-created']

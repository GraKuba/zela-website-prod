from django.db import models
from django.core.exceptions import ValidationError


class PricingConfig(models.Model):
    """Singleton table to tweak headline prices without code deploy."""
    
    # Service pricing
    hourly_clean_base = models.PositiveIntegerField(
        default=4900,
        help_text="Base hourly rate for cleaning services in AOA"
    )
    specialty_task_price = models.PositiveIntegerField(
        default=3000,
        help_text="Price for specialty tasks in AOA"
    )
    outdoor_min_price = models.PositiveIntegerField(
        default=9000,
        help_text="Minimum price for outdoor services in AOA"
    )
    
    # Placement fees
    placement_fee_domestic = models.PositiveIntegerField(
        default=65000,
        help_text="Placement fee for domestic workers in AOA"
    )
    placement_fee_nanny = models.PositiveIntegerField(
        default=85000,
        help_text="Placement fee for nannies in AOA"
    )
    
    # Additional pricing configurations
    booking_fee = models.PositiveIntegerField(
        default=500,
        help_text="Booking fee in AOA"
    )
    cancellation_fee = models.PositiveIntegerField(
        default=2000,
        help_text="Cancellation fee in AOA"
    )
    
    # Platform commission rates
    provider_commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.15,
        help_text="Commission rate for providers (e.g., 0.15 for 15%)"
    )
    
    # Service multipliers
    weekend_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.2,
        help_text="Weekend service price multiplier"
    )
    holiday_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.5,
        help_text="Holiday service price multiplier"
    )
    
    # Minimum booking amounts
    minimum_booking_amount = models.PositiveIntegerField(
        default=5000,
        help_text="Minimum booking amount in AOA"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Ensure only one PricingConfig instance exists."""
        if not self.pk and PricingConfig.objects.exists():
            raise ValidationError("Only one PricingConfig instance is allowed.")
        return super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"Pricing Configuration (Updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance, creating it if it doesn't exist."""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance
    
    @property
    def hourly_clean_base_display(self) -> str:
        """Return formatted base hourly rate."""
        return f"AOA {self.hourly_clean_base:,}"
    
    @property
    def placement_fee_domestic_display(self) -> str:
        """Return formatted domestic placement fee."""
        return f"AOA {self.placement_fee_domestic:,}"
    
    @property
    def placement_fee_nanny_display(self) -> str:
        """Return formatted nanny placement fee."""
        return f"AOA {self.placement_fee_nanny:,}"
    
    @property
    def commission_rate_percentage(self) -> str:
        """Return commission rate as percentage."""
        return f"{self.provider_commission_rate * 100:.1f}%"
    
    class Meta:
        verbose_name = 'Pricing Configuration'
        verbose_name_plural = 'Pricing Configuration'

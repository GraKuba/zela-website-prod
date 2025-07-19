from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator
from typing import List


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser."""
    
    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("provider", "Provider"),
        ("admin", "Admin"),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="customer",
        help_text="User role in the system"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number for contact"
    )
    locale = models.CharField(
        max_length=5,
        default="pt",
        help_text="User's preferred locale"
    )
    
    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Profile(models.Model):
    """Base profile model for all users."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile", 
        help_text="User account for this profile"
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's first name"
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's last name"
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="User's profile picture"
    )
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications"
    )
    sms_notifications = models.BooleanField(
        default=False,
        help_text="Receive SMS notifications"
    )
    newsletter = models.BooleanField(
        default=True,
        help_text="Subscribe to newsletter"
    )
    marketing_communications = models.BooleanField(
        default=False,
        help_text="Receive marketing communications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} - Profile"
     

class ProviderProfile(models.Model):
    """Extended profile for service providers."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="provider",
        help_text="User account for this provider"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this provider has been approved"
    )
    bio = models.TextField(
        blank=True,
        help_text="Provider's biography"
    )
    skills = models.JSONField(
        default=list,
        help_text="List of skills, e.g. ['cleaning', 'plumbing']"
    )
    service_area = models.CharField(
        max_length=120,
        help_text="Neighbourhood slug where provider operates"
    )
    id_document = models.FileField(
        upload_to="kyc/",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Identity document for KYC verification"
    )
    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="Average rating from customers"
    )
    rating_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of ratings received"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} - Provider"
    
    @property
    def display_rating(self) -> str:
        """Return formatted rating display."""
        if self.rating_count == 0:
            return "No ratings yet"
        return f"{self.rating_average:.1f} ({self.rating_count} reviews)"
    
    class Meta:
        verbose_name = 'Provider Profile'
        verbose_name_plural = 'Provider Profiles'


class PaymentMethod(models.Model):
    class Kind(models.TextChoices):
        CARD = "card", "Card"
        PAYPAL = "paypal", "PayPal"
        APPLE = "apple", "Apple Pay"

    user         = models.ForeignKey(User,
                                     related_name="payment_methods",
                                     on_delete=models.CASCADE,
                                     help_text="User who owns this payment method")
    kind         = models.CharField(max_length=20, choices=Kind.choices,
                                   help_text="Type of payment method")
    provider_id  = models.CharField(max_length=255,
                                   help_text="External provider ID (e.g. Stripe PM token)")
    brand        = models.CharField(max_length=20, blank=True,
                                   help_text="Card brand (Visa, Mastercard, etc)")
    last4        = models.CharField(max_length=4, blank=True,
                                   help_text="Last 4 digits of card number")
    expiry_month = models.PositiveSmallIntegerField(null=True, blank=True,
                                                    help_text="Card expiry month (1-12)")
    expiry_year  = models.PositiveSmallIntegerField(null=True, blank=True,
                                                   help_text="Card expiry year")
    is_default   = models.BooleanField(default=False,
                                      help_text="Default payment method for user")
    is_active    = models.BooleanField(default=True,
                                      help_text="Whether this payment method is active")
    added_at     = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        if self.kind == self.Kind.CARD and self.brand and self.last4:
            return f"{self.brand.title()} •••• {self.last4}"
        return f"{self.get_kind_display()} - {self.user.username}"
    
    @property
    def is_expired(self) -> bool:
        """Check if card is expired."""
        if self.kind != self.Kind.CARD or not self.expiry_month or not self.expiry_year:
            return False
        
        from datetime import datetime
        now = datetime.now()
        # Cards expire at end of month
        return (self.expiry_year < now.year or 
                (self.expiry_year == now.year and self.expiry_month < now.month))
    
    @property
    def display_name(self) -> str:
        """Get display name for payment method."""
        if self.kind == self.Kind.CARD:
            if self.brand and self.last4:
                return f"{self.brand.title()} •••• {self.last4}"
            return "Card"
        return self.get_kind_display()
    
    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        ordering = ['-is_default', '-added_at']
        unique_together = [['user', 'provider_id']]


class Location(models.Model):
    """User location/address model."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="locations",
        help_text="User who owns this location"
    )
    name = models.CharField(
        max_length=100,
        help_text="Location name (e.g., 'Home', 'Office')"
    )
    address_line_1 = models.CharField(
        max_length=255,
        help_text="Street address line 1"
    )
    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Street address line 2 (optional)"
    )
    city = models.CharField(
        max_length=100,
        help_text="City"
    )
    province = models.CharField(
        max_length=100,
        help_text="Province/State"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Postal/ZIP code"
    )
    country = models.CharField(
        max_length=2,
        default="AO",
        help_text="Country code (ISO 3166-1 alpha-2)"
    )
    is_main = models.BooleanField(
        default=False,
        help_text="Is this the main/default location?"
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Latitude coordinate"
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Longitude coordinate"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.name} - {self.address_line_1}, {self.city}"
    
    def save(self, *args, **kwargs):
        """Ensure only one main location per user."""
        if self.is_main:
            # Set all other locations for this user to not main
            Location.objects.filter(user=self.user, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)
    
    @property
    def full_address(self) -> str:
        """Return full formatted address."""
        parts = [self.address_line_1]
        if self.address_line_2:
            parts.append(self.address_line_2)
        parts.extend([self.city, self.province])
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(parts)
    
    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ['-is_main', '-created_at']

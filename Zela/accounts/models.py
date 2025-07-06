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

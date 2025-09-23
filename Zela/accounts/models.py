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
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="User's date of birth"
    )
    national_id_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="National ID number"
    )
    address = models.TextField(
        blank=True,
        help_text="Full address"
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
    """Extended profile for service providers.
    
    DEPRECATED: Use workers.Worker models instead.
    This model is kept for migration compatibility only.
    """
    
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
    
    # Performance statistics
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total earnings from all completed jobs"
    )
    jobs_completed = models.PositiveIntegerField(
        default=0,
        help_text="Total number of completed jobs"
    )
    jobs_total = models.PositiveIntegerField(
        default=0,
        help_text="Total number of jobs assigned"
    )
    completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Job completion rate percentage"
    )
    
    # Availability status
    is_available = models.BooleanField(
        default=True,
        help_text="Whether provider is currently available for work"
    )
    accepts_same_day = models.BooleanField(
        default=True,
        help_text="Whether provider accepts same-day bookings"
    )
    
    # Working hours (stored as JSON)
    working_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Weekly working hours schedule"
    )
    
    # Service areas and coverage
    service_areas = models.JSONField(
        default=list,
        blank=True,
        help_text="List of service areas with surcharges"
    )
    max_travel_distance = models.PositiveIntegerField(
        default=25,
        help_text="Maximum travel distance in kilometers"
    )
    preferred_radius = models.PositiveIntegerField(
        default=15,
        help_text="Preferred working radius in kilometers"
    )
    
    # Travel preferences
    include_traffic_time = models.BooleanField(
        default=True,
        help_text="Include traffic time in travel estimates"
    )
    avoid_tolls = models.BooleanField(
        default=False,
        help_text="Avoid toll roads when possible"
    )
    prefer_main_roads = models.BooleanField(
        default=True,
        help_text="Prefer main roads over shortcuts"
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
    
    def update_completion_rate(self):
        """Update the completion rate based on jobs completed vs total."""
        if self.jobs_total > 0:
            self.completion_rate = (self.jobs_completed / self.jobs_total) * 100
        else:
            self.completion_rate = 0
        self.save(update_fields=['completion_rate'])
    
    def get_default_working_hours(self):
        """Return default working hours structure."""
        return {
            'monday': {'enabled': True, 'start': '08:00', 'end': '18:00'},
            'tuesday': {'enabled': True, 'start': '08:00', 'end': '18:00'},
            'wednesday': {'enabled': True, 'start': '08:00', 'end': '18:00'},
            'thursday': {'enabled': True, 'start': '08:00', 'end': '18:00'},
            'friday': {'enabled': True, 'start': '08:00', 'end': '18:00'},
            'saturday': {'enabled': True, 'start': '09:00', 'end': '16:00'},
            'sunday': {'enabled': False, 'start': '10:00', 'end': '15:00'}
        }
    
    def get_default_service_areas(self):
        """Return default service areas for Luanda."""
        return [
            {'name': 'Luanda Centro', 'enabled': True, 'surcharge': 0, 'color': '#10b981'},
            {'name': 'Maianga', 'enabled': True, 'surcharge': 0, 'color': '#10b981'},
            {'name': 'Ingombota', 'enabled': True, 'surcharge': 5, 'color': '#f59e0b'},
            {'name': 'Rangel', 'enabled': True, 'surcharge': 10, 'color': '#f59e0b'},
            {'name': 'Cazenga', 'enabled': False, 'surcharge': 15, 'color': '#ef4444'},
            {'name': 'Viana', 'enabled': False, 'surcharge': 20, 'color': '#ef4444'}
        ]
    
    class Meta:
        verbose_name = 'Provider Profile'
        verbose_name_plural = 'Provider Profiles'


class ProviderDocument(models.Model):
    """KYC and verification documents for providers.
    
    DEPRECATED: Document verification is now handled in workers.Worker models.
    """
    
    DOCUMENT_TYPES = [
        ('national_id', 'National ID'),
        ('proof_address', 'Proof of Address'),
        ('bank_statement', 'Bank Statement'),
        ('criminal_record', 'Criminal Record Check'),
        ('insurance', 'Insurance Certificate'),
        ('license', 'Professional License'),
        ('other', 'Other Document'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Provider who owns this document"
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        help_text="Type of document"
    )
    file = models.FileField(
        upload_to="kyc_documents/",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Document file"
    )
    file_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original file name"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Document verification status"
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this document is required"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Document expiry date"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection if applicable"
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_documents",
        help_text="Admin who verified this document"
    )
    
    def __str__(self) -> str:
        return f"{self.provider.user.get_full_name()} - {self.get_document_type_display()}"
    
    @property
    def is_expired(self) -> bool:
        """Check if document is expired."""
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False
    
    class Meta:
        verbose_name = "Provider Document"
        verbose_name_plural = "Provider Documents"
        ordering = ['-uploaded_at']
        unique_together = [['provider', 'document_type']]


class ProviderContract(models.Model):
    """Legal contracts and agreements for providers.
    
    DEPRECATED: Contract management is now handled in workers.Worker models.
    """
    
    CONTRACT_TYPES = [
        ('service_agreement', 'Service Provider Agreement'),
        ('privacy_policy', 'Privacy Policy'),
        ('terms_service', 'Terms of Service'),
        ('nda', 'Non-Disclosure Agreement'),
        ('commission_agreement', 'Commission Agreement'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('signed', 'Signed'),
        ('acknowledged', 'Acknowledged'),
        ('expired', 'Expired'),
    ]
    
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="contracts",
        help_text="Provider who signed this contract"
    )
    contract_type = models.CharField(
        max_length=30,
        choices=CONTRACT_TYPES,
        help_text="Type of contract"
    )
    title = models.CharField(
        max_length=255,
        help_text="Contract title"
    )
    version = models.CharField(
        max_length=10,
        help_text="Contract version"
    )
    file = models.FileField(
        upload_to="contracts/",
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Contract PDF file"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Contract status"
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the contract was signed"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when signed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Contract expiry date"
    )
    
    def __str__(self) -> str:
        return f"{self.provider.user.get_full_name()} - {self.title}"
    
    @property
    def is_active(self) -> bool:
        """Check if contract is active."""
        if self.status not in ['signed', 'acknowledged']:
            return False
        if self.expires_at:
            from django.utils import timezone
            return self.expires_at > timezone.now()
        return True
    
    class Meta:
        verbose_name = "Provider Contract"
        verbose_name_plural = "Provider Contracts"
        ordering = ['-created_at']
        unique_together = [['provider', 'contract_type', 'version']]


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


class DistanceRequest(models.Model):
    """Track distance-based service requests to/from workers."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]
    
    worker = models.ForeignKey(
        'workers.Worker',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="distance_requests",
        help_text="Worker who received this request"
    )
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="distance_request",
        help_text="Associated booking if accepted"
    )
    from_location = models.CharField(
        max_length=255,
        help_text="Starting location/neighborhood"
    )
    to_location = models.CharField(
        max_length=255,
        help_text="Service location/neighborhood"
    )
    distance_km = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        help_text="Distance in kilometers"
    )
    surcharge_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Distance surcharge amount"
    )
    service_name = models.CharField(
        max_length=255,
        help_text="Service requested"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Request status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.from_location} → {self.to_location} ({self.distance_km}km)"
    
    class Meta:
        verbose_name = "Distance Request"
        verbose_name_plural = "Distance Requests"
        ordering = ['-created_at']


class UserSettings(models.Model):
    """User settings and preferences."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="settings",
        help_text="User account for these settings"
    )
    
    # Notification Settings
    job_alerts = models.BooleanField(
        default=True,
        help_text="Get notified when new jobs match your preferences"
    )
    payment_alerts = models.BooleanField(
        default=True,
        help_text="Notifications about payments and payouts"
    )
    weekly_reports = models.BooleanField(
        default=True,
        help_text="Summary of your weekly performance"
    )
    push_notifications = models.BooleanField(
        default=True,
        help_text="App notifications on your mobile device"
    )
    system_updates = models.BooleanField(
        default=True,
        help_text="Important system updates and maintenance"
    )
    
    # Privacy Settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('customers', 'Customers Only'),
            ('private', 'Private')
        ],
        default='public',
        help_text="Control who can see your profile information"
    )
    share_location = models.BooleanField(
        default=True,
        help_text="Allow customers to see your approximate location"
    )
    share_statistics = models.BooleanField(
        default=False,
        help_text="Share your performance statistics"
    )
    allow_reviews = models.BooleanField(
        default=True,
        help_text="Let customers leave reviews on your profile"
    )
    data_collection = models.BooleanField(
        default=True,
        help_text="Allow Zela to collect usage data for improvements"
    )
    
    # Work Preferences (Provider Only)
    auto_accept_jobs = models.BooleanField(
        default=False,
        help_text="Automatically accept jobs that match your criteria"
    )
    max_jobs_per_day = models.CharField(
        max_length=10,
        default='5',
        help_text="Maximum jobs per day (number or 'unlimited')"
    )
    preferred_job_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of preferred job types"
    )
    minimum_job_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100,
        help_text="Minimum job value in AOA"
    )
    travel_radius = models.PositiveIntegerField(
        default=15,
        help_text="Travel radius in kilometers"
    )
    
    # App Preferences
    language = models.CharField(
        max_length=5,
        choices=[
            ('pt', 'Português'),
            ('en', 'English'),
            ('fr', 'Français')
        ],
        default='pt',
        help_text="Preferred language"
    )
    timezone = models.CharField(
        max_length=50,
        default='Africa/Luanda',
        help_text="Preferred timezone"
    )
    currency = models.CharField(
        max_length=3,
        choices=[
            ('AOA', 'Kwanza (AOA)'),
            ('USD', 'US Dollar (USD)'),
            ('EUR', 'Euro (EUR)')
        ],
        default='AOA',
        help_text="Preferred currency"
    )
    theme = models.CharField(
        max_length=10,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('auto', 'Auto')
        ],
        default='light',
        help_text="App theme"
    )
    map_view = models.CharField(
        max_length=20,
        choices=[
            ('standard', 'Standard'),
            ('satellite', 'Satellite'),
            ('hybrid', 'Hybrid')
        ],
        default='satellite',
        help_text="Preferred map view"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.user.username} - Settings"
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create settings for a user."""
        settings, created = cls.objects.get_or_create(user=user)
        return settings
    
    class Meta:
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"


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
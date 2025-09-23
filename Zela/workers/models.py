from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

User = get_user_model()


class PropertyTypology(models.Model):
    """Property types for pricing calculations."""
    
    TYPOLOGY_CHOICES = [
        ('T1', 'T1 - 1 Bedroom'),
        ('T2', 'T2 - 2 Bedrooms'),
        ('T3', 'T3 - 3 Bedrooms'),
        ('T4+', 'T4+ - 4+ Bedrooms'),
    ]
    
    name = models.CharField(
        max_length=5,
        choices=TYPOLOGY_CHOICES,
        unique=True,
        help_text="Property typology classification"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this property type"
    )
    typical_sqm = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Typical size in square meters"
    )
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name = "Property Typology"
        verbose_name_plural = "Property Typologies"
        ordering = ['name']


class Worker(models.Model):
    """Base model for all service workers/providers."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
        ('inactive', 'Inactive'),
    ]
    
    # Core relationships
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="worker_profile",
        help_text="User account for this worker"
    )
    
    # Basic information
    bio = models.TextField(
        blank=True,
        help_text="Worker's biography/description"
    )
    years_experience = models.PositiveIntegerField(
        default=0,
        help_text="Years of professional experience"
    )
    languages = models.JSONField(
        default=list,
        help_text="Languages spoken, e.g. ['pt', 'en', 'fr']"
    )
    
    # Verification & Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Worker approval status"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="KYC verification completed"
    )
    background_check = models.BooleanField(
        default=False,
        help_text="Background check completed"
    )
    
    # Documents
    id_document = models.FileField(
        upload_to="worker_docs/id/",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        null=True,
        blank=True,
        help_text="Identity document"
    )
    proof_of_address = models.FileField(
        upload_to="worker_docs/address/",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        null=True,
        blank=True,
        help_text="Proof of address document"
    )
    
    # Performance metrics
    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Average rating (0-5)"
    )
    rating_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of ratings"
    )
    jobs_completed = models.PositiveIntegerField(
        default=0,
        help_text="Total completed jobs"
    )
    jobs_cancelled = models.PositiveIntegerField(
        default=0,
        help_text="Total cancelled jobs"
    )
    completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Job completion percentage"
    )
    
    # Financial
    total_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total earnings in AOA"
    )
    current_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current balance in AOA"
    )
    
    # Availability
    is_available = models.BooleanField(
        default=True,
        help_text="Currently available for work"
    )
    accepts_emergency = models.BooleanField(
        default=False,
        help_text="Accepts emergency/urgent requests"
    )
    accepts_same_day = models.BooleanField(
        default=True,
        help_text="Accepts same-day bookings"
    )
    
    # Service areas & coverage
    service_areas = models.JSONField(
        default=list,
        help_text="List of service area codes/names"
    )
    max_travel_distance = models.PositiveIntegerField(
        default=25,
        help_text="Maximum travel distance in km"
    )
    
    # Working hours (JSON format)
    working_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text="Weekly schedule, e.g. {'monday': {'start': '08:00', 'end': '18:00', 'available': true}}"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.__class__.__name__}"
    
    @property
    def display_rating(self):
        """Formatted rating display."""
        if self.rating_count == 0:
            return "No ratings yet"
        return f"{self.rating_average:.1f} ★ ({self.rating_count})"
    
    @property
    def is_active(self):
        """Check if worker is active and available."""
        return self.status == 'approved' and self.is_available
    
    def update_completion_rate(self):
        """Update completion rate based on jobs."""
        total = self.jobs_completed + self.jobs_cancelled
        if total > 0:
            self.completion_rate = (self.jobs_completed / total) * 100
        else:
            self.completion_rate = 0
        self.save(update_fields=['completion_rate'])
    
    def get_default_working_hours(self):
        """Return default working hours structure."""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        default = {}
        for day in days:
            if day in ['saturday', 'sunday']:
                default[day] = {'start': '09:00', 'end': '15:00', 'available': False}
            else:
                default[day] = {'start': '08:00', 'end': '18:00', 'available': True}
        return default
    
    class Meta:
        verbose_name = "Worker"
        verbose_name_plural = "Workers"
        ordering = ['-created_at']


# Service-specific worker models

class CleaningWorker(Worker):
    """Specialized worker for cleaning services."""
    
    CLEANING_TYPES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('specialized', 'Specialized'),
    ]
    
    specializations = models.JSONField(
        default=list,
        help_text="Cleaning specializations, e.g. ['deep_clean', 'eco_friendly', 'post_construction']"
    )
    cleaning_types = models.CharField(
        max_length=20,
        choices=CLEANING_TYPES,
        default='residential',
        help_text="Primary cleaning type"
    )
    has_own_supplies = models.BooleanField(
        default=False,
        help_text="Brings own cleaning supplies"
    )
    has_own_equipment = models.BooleanField(
        default=False,
        help_text="Has professional cleaning equipment"
    )
    certifications = models.JSONField(
        default=list,
        blank=True,
        help_text="Cleaning certifications"
    )
    
    class Meta:
        verbose_name = "Cleaning Worker"
        verbose_name_plural = "Cleaning Workers"


class ElectricianWorker(Worker):
    """Specialized worker for electrical services."""
    
    license_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Electrical license number"
    )
    license_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="License expiry date"
    )
    voltage_certifications = models.JSONField(
        default=list,
        help_text="Voltage levels certified for, e.g. ['low', 'medium', 'high']"
    )
    specializations = models.JSONField(
        default=list,
        help_text="Specializations, e.g. ['residential', 'commercial', 'industrial', 'solar']"
    )
    minimum_hours = models.PositiveIntegerField(
        default=2,
        help_text="Minimum billable hours"
    )
    typology_rates = models.JSONField(
        default=dict,
        help_text="Hourly rates by property type, e.g. {'T1': 8000, 'T2': 9000, 'T3': 10000, 'T4+': 12000}"
    )
    emergency_surcharge = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('50.00'),
        help_text="Emergency service surcharge percentage"
    )
    
    def get_default_typology_rates(self):
        """Return default typology rates."""
        return {
            'T1': 8000,
            'T2': 9000,
            'T3': 10000,
            'T4+': 12000
        }
    
    class Meta:
        verbose_name = "Electrician"
        verbose_name_plural = "Electricians"


class ACTechnicianWorker(Worker):
    """Specialized worker for AC repair and maintenance."""
    
    hvac_certification = models.CharField(
        max_length=100,
        blank=True,
        help_text="HVAC certification number"
    )
    refrigerant_license = models.CharField(
        max_length=100,
        blank=True,
        help_text="Refrigerant handling license"
    )
    brands_serviced = models.JSONField(
        default=list,
        help_text="AC brands serviced, e.g. ['LG', 'Samsung', 'Daikin']"
    )
    service_types = models.JSONField(
        default=list,
        help_text="Service types offered, e.g. ['installation', 'repair', 'maintenance', 'cleaning']"
    )
    unit_pricing = models.JSONField(
        default=dict,
        help_text="Pricing structure for multiple units"
    )
    has_diagnostic_tools = models.BooleanField(
        default=True,
        help_text="Has professional diagnostic equipment"
    )
    
    def get_default_unit_pricing(self):
        """Return default unit pricing with volume discounts."""
        return {
            '1': 16000,
            '2-3': 14400,  # -10% each
            '4-5': 13600,  # -15% each
            '6+': 12800    # -20% each
        }
    
    class Meta:
        verbose_name = "AC Technician"
        verbose_name_plural = "AC Technicians"


class PestControlWorker(Worker):
    """Specialized worker for pest control services."""
    
    SERVICE_TYPES = [
        ('general', 'General Pest Control'),
        ('deratization', 'Deratization'),
        ('both', 'Both Services'),
    ]
    
    pest_control_license = models.CharField(
        max_length=100,
        blank=True,
        help_text="Pest control license number"
    )
    chemical_certification = models.CharField(
        max_length=100,
        blank=True,
        help_text="Chemical handling certification"
    )
    service_types = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES,
        default='both',
        help_text="Types of pest control offered"
    )
    chemicals_used = models.JSONField(
        default=list,
        help_text="List of approved chemicals used"
    )
    eco_friendly_options = models.BooleanField(
        default=False,
        help_text="Offers eco-friendly pest control"
    )
    typology_pricing = models.JSONField(
        default=dict,
        help_text="Fixed pricing by property type for each service"
    )
    
    def get_default_typology_pricing(self):
        """Return default pricing by typology."""
        return {
            'general': {
                'T1': 10000,
                'T2': 20000,
                'T3': 35000,
                'T4+': 40000
            },
            'deratization': {
                'T1': 18000,
                'T2': 28000,
                'T3': 38000,
                'T4+': 50000
            }
        }
    
    class Meta:
        verbose_name = "Pest Control Worker"
        verbose_name_plural = "Pest Control Workers"


class DogTrainerWorker(Worker):
    """Specialized worker for dog training services."""
    
    TRAINING_METHODS = [
        ('positive', 'Positive Reinforcement'),
        ('balanced', 'Balanced Training'),
        ('clicker', 'Clicker Training'),
        ('behavior', 'Behavioral Modification'),
    ]
    
    certifications = models.JSONField(
        default=list,
        help_text="Training certifications, e.g. ['CCPDT', 'IAABC']"
    )
    training_methods = models.CharField(
        max_length=20,
        choices=TRAINING_METHODS,
        default='positive',
        help_text="Primary training method"
    )
    specializations = models.JSONField(
        default=list,
        help_text="Specializations, e.g. ['puppy', 'aggression', 'obedience', 'service_dog']"
    )
    breed_experience = models.JSONField(
        default=list,
        help_text="Breeds with specific experience"
    )
    max_dogs_per_session = models.PositiveIntegerField(
        default=1,
        help_text="Maximum dogs per training session"
    )
    offers_group_classes = models.BooleanField(
        default=False,
        help_text="Offers group training classes"
    )
    package_offerings = models.JSONField(
        default=dict,
        help_text="Available training packages"
    )
    
    def get_default_package_offerings(self):
        """Return default package offerings."""
        return {
            'evaluation': {'sessions': 1, 'price': 15000, 'name': 'Evaluation Session'},
            'single': {'sessions': 1, 'price': 20000, 'name': 'Single Session'},
            'pack_5': {'sessions': 5, 'price': 90000, 'name': '5-Session Pack'},
            'pack_10': {'sessions': 10, 'price': 160000, 'name': '10-Session Pack'}
        }
    
    class Meta:
        verbose_name = "Dog Trainer"
        verbose_name_plural = "Dog Trainers"


class HandymanWorker(Worker):
    """Specialized worker for general handyman services."""
    
    skills = models.JSONField(
        default=list,
        help_text="Skills list, e.g. ['carpentry', 'painting', 'plumbing_basic', 'furniture_assembly']"
    )
    tools_owned = models.JSONField(
        default=list,
        help_text="Professional tools owned"
    )
    can_source_materials = models.BooleanField(
        default=True,
        help_text="Can source materials for projects"
    )
    project_portfolio = models.URLField(
        blank=True,
        help_text="Link to portfolio/gallery"
    )
    hourly_rate = models.PositiveIntegerField(
        default=7000,
        help_text="Standard hourly rate in AOA"
    )
    
    class Meta:
        verbose_name = "Handyman"
        verbose_name_plural = "Handymen"


class GardenerWorker(Worker):
    """Specialized worker for gardening and landscaping."""
    
    services_offered = models.JSONField(
        default=list,
        help_text="Services, e.g. ['lawn_care', 'tree_trimming', 'landscaping', 'irrigation']"
    )
    equipment_owned = models.JSONField(
        default=list,
        help_text="Equipment owned, e.g. ['mower', 'trimmer', 'chainsaw']"
    )
    plant_knowledge = models.JSONField(
        default=list,
        help_text="Plant expertise, e.g. ['tropical', 'succulents', 'vegetables']"
    )
    pesticide_license = models.CharField(
        max_length=100,
        blank=True,
        help_text="Pesticide application license"
    )
    landscape_design = models.BooleanField(
        default=False,
        help_text="Offers landscape design services"
    )
    
    class Meta:
        verbose_name = "Gardener"
        verbose_name_plural = "Gardeners"


class PlacementWorker(Worker):
    """Specialized worker for full-time domestic placements."""
    
    PLACEMENT_TYPES = [
        ('live_in', 'Live-in'),
        ('live_out', 'Live-out'),
        ('both', 'Both'),
    ]
    
    placement_type = models.CharField(
        max_length=20,
        choices=PLACEMENT_TYPES,
        default='both',
        help_text="Type of placement offered"
    )
    domestic_skills = models.JSONField(
        default=list,
        help_text="Skills, e.g. ['cooking', 'childcare', 'elderly_care', 'housekeeping']"
    )
    cooking_specialties = models.JSONField(
        default=list,
        blank=True,
        help_text="Cooking specialties/cuisines"
    )
    childcare_experience = models.BooleanField(
        default=False,
        help_text="Has childcare experience"
    )
    first_aid_certified = models.BooleanField(
        default=False,
        help_text="First aid certification"
    )
    drivers_license = models.BooleanField(
        default=False,
        help_text="Has driver's license"
    )
    minimum_contract_months = models.PositiveIntegerField(
        default=6,
        help_text="Minimum contract duration in months"
    )
    expected_salary = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Expected monthly salary in AOA"
    )
    placement_fee = models.PositiveIntegerField(
        default=75000,
        help_text="One-time placement fee in AOA"
    )
    
    class Meta:
        verbose_name = "Placement Worker"
        verbose_name_plural = "Placement Workers"


# Service Package for credit-based services

class WorkerService(models.Model):
    """Link between workers and service categories they can provide."""
    
    worker = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name="worker_services",
        help_text="Worker who can provide this service"
    )
    service_category = models.ForeignKey(
        'services.ServiceCategory',
        on_delete=models.CASCADE,
        related_name="worker_services",
        help_text="Service category the worker can provide"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether worker's ability to provide this service is verified"
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Priority for this worker in this service category (higher = better match)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.worker} - {self.service_category}"
    
    class Meta:
        verbose_name = "Worker Service"
        verbose_name_plural = "Worker Services"
        unique_together = ['worker', 'service_category']
        ordering = ['-priority', 'created_at']


class WorkerServicePricing(models.Model):
    """Custom pricing for specific worker-service combinations."""
    
    worker_service = models.OneToOneField(
        WorkerService,
        on_delete=models.CASCADE,
        related_name="custom_pricing",
        help_text="Worker-service relationship this pricing applies to"
    )
    pricing_config = models.JSONField(
        default=dict,
        help_text="Custom pricing configuration overriding service defaults"
    )
    markup_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Markup percentage above base price (-50 to +200)"
    )
    minimum_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum price for this worker-service combination"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this custom pricing is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Pricing: {self.worker_service}"
    
    def calculate_price(self, base_price):
        """Calculate final price with markup."""
        if not self.is_active:
            return base_price
        
        # Apply markup percentage
        final_price = base_price * (1 + (self.markup_percentage / 100))
        
        # Apply minimum price if set
        if self.minimum_price:
            final_price = max(final_price, self.minimum_price)
        
        return int(final_price)
    
    class Meta:
        verbose_name = "Worker Service Pricing"
        verbose_name_plural = "Worker Service Pricing"


class ServicePackage(models.Model):
    """Pre-purchased service packages/credits."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('depleted', 'Depleted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="service_packages",
        help_text="Customer who purchased the package"
    )
    worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="packages_sold",
        help_text="Worker providing the service"
    )
    package_name = models.CharField(
        max_length=100,
        help_text="Name of the package, e.g. '5-Session Pack'"
    )
    package_type = models.CharField(
        max_length=50,
        help_text="Type identifier, e.g. 'dog_training_5'"
    )
    total_credits = models.PositiveIntegerField(
        help_text="Total sessions/credits in package"
    )
    used_credits = models.PositiveIntegerField(
        default=0,
        help_text="Credits already used"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount paid for package"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Package status"
    )
    purchase_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Package expiration date"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the package"
    )
    
    @property
    def remaining_credits(self):
        """Calculate remaining credits."""
        return self.total_credits - self.used_credits
    
    @property
    def is_active(self):
        """Check if package is active and usable."""
        if self.status != 'active':
            return False
        if self.remaining_credits <= 0:
            return False
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date > timezone.now()
        return True
    
    def use_credit(self, amount=1):
        """Use credits from the package."""
        if self.remaining_credits >= amount:
            self.used_credits += amount
            if self.remaining_credits == 0:
                self.status = 'depleted'
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.package_name} - {self.customer.username} ({self.remaining_credits}/{self.total_credits})"
    
    class Meta:
        verbose_name = "Service Package"
        verbose_name_plural = "Service Packages"
        ordering = ['-purchase_date']

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class PricingModel(models.TextChoices):
    """Available pricing models for services."""
    FIXED = 'fixed', 'Fixed Price'
    HOURLY = 'hourly', 'Hourly Rate'
    HOURLY_MINIMUM = 'hourly_min', 'Hourly with Minimum'
    PER_UNIT = 'per_unit', 'Per Unit Pricing'
    PACKAGE = 'package', 'Package/Credits'
    TYPOLOGY_BASED = 'typology', 'Property-Based'


class ServiceCategory(models.Model):
    """Service categories like 'Cleaning', 'Plumbing', etc."""
    
    WORKER_MODEL_CHOICES = [
        ('CleaningWorker', 'Cleaning Worker'),
        ('ElectricianWorker', 'Electrician'),
        ('ACTechnicianWorker', 'AC Technician'),
        ('PestControlWorker', 'Pest Control'),
        ('DogTrainerWorker', 'Dog Trainer'),
        ('HandymanWorker', 'Handyman'),
        ('GardenerWorker', 'Gardener'),
        ('PlacementWorker', 'Placement Worker'),
    ]
    
    name = models.CharField(
        max_length=80,
        unique=True,
        help_text="Category name (e.g., 'House Cleaning')"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly version of the name"
    )
    icon = models.CharField(
        max_length=40,
        help_text="Heroicon/Lucide icon key (e.g., 'home', 'wrench')"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description for the category"
    )
    worker_model_type = models.CharField(
        max_length=50,
        choices=WORKER_MODEL_CHOICES,
        blank=True,
        help_text="Type of worker model for this category"
    )
    pricing_model = models.CharField(
        max_length=20,
        choices=PricingModel.choices,
        default=PricingModel.FIXED,
        help_text="Default pricing model for this category"
    )
    booking_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Special requirements for booking, e.g. {'minimum_hours': 2, 'requires_property_type': true}"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return URL for service detail page."""
        return reverse('service-detail', kwargs={'slug': self.slug})
    
    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name = 'Service Category'
        verbose_name_plural = 'Service Categories'
        ordering = ['order', 'name']


class ServiceTask(models.Model):
    """Individual tasks within a service category."""
    
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="tasks",
        help_text="Service category this task belongs to"
    )
    name = models.CharField(
        max_length=100,
        help_text="Task name (e.g., 'Deep Clean', 'Basic Clean')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the task"
    )
    price = models.PositiveIntegerField(
        help_text="Base price in AOA (Angolan Kwanza)"
    )
    pricing_model = models.CharField(
        max_length=20,
        choices=PricingModel.choices,
        blank=True,
        help_text="Override category pricing model for this task"
    )
    pricing_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible pricing configuration based on pricing model"
    )
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        help_text="Estimated duration in hours"
    )
    skill_requirements = models.JSONField(
        default=list,
        blank=True,
        help_text="Required skills for workers, e.g. ['electrical_license', 'hvac_cert']"
    )
    equipment_requirements = models.JSONField(
        default=list,
        blank=True,
        help_text="Required equipment, e.g. ['diagnostic_tools', 'cleaning_supplies']"
    )
    certification_requirements = models.JSONField(
        default=list,
        blank=True,
        help_text="Required certifications"
    )
    is_addon = models.BooleanField(
        default=False,
        help_text="Whether this task is an add-on service"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this task is available for booking"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_pricing_model(self):
        """Get the effective pricing model (task override or category default)."""
        return self.pricing_model or self.category.pricing_model
    
    def get_sample_pricing_config(self):
        """Return sample pricing config based on pricing model."""
        model = self.get_pricing_model()
        if model == PricingModel.HOURLY_MINIMUM:
            return {
                'minimum_hours': 2,
                'typology_rates': {
                    'T1': 8000,
                    'T2': 9000,
                    'T3': 10000,
                    'T4+': 12000
                }
            }
        elif model == PricingModel.PER_UNIT:
            return {
                'base_price': 16000,
                'volume_discounts': {
                    '1': 0,
                    '2-3': 10,
                    '4-5': 15,
                    '6+': 20
                }
            }
        elif model == PricingModel.TYPOLOGY_BASED:
            return {
                'T1': 10000,
                'T2': 20000,
                'T3': 35000,
                'T4+': 40000
            }
        elif model == PricingModel.PACKAGE:
            return {
                'packages': [
                    {'name': 'Evaluation', 'sessions': 1, 'price': 15000},
                    {'name': 'Single', 'sessions': 1, 'price': 20000},
                    {'name': '5-Pack', 'sessions': 5, 'price': 90000},
                    {'name': '10-Pack', 'sessions': 10, 'price': 160000}
                ]
            }
        return {}
    
    def __str__(self) -> str:
        return f"{self.category.name} - {self.name}"
    
    @property
    def price_display(self) -> str:
        """Return formatted price display."""
        return f"AOA {self.price:,}"
    
    class Meta:
        verbose_name = 'Service Task'
        verbose_name_plural = 'Service Tasks'
        ordering = ['category__order', 'order', 'name']
        unique_together = ['category', 'name']

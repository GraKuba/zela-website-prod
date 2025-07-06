from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class ServiceCategory(models.Model):
    """Service categories like 'Cleaning', 'Plumbing', etc."""
    
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
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        help_text="Estimated duration in hours"
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

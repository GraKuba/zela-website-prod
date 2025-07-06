from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class PlacementInquiry(models.Model):
    """Long-term placement inquiries for domestic workers, nannies, etc."""
    
    ROLE_CHOICES = [
        ("nanny", "Nanny"),
        ("housekeeper", "Housekeeper"),
        ("elder_care", "Elder Care"),
        ("cook", "Cook"),
        ("gardener", "Gardener"),
        ("driver", "Driver"),
        ("general_helper", "General Helper"),
    ]
    
    STATUS_CHOICES = [
        ("open", "Open"),
        ("shortlist_sent", "Shortlist Sent"),
        ("interview_scheduled", "Interview Scheduled"),
        ("contracted", "Contracted"),
        ("closed", "Closed"),
        ("cancelled", "Cancelled"),
    ]
    
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="Customer making the inquiry"
    )
    role = models.CharField(
        max_length=40,
        choices=ROLE_CHOICES,
        help_text="Type of placement needed"
    )
    live_in = models.BooleanField(
        help_text="Whether the placement is live-in"
    )
    start_date = models.DateField(
        help_text="When the placement should start"
    )
    location = models.CharField(
        max_length=255,
        help_text="Location where services will be provided"
    )
    budget_min = models.PositiveIntegerField(
        help_text="Minimum budget in AOA per month"
    )
    budget_max = models.PositiveIntegerField(
        help_text="Maximum budget in AOA per month"
    )
    requirements = models.TextField(
        help_text="Specific requirements and preferences"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or special instructions"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        help_text="Current status of the inquiry"
    )
    urgency = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        default="medium",
        help_text="Urgency level of the placement"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"Placement: {self.get_role_display()} for {self.customer.get_full_name()}"
    
    @property
    def is_active(self) -> bool:
        """Check if inquiry is still active."""
        return self.status in ["open", "shortlist_sent", "interview_scheduled"]
    
    @property
    def is_urgent(self) -> bool:
        """Check if inquiry is urgent."""
        return self.urgency in ["high", "urgent"]
    
    @property
    def budget_range_display(self) -> str:
        """Return formatted budget range."""
        return f"AOA {self.budget_min:,} - AOA {self.budget_max:,}"
    
    @property
    def days_since_created(self) -> int:
        """Calculate days since inquiry was created."""
        return (timezone.now().date() - self.created_at.date()).days
    
    class Meta:
        verbose_name = 'Placement Inquiry'
        verbose_name_plural = 'Placement Inquiries'
        ordering = ['-created_at']
